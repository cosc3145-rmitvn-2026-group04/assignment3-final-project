from enum import Enum
from pygame import Surface
from pygame.math import Vector2
from pygame.font import Font
from pygame.event import Event
from part2.game.player import Player, PlayerBulletPool
from part2.game.enemy import EnemySpawner, EnemySpawnerPool, EnemyPool
from part2.game.config import (
        PLAYER_HEALTH,
        PLAYER_SPEED,
        PLAYER_ANGULAR_SPEED,
        ENEMY_SPAWNER_HEALTH)
from part2.config import (
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        MAIN_HUD_HEIGHT)


class GameStatus(Enum):
    GAME_LOST = -1
    GAME_ONGOING = 0
    GAME_WON = 1


class Game:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.game_over: bool = False
        self.status: GameStatus = GameStatus.GAME_ONGOING

        self.player_bullet_pool: PlayerBulletPool = PlayerBulletPool()
        self.enemy_spawner_pool: EnemySpawnerPool = EnemySpawnerPool()
        self.enemy_pool: EnemyPool = EnemyPool(max_size=5)

        self.player: Player = Player(
                health=PLAYER_HEALTH,
                speed=PLAYER_SPEED,
                angular_speed=PLAYER_ANGULAR_SPEED,
                position=Vector2(WINDOW_WIDTH // 2, (WINDOW_HEIGHT - MAIN_HUD_HEIGHT) // 2 + 256),
                radius=12.0,
                offset=Vector2(0, 4)
                )

        enemy_spawner: EnemySpawner = EnemySpawner(
                health=ENEMY_SPAWNER_HEALTH,
                enemy_spawn_amount=2,
                enemy_spawn_delay=5.0,
                activation_delay=3.0,
                position=Vector2(WINDOW_WIDTH // 2, (WINDOW_HEIGHT - MAIN_HUD_HEIGHT) // 2),
                radius=30.0)
        self.enemy_spawner_pool.add(enemy_spawner)

    def update(self, delta: float, events: list[Event]) -> None:
        if not self.game_over:
            self.player.update(delta, events, self.player_bullet_pool)
            self.player_bullet_pool.update(delta, events, self.enemy_spawner_pool, self.enemy_pool)
            self.enemy_spawner_pool.update(delta, events, self.enemy_pool)
            self.enemy_pool.update(delta, events, self.player, self.enemy_pool)

            if self.player.health == 0:
                self.game_over = True
                self.status = GameStatus.GAME_LOST
            if len(self.enemy_spawner_pool.objects()) == 0:
                self.game_over = True
                self.status = GameStatus.GAME_WON

    def render(self, screen: Surface, fonts: dict[str, Font]) -> None:
        self.player_bullet_pool.draw(screen)
        self.enemy_spawner_pool.draw(screen, fonts)
        self.enemy_pool.draw(screen)
        self.player.draw(screen)
