import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from typing import Any
from argparse import ArgumentParser, Namespace
import pygame
from pygame import Surface
from pygame.time import Clock
from pygame.math import Vector2
from pygame.font import SysFont, Font
from pygame.event import Event
from part2.game.phase import get_phases
from part2.game.game import Game
from part2.game.hud import MainHUD
from part2.config import (
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        FPS,
        COLOR_BACKGROUND)

# Verify models directory.
MODELS_DIR: Path = Path(__file__).resolve().parents[2] / "models" / "part2"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train(phases: dict[str, Any], output: Path | None = None) -> None:
    raise NotImplementedError  # TODO: Implement this.

def evaluate(phases: dict[str, Any], input: Path | None = None) -> None:
    raise NotImplementedError  # TODO: Implement this.

def play(phases: dict[str, Any], start_phase: int = 0) -> None:
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

def main() -> None:
    arg_parser: ArgumentParser = ArgumentParser(
            description="Assignment 3 [Undergrad] - Part 2: Arena Deep RL",
            allow_abbrev=True,
            add_help=True)
    arg_parser.add_argument(
            "-m", "--mode",
            choices=["train", "evaluate", "play"],
            required=True,
            help="Train without graphics, evaluate the learned policy (agent playing the game), or manually play the game.")
    arg_parser.add_argument(
            "-M", "--model-path",
            type=Path,
            default=None,
            help="If `mode` is set to `train` or `evaluate`, overrides path to the output/input model."
    )
    arg_parser.add_argument(
            "-p", "--start-phase",
            type=int,
            default=0,
            help="If `mode` is set to `play`, start the game at the specified phase."
    )
    args: Namespace = arg_parser.parse_args()

    phases: dict[str, Any] = get_phases()
    if args.mode == "train":
        train(phases=phases, output=Path(args.model_path))
    elif args.mode == "evaluate":
        evaluate(phases=phases, input=Path(args.model_path))
    elif args.mode == "play":
        play(phases=phases, start_phase=args.start_phase)


if __name__ == "__main__":
    main()
