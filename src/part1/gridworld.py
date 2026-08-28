import pygame
from .assets import AssetManager

from .config import TILE_SIZE

ACTION_DELTAS = {
    0: (-1, 0),  # up
    1: (1, 0),   # down
    2: (0, -1),  # left
    3: (0, 1),   # right
}

class GridWorld:
    def __init__(self, layout):
        self.layout = layout
        self.rows = len(layout)
        self.cols = len(layout[0])

        self.rocks = set()
        self.initial_apples = set()
        self.start_position = None
        self.screen = None
        self.assets = None
        self.player_direction = "down"

        for row, line in enumerate(layout):
            for col, tile in enumerate(line):
                if tile == "#":
                    self.rocks.add((row, col))
                elif tile == "A":
                    self.initial_apples.add((row, col))
                elif tile == "S":
                    self.start_position = (row, col)

        if self.start_position is None:
            raise ValueError("Level requires a starting tile")

        self.reset()

    def reset(self):
        self.player_position = self.start_position
        self.player_direction = "down"
        self.apples = set(self.initial_apples)
        return self.get_state()

    def get_state(self):
        return (
            self.player_position,
            tuple(sorted(self.apples)),
        )

    def step(self, action):
        row, col = self.player_position
        row_change, col_change = ACTION_DELTAS[action]
        destination = (row + row_change, col + col_change)
        self.player_direction = {
            0: "up",
            1: "down",
            2: "left",
            3: "right",
        }[action]

        # Rocks and boundaries prevent movement.
        if (
            0 <= destination[0] < self.rows
            and 0 <= destination[1] < self.cols
            and destination not in self.rocks
        ):
            self.player_position = destination

        reward = 0

        if self.player_position in self.apples:
            self.apples.remove(self.player_position)
            reward = 1

        done = len(self.apples) == 0

        return self.get_state(), reward, done, {}

    def render(self, message=""):
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode(
                (self.cols * TILE_SIZE, self.rows * TILE_SIZE + 40)
            )
            pygame.display.set_caption("Level 0 Q-Learning")

        if self.assets is None:
            self.assets = AssetManager()

        self.screen.fill((80, 80, 80))

        for row in range(self.rows):
            for col in range(self.cols):
                rectangle = pygame.Rect(
                    col * TILE_SIZE,
                    row * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )

                if (row, col) in self.rocks:
                    pygame.draw.rect(self.screen, (80, 80, 80), rectangle)
                    rock_rectangle = self.assets.rock.get_rect(
                        center=rectangle.center
                    )
                    self.screen.blit(self.assets.rock, rock_rectangle)

                if (row, col) in self.apples:
                    apple_rectangle = self.assets.apple.get_rect(
                        center=rectangle.center
                    )
                    self.screen.blit(self.assets.apple, apple_rectangle)

        player_row, player_col = self.player_position
        animation_index = (
            pygame.time.get_ticks() // 200
        ) % len(self.assets.player[self.player_direction])
        player_sprite = self.assets.player[
            self.player_direction
        ][animation_index]
        player_rectangle = player_sprite.get_rect(
            center=(
                player_col * TILE_SIZE + TILE_SIZE // 2,
                player_row * TILE_SIZE + TILE_SIZE // 2,
            )
        )
        self.screen.blit(player_sprite, player_rectangle)

        font = pygame.font.Font(None, 26)
        text = font.render(message, True, (255, 255, 255))
        self.screen.blit(text, (10, self.rows * TILE_SIZE + 10))

        pygame.display.flip()

    def close(self):
        pygame.quit()
