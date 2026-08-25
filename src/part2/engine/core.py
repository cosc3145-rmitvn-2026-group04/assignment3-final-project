from abc import ABC, abstractmethod
from pygame import Surface, Rect
from pygame.sprite import AbstractGroup, Sprite
from pygame.math import Vector2
import pygame
from engine.config import (
        COLOR_RENDER_DEBUG_BOUNDING_RECT,
        COLOR_RENDER_DEBUG_BOUNDING_CIRCLE,
        COLOR_RENDER_DEBUG_VELOCITY,
        COLOR_RENDER_DEBUG_ACCELERATION)


class SpatialObject(Sprite, ABC):
    def __init__(self,
            position: Vector2 | None = None,
            rotation: float = 0.0,
            scale: Vector2 | None = None,
            flip_x: bool = False,
            flip_y: bool = False,
            offset: Vector2 | None = None,
            image: Surface | None = None,
            radius: float = 0.0,
            *groups: AbstractGroup
    ):
        """
        Base class for all game objects, inherits pygame.sprite.Sprite
        features. Lean implementation of Godot's Node2D.

        Notes on properties:
        - `rotation` is in degrees.
        - `scale` does not affect `radius`, but does affect the bounding box,
        which affects rectangular but not circular collision detection (using
        `pygame.sprite.spritecollide()` and related methods).
        - `radius` is only used for circular collision detection and nothing
        else.
        - Similar to Godot's Node2D, but with built-in "Sprite" if `image` is
        specified, otherwise it would be invisible.
        - The bounding box (`rect`) and `image` is automatically updated from
        using the current values of `position`, `rotation`, `scale`, `flip_x`,
        and `flip_y`.
        - `offset` only affects the visual position of the rendered sprite on
        the screen, not the actual position of the object. Always relative to
        the object's transformation.

        Notes on methods: Modelled after Godot's architecture. These 3 methods
        should be overriden to provide custom implementations based on the game
        object:
        - `ready()` should be called outside of the game loop.
        - `update()` should be called inside of the game loop for every game
        tick, with delta time provided as an argument.
        - `free()` can be called at discretion if overriden with cleanup logic
        for performance, or to keep the game in a valid state.

        Remember to call `draw()` at each frame to render the game object.
        """
        super().__init__(*groups)
        self.position: Vector2 = position if position else Vector2(0, 0)
        self.rotation: float = rotation
        self.scale: Vector2 = scale if scale else Vector2(1, 1)
        self.flip_x: bool = flip_x
        self.flip_y: bool = flip_y
        self.offset: Vector2 = offset if offset else Vector2(0, 0)
        self.radius = radius
        self.__image_source: Surface = image if image else Surface(Vector2(0, 0))
        self.__update_internal()

    @abstractmethod 
    def ready(self) -> None:
        pass
   
    @abstractmethod
    def update(self, delta: float) -> None:
        self.__update_internal()
        pass
    
    @abstractmethod
    def free(self) -> None:
        pass

    def draw(self,
            screen: Surface,
            debug_bounding_rect: bool = False,
            debug_bounding_circle: bool = False
    ) -> None:
        draw_offset: Vector2 = -self.offset.rotate(-self.rotation)
        screen.blit(source=self.image, dest=self.rect.move(draw_offset.x, draw_offset.y))
        pygame.draw.rect(
                surface=screen,
                color=COLOR_RENDER_DEBUG_VELOCITY,
                rect=self.rect.move(draw_offset.x, draw_offset.y),
                width=1)
        if debug_bounding_rect:
            pygame.draw.rect(
                    surface=screen,
                    color=COLOR_RENDER_DEBUG_BOUNDING_RECT,
                    rect=self.rect,
                    width=1)
        if debug_bounding_circle:
            pygame.draw.circle(
                    surface=screen,
                    color=COLOR_RENDER_DEBUG_BOUNDING_CIRCLE,
                    center=self.position,
                    radius=self.radius,
                    width=1)

    def __update_internal(self) -> None:
        self.image: Surface = self.__image_source.copy()
        self.image = pygame.transform.flip(self.image, self.flip_x, self.flip_y)
        self.image = pygame.transform.smoothscale_by(self.image, (self.scale.x, self.scale.y))
        self.image = pygame.transform.rotozoom(self.image, self.rotation, 1.0) 
        self.rect: Rect = self.image.get_rect(center=self.position)


class KinematicObject(SpatialObject):
    def __init__(self,
            velocity: Vector2 | None = None,
            acceleration: Vector2 | None = None,
            mass: float = 1.0,
            **kwargs
    ):
        """
        Base class for all game objects with programmable physics-based
        properties and movement. Inherits SpatialObject. Lean implementation of
        Godot's CharacterBody2D.

        Notes:
        - The physical properties are `velocity` (defaults to zero),
        `acceleration` (defaults to zero) and `mass` (defaults to 1.0).
        - `position` can be updated either directly or automatically by using
        the `move()` method. All updates should be implemented in `update()`.
        - Unlike Godot's CharacterBody2D, there is no built-in collision
        detection. Use `pygame.sprite.spritecollide()`, related methods, plus
        manual update of `position` instead.
        - `rotation` is decoupled from movement. Provide custom implementation
        if needed.
        """
        super().__init__(**kwargs)
        self.velocity: Vector2 = velocity if velocity else Vector2(0, 0)
        self.acceleration: Vector2 = acceleration if acceleration else Vector2(0, 0)
        self.mass: float = mass
    
    @abstractmethod 
    def ready(self) -> None:
        pass
   
    @abstractmethod
    def update(self, delta: float) -> None:
        super().update(delta)
    
    @abstractmethod
    def free(self) -> None:
        pass

    def draw(self,
            screen: Surface, *args,
            debug_velocity: bool = False,
            debug_acceleration: bool = False,
            **kwargs
    ) -> None:
        super().draw(screen, *args, **kwargs)
        if debug_velocity:
            pygame.draw.line(
                    surface=screen,
                    color=COLOR_RENDER_DEBUG_VELOCITY,
                    start_pos=self.position,
                    end_pos=(self.position + self.velocity),
                    width=1)
        if debug_acceleration:
            pygame.draw.line(
                    surface=screen,
                    color=COLOR_RENDER_DEBUG_ACCELERATION,
                    start_pos=(self.position + self.velocity),
                    end_pos=(self.position + self.velocity + self.acceleration),
                    width=1)

    def move(self, delta: float) -> None:
        self.velocity += self.acceleration * delta
        self.position += self.velocity * delta
    