from __future__ import annotations
from typing import Any, Iterable
import pygame
from pygame.math import Vector2
from pygame.sprite import AbstractGroup
from pygame.key import ScancodeWrapper
from pygame.event import Event
from part2.config import ASSET_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, MAIN_HUD_HEIGHT
from part2.engine.core import KinematicObject, Group
import part2.game.enemy as enemy
from part2.game.config import PLAYER_BULLET_SPEED, PLAYER_INVULNERABLE_COOLDOWN_DURATION


class Player(KinematicObject):
    def __init__(self, health: int, speed: float, angular_speed: float, **kwargs):
        kwargs["image"] = pygame.image.load(ASSET_DIR / "sprite_player.png")
        super().__init__(**kwargs)
        self.health: int = health
        self.speed: float = speed
        self.angular_speed: float = angular_speed
        self.invulnerable: bool = False
        self.last_invulnerable_tick: int = pygame.time.get_ticks()

    def update(self, delta: float, events: list[Event], bullet_pool: PlayerBulletPool) -> None:
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
                bullet_pool.add(new_bullet)

        self.move(delta)
        self._limit_screen_bound()
        super().update(delta, events)

        if self.invulnerable:
            current_tick: int = pygame.time.get_ticks()

            if (current_tick - self.last_invulnerable_tick) / 1000.0 < 0.1:
                self.scale = Vector2(1.5, 1.5)
            else:
                self.scale = Vector2(1, 1)

            if (current_tick - self.last_invulnerable_tick) / 1000.0 > PLAYER_INVULNERABLE_COOLDOWN_DURATION:
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_player.png")
                self.invulnerable = False
            else:
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_player_invulnerable.png")

    def hurt(self) -> None:
        if self.health > 0:
            self.health -= 1
        self.invulnerable = True
        self.last_invulnerable_tick = pygame.time.get_ticks()

    def _limit_screen_bound(self) -> None:
        x: float
        y: float
        x, y = self.position.x, self.position.y
        x = pygame.math.clamp(x, self.radius, WINDOW_WIDTH - self.radius)
        y = pygame.math.clamp(y, self.radius, WINDOW_HEIGHT - MAIN_HUD_HEIGHT - self.radius)
        if x != self.position.x or y != self.position.y:
            self.position = Vector2(x, y)


class PlayerBullet(KinematicObject):
    def __init__(self, speed: float, **kwargs):
        kwargs["image"] = pygame.image.load(ASSET_DIR / "sprite_player_bullet.png")
        kwargs["radius"] = 4.0
        kwargs["offset"] = Vector2(0, -4)
        super().__init__(**kwargs)
        self.speed: float = speed
        self.__out_of_bound: bool = False
        self.__collided: bool = False

        direction = Vector2(0, -1).rotate(-self.rotation)
        self.velocity = direction * self.speed

    def update(self, delta, events: list[Event], enemy_pool: enemy.EnemyPool) -> None:
        if self.alive() and (self.__out_of_bound or self.__collided):
            self.kill()
            return

        collided_enemies: list[enemy.Enemy] = pygame.sprite.spritecollide(
                sprite=self, # type: ignore
                group=enemy_pool,
                dokill=False,
                collided=pygame.sprite.collide_circle)
        collided_enemy: enemy.Enemy
        for collided_enemy in collided_enemies:
            collided_enemy.hurt()
            if not self.__collided:
                self.__collided = True

        self.move(delta)
        if (
            self.position.x < -self.radius
            or self.position.x > WINDOW_WIDTH + self.radius
            or self.position.y < -self.radius
            or self.position.y > WINDOW_HEIGHT + self.radius
        ):
            self.__out_of_bound = True
        super().update(delta, events)


class PlayerBulletPool(Group):
    def __init__(self, *objects: Any | AbstractGroup | Iterable) -> None:
        super().__init__(*objects)
