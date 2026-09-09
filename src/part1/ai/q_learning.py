from .RLAgent import RLAgent

class QLearningAgent(RLAgent):
    def update(
        self, 
        state: tuple,
        action: int,
        reward: float,
        next_state: tuple,
        done: bool
        ) -> None:
        values = self.get_values(state)
        old_value = values[action]

        if done:
            target = reward
        else:
            target = reward + self.gamma * max(
                self.get_values(next_state)
                )

        values[action] = old_value + self.alpha * (
            target - old_value
            )
