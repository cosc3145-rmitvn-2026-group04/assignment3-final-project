import pygame

import argparse
from pathlib import Path

from src.part1.game.config import (
    ALPHA,
    EPISODES,
    EPSILON_END,
    EPSILON_START,
    FPS,
    GAMMA,
    MAX_STEPS,
)
from src.part1.game.gridworld import GridWorld
from src.part1.game.levels import LEVEL_0, LEVEL_1, LEVEL_2, LEVEL_3
from src.part1.ai.q_learning import QLearningAgent
from src.part1.ai.SARSA import SARSAAgent
from src.part1.runner import run_interactive, run_training

LEVEL_CONFIG = {
    0: {"layout": LEVEL_0, "agent_cls": QLearningAgent, "algo_name": "q_learning"},
    1: {"layout": LEVEL_1, "agent_cls": SARSAAgent, "algo_name": "sarsa"},
    2: {"layout": LEVEL_2, "agent_cls": QLearningAgent, "algo_name": "q_learning" if QLearningAgent == QLearningAgent else "sarsa"},
    3: {"layout": LEVEL_3, "agent_cls": SARSAAgent, "algo_name": "sarsa" if SARSAAgent == SARSAAgent else "sarsa"},
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
        help="select 0 for q learning, 1 for SARSA",
    )
    parser.add_argument("--algo", type=str, choices=["q_learning", "sarsa"], default=None, 
                        help="override default algorithm (q_learning or sarsa)")
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    config = LEVEL_CONFIG[arguments.level]

    env = GridWorld(config["layout"])
    model_path = get_model_path(arguments.level, config["algo_name"])
    
    if arguments.mode == "train":
        agent = QLearningAgent(ALPHA, GAMMA)
        run_training(
            env = env,
            agent = agent,
            episodes = EPISODES,
            start_eps = EPSILON_START,
            end_eps = EPSILON_END,
            save_path = model_path,
        )

    elif arguments.mode == "evaluate":
        if not model_path.exists():
            raise FileNotFoundError(f"No trained model at {model_path}")
        agent = config["agent_cls"](ALPHA, GAMMA)
        agent.load(model_path)
        run_interactive(env = env, agent = agent)

    elif arguments.mode == "manual":
        run_interactive(env=env, key_map = KEY_TO_ACTION)


if __name__ == "__main__":
    main()
