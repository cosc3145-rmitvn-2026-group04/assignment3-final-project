from .RLAgent import RLAgent

class SARSAAgent(RLAgent):
    def update(
        self, 
        state: tuple, 
        action: int, 
        reward: float, 
        next_state: tuple, 
        next_action: int, 
        done: bool
        ) -> None:
        values = self.get_values(state)
        
        old_value = values[action]

        target = reward
        if not done:
            target += self.gamma * self.get_values(next_state)[next_action]

        values[action] += self.alpha * (target - old_value)
