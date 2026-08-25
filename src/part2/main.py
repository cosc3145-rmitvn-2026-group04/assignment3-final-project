from pathlib import Path
from pygame.math import Vector2
import pygame
from game.config import *
from game.player import Player

def main():
    pygame.init()
    pygame.display.set_caption("Space Defense")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)

    player: Player = Player(
            health=100,
            position=Vector2(WIDTH // 2, HEIGHT // 2),
            velocity=Vector2(10, 8),
            radius=20.0,
            offset=Vector2(0, 20),
            image=pygame.image.load(Path("src/part2/assets/sprite_player.png")))
    player.ready()
    
    running = True
    while running:
        delta: float = clock.tick_busy_loop(FPS) / 1000.0
        screen.fill(BG)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        player.update(delta)

        player.draw(
                screen,
                debug_bounding_rect=True,
                debug_bounding_circle=True,
                debug_velocity=True,
                debug_acceleration=True)
        pygame.display.flip()
   
    player.free()
    pygame.quit()
    
if __name__ == "__main__":
    main()
