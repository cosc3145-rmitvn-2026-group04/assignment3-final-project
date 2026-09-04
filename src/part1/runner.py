import pygame

from src.part1.ai.SARSA import SARSAAgent

from src.part1.ai.RLAgent import linear_epsilon

from src.part1.game.config import MAX_STEPS


def run_training(env, agent, episodes, start_eps, end_eps, save_path):
    """encapsulates training without rendering and save learnt Q-table"""
    successful_episodes = 0
    is_sarsa = isinstance(agent, SARSAAgent)
    
    for episode in range(episodes):
        state = env.reset()
        epsilon = linear_epsilon(episode, episodes, start_eps, end_eps)
        total_reward = 0
        steps_taken = 0
        done = False
        
        # initialization for SARSA
        action = agent.choose_action(state, epsilon)
        
        for step in range(MAX_STEPS):
            next_state, reward, done, _ = env.step(action)
            
            if is_sarsa:
                next_action = agent.choose_action(next_state, epsilon)
                agent.update(
                                state, 
                                action, 
                                reward, 
                                next_state, 
                                next_action, 
                                done
                            )
                action = next_action
            else:
                # TODO: update q learning
                pass
            
            state = next_state
            total_reward += reward
            steps_taken = step + 1

            if done:
                successful_episodes += 1
                break
            
        if episode % 100 == 0 or episode == episodes - 1:
            success_rate = successful_episodes / (episode + 1)
            print(
                f"Episode {episode + 1}/{episodes} | "
                f"reward={total_reward} | "
                f"steps={steps_taken} | "
                f"epsilon={epsilon:.3f} | "
                f"success={success_rate:.1%}"
            )
            
    agent.save(save_path)
    print(f"Model saved to {save_path}")
    
    
def run_interactive(env, agent=None, key_map=None):
    """handles evaluation and manual gameplay."""
    state = env.reset()
    total_reward = 0
    steps_taken = 0
    done = False
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
                # manual controls
                elif key_map and event.key in key_map and not done:
                    action = key_map[event.key]
                    state, reward, done, _ = env.step(action)
                    total_reward += reward
                    steps_taken += 1

        # agent controls
        if agent and not done:
            action = agent.choose_action(state, epsilon=0.0)
            state, reward, done, _ = env.step(action)
            total_reward += reward
            steps_taken += 1
        
        if done:
            message = (
                f"Complete | Reward: {total_reward} | Steps: {steps_taken}\n"
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
