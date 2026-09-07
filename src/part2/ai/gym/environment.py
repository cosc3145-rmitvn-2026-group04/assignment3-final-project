from __future__ import annotations
from typing import Any, SupportsFloat
from collections.abc import Callable
from random import randint, random
import numpy as np
from gymnasium import Env, spaces
from pygame.math import Vector2, clamp
from part2.ai.gym.agent import PlayerControllerAgent
from part2.ai.gym.config import get_hyperparameters
from part2.game.player import Player, Action, ActionStyle, COMPOSITE_ACTIONS
from part2.game.enemy import EnemySpawner, Enemy
from part2.game.game import Game, GameStatus
from part2.config import WINDOW_WIDTH, WINDOW_HEIGHT, MAIN_HUD_HEIGHT, FPS


def make_train_game_environment_fn(
        action_style: ActionStyle,
        phases: dict[str, Any],
        seed: int | None = None,
        max_steps: int = 0,
) -> Callable:
    """
    Generates wrapper a function returning a GameEnvironment for use in
    multi-process parallel training with
    stable_baselines3.common.vec_env.SubprocVecEnv.
    """
    def _init() -> GameEnvironment:
        environment: GameEnvironment = GameEnvironment(
                action_style=action_style,
                phases=phases,
                random_agent_spawn_position=True,
                random_agent_spawn_rotation=True,
                max_steps=max_steps)
        environment.reset(seed=seed)
        return environment
    return _init


class GameEnvironment(Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": FPS}

    def __init__(self,
            action_style: ActionStyle,
            phases: dict[str, Any],
            random_agent_spawn_position: bool = False,
            random_agent_spawn_rotation: bool = False,
            max_steps: int = 0
    ) -> None:
        super().__init__()
        self.render_mode = None
        self.hparams: dict[str, Any] = get_hyperparameters()
        self.current_step: int = 0
        self.max_steps: int = max_steps
        self.agent: Player = Player(PlayerControllerAgent())
        self.agent.controller.attach_player(self.agent)
        self.phases: dict[str, Any] = phases
        self.random_agent_spawn_position: bool = random_agent_spawn_position
        self.random_agent_spawn_rotation: bool = random_agent_spawn_rotation
        self.set_phase(0)

        # Agent observation (normalized): [x, y, vel_x, vel_y, rotation, health, can_shoot, is_invulnerable].
        #
        # Note:
        # - can_shoot is either -1.0 (False) or 1.0 (True).
        # - is_invulnerable is either -1.0 (False) or 1.0 (True).
        player_observation_vector_len: int = 8

        # Enemy spawner observation (normalized): [rel_x, rel_y, health, exist] for the closest "max_enemy_spawner_obs" enemy spawner.
        # Enemy observation (normalized): [rel_x, rel_y, rel_vel_x, rel_vel_y, exist] for the closest "max_enemy_obs" enemies.
        #
        # Note:
        # - rel_x and rel_y are the coordinates of the enemy spawner / enemy
        # relative to the agent.
        # - rel_vel_x and rel_vel_y are the components of the enemy's velocity
        # relative to the agent's velocity.
        # - If the number of closest enemy spawners / enemies is smaller
        # than the max observation ("max_enemy_spawner_obs" and
        # "max enemy_obs"), the extra empty space will have the exist component
        # set to -1.0 (False), and everything else set to 0.0. For spaces with
        # valid data, the exist component is set to 1.0 (True).
        enemies_observation_vector_len: int = (
            self.hparams["max_enemy_spawner_obs"] * 4
            + self.hparams["max_enemy_obs"] * 5
        )

        self.observation_space = spaces.Box(
                low=-1.0, high=1.0,
                shape=(player_observation_vector_len + enemies_observation_vector_len,),
                dtype=np.float32)

        self.action_space = spaces.Discrete(len(COMPOSITE_ACTIONS[action_style]))
        self._composite_actions: dict[int, list[Action]] = COMPOSITE_ACTIONS[action_style]

    def set_phase(self, phase_index: int) -> None:
        if not 0 <= phase_index < len(self.phases["phases"]):
            raise ValueError("`phase_index` out of bound.")
        self.current_phase_index = phase_index
        self.game = Game(self.agent, self.phases["phases"][self.current_phase_index])
        if self.random_agent_spawn_position:
            self._randomize_agent_spawn_position()
        if self.random_agent_spawn_rotation:
            self._randomize_agent_spawn_rotation()

    def reset(self,
            *,
            seed: int | None = None,
            options: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, Any]]:
        super().reset(seed=seed, options=options)
        self.current_step = 0
        self.game.reset()
        if self.random_agent_spawn_position:
            self._randomize_agent_spawn_position()
        if self.random_agent_spawn_rotation:
            self._randomize_agent_spawn_rotation()
        return self._get_observation(), self._get_info()

    def step(self, action: Any) -> tuple[Any, SupportsFloat, bool, bool, dict[str, Any]]:
        self.current_step += 1

        delta: float = 1.0 / FPS  # Fixed ideal delta for gameplay simulation.

        reward: float = 0
        previous_agent_health: int = self.agent.health
        previous_enemy_spawner_count: int = len(self.game.enemy_spawner_pool.objects())
        previous_total_enemy_spawners_health: int = sum([
                enemy_spawner.health
                for enemy_spawner in self.game.enemy_spawner_pool.objects()])
        previous_enemy_count: int = len(self.game.enemy_pool.objects())

        _actions: list[Action] = self._composite_actions[action.item()]
        if isinstance(self.agent.controller, PlayerControllerAgent):
            self.agent.controller.set_actions(_actions)
        self.game.update(delta, events=[])

        # reward_step
        reward += self.hparams["reward_step"]

        # reward_agent_shoot
        if Action.SHOOT in _actions:
            reward += self.hparams["reward_agent_shoot"]

        # reward_agent_hurt
        current_agent_health: int = self.agent.health
        reward += (
            max(0, previous_agent_health - current_agent_health)
            * self.hparams["reward_agent_hurt"]
        )

        # reward_enemy_spawner_hit
        current_total_enemy_spawners_health: int = sum([
                enemy_spawner.health
                for enemy_spawner in self.game.enemy_spawner_pool.objects()])
        reward += (
            max(0, previous_total_enemy_spawners_health - current_total_enemy_spawners_health)
            * self.hparams["reward_enemy_spawner_hit"]
        )

        # reward_enemy_spawner_kill
        current_enemy_spawner_count: int = len(self.game.enemy_spawner_pool.objects())
        reward += (
            max(0, previous_enemy_spawner_count - current_enemy_spawner_count)
            * self.hparams["reward_enemy_spawner_kill"]
        )

        # reward_enemy_kill
        current_enemy_count: int = len(self.game.enemy_pool.objects())
        reward += (
            max(0, previous_enemy_count - current_enemy_count)
            * self.hparams["reward_enemy_kill"]
        )

        # reward_phase_win and reward_phase_loss
        terminated: bool = False
        if self.game.game_over:
            terminated = True
            match self.game.status:
                case GameStatus.GAME_WON:
                    reward += self.hparams["reward_phase_win"]
                case GameStatus.GAME_LOST:
                    reward += self.hparams["reward_phase_loss"]

        # reward_episode_truncated (behavior leading to soft-locks)
        truncated: bool = False
        if self.max_steps > 0 and self.current_step >= self.max_steps:
            truncated = True
            reward += self.hparams["reward_episode_truncated"]

        return self._get_observation(), reward, terminated, truncated, self._get_info()

    def _get_observation(self) -> np.ndarray:
        """Returns the observation calculated from the current game state."""
        environment_width: float = float(WINDOW_WIDTH)
        environment_height: float = float(WINDOW_HEIGHT - MAIN_HUD_HEIGHT)

        agent_observation: list = [
            (self.agent.position.x / environment_width) * 2.0 - 1.0,
            (self.agent.position.y / environment_height) * 2.0 - 1.0,
            clamp(self.agent.velocity.x / self.agent.speed, -1.0, 1.0),
            clamp(self.agent.velocity.y / self.agent.speed, -1.0, 1.0),
            (self.agent.rotation % 360.0) / 360.0 * 2.0 - 1.0,
            self.agent.health / self.agent.max_health * 2.0 - 1.0,
            1.0 if self.agent.shooting_enabled else -1.0,
            1.0 if self.agent.invulnerable else -1.0,
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
                enemy_spawner_relative_position.x / environment_width,
                enemy_spawner_relative_position.y / environment_height,
                enemy_spawner.health / enemy_spawner.max_health * 2.0 - 1.0,
                1.0,
            ])
        observed_enemies: list[Enemy] = self._get_observed_enemies()
        enemy_index: int
        for enemy_index in range(self.hparams["max_enemy_obs"]):
            if enemy_index >= len(observed_enemies):
                enemy_observation.extend([0.0, 0.0, 0.0, 0.0, -1.0])
                continue

            enemy: Enemy = observed_enemies[enemy_index]
            enemy_relative_position: Vector2 = enemy.position - self.agent.position
            enemy_relative_velocity: Vector2 = enemy.velocity - self.agent.velocity
            enemy_observation.extend([
                enemy_relative_position.x / environment_width,
                enemy_relative_position.y / environment_height,
                enemy_relative_velocity.x / environment_width,
                enemy_relative_velocity.y / environment_height,
                1.0,
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
        r: list[EnemySpawner] = self.game.enemy_spawner_pool.objects().copy()
        r.sort(key=lambda enemy_spawner: self.agent.position.distance_squared_to(enemy_spawner.position))
        if len(r) > self.hparams["max_enemy_spawner_obs"]:
            r = r[:self.hparams["max_enemy_spawner_obs"]]
        return r

    def _get_observed_enemies(self) -> list[Enemy]:
        r: list[Enemy] = self.game.enemy_pool.objects().copy()
        r.sort(key=lambda enemy: self.agent.position.distance_squared_to(enemy.position))
        if len(r) > self.hparams["max_enemy_obs"]:
            r = r[:self.hparams["max_enemy_obs"]]
        return r

    def _randomize_agent_spawn_position(self) -> None:
        self.agent.position = (Vector2(
                randint(int(self.agent.radius), int(WINDOW_WIDTH - self.agent.radius)),
                randint(int(self.agent.radius), int(WINDOW_HEIGHT - MAIN_HUD_HEIGHT - self.agent.radius))))

    def _randomize_agent_spawn_rotation(self) -> None:
        self.agent.rotation = random() * 360.0
