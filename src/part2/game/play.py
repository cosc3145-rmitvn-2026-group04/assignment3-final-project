from typing import Any
from rich import print as rprint
import pygame
from pygame import Surface
from pygame.time import Clock
from pygame.math import Vector2
from pygame.font import SysFont, Font
from pygame.event import Event
from part2.game.player import (
        Player,
        ActionStyle,
        PlayerControllerInputStyleA,
        PlayerControllerInputStyleB)
from part2.game.game import Game, GameStatus
from part2.game.hud import MainHUD, HelpHUD
from part2.config import (
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        FPS,
        COLOR_BACKGROUND)


def play(phases: dict[str, Any], start_phase: int = 0) -> None:
    rprint("[bold yellow][ MODE: PLAY ][/bold yellow]")

    pygame.init()
    pygame.display.set_caption("Space Defense - Deep RL Arena")
    screen: Surface = pygame.display.set_mode(Vector2(WINDOW_WIDTH, WINDOW_HEIGHT))
    clock: Clock = pygame.time.Clock()
    fonts: dict[str, Font] = {
        "h1": SysFont("Consolas", 26, True),
        "h2": SysFont("Consolas", 22, True),
        "h3": SysFont("Consolas", 18, False),
        "body": SysFont("Consolas", 18, False),
        "small": SysFont("Consolas", 14, False),
        "xsmall": SysFont("Consolas", 11, False),
    }

    phase_index: int
    hud_show_help: bool = False
    for phase_index in range(start_phase, len(phases["phases"])):
        player: Player = Player(controller=PlayerControllerInputStyleA())
        player.controller.attach_player(player)
        game: Game = Game(player, phases["phases"][phase_index])

        main_hud: MainHUD = MainHUD(fonts, game)
        help_hud: HelpHUD = HelpHUD(fonts)

        debug_render: bool = False
        running: bool = True
        while running:
            # ====== Frame Setup =======
            delta: float = clock.tick_busy_loop(FPS) / 1000.0
            screen.fill(COLOR_BACKGROUND)
            # ==========================

            # === Frame Global Input ===
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
                    hud_show_help = not hud_show_help
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                    debug_render = not debug_render
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                    if isinstance(player.controller, PlayerControllerInputStyleA):
                        player.controller = PlayerControllerInputStyleB()
                    else:
                        player.controller = PlayerControllerInputStyleA()
                    player.controller.player = player
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    game.reset()
            # ==========================

            # ====== Frame Update ======
            game.update(delta, events)
            main_hud.update(delta, events)
            help_hud.update(
                    delta,
                    events,
                    hud_show_help,
                    (
                        ActionStyle.STYLE_A
                        if isinstance(player.controller, PlayerControllerInputStyleA)
                        else ActionStyle.STYLE_B
                        if isinstance(player.controller, PlayerControllerInputStyleB)
                        else None
                    ))
            if (
                game.game_over
                and game.status == GameStatus.GAME_WON
                and phase_index < len(phases["phases"]) - 1
            ):
                break
            # ==========================

            # ======= Frame Draw =======
            game.render(screen, fonts, debug_render)
            main_hud.draw(screen)
            help_hud.draw(screen)
            pygame.display.flip()
            # ==========================

        if not running:
            break

    pygame.quit()
    rprint("[bold yellow][ DONE ][/bold yellow]")
