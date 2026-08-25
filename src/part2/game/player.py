import pygame
from pygame.math import Vector2
from pygame.key import ScancodeWrapper
from pygame.event import Event
from engine.core import KinematicObject


class Player(KinematicObject):
    def __init__(self, health: int, speed: int, angular_speed: float, **kwargs):
        super().__init__(**kwargs)
        self.health: int = health
        self.speed: int = speed
        self.angular_speed: float = angular_speed

    def ready(self) -> None:
        pass
   
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
                print("Bang!")

        self.move(delta)
        super().update(delta, events)

    def free(self) -> None:
        pass

class Bullet(KinematicObject):
    def __init__(self, velocity = None, acceleration = None, mass = 1, **kwargs):
        super().__init__(velocity, acceleration, mass, **kwargs)
        
    def ready(self) -> None:
        pass
    
    def update(self, delta, events):
        return super().update(delta, events)
    