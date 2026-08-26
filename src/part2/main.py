import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pygame
from pygame import Surface
from pygame.time import Clock
from pygame.math import Vector2
from pygame.font import SysFont, Font
from pygame.event import Event
from part2.game.hud import MainHUD
from part2.game.player import Player, PlayerBulletPool
from part2.game.enemy import EnemySpawner, EnemyPool
from part2.game.config import (
        PLAYER_HEALTH,
        PLAYER_SPEED,
        PLAYER_ANGULAR_SPEED,
        ENEMY_SPAWNER_HEALTH)
from part2.config import (
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        MAIN_HUD_HEIGHT,
        FPS,
        COLOR_BACKGROUND)


def main():
    pygame.init()
    pygame.display.set_caption("Space Defense")
    screen: Surface = pygame.display.set_mode(Vector2(WINDOW_WIDTH, WINDOW_HEIGHT))
    clock: Clock = pygame.time.Clock()
    fonts: dict[str, Font] = {
        "h1": SysFont("Consolas", 26, True),
        "h2": SysFont("Consolas", 22, True),
        "h3": SysFont("Consolas", 18, False),
        "body": SysFont("Consolas", 18, False),
        "small": SysFont("Consolas", 14, False),
        "xsmall": SysFont("Consolas", 12, False),
    }

    player_bullet_pool: PlayerBulletPool = PlayerBulletPool()
    enemy_pool: EnemyPool = EnemyPool(max_size=3)

    player: Player = Player(
            health=PLAYER_HEALTH,
            speed=PLAYER_SPEED,
            angular_speed=PLAYER_ANGULAR_SPEED,
            position=Vector2(WINDOW_WIDTH // 2, (WINDOW_HEIGHT - MAIN_HUD_HEIGHT) // 2 + 256),
            radius=12.0,
            offset=Vector2(0, 4)
            )
    enemy_spawner: EnemySpawner = EnemySpawner(
            health=ENEMY_SPAWNER_HEALTH,
            enemy_spawn_amount=1,
            enemy_spawn_delay=1.0,
            activation_delay=3.0,
            position=Vector2(WINDOW_WIDTH // 2, (WINDOW_HEIGHT - MAIN_HUD_HEIGHT) // 2),
            radius=30.0)

    main_hud: MainHUD = MainHUD(fonts, player)

    running: bool = True
    while running:
        # ====== Setup =======
        delta: float = clock.tick_busy_loop(FPS) / 1000.0
        screen.fill(COLOR_BACKGROUND)
        # ====================

        # === Global Input ===
        events: list[Event] = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        # ====================

        # ====== Update ======
        player.update(delta, events, player_bullet_pool)
        player_bullet_pool.update(delta, events, enemy_pool)
        enemy_spawner.update(delta, events, enemy_pool)
        enemy_pool.update(delta, events, player, enemy_pool)

        main_hud.update(delta, events)
        # ====================

        # ======= Draw =======
        player_bullet_pool.draw(screen)
        enemy_spawner.draw(screen)
        enemy_pool.draw(screen)
        player.draw(screen)

        main_hud.draw(screen)

        pygame.display.flip()
        # ====================

    pygame.quit()

if __name__ == "__main__":
    main()
