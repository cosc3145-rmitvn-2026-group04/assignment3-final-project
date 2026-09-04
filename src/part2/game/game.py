from typing import Any
from enum import Enum
from pygame import Surface
from pygame.math import Vector2
from pygame.font import Font
from pygame.event import Event
from part2.game.player import Player, PlayerBulletPool
from part2.game.enemy import EnemySpawner, EnemySpawnerPool, EnemyPool
from part2.game.config import PLAYER_HEALTH
from part2.config import (
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        MAIN_HUD_HEIGHT)


class GameStatus(Enum):
    GAME_LOST = -1
    GAME_ONGOING = 0
    GAME_WON = 1


class Game:
    def __init__(self, player: Player, phase_data: dict[str, Any]) -> None:
        self.phase_data: dict[str, Any] = phase_data
        self.player: Player = player
        self.reset()

    def reset(self) -> None:
        screen_center: Vector2 = Vector2(WINDOW_WIDTH // 2, (WINDOW_HEIGHT - MAIN_HUD_HEIGHT) // 2)

        self.game_over: bool = False
        self.status: GameStatus = GameStatus.GAME_ONGOING

        self.player.health = PLAYER_HEALTH
        self.player.rotation = 0.0
        self.player.position = screen_center + Vector2(
                self.phase_data["player_position"]["x"],
                self.phase_data["player_position"]["y"])
        self.player_bullet_pool: PlayerBulletPool = PlayerBulletPool()
        self.player.bullet_pool = self.player_bullet_pool

        self.enemy_spawner_pool: EnemySpawnerPool = EnemySpawnerPool()
        self.enemy_pool: EnemyPool = EnemyPool(max_size=self.phase_data["max_enemies"])

        spawner_index: int
        for spawner_index in range(len(self.phase_data["enemy_spawners"])):
                self.enemy_spawner_pool.add(
                        EnemySpawner(
                                health=self.phase_data["enemy_spawners"][spawner_index]["health"],
                                enemy_spawn_amount=self.phase_data["enemy_spawners"][spawner_index]["spawn_amount"],
                                enemy_spawn_delay=self.phase_data["enemy_spawners"][spawner_index]["spawn_delay"],
                                activation_delay=self.phase_data["enemy_spawners"][spawner_index]["activation_delay"],
                                position=screen_center + Vector2(
                                        self.phase_data["enemy_spawners"][spawner_index]["position"]["x"],
                                        self.phase_data["enemy_spawners"][spawner_index]["position"]["y"],
                                        ),
                                radius=30.0))

    def update(self, delta: float, events: list[Event]) -> None:
        if not self.game_over:
            self.player.update(delta, events)
            self.player_bullet_pool.update(delta, events, self.enemy_spawner_pool, self.enemy_pool)
            self.enemy_spawner_pool.update(delta, events, self.enemy_pool)
            self.enemy_pool.update(delta, events, self.player, self.enemy_pool)

            if self.player.health == 0:
                self.game_over = True
                self.status = GameStatus.GAME_LOST
            if len(self.enemy_spawner_pool.objects()) == 0:
                self.game_over = True
                self.status = GameStatus.GAME_WON
        else:
            if len(self.player_bullet_pool.objects()) > 0:
                self.player_bullet_pool.empty()
            if len(self.enemy_pool.objects()) > 0 and self.status == GameStatus.GAME_WON:
                self.enemy_pool.empty()

    def render(self, screen: Surface, fonts: dict[str, Font], debug: bool = False) -> None:
        self.player_bullet_pool.draw(
                screen,
                debug_image_rect=debug,
                debug_bounding_rect=debug,
                debug_bounding_circle=debug,
                debug_velocity=debug,
                debug_acceleration=debug)
        self.enemy_spawner_pool.draw(
                screen, fonts,
                debug_image_rect=debug,
                debug_bounding_rect=debug,
                debug_bounding_circle=debug)
        self.enemy_pool.draw(
                screen,
                debug_image_rect=debug,
                debug_bounding_rect=debug,
                debug_bounding_circle=debug,
                debug_velocity=debug,
                debug_acceleration=debug)
        self.player.draw(
                screen,
                debug_image_rect=debug,
                debug_bounding_rect=debug,
                debug_bounding_circle=debug,
                debug_velocity=debug,
                debug_acceleration=debug)
