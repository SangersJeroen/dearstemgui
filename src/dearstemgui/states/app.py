from dearstemgui.states.libertem_state import LibertemSate


class AppState:
    def __init__(self) -> None:
        self.libertem_state: LibertemSate = LibertemSate()
