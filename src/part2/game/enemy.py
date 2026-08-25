import pygame
from pygame.math import Vector2
from pygame.event import Event
from engine.core import SpatialObject, KinematicObject
from game.player import Player


class EnemySpawner(SpatialObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def ready(self) -> None:
        pass
   
    def update(self, delta: float, events: list[Event]) -> None:
        super().update(delta, events)

    def free(self) -> None:
        pass


class Enemy(KinematicObject):
    def __init__(self, health: int, speed: int, **kwargs):
        super().__init__(**kwargs)
        self.health: int = health
        self.speed: int = speed
    
    def ready(self) -> None:
        pass
   
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

    def free(self) -> None:
        pass
