import sys
import time
from typing import Any, cast
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
import json
import psutil
import cloudpickle
from rich import print as rprint
from random import Random
import numpy as np
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure, Logger, KVWriter
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import BaseCallback, LogEveryNTimesteps
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.evaluation import evaluate_policy
from part2.ai.gym.environment import make_train_game_environment_fn, GameEnvironment
from part2.game.player import ActionStyle
from part2.game.game import GameStatus
from part2.config import (
        MODELS_DIR,
        MODELS_TRAIN_TEMP_DIR,
        TRAIN_LOG_DIR,
        FPS)

ENV_HYPERPARAMS_CONFIG_FILE: Path = Path(__file__).resolve().parents[1] / "rl_env_hparams.json"
MODEL_HYPERPARAMS_CONFIG_FILE: Path = Path(__file__).resolve().parents[1] / "rl_model_hparams.json"
TRAIN_HYPERPARAMS_CONFIG_FILE: Path = Path(__file__).resolve().parents[1] / "rl_train_hparams.json"


class LearningAlgorithmType(Enum):
    PPO = 0  # Promixal Policy Optimization (on-policy).
    DQN = 1  # Deep Q-Networks (off-policy).


class GameEnvironmentPhaseCallback(BaseCallback):
    def __init__(self, win_rate_threshold: float, n_episodes: int, verbose: int = 0):
        """
        Advances the environment phase when a target win rate is reached within
        the last `n_episodes`.
        """
        super().__init__(verbose)
        self.win_rate_threshold: float = win_rate_threshold
        self.n_episodes: int = n_episodes
        self.episode_results: list[bool] = []
        self.current_phase_index: int = 0

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
            if info["game_status"] == GameStatus.GAME_WON:
                self.episode_results.append(True)
            if info["game_status"] == GameStatus.GAME_LOST:
                self.episode_results.append(False)

        if len(self.episode_results) >= self.n_episodes:
            self.episode_results = self.episode_results[-self.n_episodes:]
            win_rate: float = sum(self.episode_results) / len(self.episode_results)
            if win_rate >= self.win_rate_threshold:
                self.current_phase_index: int = self.training_env.get_attr("current_phase_index")[0]
                next_phase_index: int = self.current_phase_index + 1
                phases_count: int = len(self.training_env.get_attr("phases")[0])
                if next_phase_index < phases_count - 1:
                    self.training_env.env_method("set_phase", next_phase_index)
                    self.episode_results.clear()
                    if self.verbose > 2:
                        rprint("[green]-> Win rate %.2f/%.2f (last %d eps) current training phase (%d). Progress to next training phase (%d).[/green]" % (
                            win_rate,
                            self.win_rate_threshold,
                            self.n_episodes,
                            self.current_phase_index,
                            next_phase_index,
                        ))

        return super()._on_step()


class PPOLinearEntCoefDecayCallback(BaseCallback):
    def __init__(self, initial_ent_coef: float, total_timesteps: int, verbose: int = 0):
        super().__init__(verbose)
        self.initial_ent_coef: float = initial_ent_coef
        self.total_timesteps: float = total_timesteps

    def _on_step(self) -> bool:
        if isinstance(self.model, PPO):
            progress_remaining: float = max(0.0, 1.0 - (self.num_timesteps / self.total_timesteps))
            self.model.ent_coef = self.initial_ent_coef * progress_remaining
            self.logger.record("train/ent_coef", self.model.ent_coef)
        return super()._on_step()


class EvalBestModelCallback(BaseCallback):
    def __init__(self,
            eval_model: Any,
            temp_file_path: Path,
            eval_env: Monitor,
            eval_freq: int = FPS,
            n_eval_episodes = 10,
            verbose: int = 0
    ):
        """
        Keeps track of the best model and saves it in a temporary
        `temp_file_path`. Evaluation happens every `eval_freq` calls for
        `n_eval_episodes`.

        The best model is the one with the highest current mean reward per
        episode (logged as `mean_rew_ep`) after evaluation of
        `n_eval_episodes`.
        """
        super().__init__(verbose)
        self.eval_model: Any = eval_model
        self.best_model_temp_file_path: Path = temp_file_path
        self.eval_env: Monitor = eval_env
        self.eval_freq: int = eval_freq
        self.n_eval_episodes: int = n_eval_episodes
        self.best_model_at_step: int = 0
        self.best_mean_rew_ep: float = float("-inf")
        self.best_std_rew_ep: float = float("inf")

    def _init_callback(self) -> None:
        self.eval_model.save(self.best_model_temp_file_path)
        return super()._init_callback()

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq == 0:
            if not isinstance(self.eval_env.unwrapped, GameEnvironment):
                raise TypeError("`self.eval_env.unwrapped` must be of type GameEnvironment.")

            unwrapped_eval_env: GameEnvironment = self.eval_env.unwrapped
            mean_rew_eps: list[float] = []
            phase_index: int
            for phase_index in range(len(unwrapped_eval_env.phases)):
                unwrapped_eval_env.set_phase(phase_index)
                phase_mean_rew_ep, _ = evaluate_policy(
                        model=self.eval_model,
                        env=self.eval_env,
                        n_eval_episodes=self.n_eval_episodes,
                        deterministic=True)
                mean_rew_eps.append(cast(float, phase_mean_rew_ep))

            mean_rew_ep: float = float(np.mean(mean_rew_eps))
            std_rew_ep: float = float(np.std(mean_rew_eps))

            self.logger.record("eval/mean_rew_ep", mean_rew_ep)
            self.logger.record("eval/std_rew_ep", std_rew_ep)

            if mean_rew_ep > self.best_mean_rew_ep:
                self.best_model_at_step = self.num_timesteps
                self.best_mean_rew_ep = mean_rew_ep
                self.best_std_rew_ep = std_rew_ep
                self.eval_model.save(self.best_model_temp_file_path)

            self.logger.record("eval/best_model_at_step", self.best_model_at_step)
            self.logger.record("eval/best_mean_rew_ep", self.best_mean_rew_ep)
            self.logger.record("eval/best_std_rew_ep", self.best_std_rew_ep)

            self.logger.dump(step=self.num_timesteps)

            if self.verbose > 1:
                log_dict: dict[str, Any] = {
                    "step": self.num_timesteps,
                    "eval/mean_rew_ep": mean_rew_ep,
                    "eval/std_rew_ep": std_rew_ep,
                    "eval/best_model_at_step": self.best_model_at_step,
                    "eval/best_mean_rew_ep": self.best_mean_rew_ep,
                    "eval/best_std_rew_ep": self.best_std_rew_ep,
                }
                CYAN = "\033[36m"
                RESET = "\033[0m"
                sys.stdout.write("%sEvalStats%s%s\n" % (CYAN, json.dumps(log_dict), RESET))
                sys.stdout.flush()
        return super()._on_step()


class CompactStdoutWriter(KVWriter):
    def write(self, key_values: dict[str, Any], *args, **kwargs) -> None:
        log_dict: dict[str, Any] = {}

        key: str
        value: Any
        for key, value in key_values.items():
            if isinstance(value, (dict, list)):
                continue

            if isinstance(value, np.generic):
                log_dict[key] = value.item()
            else:
                log_dict[key] = value

        sys.stdout.write("TrainStats%s\n" % json.dumps(log_dict))
        sys.stdout.flush()

    def close(self) -> None:
        pass


def generate_curriculum_phases(
        n_phases: int,
        enemy_spawner_count_range: tuple[int, int],
        enemy_spawner_health_range: tuple[int, int],
        enemy_spawner_spawn_amount_range: tuple[int, int],
        enemy_spawner_spawn_delay_range: tuple[float, float],
        enemy_spawner_spawn_delay_max_deviation: float,
        enemy_spawner_activation_delay_range: tuple[float, float],
        enemy_spawner_activation_delay_max_deviation: float,
        max_enemy_count_range: tuple[int, int],
        seed: int = 0
) -> list[dict[str, Any]]:
    """
    Returns a list of pseudo-randomly generated (`seed` provided) sequential
    phase layouts for curriculum training. Ramps difficulty linearly over
    `n_phases` using the provided configuration kwargs.
    """
    def _lerp(v0: float, v1: float, t: float) -> float:
        return (1 - t) * v0 + t * v1

    rng: Random = Random(seed)
    phases: list[dict[str, Any]] = []
    for i in range(n_phases):
        t: float = i / max(1, n_phases - 1)
        phase: dict[str, Any] = {}

        phase["phase_name"] = "%d" % (i)
        phase["player_position"] = {
            "x": 0,  # Placeholder. Will be randomized by make_train_game_environment_fn.
            "y": 0,  # Placeholder. Will be randomized by make_train_game_environment_fn.
        }

        enemy_spawner_count: int = round(_lerp(*(*enemy_spawner_count_range, t)))
        enemy_spawner_health: int = round(_lerp(*(*enemy_spawner_health_range, t)))
        enemy_spawner_spawn_amount: int = round(_lerp(*(*enemy_spawner_spawn_amount_range, t)))
        phase["enemy_spawners"] = []
        for _ in range(enemy_spawner_count):
            enemy_spawner: dict[str, Any] = {
                "position": {
                    "x": 0,  # Placeholder. Will be randomized by make_train_game_environment_fn.
                    "y": 0,  # Placeholder. Will be randomized by make_train_game_environment_fn.
                },
                "health": enemy_spawner_health,
                "spawn_amount": enemy_spawner_spawn_amount,
                "spawn_delay": max(
                        0.0,
                        (
                            round(_lerp(*(*enemy_spawner_spawn_delay_range, t)), 1)
                            + rng.uniform(-enemy_spawner_spawn_delay_max_deviation, enemy_spawner_spawn_delay_max_deviation)
                        )),
                "activation_delay": max(
                        0.0,
                        (
                            round(_lerp(*(*enemy_spawner_activation_delay_range, t)), 1))
                            + rng.uniform(-enemy_spawner_activation_delay_max_deviation, enemy_spawner_activation_delay_max_deviation)
                        ),
            }
            phase["enemy_spawners"].append(enemy_spawner)

        phase["max_enemies"] = _lerp(*(*max_enemy_count_range, t))

        phases.append(phase)
    return phases


def train(
        action_style: ActionStyle,
        algorithm: LearningAlgorithmType,
        seed: int = 0,
        n_threads: int = 1,
        device: str = "auto",
        output_model: Path | None = None,
        verbose: int = 0
) -> None:
    rprint("[bold yellow][ MODE: TRAIN ][/bold yellow]")

    # ====== Bootstraping ======
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_TRAIN_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    TRAIN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    if verbose > 2:
        print("Default MODEL_DIR='%s'" % (str(MODELS_DIR)))
        print("Default MODELS_TRAIN_TEMP_DIR='%s'" % (str(MODELS_TRAIN_TEMP_DIR)))
        print("Default TRAIN_LOG_DIR='%s'" % (str(TRAIN_LOG_DIR)))

    set_random_seed(seed=seed, using_cuda=(device=="cuda"))
    if verbose > 0:
        rprint("[blue]-> RNG randomized.[/blue]")

    if device in ["cpu", "meta", "xla", "xpu", "mkldnn"]:
        available_cpu_count: int = len(psutil.Process().cpu_affinity())
        if not 0 < n_threads <= available_cpu_count:
            raise ValueError("`n_threads` exceeds of number of available CPU cores (%d)." % (available_cpu_count))

    algorithm_name_str: str = algorithm.name
    action_style_name_str: str = ""
    action_style_filename_str: str = ""
    match action_style:
        case ActionStyle.STYLE_A:
            action_style_name_str = "Control Style 1"
            action_style_filename_str = "control_style_1"
        case ActionStyle.STYLE_B:
            action_style_name_str = "Control Style 2"
            action_style_filename_str = "control_style_2"
    _output_model: Path = (
        output_model if output_model
        else MODELS_DIR / ("%s.%s.pkl" % (algorithm_name_str.lower(), action_style_filename_str))
    )
    train_log_subdir: Path = TRAIN_LOG_DIR / (
        "%s.%s.%d.log" % (
            algorithm_name_str.lower(),
            action_style_filename_str,
            int(time.time())
        )
    )
    train_log_subdir.mkdir(parents=True, exist_ok=True)

    env_hyperparams: dict[str, Any]
    with open(ENV_HYPERPARAMS_CONFIG_FILE, "r") as file:
        env_hyperparams = json.load(file)
    model_hyperparams: dict[str, Any]
    with open(MODEL_HYPERPARAMS_CONFIG_FILE, "r") as file:
        model_hyperparams = json.load(file)
    train_hyperparams: dict[str, Any]
    with open(TRAIN_HYPERPARAMS_CONFIG_FILE, "r") as file:
        train_hyperparams = json.load(file)
    # ==========================

    # === Environment Config ===
    # Include support for multi-process parallel training.
    train_curriculum_phases: list[dict[str, Any]] = generate_curriculum_phases(
            **train_hyperparams["train_curriculum"],
            seed=seed+10)
    train_curriculum_datadump_file: Path = train_log_subdir / "train_curriculum.json"
    with open(train_curriculum_datadump_file, "w", encoding="utf-8") as file:
        json.dump(train_curriculum_phases, file, indent=4)
    if verbose > 2:
        print("Train curriculum generated (%d phases). Datadump at '%s'." % (
            len(train_curriculum_phases),
            str(train_curriculum_datadump_file)
        ))

    vec_env: SubprocVecEnv = SubprocVecEnv([
        make_train_game_environment_fn(
                action_style=action_style,
                phases=train_curriculum_phases,
                seed=seed + env_index,
                max_steps=env_hyperparams["max_steps_episode"])
        for env_index in range(n_threads)
    ])
    env_phase_callback: GameEnvironmentPhaseCallback = GameEnvironmentPhaseCallback(
            win_rate_threshold=env_hyperparams["phase_progress_win_rate_threshold"],
            n_episodes=env_hyperparams["phase_progress_win_rate_episode_memory"],
            verbose=verbose
    )
    if verbose > 1:
        rprint("[blue]-> Environment loaded (config: '%s'):[/blue]" % (
            str(ENV_HYPERPARAMS_CONFIG_FILE)
        ))
        print(json.dumps(env_hyperparams, indent=2))
    elif verbose > 0:
        rprint("[blue]-> Environment loaded.[/blue]")
    # ==========================

    # ====== Logger Config ======
    logger: Logger = configure(str(train_log_subdir), ["csv", "tensorboard"])
    if verbose > 1:
        logger.output_formats.append(CompactStdoutWriter())
        rprint("[blue]-> Log output at: '%s'.[/blue]" % (str(train_log_subdir)))
    # ==========================

    # ====== Model Config ======
    model: BaseAlgorithm
    match algorithm:
        case LearningAlgorithmType.PPO:
            model_class: type[BaseAlgorithm] = PPO
            model = PPO(
                    policy="MlpPolicy",
                    env=vec_env,
                    **model_hyperparams["PPO"],
                    verbose=verbose,
                    device=device)
            if verbose > 1:
                rprint("[blue]-> PPO model initialized (config: '%s'):.[/blue]" % (str(MODEL_HYPERPARAMS_CONFIG_FILE)))
                print(json.dumps(model_hyperparams["PPO"], indent=2))
            elif verbose > 0:
                rprint("[blue]-> PPO model initialized.[/blue]")

        case LearningAlgorithmType.DQN:
            model_class: type[BaseAlgorithm] = DQN
            model = DQN(
                    policy="MlpPolicy",
                    env=vec_env,
                    **model_hyperparams["DQN"],
                    verbose=verbose,
                    device=device)

            if verbose > 1:
                rprint("[blue]-> DQN model initialized (config: '%s'):.[/blue]" % (str(MODEL_HYPERPARAMS_CONFIG_FILE)))
                print(json.dumps(model_hyperparams["DQN"], indent=2))
            elif verbose > 0:
                rprint("[blue]-> DQN Model initialized.[/blue]")
    model.set_logger(logger)
    # ==========================

    # ======== Training ========
    if verbose > 1:
        rprint("[green]-> Training started on %d thread(s) (config: '%s'):.[/green]" % (
            n_threads,
            str(TRAIN_HYPERPARAMS_CONFIG_FILE)
        ))
        print(json.dumps(train_hyperparams, indent=2))
    else:
        rprint("[green]-> Training started on %d thread(s).[/green]" % (n_threads))

    best_model_temp_file: _TemporaryFileWrapper = NamedTemporaryFile(
            suffix=".zip",
            dir=MODELS_TRAIN_TEMP_DIR,
            delete=False)
    best_model_temp_file_path: Path = Path(best_model_temp_file.name)
    best_model_temp_file.close()
    if verbose > 1:
        print("Tempfile: '%s'" % (str(best_model_temp_file_path)))

    ppo_linear_ent_coef_decay_callback: PPOLinearEntCoefDecayCallback = PPOLinearEntCoefDecayCallback(
            initial_ent_coef=model_hyperparams["PPO"]["ent_coef"],
            total_timesteps=train_hyperparams["total_timesteps"],
            verbose=verbose)

    eval_curriculum_phases: list[dict[str, Any]] = generate_curriculum_phases(
            **train_hyperparams["eval_curriculum"],
            seed=seed+100)
    eval_curriculum_datadump_file: Path = train_log_subdir / "eval_curriculum.json"
    with open(eval_curriculum_datadump_file, "w", encoding="utf-8") as file:
        json.dump(eval_curriculum_phases, file, indent=4)
    if verbose > 2:
        print("Eval curriculum generated (%d phases). Datadump at '%s'." % (
            len(eval_curriculum_phases),
            str(eval_curriculum_datadump_file)
        ))
    eval_best_model_callback: EvalBestModelCallback = EvalBestModelCallback(
            eval_model=model,
            temp_file_path=best_model_temp_file_path,
            eval_env=Monitor(GameEnvironment(
                    action_style=action_style,
                    phases=eval_curriculum_phases,
                    random_agent_position=True,
                    random_agent_rotation=True,
                    random_enemy_spawner_positions=True,
                    max_steps=env_hyperparams["max_steps_episode"])),
            eval_freq=train_hyperparams["eval_freq"],
            n_eval_episodes=train_hyperparams["n_eval_episodes"],
            verbose=verbose)

    model.learn(
            total_timesteps=train_hyperparams["total_timesteps"],
            callback=[
                env_phase_callback,
                ppo_linear_ent_coef_decay_callback,
                eval_best_model_callback,
                LogEveryNTimesteps(train_hyperparams["log_freq"]),
            ],
            progress_bar=(verbose > 1))

    rprint("[green]-> Training finished.[/green]")
    if verbose > 0:
        train_phases_cleared: int = env_phase_callback.current_phase_index + 1
        print("Phases cleared (train curriculum): %d/%d (%.2f)%%" % (
            train_phases_cleared,
            len(train_curriculum_phases),
            train_phases_cleared / len(train_curriculum_phases) * 100.0,
        ))
        print("Best model at step: %d" % (eval_best_model_callback.best_model_at_step))
        print("Best mean_rew_ep (eval): %.2f" % (eval_best_model_callback.best_mean_rew_ep))
        print("Best std_rew_ep (eval): %.2f" % (eval_best_model_callback.best_std_rew_ep))
    # ==========================

    # ====== Model Export ======
    best_model: Any = model_class.load(eval_best_model_callback.best_model_temp_file_path)
    best_model.env = None
    best_model.n_envs = 0
    with open(_output_model, "wb") as file:
        model_pkl: dict[str, Any] = {
            "model": best_model,
            "metadata": {
                "algorithm": algorithm_name_str,
                "control_style": action_style_name_str,
            },
        }
        cloudpickle.dump(model_pkl, file)
    if verbose > 0:
        rprint("[magenta]-> Saved model to '%s'.[/magenta]" % (str(_output_model)))

    best_model_temp_file_path.unlink()
    # ==========================

    rprint("[bold yellow][ DONE ][/bold yellow]")
