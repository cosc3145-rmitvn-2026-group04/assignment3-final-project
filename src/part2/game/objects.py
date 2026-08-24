from abc import ABC, abstractmethod
from pathlib import Path
from pygame import Vector2, Surface
import pygame


class GameObject(ABC):
    def __init__(self,
            position: Vector2 | None = None,
            rotation: float = 0.0,
            scale: Vector2 | None = None
    ):
        """Base class for all game objects."""
        self.position: Vector2 = position if position else Vector2(0, 0)
        self.rotation: float = rotation
        self.scale: Vector2 = scale if scale else Vector2(1, 1)
    
    @abstractmethod 
    def ready(self) -> None:
        pass
   
    @abstractmethod
    def update(self, delta: float) -> None:
        pass
    
    @abstractmethod
    def draw(self, screen: Surface) -> None:
        pass

    @abstractmethod
    def free(self) -> None:
        pass


class PhysicsObject(GameObject):
    def __init__(self,
            position: Vector2 | None = None,
            rotation: float = 0,
            scale: Vector2 | None = None,
            velocity: Vector2 | None = None,
            acceleration: Vector2 | None = None,
            mass: float = 1.0
    ):
        """Base class for all game objects with physics properties."""
        super().__init__(position, rotation, scale)
        self.velocity: Vector2 = velocity if velocity else Vector2(0, 0)
        self.acceleration: Vector2 = acceleration if acceleration else Vector2(0, 0)
        self.mass: float = mass
    
    @abstractmethod 
    def ready(self) -> None:
        pass
   
    @abstractmethod
    def update(self, delta: float) -> None:
        pass
    
    @abstractmethod
    def draw(self, screen: Surface) -> None:
        pass

    @abstractmethod
    def free(self) -> None:
        pass


class Player(PhysicsObject):
    def __init__(self,
            health: int,
            position: Vector2 | None = None,
            rotation: float = 0,
            scale: Vector2 | None = None,
            velocity: Vector2 | None = None,
            acceleration: Vector2 | None = None,
            mass: float = 1.0
    ):
        super().__init__(position, rotation, scale, velocity, acceleration, mass)
        self.health: int = health
        self.__sprite: Surface

    def ready(self) -> None:
        self.__sprite = pygame.image.load(Path("src/part2/assets/sprite_player.png"))
   
    def update(self, delta: float) -> None:
        pass
    
    def draw(self, screen: Surface) -> None:
        screen.blit(self.__sprite, self.position)

    def free(self) -> None:
        pass
