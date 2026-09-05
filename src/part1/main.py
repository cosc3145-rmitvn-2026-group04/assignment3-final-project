import argparse
import random
from pathlib import Path

import pygame

from src.part1.game.config import get_training_config
from src.part1.game.gridworld import GridWorld
from src.part1.game.levels import LEVEL_0, LEVEL_1, LEVEL_2, LEVEL_3
from src.part1.ai.q_learning import QLearningAgent
from src.part1.ai.SARSA import SARSAAgent
from src.part1.runner import run_interactive, run_training

LEVEL_CONFIG = {
    0: {"layout": LEVEL_0, "default_algo": "q_learning"},
    1: {"layout": LEVEL_1, "default_algo": "sarsa"},
    2: {"layout": LEVEL_2, "default_algo": "q_learning"},
    3: {"layout": LEVEL_3, "default_algo": "sarsa"},
}

AGENT_CLASSES = {
    "q_learning": QLearningAgent,
    "sarsa": SARSAAgent,
}

KEY_TO_ACTION = {
    pygame.K_UP: 0,
    pygame.K_DOWN: 1,
    pygame.K_LEFT: 2,
    pygame.K_RIGHT: 3,
}
def get_model_path(level_id: int, algo_name: str) -> Path:
    """generates path: models/part1/level{id}_{algo}.pkl"""
    base_dir = Path(__file__).resolve().parents[2] / "models" / "part1"
    return base_dir / f"level{level_id}_{algo_name}.pkl"

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Train or play the Part I gridworld."
    )
    parser.add_argument(
        "mode",
        choices=("train", "evaluate", "manual"),
        help=(
            "execution mode"
        ),
    )
    parser.add_argument(
        "--level",
        type=int,
        default=0,
        choices=list(LEVEL_CONFIG.keys()),
        help="gridworld level to run",
    )
    parser.add_argument(
        "--algo",
        choices=list(AGENT_CLASSES.keys()),
        default=None,
        help="override the level's default algorithm",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="override the configured random seed",
    )
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    config = LEVEL_CONFIG[arguments.level]
    training_config = get_training_config(arguments.level)
    algo_name = arguments.algo or config["default_algo"]
    agent_class = AGENT_CLASSES[algo_name]
    random_seed = (
        arguments.seed
        if arguments.seed is not None
        else training_config["seed"]
    )
    random.seed(random_seed)

    env = GridWorld(config["layout"])
    model_path = get_model_path(arguments.level, algo_name)
    
    if arguments.mode == "train":
        agent = agent_class(
            training_config["alpha"],
            training_config["gamma"],
        )
        run_training(
            env = env,
            agent = agent,
            episodes = training_config["episodes"],
            start_eps = training_config["epsilon_start"],
            end_eps = training_config["epsilon_end"],
            save_path = model_path,
            max_steps = training_config["max_steps"],
            epsilon_decay_fraction = training_config[
                "epsilon_decay_fraction"
            ],
        )

    elif arguments.mode == "evaluate":
        if not model_path.exists():
            raise FileNotFoundError(f"No trained model at {model_path}")
        agent = agent_class(
            training_config["alpha"],
            training_config["gamma"],
        )
        agent.load(model_path)
        run_interactive(env = env, agent = agent)

    elif arguments.mode == "manual":
        run_interactive(env=env, key_map = KEY_TO_ACTION)


if __name__ == "__main__":
    main()
