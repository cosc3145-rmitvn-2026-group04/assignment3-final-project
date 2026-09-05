from pathlib import Path
from pygame.color import Color

# Paths
BASE_DIR: Path = Path(__file__).resolve().parent
ASSET_DIR: Path = BASE_DIR / "assets"
MODELS_DIR: Path = Path(__file__).resolve().parents[2] / "models" / "part2"

# Display
WINDOW_WIDTH: int = 800
WINDOW_HEIGHT: int = 664
MAIN_HUD_HEIGHT: int = 64  # Main HUD is positioned at the bottom of the screen.
FPS: int = 60

# Colors
COLOR_BACKGROUND = Color(39, 35, 47)
COLOR_MAIN_HUD_FOREGROUND = Color(255, 255, 255)
COLOR_MAIN_HUD_BACKGROUND = Color(0, 0, 0)
COLOR_HELP_HUD_FOREGROUND = Color(131, 127, 151)
COLOR_RED = Color(240, 57, 57)
