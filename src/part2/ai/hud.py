import pygame
from pygame import Rect, Surface
from pygame.math import Vector2
from pygame.event import Event
from pygame.color import Color
from pygame.font import Font
from pygame.math import Vector2
from part2.ai.config import (
        COLOR_EVAL_AUX_HUD_HELP_FOREGROUND,
        COLOR_EVAL_AUX_HUD_INFO_FOREGROUND,
        COLOR_EVAL_AUX_HUD_INFO_FOREGROUND_DIM)
from part2.engine.core import UserInterface
from part2.game.textlabel import blit_lines, TextAlignment
from part2.game.player import ActionStyle
from part2.config import (
        WINDOW_WIDTH, WINDOW_HEIGHT,
        MAIN_HUD_HEIGHT)


class EvaluationAuxiliaryHUD(UserInterface):
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
            cumulative_reward: float,
            *args, **kwargs
    ) -> None:
        self.surface.fill(Color(0, 0, 0, 0))

        help_text: str = "[F1] Help"
        if show_instructions:
            help_text += "  [F2] Toggle Debug Draw"
            help_text += "  [R] Restart Phase"
        blit_lines(
                self.surface,
                Vector2(10, 10),
                help_text,
                self.fonts["small"],
                COLOR_EVAL_AUX_HUD_HELP_FOREGROUND,
                int(self.fonts["small"].get_linesize() * 1.15))

        eval_info_reward_text: str = "Reward: %.2f" %  (cumulative_reward)
        blit_lines(
                self.surface,
                Vector2(WINDOW_WIDTH - 10, 10),
                eval_info_reward_text,
                self.fonts["small"],
                COLOR_EVAL_AUX_HUD_INFO_FOREGROUND,
                int(self.fonts["small"].get_linesize() * 1.15),
                align=TextAlignment.RIGHT)

        control_style_num: int = -1
        match control_style:
            case ActionStyle.STYLE_A:
                control_style_num = 1
            case ActionStyle.STYLE_B:
                control_style_num = 2
        eval_info_control_line_text: str = "\nControl Style %d\n" % (control_style_num)
        blit_lines(
                self.surface,
                Vector2(WINDOW_WIDTH - 10, 10),
                eval_info_control_line_text,
                self.fonts["xsmall"],
                COLOR_EVAL_AUX_HUD_INFO_FOREGROUND_DIM,
                int(self.fonts["small"].get_linesize() * 1.1),
                align=TextAlignment.RIGHT)
