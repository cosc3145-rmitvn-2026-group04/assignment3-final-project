import argparse
from pathlib import Path

import pygame

from .config import (
    ALPHA,
    EPISODES,
    EPSILON_END,
    EPSILON_START,
    FPS,
    GAMMA,
    MAX_STEPS,
)
from .gridworld import GridWorld
from .levels import LEVEL_0
from .q_learning import QLearningAgent, linear_epsilon


MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "models"
    / "part1"
    / "level0_q.pkl"
)

KEY_TO_ACTION = {
    pygame.K_UP: 0,
    pygame.K_DOWN: 1,
    pygame.K_LEFT: 2,
    pygame.K_RIGHT: 3,
}


def train():
    """Train Level 0 without rendering and save the learned Q-table."""
    environment = GridWorld(LEVEL_0)
    agent = QLearningAgent(ALPHA, GAMMA)
    successful_episodes = 0

    for episode in range(EPISODES):
        state = environment.reset()
        epsilon = linear_epsilon(
            episode,
            EPISODES,
            EPSILON_START,
            EPSILON_END,
        )
        total_reward = 0
        done = False
        steps_taken = 0

        for step in range(MAX_STEPS):
            action = agent.choose_action(state, epsilon)
            next_state, reward, done, _ = environment.step(action)

            agent.update(
                state,
                action,
                reward,
                next_state,
                done,
            )

            state = next_state
            total_reward += reward
            steps_taken = step + 1

            if done:
                successful_episodes += 1
                break

        if episode % 100 == 0 or episode == EPISODES - 1:
            success_rate = successful_episodes / (episode + 1)
            print(
                f"Episode {episode + 1}/{EPISODES} | "
                f"reward={total_reward} | "
                f"steps={steps_taken} | "
                f"epsilon={epsilon:.3f} | "
                f"success={success_rate:.1%}"
            )

    agent.save(MODEL_PATH)
    print(f"Saved trained Q-table to: {MODEL_PATH}")


def evaluate():
    """Open Pygame and animate the policy stored in the trained Q-table."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "No trained model was found. Run "
            "'python -m src.part1.main train' first."
        )

    environment = GridWorld(LEVEL_0)
    agent = QLearningAgent(ALPHA, GAMMA)
    agent.load(MODEL_PATH)

    state = environment.reset()
    total_reward = 0
    steps_taken = 0
    done = False
    running = True

    environment.render(
        "Evaluating learned policy\nR: replay | Esc: quit"
    )
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    state = environment.reset()
                    total_reward = 0
                    steps_taken = 0
                    done = False

        if not done:
            action = agent.choose_action(state, epsilon=0.0)
            state, reward, done, _ = environment.step(action)
            total_reward += reward
            steps_taken += 1

        if done:
            message = (
                f"Complete | Reward: {total_reward} | Steps: {steps_taken}\n"
                "R: replay | Esc: quit"
            )
        else:
            message = (
                f"Evaluating | Reward: {total_reward} | Steps: {steps_taken}\n"
                "R: replay | Esc: quit"
            )

        environment.render(message)
        clock.tick(FPS)

    environment.close()


def manual():
    """Open Pygame and let a person test Level 0 with the arrow keys."""
    environment = GridWorld(LEVEL_0)
    environment.reset()

    total_reward = 0
    steps_taken = 0
    done = False
    running = True

    environment.render(
        "Manual mode\nArrow keys: move | R: reset | Esc: quit"
    )
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    environment.reset()
                    total_reward = 0
                    steps_taken = 0
                    done = False
                elif event.key in KEY_TO_ACTION and not done:
                    action = KEY_TO_ACTION[event.key]
                    _, reward, done, _ = environment.step(action)
                    total_reward += reward
                    steps_taken += 1

        if done:
            message = (
                f"Complete | Reward: {total_reward} | Steps: {steps_taken}\n"
                "R: reset | Esc: quit"
            )
        else:
            message = (
                f"Manual | Reward: {total_reward} | Steps: {steps_taken}\n"
                "Arrow keys: move | R: reset | Esc: quit"
            )

        environment.render(message)
        clock.tick(60)

    environment.close()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Train or play the Part I Level 0 gridworld."
    )
    parser.add_argument(
        "mode",
        choices=("train", "evaluate", "manual"),
        help=(
            "train without graphics, evaluate the learned policy, "
            "or control the player manually"
        ),
    )
    return parser.parse_args()


def main():
    arguments = parse_arguments()

    if arguments.mode == "train":
        train()
    elif arguments.mode == "evaluate":
        evaluate()
    else:
        manual()


if __name__ == "__main__":
    main()
