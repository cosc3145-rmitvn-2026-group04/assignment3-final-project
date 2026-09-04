# Agent observation capability tunings.
MAX_ENEMY_SPAWNER_OBS: int = 2
MAX_ENEMY_OBS: int = 5

# Reward tunings.
REWARD_STEP: float = -0.01  # Encourage speedrunning.
REWARD_AGENT_SHOOT: float = -0.1  # Encourage efficient use of bullets.
REWARD_AGENT_HURT: float = -10.0
REWARD_ENEMY_SPAWNER_KILL: float = 20.0
REWARD_ENEMY_KILL: float = 2.0
REWARD_WIN: float = 100.0
REWARD_LOSS: float = -100.0
