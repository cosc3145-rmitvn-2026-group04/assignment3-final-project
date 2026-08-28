import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pygame
from pygame import Surface
from pygame.time import Clock
from pygame.math import Vector2
from pygame.font import SysFont, Font
from pygame.event import Event
from part2.game.game import Game
from part2.game.hud import MainHUD
from part2.config import (
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
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

    game: Game = Game()

    debug_render: bool = False
    main_hud: MainHUD = MainHUD(fonts, game)

    running: bool = True
    while running:
        # ====== Setup =======
        delta: float = clock.tick_busy_loop(FPS) / 1000.0
        screen.fill(COLOR_BACKGROUND)
        # ====================

        # === Global Input ===
        events: list[Event] = pygame.event.get()
        for event in events:
            if (
                event.type == pygame.QUIT
                or (
                   event.type == pygame.KEYDOWN
                   and event.key == pygame.K_ESCAPE
                )
            ):
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                debug_render = not debug_render
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game.reset()
        # ====================

        # ====== Update ======
        game.update(delta, events)
        main_hud.update(delta, events)
        # ====================

        # ======= Draw =======
        game.render(screen, fonts, debug_render)
        main_hud.draw(screen)

        pygame.display.flip()
        # ====================

    pygame.quit()

if __name__ == "__main__":
    main()
