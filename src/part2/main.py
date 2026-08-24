import pygame
import sys, random
from pygame.math import Vector2
from game.config import *
from game.objects import Player

def main():
    pygame.init()
    pygame.display.set_caption("Space Defense")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)

    player: Player = Player(
            health=100,
            position=Vector2(WIDTH // 2, HEIGHT // 2))
    player.ready()
    
    running = True
    while running:
        delta: float = clock.tick(FPS) / 1000.0
        screen.fill(BG)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        player.update(delta)
        player.draw(screen)
        
        pygame.display.flip()
   
    player.free()
    pygame.quit()
    sys.exit(0)
    
if __name__ == "__main__":
    main()
