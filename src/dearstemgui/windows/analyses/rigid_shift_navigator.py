from typing import Any

import dearpygui.dearpygui as dpg
from jtools.comtools.libertemudf import RigidShiftAnalysis, RigidShiftAnalysisCircle
from libertem.api import UDF, Context
from libertem.udf.raw import PickUDF
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets import (
    ImPlotElement,
    navigation_element,
)
from dearstemgui.windows.analyses.signal_navigator import MRSTEMNavigator


class RigidShiftNavigator(MRSTEMNavigator):
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        super().__init__(measurement, ctx, tag_suffix)
        self.tag_prefix: str = str(measurement.index) + "_rigid_nav"
        self._live: bool = False
        self._edges: bool = False

    def _toggle_live(self, sender: int, app_data: bool, user_data: Any) -> None:
        self._live = app_data

    def _toggle_edges(self, sender: int, app_data: bool, user_data: Any) -> None:
        self._edges = app_data

    @property
    def method(self) -> str:
        return dpg.get_value(self._tag("_method_selector"))

    def update_signal(self) -> None:
        super().update_signal()
        print(f"update signal: live {self._live}, method: {self.method}")
        # TODO: Update crosshair, deviation arrow
        if self._live and self.method in [
            "fit circle",
            "cross corr.",
        ]:
            print("calculating rigid shift for frame")
            result = self.ctx.run_udf(dataset=self.ds, udf=self.udf, roi=self.roi)
            signal = np.array(result["rigid_deflection"].data[self.roi, :])
            sy, sx = signal[0, :]
            print(sy, sx)

            if self.method == "fit circle":
                sy += 64
                sx += 64
            if self.method == "cross corr.":
                sy += self.measurement.reference_center[0]
                sx += self.measurement.reference_center[1]

            dpg.draw_line(
                (sx * self.signal_plot.scale_x - 10, sy * self.signal_plot.scale_y),
                (sx * self.signal_plot.scale_x + 10, sy * self.signal_plot.scale_y),
                thickness=2,
                color=(180, 0, 0),
                parent=self.signal_plot.draw_list_tag,
            )
            dpg.draw_line(
                (sx * self.signal_plot.scale_x, sy * self.signal_plot.scale_y - 10),
                (sx * self.signal_plot.scale_x, sy * self.signal_plot.scale_y + 10),
                thickness=2,
                color=(180, 0, 0),
                parent=self.signal_plot.draw_list_tag,
            )

    @property
    def roi(self) -> np.ndarray:
        roi = np.zeros(self.nav_shape, dtype=bool)
        roi[
            self.measurement.pos_y_idx,
            self.measurement.pos_x_idx,
        ] = True
        return roi

    @property
    def reference_frame(self) -> None:
        pick_udf = PickUDF()
        result = self.ctx.run_udf(dataset=self.ds, udf=pick_udf, roi=self.roi)
        return np.array(result["intensity"].data[0].reshape(self.sig_shape))

    @property
    def udf(self) -> UDF:
        method = dpg.get_value(self._tag("_method_selector"))
        use_edges = dpg.get_value(self._tag("_use_edges"))
        threshold = dpg.get_value(self._tag("_threshold"))

        if method == "fit circle":
            udf = RigidShiftAnalysisCircle(threshold=threshold)
        elif method == "cross corr.":
            udf = RigidShiftAnalysis(
                reference_frame=self.reference_frame, use_edges=use_edges
            )
        else:
            dpg.popup("select method")
        return udf

    def move_dot(self) -> None:
        self.update_result()

    def compute(self) -> None:
        udf = self.udf

        result = self.ctx.run_udf(dataset=self.ds, udf=udf, progress=True, sync=True)
        rigid_shift_signal = np.array(
            result["rigid_deflection"].data.reshape((*self.nav_shape, 2))
        )

        self.sx_signal = rigid_shift_signal[..., 1]
        self.sy_signal = rigid_shift_signal[..., 0]

        self.measurement.rigid_shift_sensor_axis_0 = self.sy_signal
        self.measurement.rigid_shift_sensor_axis_1 = self.sx_signal

        self.sx_plot.update(data=self.sx_signal)
        self.sy_plot.update(data=self.sy_signal)

    def _use_curr_cbed_as_ref(self) -> None:
        dpg.set_value(self._tag("_x_idx_ref"), self.measurement.pos_x_idx)
        dpg.set_value(self._tag("_y_idx_ref"), self.measurement.pos_y_idx)

    def update_result(self) -> None:
        self.sx_plot.range_slider.update()
        self.sx_plot.update()
        self.sy_plot.range_slider.update()
        self.sy_plot.update()
        dpg.draw_circle(
            (
                self.measurement.pos_x_idx * self.sx_plot.scale_x,
                self.measurement.pos_y_idx * self.sx_plot.scale_y,
            ),
            2,
            color=(180, 0, 0),
            parent=self.sx_plot.draw_list_tag,
        )
        dpg.draw_circle(
            (
                self.measurement.pos_x_idx * self.sy_plot.scale_x,
                self.measurement.pos_y_idx * self.sy_plot.scale_y,
            ),
            2,
            color=(180, 0, 0),
            parent=self.sy_plot.draw_list_tag,
        )

    def update(self) -> None:
        self.ui_update()
        self.update_signal()
        self.update_result()

    def render(self) -> None:
        with dpg.window(
            tag=self._tag("rigid_shift_navigator"),
            label=str(self.measurement.index) + " Rigid Shift Navigator",
            no_scrollbar=True,
            min_size=(800, 700),
        ):
            with dpg.group(horizontal=True):
                self.signal_plot = ImPlotElement(
                    shape=self.sig_shape,
                    tag_prefix=self._tag("_signal_image"),
                    parent_tag=self._tag("rigid_shift_navigator"),
                    size_fraction=(0.33, 0),
                )
                self.signal_plot.render()
                self.sx_plot = ImPlotElement(
                    shape=self.nav_shape,
                    tag_prefix=self._tag("_sx_signal"),
                    parent_tag=self._tag("rigid_shift_navigator"),
                    size_fraction=(0.33, 0),
                )
                self.sx_plot.render()
                self.sx_plot.range_slider.set_limits(vmin=-5, vmax=5)
                self.sy_plot = ImPlotElement(
                    shape=self.nav_shape,
                    tag_prefix=self._tag("_sy_signal"),
                    parent_tag=self._tag("rigid_shift_navigator"),
                    size_fraction=(0.33, 0),
                )
                self.sy_plot.render()
                self.sy_plot.range_slider.set_limits(vmin=-5, vmax=5)
            with (
                dpg.child_window(no_scrollbar=True, tag=self._tag("_controls")),
                dpg.group(horizontal=True),
            ):
                with dpg.group():
                    dpg.add_text(
                        f"Postition: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
                        tag=self._tag("position_text"),
                    )
                    dpg.add_checkbox(
                        label="live result",
                        callback=lambda s, a, u: self._toggle_live(s, a, u),
                    )
                    navigation_element(
                        [
                            self._move_up,
                            self._move_left,
                            self._move_right,
                            self._move_down,
                        ],
                        tag=self._tag("sig_move"),
                    )
                    dpg.add_button(
                        label="compute",
                        callback=lambda: self.compute(),
                    )
                with dpg.group():
                    with dpg.group():
                        dpg.add_text("method:")
                        dpg.add_combo(
                            items=["fit circle", "cross corr."],
                            tag=self._tag("_method_selector"),
                        )
                    with dpg.group(label="cross correlation options"):
                        dpg.add_checkbox(
                            label="use edges",
                            tag=self._tag("_use_edges"),
                            callback=lambda s, a, u: self._toggle_edges(s, a, u),
                        )
                        dpg.add_text("reference CBED")
                        dpg.add_input_int(
                            label="x",
                            min_value=0,
                            max_value=self.nav_shape[1],
                            tag=self._tag("_x_idx_ref"),
                        )
                        dpg.add_input_int(
                            label="y",
                            min_value=0,
                            max_value=self.nav_shape[0],
                            tag=self._tag("_y_idx_ref"),
                        )
                        dpg.add_button(
                            label="use current",
                            callback=lambda: self._use_curr_cbed_as_ref(),
                        )
                    with dpg.group(label="fit circle options"):
                        dpg.add_slider_float(
                            label="fraction of max",
                            default_value=0.75,
                            min_value=0.1,
                            max_value=0.9,
                            tag=self._tag("_threshold"),
                        )
        self.update()
