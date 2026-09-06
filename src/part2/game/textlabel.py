from typing import Any, Union, Tuple, Sequence
from enum import Enum
from pygame import Surface, Color
from pygame.math import Vector2
from pygame.font import Font

# Type definitions based on the pygame library in _common.pyi.
Coordinate = Union[Tuple[float, float], Sequence[float], Vector2]
RGBAOutput = Tuple[int, int, int, int]
ColorValue = Union[Color, int, str, Tuple[int, int, int], RGBAOutput, Sequence[int]]


class TextAlignment(Enum):
    LEFT = -1
    CENTER = 0
    RIGHT = 1


def blit_lines(
    screen: Surface,
    pos: Coordinate,
    text: str,
    font: Any,
    color: ColorValue,
    line_height: int,
    align: TextAlignment = TextAlignment.LEFT
) -> None:
    if not isinstance(font, Font):
        raise TypeError("`font` parameter must be of type pygame.font.Font.")

    text_lines = text.splitlines()
    for line_count, line in enumerate(text_lines):
        text_surface: Surface = font.render(line, True, color)
        aligned_x: float
        match align:
            case TextAlignment.LEFT:
                aligned_x = 0.0
            case TextAlignment.CENTER:
                aligned_x = -text_surface.get_width() / 2
            case TextAlignment.RIGHT:
                aligned_x = -text_surface.get_width()
        screen.blit(text_surface, Vector2(pos) + Vector2(aligned_x, line_count * line_height))
