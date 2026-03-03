from typing import Any
import dearpygui.dearpygui as dpg
from libertem.api import UDF, Context
from libertem.udf.raw import PickUDF
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets import (
    ImPlotElement,
    navigation_element,
)
from dearstemgui.windows.analyses.signal_navigator import MRSTEMNavigator
from jtools.comtools.libertemudf import CoMShiftAnalysis


class COMShiftNavigator(MRSTEMNavigator):
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        super().__init__(measurement, ctx, tag_suffix)
        self.tag_prefix: str = str(measurement.index) + "_com_nav"

        self._center_y: float = self.sig_shape[0] / 2
        self._center_x: float = self.sig_shape[1] / 2

    @property
    def _live(self) -> bool:
        return dpg.get_value(self._tag("_live"))

    def _mask_up(self) -> None:
        if self._center_y > 0:
            self._center_y -= 1
        self.update_signal()

    def _mask_left(self) -> None:
        if self._center_x > 0:
            self._center_x -= 1
        self.update_signal()

    def _mask_down(self) -> None:
        if self._center_y < self.sig_shape[0] - 1:
            self._center_y += 1
        self.update_signal()

    def _mask_right(self) -> None:
        if self._center_x < self.sig_shape[1] - 1:
            self._center_x += 1
        self.update_signal()

    def reset_mask(self) -> None:
        self._center_y: float = self.sig_shape[0] / 2
        self._center_x: float = self.sig_shape[1] / 2

    @property
    def correct_shift(self) -> bool:
        return dpg.get_value(self._tag("_correct_shift"))

    @property
    def subtract_image(self) -> bool:
        return dpg.get_value(self._tag("_subtract_image"))

    @property
    def center(self) -> tuple[float, float]:
        return (self._center_y, self._center_x)

    @property
    def radius(self) -> float:
        return dpg.get_value(self._tag("_radius_slider"))

    def update_signal(self) -> None:
        super().update_signal()
        scale = self.signal_plot.scale_y

        if self.correct_shift:
            xcircle = (
                self._center_x + self.measurement.rigid_shift_sensor_axis_1[self.roi]
            )
            ycircle = (
                self._center_y + self.measurement.rigid_shift_sensor_axis_0[self.roi]
            )
        else:
            xcircle = self._center_x
            ycircle = self._center_y

        dpg.draw_circle(
            (xcircle * scale, ycircle * scale),
            radius=self.radius * scale,
            color=(180, 0, 0),
            parent=self.signal_plot.draw_list_tag,
        )
        print(f"update signal: live {self._live}")
        if self._live:
            print("calculating com shift for frame")
            result = self.ctx.run_udf(dataset=self.ds, udf=self.udf, roi=self.roi)
            signal = np.array(result["com_deflection"].data[self.roi, :])
            sy: float
            sx: float
            sy, sx = signal[0, :]
            print(sy, sx)

            sy += self._center_y
            sx += self._center_x

            if self.correct_shift:
                sy += self.measurement.rigid_shift_sensor_axis_0[self.roi]
                sx += self.measurement.rigid_shift_sensor_axis_1[self.roi]

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
        roi = np.zeros(self.nav_shape, dtype=bool)
        roi[
            dpg.get_value(self._tag("_y_idx_ref")),
            dpg.get_value(self._tag("_x_idx_ref")),
        ] = True
        result = self.ctx.run_udf(dataset=self.ds, udf=pick_udf, roi=roi)
        return np.array(result["intensity"].data[0].reshape(self.sig_shape))

    @property
    def udf(self) -> UDF:
        radius = self.radius
        center = self.center

        correct_shift = None
        if self.correct_shift:
            if self.measurement.rigid_shift_sensor_axis_0 is None:
                print("No correction signal found")
            else:
                correct_shift = np.stack(
                    [
                        self.measurement.rigid_shift_sensor_axis_0,
                        self.measurement.rigid_shift_sensor_axis_1,
                    ],
                    axis=0,
                )
                print(correct_shift.shape)

        subtract = None
        if self.subtract_image:
            if dpg.get_value(self._tag("_use_pacbed")):
                if self.measurement.pacbed is not None:
                    subtract = self.measurement.pacbed
                else:
                    # TODO: call pacbed window
                    print("No PACBED computed yet")
            else:
                subtract = self.reference_frame

        print(
            f"Created UDF with radius: {radius}, center: {center},\
            correct shift: {self.correct_shift},\
            subtract image: {self.subtract_image} with "
            + "pacbed" * dpg.get_value(self._tag("_use_pacbed"))
        )
        udf: UDF = CoMShiftAnalysis(
            radius=radius,
            center=center,
            subtract_im=subtract,
            correct_shift=correct_shift,
        )
        return udf

    # @override
    def move_dot(self) -> None:
        self.update_result()

    def compute(self) -> None:
        udf = self.udf

        result = self.ctx.run_udf(dataset=self.ds, udf=udf, progress=True, sync=True)
        com_shift_signal = np.array(
            result["com_deflection"].data.reshape((*self.nav_shape, 2))
        )

        self.sx_signal = com_shift_signal[..., 1]
        self.sy_signal = com_shift_signal[..., 0]

        self.measurement.com_shift_sensor_axis_0 = self.sy_signal
        self.measurement.com_shift_sensor_axis_1 = self.sx_signal

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
            tag=self._tag("com_shift_navigator"),
            label=str(self.measurement.index) + " " + "COM Shift Navigator",
            no_scrollbar=True,
            min_size=(800, 700),
        ):
            with dpg.group(horizontal=True):
                self.signal_plot = ImPlotElement(
                    shape=self.sig_shape,
                    tag_prefix=self._tag("_signal_image"),
                    parent_tag=self._tag("com_shift_navigator"),
                    size_fraction=(0.33, 0),
                )
                self.signal_plot.render()
                self.sx_plot = ImPlotElement(
                    shape=self.nav_shape,
                    tag_prefix=self._tag("_sx_signal"),
                    parent_tag=self._tag("com_shift_navigator"),
                    size_fraction=(0.33, 0),
                )
                self.sx_plot.render()
                self.sy_plot = ImPlotElement(
                    shape=self.nav_shape,
                    tag_prefix=self._tag("_sy_signal"),
                    parent_tag=self._tag("com_shift_navigator"),
                    size_fraction=(0.33, 0),
                )
                self.sy_plot.render()
            with dpg.child_window(no_scrollbar=True, tag=self._tag("_controls")):
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text(
                            f"Postition: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
                            tag=self._tag("position_text"),
                        )
                        dpg.add_checkbox(label="live result", tag=self._tag("_live"))
                        navigation_element(
                            [
                                self._move_up,
                                self._move_left,
                                self._move_right,
                                self._move_down,
                            ],
                            tag=self._tag("sig_move"),
                        )
                    with dpg.group():
                        dpg.add_text(
                            f"Mask center: ({self._center_y}, {self._center_x})",
                            tag=self._tag("mask_text"),
                        )
                        dpg.add_button(
                            label="reset position",
                            callback=lambda: self.reset_mask(),
                        )
                        navigation_element(
                            [
                                self._mask_up,
                                self._mask_left,
                                self._mask_right,
                                self._mask_down,
                            ],
                            tag=self._tag("mask_move"),
                        )
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(
                                label="subtract image", tag=self._tag("_subtract_image")
                            )
                            dpg.add_button(
                                label="use current",
                                callback=lambda: self._use_curr_cbed_as_ref(),
                            )
                            dpg.add_checkbox(
                                label="use PACBED", tag=self._tag("_use_pacbed")
                            )
                        with dpg.group(horizontal=True):
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
                        dpg.add_checkbox(
                            label="correct shift", tag=self._tag("_correct_shift")
                        )
                        dpg.add_slider_float(
                            label="radius",
                            tag=self._tag("_radius_slider"),
                            min_value=0,
                            max_value=128,
                        )
            dpg.add_button(
                label="compute",
                callback=lambda: self.compute(),
            )
        self.update()
