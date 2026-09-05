from pathlib import Path

import pygame

from .config import TILE_SIZE


PART1_ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
FARM_ASSET_ROOT = (
    PART1_ASSET_ROOT / "Farm RPG FREE 16x16 - Tiny Asset Pack"
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

        self.apple = self._frame(
            "Apple.png",
            column=0,
            row=0,
            frame_size=32,
            output_size=TILE_SIZE,
            asset_root=PART1_ASSET_ROOT,
        )

        # The farm-pack objects and animals use 16x16 frames.
        self.rock = self._frame(
            "Objects/Road copiar.png",
            column=0,
            row=0,
            frame_size=16,
            output_size=TILE_SIZE,
        )

        # The fire sheet is an 8x8 grid of 100x100 cells. Crop the
        # transparent padding from the first row to create an animation.
        self.fire = [
            self._region(
                "9_brightfire_spritesheet.png",
                x=column * 100 + 40,
                y=32,
                width=28,
                height=42,
                output_size=(TILE_SIZE * 2 // 3, TILE_SIZE),
                asset_root=PART1_ASSET_ROOT,
            )
            for column in range(8)
        ]

        self.chest_closed = self._frame(
            "RPG Chests.png",
            column=5,
            row=0,
            frame_size=32,
            output_size=TILE_SIZE,
            asset_root=PART1_ASSET_ROOT,
        )

        self.chest_open = self._frame(
            "RPG Chests.png",
            column=5,
            row=3,
            frame_size=32,
            output_size=TILE_SIZE ,
            asset_root=PART1_ASSET_ROOT,
        )

        self.monster = self._frame(
            "Farm Animals/Chicken Red.png",
            column=0,
            row=0,
            frame_size=16,
            output_size=TILE_SIZE // 2,
        )
        self.key = self._create_key()

    def _load_sheet(self, relative_path, asset_root=FARM_ASSET_ROOT):
        cache_key = (asset_root, relative_path)
        if cache_key not in self._sheets:
            path = asset_root / relative_path
            if not path.exists():
                raise FileNotFoundError(f"Missing Pygame asset: {path}")

            self._sheets[cache_key] = pygame.image.load(
                str(path)
            ).convert_alpha()

        return self._sheets[cache_key]

    def _frame(
        self,
        relative_path,
        column,
        row,
        frame_size,
        output_size,
        asset_root=FARM_ASSET_ROOT,
    ):
        sheet = self._load_sheet(relative_path, asset_root)

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

    def _region(
        self,
        relative_path,
        x,
        y,
        width,
        height,
        output_size,
        asset_root=FARM_ASSET_ROOT,
    ):
        sheet = self._load_sheet(relative_path, asset_root)
        source_rectangle = pygame.Rect(x, y, width, height)
        frame = pygame.Surface((width, height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), source_rectangle)
        return pygame.transform.scale(frame, output_size)

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

    def _create_key(self):
        """Create a key icon with Pygame shapes when no sprite is available."""
        size = TILE_SIZE // 2
        key = pygame.Surface((size, size), pygame.SRCALPHA)
        outline = (116, 76, 18)
        gold = (255, 205, 55)

        pygame.draw.circle(key, outline, (9, 9), 8, 5)
        pygame.draw.circle(key, gold, (9, 9), 7, 3)
        pygame.draw.line(key, outline, (14, 14), (27, 27), 7)
        pygame.draw.line(key, gold, (14, 14), (27, 27), 3)
        pygame.draw.line(key, outline, (22, 22), (27, 17), 5)
        pygame.draw.line(key, gold, (22, 22), (27, 17), 2)
        pygame.draw.line(key, outline, (26, 26), (30, 22), 5)
        pygame.draw.line(key, gold, (26, 26), (30, 22), 2)

        return key
