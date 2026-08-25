from pathlib import Path
import pygame
from pygame.math import Vector2
from pygame.event import Event
from game.config import *
from game.player import Player
from game.enemy import Enemy

def main():
    pygame.init()
    pygame.display.set_caption("Space Defense")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)

    player: Player = Player(
            health=PLAYER_HEALTH,
            speed=PLAYER_SPEED,
            angular_speed=PLAYER_ANGULAR_SPEED,
            position=Vector2(WIDTH // 2, HEIGHT // 2),
            radius=12.0,
            offset=Vector2(0, 4),
            image=pygame.image.load(Path("src/part2/assets/sprite_player.png")))
    player.ready()
    enemy: Enemy = Enemy(
            health=ENEMY_HEALTH,
            speed=ENEMY_SPEED,
            radius=9.5,
            image=pygame.image.load(Path("src/part2/assets/sprite_enemy.png")))
    
    running = True
    while running:
        delta: float = clock.tick_busy_loop(FPS) / 1000.0
        screen.fill(COLOR_BG)

        events: list[Event] = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        player.update(delta, events)
        enemy.update(delta, events, player=player)

        player.draw(screen)
        enemy.draw(screen)
        pygame.display.flip()
   
    player.free()
    pygame.quit()
    
if __name__ == "__main__":
    main()
