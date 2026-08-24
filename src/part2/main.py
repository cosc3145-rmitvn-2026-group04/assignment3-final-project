import pygame
import sys, random
from pygame.math import Vector2
from game.config import *

def main():
    pygame.init()
    pygame.display.set_caption("Space Defense")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)
       
    running = True
    while running:
        dt: float = clock.tick(FPS) / 1000.0
        screen.fill(BG)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        pygame.display.flip()
    pygame.quit()
    sys.exit(0)
    
if __name__ == "__main__":
    main()
