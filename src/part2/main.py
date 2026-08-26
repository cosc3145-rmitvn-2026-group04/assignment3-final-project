from pathlib import Path
import pygame
from pygame.math import Vector2
from pygame.event import Event
from game.config import *
from game.player import Player, Bullet
from game.enemy import EnemySpawner

def main():
    pygame.init()
    pygame.display.set_caption("Space Defense")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)
    
    bullets: list[Bullet] = []

    player: Player = Player(
            health=PLAYER_HEALTH,
            speed=PLAYER_SPEED,
            angular_speed=PLAYER_ANGULAR_SPEED,
            position=Vector2(WIDTH // 2, HEIGHT // 2),
            radius=12.0,
            offset=Vector2(0, 4),
            image=pygame.image.load(Path("src/part2/assets/sprite_player.png")),
            bullets_list = bullets
            )
    player.ready()
    enemy_spawner: EnemySpawner = EnemySpawner(
            health=ENEMY_SPAWNER_HEALTH,
            enemy_pool=[],
            enemy_spawn_amount=1,
            max_enemy_count=3,
            enemy_spawn_delay=5.0,
            activation_delay=3.0,
            position=Vector2(WIDTH // 2, HEIGHT // 2),
            radius=30.0)
    enemy_spawner.ready()
    
    running = True
    while running:
        delta: float = clock.tick_busy_loop(FPS) / 1000.0
        screen.fill(COLOR_BG)

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
        enemy.draw(screen)
        pygame.display.flip()

    player.free()
    enemy_spawner.free()
    pygame.quit()
    
if __name__ == "__main__":
    main()
