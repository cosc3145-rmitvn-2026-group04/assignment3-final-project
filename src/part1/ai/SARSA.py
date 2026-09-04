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
        current_q = self.get_q_value(state, action)
        
        target = reward
        if not done:
            target += self.gamma * self.get_q_value(next_state, next_action)

        self.q_table[state][action] += self.alpha * (target - current_q)
