from __future__ import annotations
from typing import Any, SupportsFloat
from collections.abc import Callable
from statistics import mean
import numpy as np
from gymnasium import Env, spaces
from pygame.math import Vector2
from part2.ai.gym.agent import PlayerControllerAgent
from part2.ai.gym.config import get_hyperparameters
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
        self.render_mode = None
        self.hparams: dict[str, Any] = get_hyperparameters()
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

        # Enemy spawner observation (normalized): [rel_x, rel_y, health, exist] for the closest "max_enemy_spawner_obs" enemy spawner.
        # Enemy observation (normalized): [rel_x, rel_y, exist] for the closest "max_enemy_obs" enemies.
        #
        # Note:
        # - rel_x and rel_y are the coordinates of the enemy spawner / enemy
        # relative to the agent.
        # - If the number of closest enemy spawners / enemies is smaller
        # than the max observation ("max_enemy_spawner_obs" and
        # "max enemy_obs"), the extra empty space will have the exist component
        # set to -1.0 (False), and everything else set to 0.0. For spaces with
        # valid data, the exist component is set to 1.0 (True).
        enemies_observation_vector_len: int = (
            self.hparams["max_enemy_spawner_obs"] * 4
            + self.hparams["max_enemy_obs"] * 3
        )

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
        return self._get_observation(), self._get_info()

    def step(self, action: Any) -> tuple[Any, SupportsFloat, bool, bool, dict[str, Any]]:
        delta: float = 1.0 / FPS  # Fixed ideal delta for gameplay simulation.
        reward: float = self.hparams["reward_step"]

        previous_agent_position: Vector2 = self.agent.position
        previous_agent_rotation: float = self.agent.rotation
        previous_agent_health: int = self.game.player.health
        previous_enemy_spawner_count: int = len(self.game.enemy_spawner_pool.objects())
        previous_total_enemy_spawners_health: int = sum([
                enemy_spawner.health
                for enemy_spawner in self.game.enemy_spawner_pool.objects()])
        previous_enemy_count: int = len(self.game.enemy_pool.objects())

        _action: Action = self._actions[action.item()]
        self.agent.controller.update(delta, [], _action)
        self.game.update(delta, events=[])

        current_agent_position: Vector2 = self.agent.position
        reward += (
            current_agent_position.distance_to(previous_agent_position)
            * self.hparams["reward_agent_movement"]
        )

        current_agent_rotation: float = self.agent.rotation
        reward += (
            abs(current_agent_rotation - previous_agent_rotation)
            * self.hparams["reward_agent_rotation"]
        )

        if _action == Action.SHOOT:
            reward += self.hparams["reward_agent_shoot"]

        observed_enemies: list[Enemy] = self._get_observed_enemies()
        mean_distance_to_observed_enemies: float = 0.0 if len(observed_enemies) == 0 else mean([
                self.agent.position.distance_to(enemy.position)
                for enemy in self._get_observed_enemies()])
        if mean_distance_to_observed_enemies > 0.0:
            reward -= (
                self.hparams["reward_agent_enemy_max_obs_distance"] / mean_distance_to_observed_enemies
                * self.hparams["reward_agent_enemy_distance"]
            )

        current_agent_health: int = self.game.player.health
        reward += (
            max(0, previous_agent_health - current_agent_health)
            * self.hparams["reward_agent_hurt"]
        )

        current_total_enemy_spawners_health: int = sum([
                enemy_spawner.health
                for enemy_spawner in self.game.enemy_spawner_pool.objects()])
        reward += (
            max(0, previous_total_enemy_spawners_health - current_total_enemy_spawners_health)
            * self.hparams["reward_enemy_spawner_hit"]
        )

        current_enemy_spawner_count: int = len(self.game.enemy_spawner_pool.objects())
        reward += (
            max(0, previous_enemy_spawner_count - current_enemy_spawner_count)
            * self.hparams["reward_enemy_spawner_kill"]
        )

        current_enemy_count: int = len(self.game.enemy_pool.objects())
        reward += (
            max(0, previous_enemy_count - current_enemy_count)
            * self.hparams["reward_enemy_kill"]
        )

        terminated: bool = False
        truncated: bool = False
        if self.game.game_over:
            terminated = True
            match self.game.status:
                case GameStatus.GAME_WON:
                    reward += self.hparams["reward_phase_win"]
                case GameStatus.GAME_LOST:
                    reward += self.hparams["reward_phase_loss"]

        return self._get_observation(), reward, terminated, truncated, self._get_info()

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
        observed_enemy_spawers: list[EnemySpawner] = self._get_observed_enemy_spawners()
        enemy_spawner_index: int
        for enemy_spawner_index in range(self.hparams["max_enemy_spawner_obs"]):
            if enemy_spawner_index >= len(observed_enemy_spawers):
                enemy_observation.extend([0.0, 0.0, 0.0, -1.0])
                continue

            enemy_spawner: EnemySpawner = observed_enemy_spawers[enemy_spawner_index]
            enemy_spawner_relative_position: Vector2 = enemy_spawner.position - self.agent.position
            enemy_observation.extend([
                enemy_spawner_relative_position.x,
                enemy_spawner_relative_position.y,
                enemy_spawner.health / enemy_spawner.max_health * 2.0 - 1.0,
                1.0
            ])
        observed_enemies: list[Enemy] = self._get_observed_enemies()
        enemy_index: int
        for enemy_index in range(self.hparams["max_enemy_obs"]):
            if enemy_index >= len(observed_enemies):
                enemy_observation.extend([0.0, 0.0, -1.0])
                continue

            enemy: Enemy = observed_enemies[enemy_index]
            enemy_relative_position: Vector2 = enemy.position - self.agent.position
            enemy_observation.extend([
                enemy_relative_position.x,
                enemy_relative_position.y,
                1.0
            ])

        return np.array(agent_observation + enemy_observation, dtype=np.float32)

    def _get_info(self) -> dict[str, Any]:
        """Returns auxiliary information of the current game state."""
        return {
            "phase": self.game.phase_data["phase_name"],
            "enemy_spawner_count": len(self.game.enemy_spawner_pool.objects()),
            "enemy_count": len(self.game.enemy_pool.objects()),
            "game_status": self.game.status,
        }

    def _get_observed_enemy_spawners(self) -> list[EnemySpawner]:
        r: list[EnemySpawner] = self.game.enemy_spawner_pool.objects()
        r.sort(key=lambda enemy_spawner: self.agent.position.distance_squared_to(enemy_spawner.position))
        if len(r) > self.hparams["max_enemy_spawner_obs"]:
            r = r[:self.hparams["max_enemy_spawner_obs"]]
        return r

    def _get_observed_enemies(self) -> list[Enemy]:
        r: list[Enemy] = self.game.enemy_pool.objects()
        r.sort(key=lambda enemy: self.agent.position.distance_squared_to(enemy.position))
        if len(r) > self.hparams["max_enemy_obs"]:
            r = r[:self.hparams["max_enemy_obs"]]
        return r
