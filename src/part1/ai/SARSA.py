from .RLAgent import RLAgent

class SARSAAgent(RLAgent):
    def update(self, state, action, reward, next_state, next_action, done):
        values = self.get_values(state)
        old_value = values[action]

        if done:
            target = reward
        else:
            target = reward + self.gamma * self.get_values(next_state)[next_action]

        values[action] = old_value + self.alpha * (target - old_value)
