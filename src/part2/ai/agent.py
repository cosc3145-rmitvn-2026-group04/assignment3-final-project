from pygame import Event
from part2.game.player import Action, PlayerController


class PlayerControllerAI(PlayerController):
    def __init__(self) -> None:
        super().__init__()

    def update(self,
            delta: float,
            events: list[Event],
            action: Action = Action.NONE,
            *args, **kwargs
    ) -> None:
        super().update(delta, events, *args, **kwargs)
        if self.player and action != Action.NONE:
            self.player.apply_action(delta, action)
