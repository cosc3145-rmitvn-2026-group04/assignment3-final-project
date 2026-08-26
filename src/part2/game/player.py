import pygame
from pygame.math import Vector2
from pygame.key import ScancodeWrapper
from pygame.event import Event
from engine.core import KinematicObject
from game.config import *
from pathlib import Path


class Player(KinematicObject):
    def __init__(self, health: int, speed: int, bullets_list: list, angular_speed: float, **kwargs):
        kwargs["image"] = pygame.image.load(Path("src/part2/assets/sprite_player.png"))
        super().__init__(**kwargs)
        self.health: int = health
        self.speed: int = speed
        self.angular_speed: float = angular_speed
        self.bullets_list = bullets_list
 
    def update(self, delta: float, events: list[Event]) -> None:
        self.velocity = Vector2(0, 0)

        pressed_keys: ScancodeWrapper = pygame.key.get_pressed()
        if pressed_keys[pygame.K_UP] or pressed_keys[pygame.K_w]:
            self.velocity = Vector2(0, -1).rotate(-self.rotation) * self.speed
        if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
            self.rotation += self.angular_speed * delta
        if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
            self.rotation -= self.angular_speed * delta

        event: Event
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                new_bullet = PlayerBullet(
                    speed = PLAYER_BULLET_SPEED,
                    position = Vector2(self.position),
                    rotation = self.rotation,
                )
                self.bullets_list.append(new_bullet)

        self.move(delta)
        super().update(delta, events)


class PlayerBullet(KinematicObject):
    def __init__(self, speed: int, **kwargs):
        kwargs["image"] = pygame.image.load(Path("src/part2/assets/sprite_bullet.png"))
        super().__init__(**kwargs)
        self.speed: int = speed

        direction = Vector2(0, -1).rotate(-self.rotation)
        self.velocity = direction * self.speed
        
    def update(self, delta, events: list[Event]) -> None:
        self.move (delta)
        super().update(delta, events)
