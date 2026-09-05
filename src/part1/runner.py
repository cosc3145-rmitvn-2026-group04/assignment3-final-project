from pathlib import Path

import pygame

from src.part1.ai.SARSA import SARSAAgent

from src.part1.ai.RLAgent import linear_epsilon

from src.part1.game.config import MAX_STEPS


def evaluate_policy(env, agent, episodes=100, max_steps=MAX_STEPS):
    """Evaluate a greedy policy without rendering or learning."""
    successes = 0
    deaths = 0

    for _ in range(episodes):
        state = env.reset()
        for _ in range(max_steps):
            action = agent.choose_action(state, epsilon=0.0)
            state, _, done, info = env.step(action)
            if done:
                successes += int(info.get("success", False))
                deaths += int(info.get("died", False))
                break

    return {
        "successes": successes,
        "deaths": deaths,
        "timeouts": episodes - successes - deaths,
    }


def run_training(
    env,
    agent,
    episodes,
    start_eps,
    end_eps,
    save_path,
    max_steps=MAX_STEPS,
    epsilon_decay_fraction=1.0,
):
    """Train without rendering and save the learned Q-table."""
    if not 0 < epsilon_decay_fraction <= 1:
        raise ValueError("epsilon_decay_fraction must be between 0 and 1")

    successful_episodes = 0
    is_sarsa = isinstance(agent, SARSAAgent)
    decay_episodes = max(2, int(episodes * epsilon_decay_fraction))
    
    for episode in range(episodes):
        state = env.reset()
        epsilon_episode = min(episode, decay_episodes - 1)
        epsilon = linear_epsilon(
            epsilon_episode,
            decay_episodes,
            start_eps,
            end_eps,
        )
        total_reward = 0
        steps_taken = 0
        done = False
        
        # initialization for SARSA
        action = agent.choose_action(state, epsilon)
        
        for step in range(max_steps):
            next_state, reward, done, info = env.step(action)
            time_limit_reached = step == max_steps - 1
            update_done = done or time_limit_reached
            
            if is_sarsa:
                next_action = (
                    agent.choose_action(next_state, epsilon)
                    if not update_done
                    else None
                )
                agent.update(
                    state,
                    action,
                    reward,
                    next_state,
                    next_action,
                    update_done,
                )
            else:
                agent.update(
                    state,
                    action,
                    reward,
                    next_state,
                    update_done,
                )
                next_action = (
                    agent.choose_action(next_state, epsilon)
                    if not update_done
                    else None
                )
            
            state = next_state
            total_reward += reward
            steps_taken = step + 1

            if done:
                if info.get("success", False):
                    successful_episodes += 1
                break

            # SARSA follows the exact action used in its update. 
            # Q-learning chooses the next behaviour-policy action.
            action = next_action
            
        if episode % 100 == 0 or episode == episodes - 1:
            success_rate = successful_episodes / (episode + 1)
            print(
                f"Episode {episode + 1}/{episodes} | "
                f"reward={total_reward} | "
                f"steps={steps_taken} | "
                f"epsilon={epsilon:.3f} | "
                f"training_success={success_rate:.1%}"
            )
            
    agent.save(save_path)
    # Printing only the filename avoids Windows console encoding failures
    # when a parent directory contains accented or combining characters.
    print(f"Model saved as {Path(save_path).name}")
    evaluation = evaluate_policy(env, agent, max_steps=max_steps)
    print(
        "Greedy evaluation | "
        f"success={evaluation['successes']}/100 | "
        f"deaths={evaluation['deaths']} | "
        f"timeouts={evaluation['timeouts']}"
    )
    
    
def run_interactive(env, agent=None, key_map=None):
    """handles evaluation and manual gameplay."""
    state = env.reset()
    total_reward = 0
    steps_taken = 0
    done = False
    info = {}
    running = True

    title = "Evaluation Mode" if agent else "Manual Mode"
    env.render(f"{title}\nR: replay | Esc: quit")
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    state = env.reset()
                    total_reward = 0
                    steps_taken = 0
                    done = False
                    info = {}
                # manual controls
                elif key_map and event.key in key_map and not done:
                    action = key_map[event.key]
                    state, reward, done, info = env.step(action)
                    total_reward += reward
                    steps_taken += 1

        # agent controls
        if agent and not done:
            action = agent.choose_action(state, epsilon=0.0)
            state, reward, done, info = env.step(action)
            total_reward += reward
            steps_taken += 1
        
        if done:
            result = "Complete" if info.get("success", False) else "You died"
            message = (
                f"{result} | Reward: {total_reward} | Steps: {steps_taken}\n"
                "R: reset | Esc: quit"
            )
        else:
            message = (
                f"{title} | Reward: {total_reward} | Steps: {steps_taken}\n"
                "Arrow keys: move | R: reset | Esc: quit"
            )

        env.render(message)
        clock.tick(60)

    env.close()
