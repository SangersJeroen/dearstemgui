from dearstemgui.states.libertem_state import LibertemSate
from libertem.api import DataSet
from typing import Any


class AppState:
    def __init__(self) -> None:
        self.libertem_state: LibertemSate = LibertemSate()
        self.loaded_measurements: dict[int, Any] = {}

    def add_measurement(self, measurement) -> None:
        indices = sorted(self.loaded_measurements.keys())
        if len(indices) > 0:
            new_idx: int = indices[-1] + 1
        else:
            new_idx: int = 0
        self.loaded_measurements[new_idx] = measurement
