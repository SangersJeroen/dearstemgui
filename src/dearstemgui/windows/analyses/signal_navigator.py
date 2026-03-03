from typing import TYPE_CHECKING

import dearpygui.dearpygui as dpg
from libertem.api import Context

if TYPE_CHECKING:
    from libertem.io.dataset.empad import EMPADDataSet

from libertem.udf.raw import PickUDF
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets import ImPlotElement, navigation_element


class MRSTEMNavigator:
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        self.tag_prefix: str = str(measurement.index) + "_" + "ds_nav_"
        self.tag_suffix: str = "_" + tag_suffix

        self.measurement: EMPAD_Measurements = measurement
        self.measurement.update_nav_callbacks.append(self.update_signal)

        self.ds: EMPADDataSet = measurement.dataset
        self.ctx: Context = ctx

        self.nav_shape: tuple[int, int] = self.ds.shape.nav
        self.sig_shape: tuple[int, int] = self.ds.shape.sig

        self.signal_plot: ImPlotElement

    def _tag(self, tag: str) -> str:
        return self.tag_prefix + tag + self.tag_suffix

    def _move_up(self) -> None:
        if self.measurement.pos_y_idx > 0:
            self.measurement.pos_y_idx -= 1
        self.measurement.update_open()
        self.ui_update()
        self.move_dot()

    def _move_down(self) -> None:
        if self.measurement.pos_y_idx < self.nav_shape[0] - 1:
            self.measurement.pos_y_idx += 1
        self.measurement.update_open()
        self.ui_update()
        self.move_dot()

    def _move_left(self) -> None:
        if self.measurement.pos_x_idx > 0:
            self.measurement.pos_x_idx -= 1
        self.measurement.update_open()
        self.ui_update()
        self.move_dot()

    def _move_right(self) -> None:
        if self.measurement.pos_x_idx < self.nav_shape[1] - 1:
            self.measurement.pos_x_idx += 1
        self.measurement.update_open()
        self.ui_update()
        self.move_dot()

    def move_dot(self) -> None:
        pass

    def update_signal(self) -> None:
        roi = np.zeros(self.nav_shape, dtype=bool)
        roi[self.measurement.pos_y_idx, self.measurement.pos_x_idx] = True

        pick_udf = PickUDF()
        result = self.ctx.run_udf(dataset=self.ds, udf=pick_udf, roi=roi)
        signal_data = np.array(result["intensity"].data[0].reshape(self.sig_shape))

        self.signal_plot.range_slider.update()
        self.signal_plot.update(data=signal_data)

    def update(self) -> None:
        self.signal_plot.update()
        self.ui_update()

    def ui_update(self) -> None:
        dpg.set_value(
            self._tag("position_text"),
            f"Position: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
        )

    def render(self) -> None:
        with dpg.window(
            tag=self._tag("stem_navigator"),
            label=str(self.measurement.index) + " Navigator",
            no_scrollbar=True,
            min_size=(150, 200),
        ):
            self.signal_plot = ImPlotElement(
                shape=self.sig_shape,
                tag_prefix=self.tag_prefix + "_signal_image",
                parent_tag=self._tag("stem_navigator"),
            )
            self.signal_plot.render()

            with dpg.child_window(no_scrollbar=True):
                dpg.add_text(
                    f"Position: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
                    tag=self._tag("position_text"),
                )
                with dpg.group(horizontal=True):
                    navigation_element(
                        [
                            self._move_up,
                            self._move_left,
                            self._move_right,
                            self._move_down,
                        ],
                        tag=self._tag("sig_move"),
                    )
        self.update()
