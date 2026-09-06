import sys
from typing import Any
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
import json
import psutil
import cloudpickle
from rich import print as rprint
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure, Logger, KVWriter
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import BaseCallback, LogEveryNTimesteps
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.evaluation import evaluate_policy
from part2.ai.gym.environment import make_environment_fn, GameEnvironment
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
                phases_count: int = len(self.training_env.get_attr("phases")[0]["phases"])
                if next_phase_index < phases_count - 1:
                    self.training_env.env_method("set_phase", next_phase_index)
                    self.episode_results.clear()
                    if self.verbose > 2:
                        rprint("[cyan]-> Win rate %.2f/%.2f (last %d eps) current Phase (%d). Progress to next Phase (%d).[/cyan]" % (
                            win_rate,
                            self.win_rate_threshold,
                            self.n_episodes,
                            self.current_phase_index,
                            next_phase_index,
                        ))

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
        Keeps track of the best model in `self.best_model`. Evaluation happens
        every `eval_freq` calls for `n_eval_episodes`.
        """
        super().__init__(verbose)
        self.eval_model: Any = eval_model
        self.best_model_temp_file_path: Path = temp_file_path
        self.best_model: Any = None
        self.eval_env: Monitor = eval_env
        self.eval_freq: int = eval_freq
        self.n_eval_episodes: int = n_eval_episodes
        self.best_mean_reward: float = float("-inf")

    def _init_callback(self) -> None:
        self.eval_model.save(self.best_model_temp_file_path)
        return super()._init_callback()

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq == 0:
            mean_reward, _std_reward_per_episode = evaluate_policy(
                    model=self.eval_model,
                    env=self.eval_env,
                    n_eval_episodes=self.n_eval_episodes,
                    deterministic=True)
            if mean_reward > self.best_mean_reward: # type: ignore
                    self.best_mean_reward = mean_reward # type: ignore
                    self.eval_model.save(self.best_model_temp_file_path)

        return super()._on_step()


class CompactStdoutWriter(KVWriter):
    def write(self, key_values: dict[str, Any], key_excluded: dict[str, tuple[str, ...]], step: int = 0) -> None:
        log_dict = { "step": step, **key_values }
        sys.stdout.write("TrainStats%s\n" % (json.dumps(log_dict)))
        sys.stdout.flush()

    def close(self) -> None:
        pass


def train(
        action_style: ActionStyle,
        phases: dict[str, Any],
        algorithm: LearningAlgorithmType,
        seed: int = 0,
        n_threads: int = 1,
        device: str = "auto",
        output_model: Path | None = None,
        verbose: int = 0
) -> None:
    rprint("[bold yellow][ MODE: TRAIN ][/bold yellow]")

    # Verify directories.
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_TRAIN_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    TRAIN_LOG_DIR.mkdir(parents=True, exist_ok=True)

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

    # === Environment Config ===
    # Include support for multi-process parallel training.
    env_hyperparams: dict[str, Any]
    with open(ENV_HYPERPARAMS_CONFIG_FILE, "r") as file:
        env_hyperparams = json.load(file)
    vec_env: SubprocVecEnv = SubprocVecEnv([
        make_environment_fn(action_style, phases, seed + env_index)
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

    # ====== Model Config ======
    logger: Logger = configure(str(TRAIN_LOG_DIR), ["csv", "tensorboard"])
    if verbose > 1:
        logger.output_formats.append(CompactStdoutWriter())

    model_hyperparams: dict[str, Any]
    with open(MODEL_HYPERPARAMS_CONFIG_FILE, "r") as file:
        model_hyperparams = json.load(file)
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
            policy_kwargs: dict[str, Any] = {
                "net_arch": model_hyperparams["policy_net_arch"]
            }
            model_class: type[BaseAlgorithm] = DQN
            model = DQN(
                    policy="MlpPolicy",
                    policy_kwargs=policy_kwargs,
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
    train_hyperparams: dict[str, Any]
    with open(TRAIN_HYPERPARAMS_CONFIG_FILE, "r") as file:
        train_hyperparams = json.load(file)

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

    eval_best_model_callback: EvalBestModelCallback = EvalBestModelCallback(
            eval_model=model,
            temp_file_path=best_model_temp_file_path,
            eval_env=Monitor(GameEnvironment(action_style=action_style, phases=phases)),
            eval_freq=train_hyperparams["eval_freq"],
            n_eval_episodes=train_hyperparams["n_eval_episodes"],
            verbose=verbose)

    model.learn(
            total_timesteps=train_hyperparams["total_timesteps"],
            callback=[
                env_phase_callback,
                eval_best_model_callback,
                LogEveryNTimesteps(train_hyperparams["log_freq"]),
            ],
            progress_bar=(verbose > 1))

    rprint("[green]-> Training finished.[/green]")
    if verbose > 0:
        print("Phases cleared: %d" % (env_phase_callback.current_phase_index + 1))
        print("Best evaluated mean reward: %.2f" % (eval_best_model_callback.best_mean_reward))
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
