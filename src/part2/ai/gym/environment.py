from __future__ import annotations
from typing import Any, SupportsFloat
from collections.abc import Callable
import numpy as np
from gymnasium import Env, spaces
from pygame import Surface
from pygame.math import Vector2
from pygame.font import Font
from part2.ai.gym.agent import PlayerControllerAgent
from part2.ai.gym.config import (
        MAX_ENEMY_SPAWNER_OBS,
        MAX_ENEMY_OBS,
        REWARD_STEP,
        REWARD_AGENT_SHOOT,
        REWARD_AGENT_HURT,
        REWARD_ENEMY_SPAWNER_KILL,
        REWARD_ENEMY_KILL,
        REWARD_WIN,
        REWARD_LOSS)
from part2.game.player import Player, Action, ActionStyle, ACTIONS
from part2.game.enemy import EnemySpawner, Enemy
from part2.game.game import Game, GameStatus
from part2.config import WINDOW_WIDTH, WINDOW_HEIGHT, MAIN_HUD_HEIGHT, FPS


def make_environment_fn(
        action_style: ActionStyle,
        phases: dict[str, Any],
        seed: int | None = None
) -> Callable:
    """
    Generates wrapper a function returning a GameEnvironment for use in
    multi-process parallel training with
    stable_baselines3.common.vec_env.SubprocVecEnv
    """
    def _init() -> GameEnvironment:
        environment: GameEnvironment = GameEnvironment(action_style, phases)
        environment.reset(seed=seed)
        return environment
    return _init


class GameEnvironment(Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": FPS}

    def __init__(self,
            action_style: ActionStyle,
            phases: dict[str, Any]
    ) -> None:
        super().__init__()
        self.render_mode = "rbg_array"
        self.agent: Player = Player(PlayerControllerAgent())
        self.agent.controller.attach_player(self.agent)
        self.phases: dict[str, Any] = phases
        self.set_phase(0)

        # Agent observation (normalized): [x, y, vel_x, vel_y, rotation, health, can_shoot, is_invulnerable].
        #
        # Note:
        # - can_shoot is either -1.0 (False) or 1.0 (True).
        # - is_invulnerable is either -1.0 (False) or 1.0 (True).
        player_observation_vector_len: int = 8

        # Enemy spawner observation (normalized): [rel_x, rel_y, health, exist] for the closest MAX_ENEMY_SPAWNER_OBS enemy spawner.
        # Enemy observation (normalized): [rel_x, rel_y, exist] for the closest MAX_ENEMY_OBS enemies.
        #
        # Note:
        # - rel_x and rel_y are the coordinates of the enemy spawner / enemy
        # relative to the agent.
        # - If the number of closest enemy spawners / enemies is smaller
        # than the max observation (MAX_ENEMY_SPAWNER_OBS and MAX ENEMY_OBS),
        # the extra empty space will have the exist component set to -1.0
        # (False), and everything else set to 0.0. For spaces with valid data,
        # the exist component is set to 1.0 (True).
        enemies_observation_vector_len: int = MAX_ENEMY_SPAWNER_OBS * 4 + MAX_ENEMY_OBS * 3

        self.observation_space = spaces.Box(
                low=-1.0, high=1.0,
                shape=(player_observation_vector_len + enemies_observation_vector_len,),
                dtype=np.float32)

        self.action_space = spaces.Discrete(len(ACTIONS[action_style]))
        self._actions: dict[int, Action] = ACTIONS[action_style]

    def set_phase(self, phase_index: int) -> None:
        if not 0 <= phase_index < len(self.phases["phases"]):
            raise ValueError("`phase_index` out of bound.")
        self.current_phase_index = phase_index
        self.game = Game(self.agent, self.phases["phases"][self.current_phase_index])

    def reset(self,
            *,
            seed: int | None = None,
            options: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, Any]]:
        super().reset(seed=seed, options=options)
        self.game.reset()
        return self._get_observation, self._get_info()

    def step(self, action: Any) -> tuple[Any, SupportsFloat, bool, bool, dict[str, Any]]:
        delta: float = 1.0 / FPS  # Fixed ideal delta for gameplay simulation.
        reward: float = REWARD_STEP

        previous_agent_bullet_count: int = len(self.game.player_bullet_pool.objects())
        previous_enemy_spawner_count: int = len(self.game.enemy_spawner_pool.objects())
        previous_enemy_count: int = len(self.game.enemy_pool.objects())
        previous_agent_health: int = self.game.player.health

        _action: Action = self._actions[action]
        self.agent.controller.update(delta, [], _action)
        self.game.update(delta, events=[])

        current_agent_bullet_count: int = len(self.game.player_bullet_pool.objects())
        agent_shot_count: int = previous_agent_bullet_count - current_agent_bullet_count
        reward += agent_shot_count * REWARD_AGENT_SHOOT

        current_enemy_spawner_count: int = len(self.game.enemy_spawner_pool.objects())
        enemy_spawner_kill_count: int = previous_enemy_spawner_count - current_enemy_spawner_count
        reward += enemy_spawner_kill_count * REWARD_ENEMY_SPAWNER_KILL

        current_enemy_count: int = len(self.game.enemy_pool.objects())
        enemy_kill_count: int = previous_enemy_count - current_enemy_count
        reward += enemy_kill_count * REWARD_ENEMY_KILL

        current_agent_health: int = self.game.player.health
        agent_health_loss: int = previous_agent_health - current_agent_health
        reward += agent_health_loss * REWARD_AGENT_HURT

        terminated: bool = False
        truncated: bool = False
        if self.game.game_over:
            terminated = True
            match self.game.status:
                case GameStatus.GAME_WON:
                    reward += REWARD_WIN
                case GameStatus.GAME_LOST:
                    reward += REWARD_LOSS

        return self._get_observation, reward, terminated, truncated, self._get_info()

    def render_custom(self, screen: Surface, fonts: dict[str, Font], debug: bool = False) -> None:
        self.game.render(screen, fonts, debug)

    def _get_observation(self) -> np.ndarray:
        """Returns the observation calculated from the current game state."""
        environment_width: float = float(WINDOW_WIDTH)
        environment_height: float = float(WINDOW_HEIGHT - MAIN_HUD_HEIGHT)

        agent_velocity_normalized: Vector2 = (
            self.agent.velocity.normalize()
            if self.agent.velocity.length_squared() > 0.0
            else Vector2(0, 0)
        )
        agent_observation: list = [
            (self.agent.position.x / environment_width) * 2.0 - 1.0,
            (self.agent.position.y / environment_height) * 2.0 - 1.0,
            agent_velocity_normalized.x,
            agent_velocity_normalized.y,
            (self.agent.rotation % 360.0) / 360.0 * 2.0 - 1.0,
            self.agent.health / self.agent.max_health * 2.0 - 1.0,
            1.0 if self.agent.shooting_enabled else -1.0,
            1.0 if self.agent.invulnerable else -1.0
        ]

        enemy_observation: list = []
        enemy_spawers: list[EnemySpawner] = self.game.enemy_spawner_pool.objects()
        enemy_spawers.sort(key=lambda enemy_spawner: self.agent.position.distance_squared_to(enemy_spawner.position))
        enemy_spawner_index: int
        for enemy_spawner_index in range(MAX_ENEMY_SPAWNER_OBS):
            if enemy_spawner_index >= len(enemy_spawers):
                enemy_observation.extend([0.0, 0.0, 0.0, -1.0])
                continue

            enemy_spawner: EnemySpawner = enemy_spawers[enemy_spawner_index]
            enemy_spawner_relative_position: Vector2 = enemy_spawner.position - self.agent.position
            enemy_observation.extend([
                enemy_spawner_relative_position.x,
                enemy_spawner_relative_position.y,
                enemy_spawner.health / enemy_spawner.max_health * 2.0 - 1.0,
                1.0
            ])
        enemies: list[Enemy] = self.game.enemy_pool.objects()
        enemies.sort(key=lambda enemy: self.agent.position.distance_squared_to(enemy.position))
        enemy_index: int
        for enemy_index in range(MAX_ENEMY_OBS):
            if enemy_index >= len(enemies):
                enemy_observation.extend([0.0, 0.0, -1.0])
                continue

            enemy: Enemy = enemies[enemy_index]
            enemy_relative_position: Vector2 = enemy.position - self.agent.position
            enemy_observation.extend([
                enemy_relative_position.x,
                enemy_relative_position.y,
                1.0
            ])

        return np.ndarray(agent_observation + enemy_observation, dtype=np.float32)

    def _get_info(self) -> dict[str, Any]:
        """Returns auxiliary information of the current game state."""
        return {
            "phase": self.game.phase_data["phase_name"],
            "enemy_spawner_count": len(self.game.enemy_spawner_pool.objects()),
            "enemy_count": len(self.game.enemy_pool.objects()),
            "game_status": self.game.status,
        }
