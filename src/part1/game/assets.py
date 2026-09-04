from pathlib import Path

import pygame

from .config import TILE_SIZE


ASSET_ROOT = (
    Path(__file__).resolve().parent
    / "assets"
    / "Farm RPG FREE 16x16 - Tiny Asset Pack"
)


class AssetManager:
    """Load and crop the Part I sprite sheets once for reuse."""

    def __init__(self):
        self._sheets = {}

        # Idle.png contains four 32x32 frames per direction.
        self.player = {
            "down": self._row("Character/Idle.png", 0, 4, 32),
            "up": self._row("Character/Idle.png", 1, 4, 32),
            "right": self._row("Character/Idle.png", 2, 4, 32),
        }

        # The pack has one sideways direction, so flip it for left.
        self.player["left"] = [
            pygame.transform.flip(frame, True, False)
            for frame in self.player["right"]
        ]

        # Objects and animals use 16x16 frames.
        self.apple = self._frame(
            "Objects/Spring Crops.png",
            column=12,
            row=1,
            frame_size=16,
            output_size=TILE_SIZE // 2,
        )

        self.rock = self._frame(
            "Objects/Road copiar.png",
            column=0,
            row=0,
            frame_size=16,
            output_size=TILE_SIZE,
        )

        self.chest_closed = self._frame(
            "Objects/chest.png",
            column=0,
            row=0,
            frame_size=16,
            output_size=TILE_SIZE // 2,
        )

        self.chest_open = self._frame(
            "Objects/chest.png",
            column=0,
            row=1,
            frame_size=16,
            output_size=TILE_SIZE // 2,
        )

        self.monster = self._frame(
            "Farm Animals/Chicken Red.png",
            column=0,
            row=0,
            frame_size=16,
            output_size=TILE_SIZE // 2,
        )

    def _load_sheet(self, relative_path):
        if relative_path not in self._sheets:
            path = ASSET_ROOT / relative_path
            if not path.exists():
                raise FileNotFoundError(f"Missing Pygame asset: {path}")

            self._sheets[relative_path] = pygame.image.load(
                str(path)
            ).convert_alpha()

        return self._sheets[relative_path]

    def _frame(
        self,
        relative_path,
        column,
        row,
        frame_size,
        output_size,
    ):
        sheet = self._load_sheet(relative_path)

        source_rectangle = pygame.Rect(
            column * frame_size,
            row * frame_size,
            frame_size,
            frame_size,
        )

        frame = pygame.Surface(
            (frame_size, frame_size),
            pygame.SRCALPHA,
        )
        frame.blit(sheet, (0, 0), source_rectangle)

        # Normal scale preserves the sharp pixel-art appearance.
        return pygame.transform.scale(
            frame,
            (output_size, output_size),
        )

    def _row(self, relative_path, row, frame_count, frame_size):
        return [
            self._frame(
                relative_path,
                column,
                row,
                frame_size,
                TILE_SIZE,
            )
            for column in range(frame_count)
        ]
