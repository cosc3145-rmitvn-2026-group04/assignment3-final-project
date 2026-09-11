from pygame.event import Event
from part2.game.player import Action, PlayerController


class PlayerControllerAgent(PlayerController):
    def __init__(self) -> None:
        super().__init__()
        self.__actions: list[Action] = []

    def set_actions(self, actions: list[Action]) -> None:
        self.__actions = actions

    def get_actions(self) -> list[Action]:
        return self.__actions

    def update(self, delta: float, events: list[Event], *args, **kwargs) -> None:
        super().update(delta, events, *args, **kwargs)
        action: Action
        for action in self.__actions:
            if self.player and action != Action.NONE:
                self.player.apply_action(action)
