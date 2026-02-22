import dearpygui.dearpygui as dpg
from libertem.api import Context, DataSet
from libertem.udf.raw import PickUDF
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets.elements import ImPlotElement, navigation_element


class MRSTEMNavigator:
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        self.tag_prefix: str = str(measurement.index) + "_" + "ds_nav_"
        self.tag_suffix: str = "_" + tag_suffix

        self.measurement: EMPAD_Measurements = measurement
        self.measurement.update_nav_callbacks.append(self.update_signal)

        self.ds: DataSet = measurement.dataset
        self.ctx: Context = ctx

        self.nav_shape: tuple[int, int] = self.ds.shape.nav
        self.sig_shape: tuple[int, int] = self.ds.shape.sig

        self.vmax: float = np.inf
        self.plot_log: bool = False

        self.signal_plot: ImPlotElement = ImPlotElement(
            shape=self.sig_shape,
            tag_prefix=self.tag_prefix + "_signal_image",
            parent_tag=self._tag("signal_wrapper"),
        )

    def _tag(self, tag: str) -> str:
        return self.tag_prefix + tag + self.tag_suffix

    def _move_up(self) -> None:
        if self.measurement.pos_y_idx > 0:
            self.measurement.pos_y_idx -= 1
        self.measurement.update_open()

    def _move_down(self) -> None:
        if self.measurement.pos_y_idx < self.nav_shape[0] - 1:
            self.measurement.pos_y_idx += 1
        self.measurement.update_open()

    def _move_left(self) -> None:
        if self.measurement.pos_x_idx > 0:
            self.measurement.pos_x_idx -= 1
        self.measurement.update_open()

    def _move_right(self) -> None:
        if self.measurement.pos_x_idx < self.nav_shape[1] - 1:
            self.measurement.pos_x_idx += 1
        self.measurement.update_open()

    def _toggle_log(self) -> None:
        self.plot_log = not self.plot_log
        self.update_signal()

    def update_signal(self) -> None:
        roi = np.zeros(self.nav_shape, dtype=bool)
        roi[self.measurement.pos_y_idx, self.measurement.pos_x_idx] = True

        pick_udf = PickUDF()
        result = self.ctx.run_udf(dataset=self.ds, udf=pick_udf, roi=roi)
        signal_data = np.array(result["intensity"].data[0].reshape(self.sig_shape))

        self.vmax = float(dpg.get_value(self._tag("vmax")))
        self.signal_plot.update(data=signal_data)
        self._push_update()

    def _push_update(self) -> None:
        self.signal_plot.update()
        dpg.set_value(
            self._tag("position_text"),
            f"Position: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
        )

    def render(self) -> None:
        with dpg.window(
            tag=self._tag("stem_navigator"),
            label=str(self.measurement.index) + " Navigator",
            no_scrollbar=True,
        ):
            with dpg.child_window(no_scrollbar=True, tag=self._tag("signal_wrapper")):
                dpg.add_text(
                    f"Position: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
                    tag=self._tag("position_text"),
                )
                self.signal_plot.render()

            with dpg.child_window(no_scrollbar=True):
                with dpg.group(horizontal=True):
                    navigation_element([
                        self._move_up,
                        self._move_left,
                        self._move_right,
                        self._move_down,
                    ])
                    with dpg.group():
                        dpg.add_button(label="log", callback=self._toggle_log)
                        dpg.add_input_float(
                            tag=self._tag("vmax"),
                            label="vmax",
                            default_value=self.vmax,
                            step=1_000,
                        )
        self.update_signal()
