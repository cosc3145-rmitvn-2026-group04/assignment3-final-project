import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from typing import Any
from enum import Enum
from argparse import ArgumentParser, Namespace
import psutil
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import BaseCallback
from part2.ai.gym.environment import make_environment, GameEnvironment
from part2.game.play import play
from part2.game.phase import get_phases
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

def evaluate(
        phases: dict[str, Any],
        start_phase: int = 0,
        input_model: Path | None = None
) -> None:
    raise NotImplementedError  # TODO: Implement this.

def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)  # Verify models directory.

    arg_parser: ArgumentParser = ArgumentParser(
            description="Assignment 3 [Undergrad] - Part 2: Arena Deep RL",
            allow_abbrev=True,
            add_help=True)
    arg_parser.add_argument(
            "-m", "--mode",
            choices=["train", "evaluate", "play"],
            required=True,
            help="Train without graphics, evaluate the learned policy (agent playing the game), or manually play the game.")
    arg_parser.add_argument(
            "-c", "--control-style",
            choices=[1, 2],
            default=1,
            help="Sets the control style for `train` mode."
    )
    arg_parser.add_argument(
            "-a", "--algorithm",
            choices=["PPO", "DQN"],
            default="PPO",
            help="Sets the reinforcement learning algorithm for `train` mode."
    )
    arg_parser.add_argument(
            "-n", "--n-env",
            type=int,
            default=1,
            help="If `mode` is set to `train`, sets the number of parallel training processes (limited by the number of available CPU cores)."
    )
    arg_parser.add_argument(
            "-M", "--model-path",
            type=Path,
            default=None,
            help="If `mode` is set to `train` or `evaluate`, sets path to the output/input model. If `mode` is `train` and this is not specified, a default path in 'models/part2' will be used."
    )
    arg_parser.add_argument(
            "-p", "--start-phase",
            type=int,
            default=0,
            help="If `mode` is set to `play` or `evaluate`, starts the game at the specified phase."
    )
    args: Namespace = arg_parser.parse_args()

    phases: dict[str, Any] = get_phases()
    match args.mode:
        case "train":
            action_style: ActionStyle
            match args.control_style:
                case 1:
                    action_style = ActionStyle.STYLE_A
                case 2:
                    action_style = ActionStyle.STYLE_B
                case _:
                    raise ValueError("Unrecognized control style.")
            algorithm: LearningAlgorithmType
            match args.algorithm:
                case "PPO":
                    algorithm = LearningAlgorithmType.PPO
                case "DQN":
                    algorithm = LearningAlgorithmType.DQN
                case _:
                    raise ValueError("Unrecognized RL algorithm.")
            model_path: Path = args.model_path
            if model_path:
                if model_path.suffix != ".zip":
                    raise ValueError("Output model must be a .zip file.")
                if not model_path.resolve().parent.exists():
                    raise FileNotFoundError("Invalid path to model: %s" % (model_path.resolve().parent))
            train(
                    phases=phases,
                    action_style=action_style,
                    algorithm=algorithm,
                    output_model=model_path,
                    n_env=args.n_env)
        case "evaluate":
            model_path: Path = args.model_path
            if model_path.suffix != ".zip":
                raise ValueError("Input model must be a .zip file.")
            if not model_path.exists():
                raise FileNotFoundError("Model not found at '%s'" % (model_path))
            evaluate(
                    phases=phases,
                    start_phase=args.start_phase,
                    input_model=model_path)
        case "play":
            if args.start_phase < 0 or args.start_phase > len(phases["phases"]) - 1:
                raise RuntimeError("Invalid start phase specified.")
            play(phases=phases, start_phase=args.start_phase)


if __name__ == "__main__":
    main()
