from __future__ import annotations
from typing import Any, Iterable
from enum import Enum
import pygame
from pygame.math import Vector2
from pygame.sprite import AbstractGroup
from pygame.key import ScancodeWrapper
from pygame.event import Event
from part2.config import (
        ASSET_DIR,
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        MAIN_HUD_HEIGHT)
from part2.engine.core import GameObject, Timer, KinematicObject, Group
import part2.game.enemy as enemy
from part2.game.config import (
        PLAYER_HEALTH,
        PLAYER_INVULNERABLE_COOLDOWN_DURATION,
        PLAYER_SPEED,
        PLAYER_ANGULAR_SPEED,
        PLAYER_SHOOTING_COOLDOWN,
        PLAYER_BULLET_SPEED)


class Action(Enum):
    NONE = 0
    SHOOT = 1

    # Action style A.
    THRUST_FORWARD = 2
    ROTATE_LEFT = 3
    ROTATE_RIGHT = 4

    # Action style B.
    MOVE_UP = 5
    MOVE_LEFT = 6
    MOVE_DOWN = 7
    MOVE_RIGHT = 8


class ActionStyle(Enum):
    STYLE_A = 0
    STYLE_B = 1


ACTIONS: dict[ActionStyle, dict[int, Action]] = {
    ActionStyle.STYLE_A: {
        0: Action.NONE,
        1: Action.SHOOT,
        2: Action.THRUST_FORWARD,
        3: Action.ROTATE_LEFT,
        4: Action.ROTATE_RIGHT,
    },
    ActionStyle.STYLE_B: {
        0: Action.NONE,
        1: Action.SHOOT,
        2: Action.MOVE_UP,
        3: Action.MOVE_LEFT,
        4: Action.MOVE_DOWN,
        5: Action.MOVE_RIGHT,
    },
}


class PlayerController(GameObject):
    def __init__(self) -> None:
        super().__init__()
        self.player: Player | None = None

    def attach_player(self, player: Player) -> None:
        self.player = player


class PlayerControllerInputStyleA(PlayerController):
    def __init__(self) -> None:
        super().__init__()

    def update(self, delta: float, events: list[Event], *args, **kwargs) -> None:
        super().update(delta, events, *args, **kwargs)

        if self.player:
            pressed_keys: ScancodeWrapper = pygame.key.get_pressed()
            if pressed_keys[pygame.K_SPACE]:
                self.player.apply_action(Action.SHOOT)
            if pressed_keys[pygame.K_UP] or pressed_keys[pygame.K_w]:
                self.player.apply_action(Action.THRUST_FORWARD)
            if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
                self.player.apply_action(Action.ROTATE_LEFT)
            if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
                self.player.apply_action(Action.ROTATE_RIGHT)


class PlayerControllerInputStyleB(PlayerController):
    def __init__(self) -> None:
        super().__init__()

    def update(self, delta: float, events: list[Event], *args, **kwargs) -> None:
        super().update(delta, events, *args, **kwargs)

        if self.player:
            pressed_keys: ScancodeWrapper = pygame.key.get_pressed()
            if pressed_keys[pygame.K_SPACE]:
                self.player.apply_action(Action.SHOOT)
            if pressed_keys[pygame.K_UP] or pressed_keys[pygame.K_w]:
                self.player.apply_action(Action.MOVE_UP)
            if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
                self.player.apply_action(Action.MOVE_LEFT)
            if pressed_keys[pygame.K_DOWN] or pressed_keys[pygame.K_s]:
                self.player.apply_action(Action.MOVE_DOWN)
            if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
                self.player.apply_action(Action.MOVE_RIGHT)


class Player(KinematicObject):
    def __init__(self,
            controller: PlayerController,
            health: int = PLAYER_HEALTH,
            speed: float = PLAYER_SPEED,
            angular_speed: float = PLAYER_ANGULAR_SPEED,
            bullet_pool: PlayerBulletPool | None = None,
            position: Vector2 | None = None,
            **kwargs
    ):
        kwargs["position"] = position if position else Vector2(0, 0)
        kwargs["image"] = pygame.image.load(ASSET_DIR / "sprite_player.png")
        kwargs["radius"]=12.0
        kwargs["offset"]=Vector2(0, 4)
        super().__init__(**kwargs)
        self.controller: PlayerController = controller
        self.health: int = health
        self.max_health: int = health
        self.speed: float = speed
        self.angular_speed: float = angular_speed
        self.angular_velocity: float = 0.0
        self.bullet_pool: PlayerBulletPool | None = bullet_pool
        self.shooting_enabled: bool = True
        self.shooting_cooldown_timer: Timer = Timer(wait_time=PLAYER_SHOOTING_COOLDOWN, one_shot=True)
        self.invulnerable: bool = False
        self.invulnerable_timer: Timer = Timer(wait_time=PLAYER_INVULNERABLE_COOLDOWN_DURATION, one_shot=True)

    def update(self, delta: float, events: list[Event]) -> None:
        self.angular_velocity = 0.0
        self.velocity = Vector2(0, 0)
        self.controller.update(delta, events)

        self.move(delta)
        self._limit_screen_bound()
        super().update(delta, events)

        self.shooting_cooldown_timer.update(delta)
        if not self.shooting_enabled and self.shooting_cooldown_timer.is_stopped():
            self.shooting_enabled = True

        self.invulnerable_timer.update(delta)
        if self.invulnerable:
            if (
                not self.invulnerable_timer.is_stopped()
                and self.invulnerable_timer.wait_time - self.invulnerable_timer.time_left < 0.1
            ):
                self.scale = Vector2(0.9, 0.9)
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_player_hurt.png")
            elif not self.invulnerable_timer.is_stopped():
                self.scale = Vector2(1, 1)
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_player_invulnerable.png")
            else:
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_player.png")
                self.invulnerable = False

    def apply_action(self, action: Action) -> None:
        self.angular_velocity = 0.0
        match action:
            case Action.NONE:
                return
            case Action.SHOOT:
                self.shoot()

            # Action style A.
            case Action.THRUST_FORWARD:
                self.velocity = Vector2(0, -1).rotate(-self.rotation) * self.speed
            case Action.ROTATE_LEFT:
                self.angular_velocity = self.angular_speed
            case Action.ROTATE_RIGHT:
                self.angular_velocity = -self.angular_speed

            # Action style B.
            case Action.MOVE_UP:
                self.rotation = 0.0
                self.velocity = Vector2(0, -1).rotate(-self.rotation) * self.speed
            case Action.MOVE_LEFT:
                self.rotation = 90.0
                self.velocity = Vector2(0, -1).rotate(-self.rotation) * self.speed
            case Action.MOVE_DOWN:
                self.rotation = 180.0
                self.velocity = Vector2(0, -1).rotate(-self.rotation) * self.speed
            case Action.MOVE_RIGHT:
                self.rotation = 270.0
                self.velocity = Vector2(0, -1).rotate(-self.rotation) * self.speed

    def shoot(self) -> None:
        if self.shooting_enabled and not self.bullet_pool is None:
            self.shooting_enabled = False
            self.shooting_cooldown_timer.start()
            new_bullet = PlayerBullet(
                speed = PLAYER_BULLET_SPEED,
                position = Vector2(self.position),
                rotation = self.rotation,
            )
            self.bullet_pool.add(new_bullet)

    def hurt(self) -> None:
        if self.health > 0:
            self.health -= 1
        self.invulnerable = True
        self.invulnerable_timer.start()

    def move(self, delta: float) -> None:
        self.rotation += self.angular_velocity * delta
        return super().move(delta)

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

    def update(self,
            delta,
            events: list[Event],
            enemy_spawner_pool: enemy.EnemySpawnerPool,
            enemy_pool: enemy.EnemyPool
    ) -> None:
        if self.alive() and (self.__out_of_bound or self.__collided):
            self.kill()
            return

        collided_enemy_spawners: list[enemy.EnemySpawner] = pygame.sprite.spritecollide(
                sprite=self, # type: ignore
                group=enemy_spawner_pool,
                dokill=False,
                collided=pygame.sprite.collide_circle)
        collided_enemy_spawner: enemy.EnemySpawner
        for collided_enemy_spawner in collided_enemy_spawners:
            collided_enemy_spawner.hurt()
            if not self.__collided:
                self.__collided = True

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

        if not self.__collided:
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
