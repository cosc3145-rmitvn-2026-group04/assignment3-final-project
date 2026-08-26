from pygame import Rect, Surface
from pygame.math import Vector2
from pygame.event import Event
from pygame.font import Font
from part2.engine.core import UserInterface
from part2.game.config import PLAYER_HEALTH
from part2.game.player import Player
from part2.config import (
        WINDOW_WIDTH, WINDOW_HEIGHT,
        MAIN_HUD_HEIGHT,
        COLOR_MAIN_HUD_FOREGROUND,
        COLOR_MAIN_HUD_BACKGROUND)


class MainHUD(UserInterface):
    def __init__(self, fonts: dict[str, Font], player: Player):
        rect: Rect = Rect(
                0, WINDOW_HEIGHT - MAIN_HUD_HEIGHT,
                WINDOW_WIDTH, MAIN_HUD_HEIGHT)
        super().__init__(rect, fonts)
        self.player: Player = player

    def update(self, delta: float, events: list[Event], *args, **kwargs) -> None:
        self.surface.fill(COLOR_MAIN_HUD_BACKGROUND)

        player_hp: int = self.player.health
        player_hp_bar_fill_text: str = "▌" * player_hp
        player_hp_bar_null_text: str = " " * (PLAYER_HEALTH - player_hp)
        player_hp_text: str = "HP %s%s %d" % (
            player_hp_bar_fill_text,
            player_hp_bar_null_text,
            player_hp,
        )
        player_hp_label: Surface = self.fonts["h1"].render(
                player_hp_text,
                True, COLOR_MAIN_HUD_FOREGROUND)
        self.surface.blit(player_hp_label, Vector2(20, 20))

        return super().update(delta, events, *args, **kwargs)
