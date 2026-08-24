from pygame import Vector2


class GameObject:
    def __init__(self,
            position: Vector2 = Vector2(0, 0),
            rotation: float = 0.0,
            scale: Vector2 = Vector2(1, 1)
    ):
        """Base class for all game objects.

        Args:
            position (Vector2, optional): Global position in the game window.
                Defaults to Vector2(0, 0).
            rotation (float, optional): Rotation in degrees. Positive rotates
                anti-clockwise, nagative rotates clockwise. Defaults to 0.0
                (pointing upward).
            scale (Vector2, optional): Global scale of the game object.
                Defaults to Vector2(1, 1).
        """
        self.position: Vector2 = position
        self.rotation: float = rotation
        self.scale: Vector2 = scale
        self.components: list[Component] = []


class Component:
    def __init__(self, parent: GameObject) -> None:
        self.parent: GameObject
