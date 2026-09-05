from pathlib import Path
from typing import Any
from enum import Enum
import psutil
import json
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from part2.ai.gym.environment import make_environment_fn
from part2.game.player import ActionStyle
from part2.game.game import GameStatus
from part2.config import MODELS_DIR

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
                current_phase_index: int = self.training_env.env_method("get_attr", "current_phase_index")[0]
                next_phase_index: int = current_phase_index + 1
                phases_count: int = len(self.training_env.env_method("get_attr", "phases")[0]["phases"])
                if next_phase_index < phases_count - 1:
                    self.training_env.env_method("set_phase", next_phase_index)
                    self.episode_results.clear()
                    if self.verbose > 0:
                        print("-> Win rate %.2f (last %i eps) achieved for Phase index %i. Progressed to Phase index %i" % (
                            self.win_rate_threshold,
                            self.n_episodes,
                            current_phase_index,
                            next_phase_index,
                        ))
                elif self.verbose > 0:
                    print("-> Win rate %.2f achieved for all %i phases." % (self.win_rate_threshold, phases_count))

        return super()._on_step()


def train(
        action_style: ActionStyle,
        phases: dict[str, Any],
        algorithm: LearningAlgorithmType,
        seed: int = 0,
        n_env: int = 1,
        output_model: Path | None = None,
        verbose: int = 0
) -> None:
    print("[ MODE: TRAIN ]")

    available_cpu_count: int = len(psutil.Process().cpu_affinity())
    if not 0 < n_env <= available_cpu_count:
        raise ValueError("`n_env` exceeds of number of available CPU cores (%d)." % (available_cpu_count))

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
    vec_env: DummyVecEnv = DummyVecEnv([
        make_environment_fn(action_style, phases, seed + env_index)
        for env_index in range(n_env)
    ])
    env_phase_callback: GameEnvironmentPhaseCallback = GameEnvironmentPhaseCallback(
            win_rate_threshold=0.85,
            n_episodes=50,
            verbose=verbose
    )
    if verbose > 0:
        print("-> Environment loaded.")
    # ==========================

    # ====== Model Config ======
    model_hyperparams: dict[str, Any]
    with open(MODEL_HYPERPARAMS_CONFIG_FILE, "r") as file:
        model_hyperparams = json.load(file)
    if verbose > 0:
        print("-> Loaded model hyperparams for %s from '%s'." % (
            algorithm.name,
            str(MODEL_HYPERPARAMS_CONFIG_FILE)
        ))

    model: BaseAlgorithm
    match algorithm:
        case LearningAlgorithmType.PPO:
            model = PPO(
                    policy="MlpPolicy",
                    env=vec_env,
                    **model_hyperparams["PPO"],
                    verbose=verbose)
            if verbose > 1:
                print(json.dumps(model_hyperparams["PPO"], indent=2))
        case LearningAlgorithmType.DQN:
            model = DQN(
                    policy="MlpPolicy",
                    env=vec_env,
                    **model_hyperparams["DQN"],
                    verbose=verbose)
            if verbose > 1:
                print(json.dumps(model_hyperparams["DQN"], indent=2))
    # ==========================

    # ======== Training ========
    train_hyperparams: dict[str, Any]
    with open(TRAIN_HYPERPARAMS_CONFIG_FILE, "r") as file:
        train_hyperparams = json.load(file)
    if verbose > 0:
        print("-> Loaded training hyperparams from '%s'." % (
            str(TRAIN_HYPERPARAMS_CONFIG_FILE)
        ))
    if verbose > 1:
        print(json.dumps(train_hyperparams, indent=2))

    if verbose > 0:
        print("-> Training started.")
    model.learn(
            **train_hyperparams,
            callback=[env_phase_callback],
            progress_bar=(verbose > 1))
    if verbose > 0:
        print("-> Training finished.")
    # ==========================

    # ====== Model Export ======
    model.save(_output_model)
    if verbose > 0:
        print("-> Saved model to '%s'" % (str(_output_model)))
    # ==========================

    print("[ DONE ]")
