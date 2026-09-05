from pathlib import Path
from typing import Any
from enum import Enum
import psutil
import json
from rich import print as rprint
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import SubprocVecEnv
from part2.ai.gym.environment import make_environment_fn
from part2.game.player import ActionStyle
from part2.game.game import GameStatus
from part2.config import MODELS_DIR

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
        self.win_rate_threshold: float = win_rate_threshold
        self.n_episodes: int = n_episodes
        self.episode_results: list[bool] = []
        self.current_phase_index: int = 0
        super().__init__(verbose)

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
                            self.n_episodes,
                            win_rate,
                            self.win_rate_threshold,
                            self.current_phase_index,
                            next_phase_index,
                        ))

        return super()._on_step()


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

    if device in ["cpu", "meta", "xla", "xpu", "mkldnn"]:
        available_cpu_count: int = len(psutil.Process().cpu_affinity())
        if not 0 < n_threads <= available_cpu_count:
            raise ValueError("`n_threads` exceeds of number of available CPU cores (%d)." % (available_cpu_count))

    filename_algorithm: str = algorithm.name.lower()
    filename_action_style: str = ""
    match action_style:
        case ActionStyle.STYLE_A:
            filename_action_style = "control_style_1"
        case ActionStyle.STYLE_B:
            filename_action_style = "control_style_2"
    _output_model: Path = (
        output_model if output_model
        else MODELS_DIR / ("%s.%s.zip" % (filename_algorithm, filename_action_style))
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
    model_hyperparams: dict[str, Any]
    with open(MODEL_HYPERPARAMS_CONFIG_FILE, "r") as file:
        model_hyperparams = json.load(file)
    model: BaseAlgorithm
    match algorithm:
        case LearningAlgorithmType.PPO:
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

    model.learn(
            **train_hyperparams,
            callback=[env_phase_callback],
            progress_bar=(verbose > 1))

    rprint("[green]-> Training finished.[/green]")
    if verbose > 0:
        print("Phases cleared: %d" % (env_phase_callback.current_phase_index + 1))
    # ==========================

    # ====== Model Export ======
    model.save(_output_model)
    if verbose > 0:
        rprint("[magenta]-> Saved model to '%s'.[/magenta]" % (str(_output_model)))
    # ==========================

    rprint("[bold yellow][ DONE ][/bold yellow]")
