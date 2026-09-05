TILE_SIZE = 64
FPS = 8

EPISODES = 10_000
MAX_STEPS = 300

ALPHA = 0.2
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY_FRACTION = 1.0
RANDOM_SEED = 2026


# Level 1 needs more stable SARSA updates than the larger Level 2 state space.
# Values not listed here inherit the defaults above.
LEVEL_TRAINING_OVERRIDES = {
    1: {
        "episodes": 20_000,
        "alpha": 0.1,
        "gamma": 0.95,
        "seed": 8101,
    },
}


def get_training_config(level_id):
    """Return a complete training configuration for one level."""
    training_config = {
        "episodes": EPISODES,
        "max_steps": MAX_STEPS,
        "alpha": ALPHA,
        "gamma": GAMMA,
        "epsilon_start": EPSILON_START,
        "epsilon_end": EPSILON_END,
        "epsilon_decay_fraction": EPSILON_DECAY_FRACTION,
        "seed": RANDOM_SEED,
    }
    training_config.update(LEVEL_TRAINING_OVERRIDES.get(level_id, {}))
    return training_config
