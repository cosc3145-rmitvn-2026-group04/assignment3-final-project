import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pygame
from pygame.math import Vector2
from pygame.event import Event
from part2.game.player import Player, PlayerBullet
from part2.game.enemy import EnemySpawner
from part2.game.config import (
        PLAYER_HEALTH,
        PLAYER_SPEED,
        PLAYER_ANGULAR_SPEED,
        ENEMY_SPAWNER_HEALTH)
from part2.config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, COLOR_BACKGROUND

def main():
    pygame.init()
    pygame.display.set_caption("Space Defense")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)
    
    bullets: list[PlayerBullet] = []

    player: Player = Player(
            health=PLAYER_HEALTH,
            speed=PLAYER_SPEED,
            angular_speed=PLAYER_ANGULAR_SPEED,
            position=Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 256),
            radius=12.0,
            offset=Vector2(0, 4),
            bullets_list = bullets
            )
    enemy_spawner: EnemySpawner = EnemySpawner(
            health=ENEMY_SPAWNER_HEALTH,
            enemy_pool=[],
            enemy_spawn_amount=1,
            max_enemy_count=3,
            enemy_spawn_delay=5.0,
            activation_delay=3.0,
            position=Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2),
            radius=30.0)
    
    running = True
    while running:
        delta: float = clock.tick_busy_loop(FPS) / 1000.0
        screen.fill(COLOR_BACKGROUND)

        events: list[Event] = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        player.update(delta, events)
        for bullet in bullets:
            bullet.update(delta, events)
        enemy_spawner.update(delta, events)
        for enemy in enemy_spawner.enemy_pool:
            enemy.update(delta, events, player)

        for bullet in bullets:
            bullet.draw(screen)
        enemy_spawner.draw(screen)
        for enemy in enemy_spawner.enemy_pool:
            enemy.draw(screen)
        player.draw(screen)
        pygame.display.flip()

    pygame.quit()
    
if __name__ == "__main__":
    main()
