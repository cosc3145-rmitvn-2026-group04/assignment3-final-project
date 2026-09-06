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
from part2.engine.core import Timer, SpatialObject, KinematicObject, Group
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
        self.max_health: int = health
        self.enemy_spawn_amount: int = enemy_spawn_amount  # The amount of enemies being spawned at once per spawn cycle.
        self.enemy_spawn_cooldown_timer: Timer = Timer(wait_time=enemy_spawn_delay, one_shot=True)
        self.activation_timer: Timer = Timer(wait_time=activation_delay, one_shot=True, autostart=True)
        self.invulnerable: bool = False
        self.invulnerable_timer: Timer = Timer(0.1, one_shot=True)
        self.__first_spawn: bool = True
        self.__killed: bool = False
        self.__kill_cooldown_timer: Timer = Timer(wait_time=0.05, one_shot=True)

    def update(self, delta: float, events: list[Event], enemy_pool: EnemyPool) -> None:
        self.__kill_cooldown_timer.update(delta)
        if self.__killed and self.__kill_cooldown_timer.is_stopped():
            self.kill()
            return

        self.activation_timer.update(delta)
        self.enemy_spawn_cooldown_timer.update(delta)
        active: bool = self.activation_timer.is_stopped()
        spawn_ready: bool = self.enemy_spawn_cooldown_timer.is_stopped()
        if (
            active
            and (spawn_ready or self.__first_spawn)
            and len(enemy_pool.objects()) < enemy_pool.max_size
        ):
            self.enemy_spawn_cooldown_timer.start()
            if self.__first_spawn:
                self.__first_spawn = False
            for _ in range(self.enemy_spawn_amount):
                new_enemy: Enemy = Enemy(
                        speed=ENEMY_SPEED,
                        position=self.position.copy())
                enemy_pool.add(new_enemy)
        super().update(delta, events)

        if (
            not self.__first_spawn
            and self.enemy_spawn_cooldown_timer.wait_time - self.enemy_spawn_cooldown_timer.time_left <= 0.1
            and len(enemy_pool.objects()) <= enemy_pool.max_size
        ):
            self.scale = Vector2(1.1, 1.1)
        else:
            self.scale = Vector2(1.0, 1.0)

        self.invulnerable_timer.update(delta)
        if self.invulnerable:
            if not self.invulnerable_timer.is_stopped():
                self.scale = Vector2(0.9, 0.9)
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_enemy_spawner_hurt.png")
            else:
                self.scale = Vector2(1.0, 1.0)
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_enemy_spawner.png")
                self.invulnerable = False

    def hurt(self) -> None:
        if not self.invulnerable:
            if self.health > 0:
                self.health -= 1
            if self.health == 0:
                self.scale = Vector2(0.8, 0.8)
                self._image_source = pygame.image.load(ASSET_DIR / "sprite_enemy_spawner_kill.png")
                self.__killed = True
                self.__kill_cooldown_timer.start()
                return
            self.invulnerable = True
            self.invulnerable_timer.start()

    def draw(self,
            screen: Surface,
            fonts: dict[str, Font],
            *args, **kwargs
    ) -> None:
        super().draw(screen, *args, **kwargs)
        hp_bar_text: str = "[%d/%d HP]" % (self.health, self.max_health)
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
    def __init__(self, speed: float, **kwargs):
        kwargs["image"] = pygame.image.load(ASSET_DIR / "sprite_enemy.png")
        kwargs["radius"] = 10.0
        super().__init__(**kwargs)
        self.speed: float = speed

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
