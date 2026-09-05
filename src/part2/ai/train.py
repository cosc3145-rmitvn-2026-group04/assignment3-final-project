from pathlib import Path
from typing import Any
from enum import Enum
import psutil
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import BaseCallback
from part2.ai.gym.environment import make_environment, GameEnvironment
from part2.game.player import ActionStyle
from part2.game.game import GameStatus
from part2.config import MODELS_DIR


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
                        print("Win rate %.2f (last %i eps) achieved for Phase index %i. Progressed to Phase index %i" % (
                            self.win_rate_threshold,
                            self.n_episodes,
                            current_phase_index,
                            next_phase_index,
                        ))
                elif self.verbose > 0:
                    print("Win rate %.2f achieved for all %i phases." % (self.win_rate_threshold, phases_count))

        return super()._on_step()


def train(
        phases: dict[str, Any],
        action_style: ActionStyle,
        algorithm: LearningAlgorithmType,
        output_model: Path | None = None,
        n_env: int = 1
) -> None:
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

    model: BaseAlgorithm

    raise NotImplementedError("Incomplete implementation.")
