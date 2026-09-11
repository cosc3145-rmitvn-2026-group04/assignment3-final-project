TILE_SIZE = 64
FPS = 8

EPISODES = 10_000
MAX_STEPS = 300

ALPHA = 0.2
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY_FRACTION = 1.0
INTRINSIC_REWARD_STRENGTH = 0.02
RANDOM_SEED = 2026
MONSTER_MOVE_PROBABILITY = 0.4


# Per-level values override the defaults above only where needed.
LEVEL_TRAINING_OVERRIDES = {
    1: {
        "episodes": 20_000,
        "alpha": 0.1,
        "gamma": 0.95,
        "seed": 8101,
    },
    4: {
        "episodes": 20_000,
        "max_steps": 400,
        "epsilon_decay_fraction": 0.8,
    },
    5: {
        "episodes": 40_000,
        "max_steps": 400,
        "epsilon_decay_fraction": 0.8,
    },
    6: {
        "episodes": 40_000,
        "max_steps": 400,
        "epsilon_decay_fraction": 0.8,
    },
}


LEVEL_ALGORITHM_TRAINING_OVERRIDES = {
    (4, "sarsa"): {
        "alpha": 0.1,
        "gamma": 0.95,
    },
}


def get_training_config(level_id, algo_name=None):
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
    training_config.update(
        LEVEL_ALGORITHM_TRAINING_OVERRIDES.get(
            (level_id, algo_name),
            {},
        )
    )
    return training_config
