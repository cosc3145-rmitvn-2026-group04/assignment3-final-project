from pathlib import Path
import pygame
from pygame.math import Vector2
from pygame.event import Event
from game.config import *
from game.player import Player

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
    
    running = True
    while running:
        delta: float = clock.tick_busy_loop(FPS) / 1000.0
        screen.fill(COLOR_BG)

        events: list[Event] = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        player.update(delta, events)

        player.draw(
                screen,
                debug_image_rect=True,
                debug_bounding_rect=True,
                debug_bounding_circle=True,
                debug_velocity=True,
                debug_acceleration=True
        )
        pygame.display.flip()
   
    player.free()
    pygame.quit()
    
if __name__ == "__main__":
    main()
