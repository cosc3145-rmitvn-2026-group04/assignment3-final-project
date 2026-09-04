import pickle
import random
from pathlib import Path


class RLAgent:
    def __init__(self, alpha: float, gamma: float):
        self.alpha = alpha
        self.gamma = gamma
        self.q_table = {}
        
    def get_values(self, state):
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0, 0.0, 0.0]
        return self.q_table[state]
    
    def choose_action (self, state, epsilon: float) -> int:
        if random.random() < epsilon:
            return random.randrange(4)
        
        values = self.get_values(state)
        best_value = max(values)
        
        # random tie-breaking.
        best_actions = [
            action
            for action, value in enumerate(values)
            if value == best_value
        ]
        return random.choice(best_actions)
    
    def save(self, filename: str):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as file:
            pickle.dump(self.q_table, file)

    def load(self, filename):
        with Path(filename).open("rb") as file:
            self.q_table = pickle.load(file)
    
def linear_epsilon(episode: int, total_episodes: int, start: float, end: float) -> float:
    if total_episodes <= 1:
        return end
    progress = episode / (total_episodes - 1)
    return start + progress * (end - start)
