import dearpygui.dearpygui as dpg
from libertem.api import Context
from libertem.udf.raw import PickUDF
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets import (
    ImPlotElement,
    navigation_element,
)
from dearstemgui.windows.analyses.signal_navigator import MRSTEMNavigator
from jtools.comtools.libertemudf import RigidShiftAnalysisCircle, RigidShiftAnalysis


class RigidShiftNavigator(MRSTEMNavigator):
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        super().__init__(measurement, ctx, tag_suffix)
        self.tag_prefix: str = str(measurement.index) + "_rigid_nav"

    def update_signal(self) -> None:
        super().update_signal()
        # TODO: Update crosshair, deviation arrow

    @property
    def reference_frame(self) -> None:
        roi = np.zeros(self.nav_shape, dtype=bool)
        roi[
            dpg.get_value(self._tag("_y_idx_ref")),
            dpg.get_value(self._tag("_x_idx_ref")),
        ] = True

        pick_udf = PickUDF()
        result = self.ctx.run_udf(dataset=self.ds, udf=pick_udf, roi=roi)
        return np.array(result["intensity"].data[0].reshape(self.sig_shape))

    def compute(self) -> None:
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
            dpg.popup('select method')

        result = self.ctx.run_udf(dataset=self.ds, udf=udf, progress=True, sync=True)
        rigid_shift_signal = np.array(
            result["rigid_deflection"].data.reshape((*self.nav_shape, 2))
        )

        self.sx_signal = rigid_shift_signal[..., 1]
        self.sy_signal = rigid_shift_signal[..., 0]

        self.sx_plot.update(data=self.sx_signal)
        self.sy_plot.update(data=self.sy_signal)
        self.sx_plot.range_slider.update()
        self.sy_plot.range_slider.update()

    def _use_curr_cbed_as_ref(self) -> None:
        dpg.set_value(self._tag("_x_idx_ref"), self.measurement.pos_x_idx)
        dpg.set_value(self._tag("_y_idx_ref"), self.measurement.pos_y_idx)

    def render(self) -> None:
        with dpg.window(
            tag=self._tag("rigid_shift_navigator"),
            label=str(self.measurement.index) + "Rigid Shift Navigator",
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
                self.sy_plot = ImPlotElement(
                    shape=self.nav_shape,
                    tag_prefix=self._tag("_sy_signal"),
                    parent_tag=self._tag("rigid_shift_navigator"),
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
                        dpg.add_text("method:")
                        dpg.add_combo(
                            items=["fit circle", "cross corr."],
                            tag=self._tag("_method_selector"),
                        )
                    with dpg.group(label="cross correlation options"):
                        dpg.add_radio_button(
                            label="use edges", tag=self._tag("_use_edges")
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
                            label="use current", callback=self._use_curr_cbed_as_ref
                        )
                    with dpg.group(label="fit circle options"):
                        dpg.add_slider_float(
                            label="fraction of max",
                            default_value=0.75,
                            min_value=0.1,
                            max_value=0.9,
                            tag=self._tag("_threshold"),
                        )
            dpg.add_button(label="compute", callback=self.compute)
        self.update()
