from engine.core import KinematicObject


class Player(KinematicObject):
    def __init__(self, health: int, **kwargs):
        super().__init__(**kwargs)
        self.health: int = health

    def ready(self) -> None:
        pass
   
    def update(self, delta: float) -> None:
        super().update(delta)
        self.rotation += 20 * delta
        self.move(delta)

    def free(self) -> None:
        pass
