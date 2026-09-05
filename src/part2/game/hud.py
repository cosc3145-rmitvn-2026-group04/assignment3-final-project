import pygame
from pygame import Rect, Surface
from pygame.math import Vector2
from pygame.event import Event
from pygame.color import Color
from pygame.font import Font
from pygame.math import Vector2
from part2.engine.core import UserInterface
from part2.game.textlabel import blit_lines
from part2.game.game import Game, GameStatus
from part2.game.player import ActionStyle
from part2.config import (
        WINDOW_WIDTH, WINDOW_HEIGHT,
        MAIN_HUD_HEIGHT,
        COLOR_MAIN_HUD_FOREGROUND,
        COLOR_MAIN_HUD_BACKGROUND,
        COLOR_HELP_HUD_FOREGROUND)


class MainHUD(UserInterface):
    def __init__(self, fonts: dict[str, Font], game: Game):
        rect: Rect = Rect(
                0, WINDOW_HEIGHT - MAIN_HUD_HEIGHT,
                WINDOW_WIDTH, MAIN_HUD_HEIGHT)
        super().__init__(rect, fonts)
        self.game: Game = game

    def update(self, delta: float, events: list[Event], *args, **kwargs) -> None:
        self.surface.fill(COLOR_MAIN_HUD_BACKGROUND)

        player_hp: int = self.game.player.health
        player_max_hp: int = self.game.player.max_health
        player_hp_bar_fill_text: str = "•" * player_hp
        player_hp_bar_null_text: str = " " * (player_max_hp - player_hp)
        player_hp_text: str = "HP [%s%s] %d %s" % (
            player_hp_bar_fill_text,
            player_hp_bar_null_text,
            player_hp,
            (
                "(INVULN %.1f)" % (self.game.player.invulnerable_timer.time_left)
                if not self.game.game_over and self.game.player.invulnerable
                else ""
            )
        )
        player_hp_label: Surface = self.fonts["h2"].render(
                player_hp_text,
                True, COLOR_MAIN_HUD_FOREGROUND)
        self.surface.blit(player_hp_label, Vector2(20, 20))

        phase_name: str = self.game.phase_data["phase_name"]
        if self.game.status == GameStatus.GAME_IN_PROGRESS:
            phase_label: Surface = self.fonts["h2"].render(
                "PHASE %s" % phase_name,
                True, COLOR_MAIN_HUD_FOREGROUND)
            self.surface.blit(
                    phase_label,
                    Vector2(WINDOW_WIDTH - phase_label.get_width() - 20, 20))
        else:
            game_result_label: Surface = self.fonts["h2"].render(
                (
                    "GAME WON" if self.game.status == GameStatus.GAME_WON
                    else "PHASE %s LOST" % phase_name
                ),
                True, COLOR_MAIN_HUD_FOREGROUND)
            self.surface.blit(
                    game_result_label,
                    Vector2(WINDOW_WIDTH - game_result_label.get_width() - 20, 20))

        return super().update(delta, events, *args, **kwargs)


class HelpHUD(UserInterface):
    def __init__(self, fonts: dict[str, Font]):
        rect: Rect = Rect(
                0, 0,
                WINDOW_WIDTH, WINDOW_HEIGHT - MAIN_HUD_HEIGHT)
        super().__init__(rect, fonts)
        self.surface: Surface = Surface(Vector2(self.rect.width, self.rect.height), pygame.SRCALPHA)

    def update(self,
            delta: float,
            events: list[Event],
            show_instructions: bool,
            control_style: ActionStyle | None,
            *args, **kwargs
    ) -> None:
        self.surface.fill(Color(0, 0, 0, 0))

        control_keybinds: dict[ActionStyle, str] = {
            ActionStyle.STYLE_A: "[W][↑] THRUST FWD  [A][←] ROT LEFT  [D][→] ROT RIGHT  [SPACE] SHOOT",
            ActionStyle.STYLE_B: "[W][↑] MOV UP  [A][←] MOV LEFT  [S][↓] MOV DOWN  [D][→] MOV RIGHT  [SPACE] SHOOT",
        }

        help_text: str = "[F1] Help"
        if show_instructions:
            help_text += "  [F2] Toggle Debug Draw"
            if control_style:
                help_text += "  [F3] Switch Control Style (%s)" % (
                    "STYLE 1" if control_style == ActionStyle.STYLE_A
                    else "STYLE 2" if control_style == ActionStyle.STYLE_B
                    else "ERR"
                )
                help_text = "%s\n%s" % (help_text, control_keybinds[control_style])
        blit_lines(
                self.surface,
                Vector2(10, 10),
                help_text,
                self.fonts["small"],
                COLOR_HELP_HUD_FOREGROUND,
                int(self.fonts["small"].get_linesize() * 1.15))
