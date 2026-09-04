from pygame import Rect, Surface
from pygame.math import Vector2
from pygame.event import Event
from pygame.font import Font
from part2.engine.core import UserInterface
from part2.game.config import PLAYER_INVULNERABLE_COOLDOWN_DURATION
from part2.game.game import Game, GameStatus
from part2.config import (
        WINDOW_WIDTH, WINDOW_HEIGHT,
        MAIN_HUD_HEIGHT,
        COLOR_MAIN_HUD_FOREGROUND,
        COLOR_MAIN_HUD_BACKGROUND)


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
        if self.game.status == GameStatus.GAME_ONGOING:
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
