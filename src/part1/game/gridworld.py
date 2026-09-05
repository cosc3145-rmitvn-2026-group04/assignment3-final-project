import pygame
from .assets import AssetManager
import random
from .config import TILE_SIZE

HUD_HEIGHT = 80

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
        self.fires = set()
        self.initial_apples = set()
        self.start_position = None
        self.key_pos = None
        self.chest_pos = None
        self.initial_monsters = set()
        self.screen = None
        self.assets = None
        self.player_direction = "down"

        for row, line in enumerate(layout):
            for col, tile in enumerate(line):
                if tile == "#":
                    self.rocks.add((row, col))
                elif tile == "F":
                    self.fires.add((row, col))
                elif tile == "A":
                    self.initial_apples.add((row, col))
                elif tile == "S":
                    self.start_position = (row, col)
                elif tile == "K":
                    self.key_pos = (row, col)
                elif tile == "C":
                    self.chest_pos = (row, col)
                elif tile == "M":
                    self.initial_monsters.add((row,col))

        if self.start_position is None:
            raise ValueError("Level requires a starting tile")

        self.reset()

    def reset(self):
        self.player_position = self.start_position
        self.player_direction = "down"
        self.apples = set(self.initial_apples)
        self.monsters = set(self.initial_monsters)
        self.has_key = False
        self.chest_open = False
        self.is_dead = False
        return self.get_state()

    def get_state(self):
        return (
            self.player_position,
            tuple(sorted(self.apples)),
            self.has_key,
            self.chest_open,
            tuple(sorted(self.monsters)),
        )

    def all_rewards_collected(self):
        """Return True when no apple or unopened chest reward remains."""
        apples_collected = len(self.apples) == 0
        chest_collected = self.chest_pos is None or self.chest_open
        return apples_collected and chest_collected
        
    # TODO: add monsters
        
    def step(self, action):
        if self.is_dead:
            return self.get_state(), 0, True, {
                "success": False,
                "died": True,
                "termination_reason": "fire",
            }

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
        self.is_dead = self.player_position in self.fires

        if not self.is_dead:
            # Pick up an apple.
            if self.player_position in self.apples:
                self.apples.remove(self.player_position)
                reward = 1

            # Pick up the key without changing the reward.
            if (
                self.key_pos
                and self.player_position == self.key_pos
                and not self.has_key
            ):
                self.has_key = True

            # Open the chest only after collecting the key.
            if (
                self.chest_pos
                and self.player_position == self.chest_pos
                and self.has_key
                and not self.chest_open
            ):
                self.chest_open = True
                reward += 2

        success = not self.is_dead and self.all_rewards_collected()
        done = self.is_dead or success
        termination_reason = "fire" if self.is_dead else (
            "completed" if success else None
        )

        return self.get_state(), reward, done, {
            "success": success,
            "died": self.is_dead,
            "termination_reason": termination_reason,
        }

    def render(self, message=""):
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode(
                (
                    self.cols * TILE_SIZE,
                    self.rows * TILE_SIZE + HUD_HEIGHT,
                )
            )
            pygame.display.set_caption("Classical RL Gridworld")

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
                pos = (row, col)

                if pos in self.rocks:
                    pygame.draw.rect(self.screen, (80, 80, 80), rectangle)
                    rock_rectangle = self.assets.rock.get_rect(
                        center=rectangle.center
                    )
                    self.screen.blit(self.assets.rock, rock_rectangle)

                if pos in self.fires:
                    fire_index = (
                        pygame.time.get_ticks() // 100
                    ) % len(self.assets.fire)
                    fire_sprite = self.assets.fire[fire_index]
                    fire_rectangle = fire_sprite.get_rect(
                        center=rectangle.center
                    )
                    self.screen.blit(fire_sprite, fire_rectangle)

                if pos in self.apples:
                    apple_rectangle = self.assets.apple.get_rect(
                        center=rectangle.center
                    )
                    self.screen.blit(self.assets.apple, apple_rectangle)

                if pos == self.key_pos and not self.has_key:
                    key_rectangle = self.assets.key.get_rect(
                        center=rectangle.center
                    )
                    self.screen.blit(self.assets.key, key_rectangle)

                if pos == self.chest_pos:
                    chest_sprite = (
                        self.assets.chest_open
                        if self.chest_open
                        else self.assets.chest_closed
                    )
                    chest_rectangle = chest_sprite.get_rect(
                        center=rectangle.center
                    )
                    self.screen.blit(chest_sprite, chest_rectangle)

                if pos in self.monsters:
                    monster_rectangle = self.assets.monster.get_rect(
                        center=rectangle.center
                    )
                    self.screen.blit(self.assets.monster, monster_rectangle)

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

        font = pygame.font.SysFont("consolas", 26)
        text_y = self.rows * TILE_SIZE + 8

        for line_number, line in enumerate(message.splitlines()):
            text_surface = font.render(line, True, (255, 255, 255))
            self.screen.blit(
                text_surface,
                (
                    10,
                    text_y + line_number * font.get_linesize(),
                ),
            )

        pygame.display.flip()

    def close(self):
        pygame.quit()
