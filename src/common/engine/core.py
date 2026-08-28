from typing import Any, Iterable, List

import pygame
from pygame import Surface, Rect
from pygame.math import Vector2
from pygame.event import Event
from pygame.font import Font
from pygame.sprite import AbstractGroup, Group as PygameSpriteGroup, Sprite
from common.engine.config import (
        COLOR_RENDER_DEBUG_IMAGE_RECT,
        COLOR_RENDER_DEBUG_BOUNDING_RECT,
        COLOR_RENDER_DEBUG_BOUNDING_CIRCLE,
        COLOR_RENDER_DEBUG_VELOCITY,
        COLOR_RENDER_DEBUG_ACCELERATION)


class GameObject:
    def __init__(self) -> None:
        """
        Base class for all game objects. Lean implementation of Godot's `Node`.

        - The constructor (`__init__()`) acts like both `Node._init()` and
        `Node._ready()`.
        - `update()` should be called inside of the game loop for every game
        tick, with `delta` time and `events` provided as arguments. Acts as a
        hook for custom logic. Similar in role to `Node._process()` combined
        with `Node._input()` in Godot. More arguments can be passed in using
        `*args` and `**kwargs` for access to external references.
        """
        pass

    def update(self, delta: float, events: list[Event], *args, **kwargs) -> None:
        pass


class UserInterface(GameObject):
    def __init__(self,
            rect: Rect,
            fonts: dict[str, Font]
    ):
        """
        Base class for game UI. Manipulate the `surface` property in `update()`
        to be rendered in `draw()`.
        """
        super().__init__()
        self.rect: Rect = rect
        self.fonts: dict[str, Font] = fonts
        self.surface: Surface = Surface(Vector2(self.rect.width, self.rect.height))

    def update(self, delta: float, events: list[Event], *args, **kwargs) -> None:
        pass

    def draw(self, screen: Surface) -> None:
        screen.blit(self.surface, Vector2(self.rect.x, self.rect.y))


class SpatialObject(GameObject, Sprite):
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
        Base class for all visible game objects, inherits
        `pygame.sprite.Sprite` features. Lean implementation of Godot's
        `Node2D`.

        Notes on properties:
        - `rotation` is in degrees.
        - `scale` does not affect `radius`, but does affect the bounding box,
        which affects rectangular but not circular collision detection (using
        `pygame.sprite.spritecollide()` and related methods).
        - `radius` is only used for circular collision detection and nothing
        else.
        - Similar to Godot's `Node2D`, but with built-in "Sprite" if `image` is
        specified, otherwise it would be invisible.
        - The bounding box (`rect`) and `image` is automatically updated from
        using the current values of `position`, `rotation`, `scale`, `flip_x`,
        and `flip_y`.
        - `offset` only affects the visual position of the rendered sprite on
        the screen, not the actual position of the object. Always relative to
        the object's transformation.

        Compatible with `pygame.sprite.Group` and its children classes, except
        for the `draw()` method, which must be manually called for each object
        per frame due to its custom rendering logic. USING
        `pygame.sprite.Group.draw()` WILL RESULT IN INCORRECT OUTPUT.
        """
        GameObject.__init__(self)
        Sprite.__init__(self, *groups)
        self.position: Vector2 = position if position else Vector2(0, 0)
        self.rotation: float = rotation
        self.scale: Vector2 = scale if scale else Vector2(1, 1)
        self.flip_x: bool = flip_x
        self.flip_y: bool = flip_y
        self.offset: Vector2 = offset if offset else Vector2(0, 0)
        self.radius = radius
        self._image_source: Surface = image if image else Surface(Vector2(0, 0))
        self.__update_internal()

    def update(self, delta: float, events: list[Event], *args, **kwargs) -> None:
        self.__update_internal()
        super().update(delta, events, *args, **kwargs)

    def draw(self,
            screen: Surface,
            debug_image_rect: bool = False,
            debug_bounding_rect: bool = False,
            debug_bounding_circle: bool = False
    ) -> None:
        draw_offset: Vector2 = -self.offset.rotate(-self.rotation)
        screen.blit(source=self.image, dest=self.rect.move(draw_offset.x, draw_offset.y))
        if debug_image_rect:
            pygame.draw.rect(
                    surface=screen,
                    color=COLOR_RENDER_DEBUG_IMAGE_RECT,
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
        self.image: Surface = self._image_source.copy()
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
        properties and movement. Inherits `SpatialObject`. Lean implementation
        of Godot's `CharacterBody2D`.

        Notes:
        - The physical properties are `velocity` (defaults to zero),
        `acceleration` (defaults to zero) and `mass` (defaults to 1.0).
        - `position` can be updated either directly or automatically by using
        the `move()` method. All updates should be implemented in `update()`.
        - Unlike Godot's `CharacterBody2D`, there is no built-in collision
        detection. Use `pygame.sprite.spritecollide()`, related methods, plus
        manual update of `position` instead.
        - `rotation` is decoupled from movement and there is no angular
        momentum. Provide custom implementation if needed.
        """
        super().__init__(**kwargs)
        self.velocity: Vector2 = velocity if velocity else Vector2(0, 0)
        self.acceleration: Vector2 = acceleration if acceleration else Vector2(0, 0)
        self.mass: float = mass

    def update(self, delta: float, events: list[Event], *args, **kwargs) -> None:
        super().update(delta, events, *args, **kwargs)

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


class Group(PygameSpriteGroup):
    def __init__(self, *game_objects: Any | AbstractGroup | Iterable) -> None:
        """
        Thin wrapper for `pygame.sprite.Group` with logic for custom classes in
        this project.
        """
        super().__init__(*game_objects)

    def objects(self) -> List:
        """Returns a list of objects in the group"""
        return super().sprites()

    def draw(self, surface: Surface, *args, **kwargs) -> List[Rect]:
        # Overload pygame.sprite.Group.draw() behavior.
        for obj in self.objects():
            if hasattr(obj, "draw") and callable(getattr(obj, "draw")):
                obj.draw(surface, *args, **kwargs)

        # This is what pygame does in pygame.sprite.Group.draw() to set the
        # correct state and return value. Do not modify.
        self.lostsprites = []
        dirty = self.lostsprites
        return dirty
