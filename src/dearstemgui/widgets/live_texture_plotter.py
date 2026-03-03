from types import UnionType
from typing import Callable
from libertem.api import UDF, UDFResults
from libertem.io.dataset.empad import EMPADDataSet
from libertem.viz.base import Live2DPlot

import numpy as np

Channel: UnionType = str | tuple[str, Callable[[np.ndarray], np.ndarray]] | None


class LiveImPlotElement(Live2DPlot):
    def __init__(
        self,
        dataset: EMPADDataSet,
        udf: UDF,
        update_callback: Callable[[np.ndarray], None],
        roi: np.ndarray | None = None,
        channel: Channel = None,
        title: str | None = None,
        min_delta: float = 1/60,
        udfresult: UDFResults | None = None,
    ):
        self._callback = update_callback
        super().__init__(dataset, udf, roi, channel, title, min_delta, udfresult)

    def display(self) -> None:
        # Should be handles by the `ImPlotElement`
        pass

    def update(self, damage: np.ndarray, force: bool = False) -> None:
        self._callback(self.data)
