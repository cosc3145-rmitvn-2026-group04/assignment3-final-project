from __future__ import annotations
from pathlib import Path
import pygame
from pygame.math import Vector2
from pygame.event import Event
from engine.core import SpatialObject, KinematicObject
from game.player import Player
from game.config import *


class EnemySpawner(SpatialObject):
    def __init__(self,
            health: int,
            enemy_pool: list[Enemy],
            max_enemy_count: int,
            enemy_spawn_amount: int,
            enemy_spawn_delay: float,
            activation_delay: float,
            **kwargs
    ):
        kwargs["image"] = pygame.image.load(Path("src/part2/assets/sprite_enemy_spawner.png"))
        kwargs["radius"] = 30.0
        super().__init__(**kwargs)
        self.health: int = health
        self.enemy_pool = enemy_pool
        self.max_enemy_count: int = max_enemy_count  # The maximum amount of enemies that `pool` can have.
        self.spawn_amount: int = enemy_spawn_amount  # The amount of enemies being spawned at once per spawn cycle.
        self.enemy_spawn_delay: float = enemy_spawn_delay  # The delay in seconds between spawn cycles.
        self.activation_delay: float = activation_delay  # The duration that this spawner will sleep before activating.
        self.__ready_tick: int = pygame.time.get_ticks()
        self.__last_spawn_tick: int = 0

    def update(self, delta: float, events: list[Event]) -> None:
        current_tick: int = pygame.time.get_ticks()
        active: bool = (current_tick - self.__ready_tick) / 1000.0 >= self.activation_delay
        spawn_ready: bool = (current_tick - self.__last_spawn_tick) / 1000.0 >= self.enemy_spawn_delay
        if active and spawn_ready and len(self.enemy_pool) < self.max_enemy_count:
            self.__last_spawn_tick = current_tick
            for _ in range(self.spawn_amount):
                new_enemy: Enemy = Enemy(
                        health=ENEMY_HEALTH,
                        speed=ENEMY_SPEED,
                        position=self.position.copy())
                self.enemy_pool.append(new_enemy)
        super().update(delta, events)


class Enemy(KinematicObject):
    def __init__(self, health: int, speed: int, **kwargs):
        kwargs["image"] = pygame.image.load(Path("src/part2/assets/sprite_enemy.png"))
        kwargs["radius"] = 9.5
        super().__init__(**kwargs)
        self.health: int = health
        self.speed: int = speed

    def update(self, delta: float, events: list[Event], player: Player) -> None:
        desired_velocity: Vector2 = player.position - self.position
        if desired_velocity.length_squared() > 0.0:
            desired_velocity.clamp_magnitude_ip(self.speed, self.speed)
        steering_force: Vector2 = desired_velocity - self.velocity
        self.acceleration = steering_force / self.mass

        self.move(delta)
        super().update(delta, events)
        self.rotation = -self.velocity.as_polar()[1] - 90

        if pygame.sprite.collide_circle(self, player):
            print("Ouch!")
