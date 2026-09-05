import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from typing import Any
from argparse import ArgumentParser, Namespace
from part2.ai.train import train, LearningAlgorithmType
from part2.ai.evaluate import evaluate
from part2.game.play import play
from part2.game.phase import get_phases
from part2.game.player import ActionStyle
from part2.config import MODELS_DIR


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
            choices=["1", "2"],
            default="1",
            help="Sets the control style for 'train' mode. Default: '1'."
    )
    arg_parser.add_argument(
            "-a", "--algorithm",
            choices=["PPO", "DQN"],
            default="PPO",
            help="Sets the reinforcement learning algorithm for 'train' mode. Default: 'PPO'."
    )
    arg_parser.add_argument(
            "-s", "--seed",
            type=int,
            default=0,
            help="If `mode` is set to 'train', sets RNG seed for the training environment. Default: 0."
    )
    arg_parser.add_argument(
            "-n", "--n-threads",
            type=int,
            default=1,
            help="If `mode` is set to 'train' and `device` is a CPU type, sets the number of parallel training processes (limited by the number of available CPU cores). Default: 1."
    )
    arg_parser.add_argument(
            "-d", "--device",
            choices=[
                "auto", "cpu", "cuda", "ipu", "xpu", "mkldnn", "opengl",
                "opencl", "ideep", "hip", "ve", "fpga", "maia", "xla", "lazy",
                "vulkan", "mps", "meta", "hpu", "mtia", "privateuseone",
            ],
            default="auto",
            help="If `mode` is set to 'train', sets the device used by the training algorithm. Default: 'auto'."
    )
    arg_parser.add_argument(
            "-M", "--model-path",
            type=Path,
            default=None,
            help="If `mode` is set to 'train' or 'evaluate', sets path to the output/input model. If `mode` is 'train' and this is not specified, a default path in 'models/part2' will be used."
    )
    arg_parser.add_argument(
            "-p", "--start-phase",
            type=int,
            default=0,
            help="If `mode` is set to 'play' or 'evaluate', starts the game at the specified phase. Default: 0."
    )
    arg_parser.add_argument(
            "-v", "--verbose",
            type=int,
            default=0,
            help="Sets the CLI output verbose level. Default: 0."
    )
    args: Namespace = arg_parser.parse_args()

    phases: dict[str, Any] = get_phases()
    match args.mode:
        case "train":
            action_style: ActionStyle
            match args.control_style:
                case "1":
                    action_style = ActionStyle.STYLE_A
                case "2":
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
                    raise ValueError("Output model must be a .pkl file.")
                if not model_path.resolve().parent.exists():
                    raise FileNotFoundError("Invalid path to model: %s" % (model_path.resolve().parent))
            train(
                    action_style=action_style,
                    phases=phases,
                    algorithm=algorithm,
                    seed=args.seed,
                    n_threads=args.n_threads,
                    device=args.device,
                    output_model=model_path,
                    verbose=args.verbose)
        case "evaluate":
            model_path: Path = args.model_path
            if not model_path:
                raise RuntimeError("No input model provided for 'evaluate' mode.")
            if model_path.suffix != ".pkl":
                raise ValueError("Input model must be a .pkl file.")
            if not model_path.exists():
                raise FileNotFoundError("Model not found at '%s'" % (model_path))
            evaluate(
                    phases=phases,
                    start_phase=args.start_phase,
                    input_model=model_path,
                    verbose=args.verbose)
        case "play":
            if args.start_phase < 0 or args.start_phase > len(phases["phases"]) - 1:
                raise RuntimeError("Invalid start phase specified.")
            play(phases=phases, start_phase=args.start_phase, verbose=args.verbose)


if __name__ == "__main__":
    main()
