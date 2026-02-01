from typing import Any

from dearstemgui.states.libertem_state import LibertemSate


class AppState:
    def __init__(self) -> None:
        self.libertem_state: LibertemSate = LibertemSate()
        self.loaded_measurements: dict[int, Any] = {}

    def add_measurement(self, measurement) -> int:
        indices = sorted(self.loaded_measurements.keys())
        if len(indices) > 0:
            new_idx: int = indices[-1] + 1
        else:
            new_idx: int = 0
        self.loaded_measurements[new_idx] = measurement
        return new_idx
