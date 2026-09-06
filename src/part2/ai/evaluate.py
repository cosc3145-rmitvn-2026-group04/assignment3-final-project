from typing import Any
from pathlib import Path
import cloudpickle
from rich import print as rprint
import pygame
from pygame import Surface
from pygame.time import Clock
from pygame.math import Vector2
from pygame.font import SysFont, Font
from pygame.event import Event
from part2.ai.gym.environment import GameEnvironment
from part2.ai.hud import EvaluationAuxiliaryHUD
from part2.game.player import ActionStyle
from part2.game.game import GameStatus
from part2.game.hud import MainHUD
from part2.config import (
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        FPS,
        COLOR_BACKGROUND)


def evaluate(
        phases: dict[str, Any],
        start_phase: int,
        input_model: Path,
        verbose: int = 0
) -> None:
    rprint("[bold yellow][ MODE: EVALUATE ][/bold yellow]")
    print("Model: '%s'" % (input_model))

    env: GameEnvironment = GameEnvironment(action_style=ActionStyle.STYLE_A, phases=phases)
    observation: Any
    total_reward: float = 0.0
    terminated: bool
    truncated: bool
    info: dict[str, Any]
    observation, info = env.reset()

    model_pkl: dict[str, Any]
    with open(input_model, "rb") as file:
        model_pkl = cloudpickle.load(file)
    model: Any = model_pkl["model"]
    model_algorithm_name: str = model_pkl["metadata"]["algorithm"]
    model_control_style_name: str = model_pkl["metadata"]["control_style"]
    action: Any
    states: Any

    pygame.init()
    pygame.display.set_caption("Space Defense - Deep RL Arena [ MODE: EVALUATE ]")
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
        env.set_phase(phase_index)

        main_hud: MainHUD = MainHUD(fonts, env.game)
        eval_aux_hud: EvaluationAuxiliaryHUD = EvaluationAuxiliaryHUD(fonts)

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
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    observation, info = env.reset()
            # ==========================


            # ====== Frame Update ======
            action, states = model.predict(
                    observation=observation,
                    deterministic=True)
            observation, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)

            main_hud.update(delta, events)
            eval_aux_hud.update(
                    delta,
                    events,
                    hud_show_help,
                    model_algorithm_name,
                    model_control_style_name,
                    total_reward)

            if (
                terminated or truncated
                and info["game_status"] == GameStatus.GAME_WON
                and phase_index < len(phases["phases"]) - 1
            ):
                if verbose > 0:
                    rprint("[cyan]-> Phase %s. Cumulative reward: %.2f[/cyan]" % (
                        "won" if info["game_status"] == GameStatus.GAME_WON else "lost",
                        total_reward
                    ))
                break
            # ==========================


            # ======= Frame Draw =======
            env.game.render(screen, fonts, debug_render)
            main_hud.draw(screen)
            eval_aux_hud.draw(screen)
            pygame.display.flip()
            # ==========================

        if not running:
            match info["game_status"]:
                case GameStatus.GAME_IN_PROGRESS:
                    if verbose > 0:
                        rprint("[blue]-> Evaluation force terminated. Total reward: %.2f[/blue]" % (total_reward))
                case GameStatus.GAME_WON:
                    if verbose > 0:
                        rprint("[blue]-> Game won. Total reward: %.2f[/blue]" % (total_reward))
            break

    pygame.quit()
    rprint("[bold yellow][ DONE ][/bold yellow]")
