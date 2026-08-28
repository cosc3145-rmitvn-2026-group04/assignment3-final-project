from __future__ import annotations
from typing import Any, Iterable
import pygame
from pygame import Surface
from pygame.math import Vector2
from pygame.sprite import AbstractGroup
from pygame.font import Font
from pygame.event import Event
from part2.config import (
        ASSET_DIR,
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        MAIN_HUD_HEIGHT,
        COLOR_RED)
from common.engine.core import SpatialObject, KinematicObject, Group
import part2.game.player as player
from part2.game.config import (
        ENEMY_SPEED,
        ENEMY_SEPARATION_ACTIVATE_RADIUS,
        ENEMY_SEPARATION_FORCE_WEIGHT)


class EnemySpawner(SpatialObject):
    def __init__(self,
            health: int,
            enemy_spawn_amount: int,
            enemy_spawn_delay: float,
            activation_delay: float,
            **kwargs
    ):
        kwargs["image"] = pygame.image.load(ASSET_DIR / "sprite_enemy_spawner.png")
        kwargs["radius"] = 30.0
        super().__init__(**kwargs)
        self.health: int = health
        self.spawn_amount: int = enemy_spawn_amount  # The amount of enemies being spawned at once per spawn cycle.
        self.enemy_spawn_delay: float = enemy_spawn_delay  # The delay in seconds between spawn cycles.
        self.activation_delay: float = activation_delay  # The duration that this spawner will sleep before activating.
        self.invulnerable: bool = False
        self.last_invulnerable_tick: int = pygame.time.get_ticks()
        self.__max_health: int = health
        self.__ready_tick: int = pygame.time.get_ticks()
        self.__last_spawn_tick: int = pygame.time.get_ticks()
        self.__first_spawn: bool = True
        self.__killed: bool = False
        self.__killed_tick: int = pygame.time.get_ticks()

    def update(self, delta: float, events: list[Event], enemy_pool: EnemyPool) -> None:
        current_tick: int = pygame.time.get_ticks()

        if self.__killed and (current_tick - self.__killed_tick) / 1000.0 > 0.05:
            self.kill()
            return

        active: bool = (current_tick - self.__ready_tick) / 1000.0 >= self.activation_delay
        spawn_ready: bool = (current_tick - self.__last_spawn_tick) / 1000.0 >= self.enemy_spawn_delay
        if (
            active
            and (spawn_ready or self.__first_spawn)
            and len(enemy_pool.objects()) < enemy_pool.max_size
        ):
            if self.__first_spawn:
                self.__first_spawn = False
            self.__last_spawn_tick = current_tick
            for _ in range(self.spawn_amount):
                new_enemy: Enemy = Enemy(
                        speed=ENEMY_SPEED,
                        position=self.position.copy())
                enemy_pool.add(new_enemy)
        super().update(delta, events)

        if (
            not self.__first_spawn
            and (current_tick - self.__last_spawn_tick) / 1000.0 <= 0.1
            and len(enemy_pool.objects()) <= enemy_pool.max_size
        ):
            self.scale = Vector2(1.1, 1.1)
        else:
            self.scale = Vector2(1.0, 1.0)

        if self.invulnerable:
            current_tick: int = pygame.time.get_ticks()

            if (current_tick - self.last_invulnerable_tick) / 1000.0 <= 0.1:
                self.scale = Vector2(0.9, 0.9)
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_enemy_spawner_hurt.png")
            else:
                self.scale = Vector2(1.0, 1.0)
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_enemy_spawner.png")
                self.invulnerable = False

    def hurt(self) -> None:
        if self.health > 0:
            self.health -= 1
        if self.health == 0:
            self.scale = Vector2(0.8, 0.8)
            self._image_source = pygame.image.load(ASSET_DIR / "sprite_enemy_spawner_kill.png")
            self.__killed = True
            self.__killed_tick = pygame.time.get_ticks()
            return
        self.invulnerable = True
        self.last_invulnerable_tick = pygame.time.get_ticks()

    def draw(self,
            screen: Surface,
            fonts: dict[str, Font],
            *args, **kwargs
    ) -> None:
        super().draw(screen, *args, **kwargs)
        hp_bar_text: str = "[%d/%d HP]" % (self.health, self.__max_health)
        hp_bar_label: Surface = fonts["small"].render(
                hp_bar_text,
                True, COLOR_RED)
        screen.blit(
                hp_bar_label,
                (
                    self.position
                    - Vector2(
                            hp_bar_label.get_width() // 2,
                            self.radius + hp_bar_label.get_height() * 1.5)
                ))


class EnemySpawnerPool(Group):
    def __init__(self, *game_objects: Any | AbstractGroup | Iterable) -> None:
        super().__init__(*game_objects)


class Enemy(KinematicObject):
    def __init__(self, speed: int, **kwargs):
        kwargs["image"] = pygame.image.load(ASSET_DIR / "sprite_enemy.png")
        kwargs["radius"] = 10.0
        super().__init__(**kwargs)
        self.speed: int = speed

    def update(self,
            delta: float,
            events: list[Event],
            player: player.Player,
            enemy_pool: EnemyPool
    ) -> None:
        self.acceleration = self._get_seek_force(player.position)
        self.acceleration += self._get_separation_force(enemy_pool)

        self.move(delta)
        self._limit_screen_bound()
        super().update(delta, events)
        self.rotation = -self.velocity.as_polar()[1] - 90

        if pygame.sprite.collide_circle(self, player):
            if not player.invulnerable:
                player.hurt()

    def hurt(self) -> None:
        self.kill()

    def _get_seek_force(self, target_position: Vector2) -> Vector2:
        desired_velocity: Vector2 = target_position - self.position
        if desired_velocity.length_squared() > 0.0:
            desired_velocity.clamp_magnitude_ip(self.speed, self.speed)
        return desired_velocity - self.velocity

    def _get_separation_force(self, enemy_pool: EnemyPool) -> Vector2:
        r: Vector2 = Vector2(0, 0)
        neighbor: Enemy
        for neighbor in enemy_pool.objects():
            if not self is neighbor:
                to_neighbor: Vector2 = self.position - neighbor.position
                distance_to_neighbor: float = to_neighbor.length()
                if 0.0 < distance_to_neighbor <= ENEMY_SEPARATION_ACTIVATE_RADIUS:
                    separation_force: Vector2 = (
                        to_neighbor
                        * ENEMY_SEPARATION_FORCE_WEIGHT
                        / distance_to_neighbor
                    )
                    r += separation_force
        return r

    def _limit_screen_bound(self) -> None:
        x: float
        y: float
        x, y = self.position.x, self.position.y
        x = pygame.math.clamp(x, self.radius, WINDOW_WIDTH - self.radius)
        y = pygame.math.clamp(y, self.radius, WINDOW_HEIGHT - MAIN_HUD_HEIGHT - self.radius)
        if x != self.position.x or y != self.position.y:
            self.position = Vector2(x, y)


class EnemyPool(Group):
    def __init__(self,
            max_size: int,
            *objects: Any | AbstractGroup | Iterable
    ) -> None:
        self.max_size: int = max_size
        super().__init__(*objects)

    def add(self, *sprites: Any | AbstractGroup | Iterable) -> None:
        if len(self.objects()) < self.max_size:
            super().add(*sprites)
