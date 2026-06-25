from dearstemgui.widgets.texture_plotter import ImPlotElement
import dearpygui.dearpygui as dpg
from libertem.api import Context
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets import navigation_element
from dearstemgui.windows.analyses.abf_udf_navigator import ABFNavigator


class PointSignalNavigator(ABFNavigator):
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        super().__init__(measurement, ctx, tag_suffix)
        self.tag_prefix: str = str(measurement.index) + "_" + "ds_point_"
        self.tag_suffix: str = "_" + tag_suffix

    def update_signal(self) -> None:
        super().update_signal()

    def update_mask(self) -> None:
        dlt = self.signal_plot.draw_list_tag
        scale: float = self.signal_plot.scale_x
        if dpg.does_item_exist(self._tag("signal_point")):
            dpg.delete_item(self._tag("signal_point"))

        dpg.draw_circle(
            center=(self.mask_x * scale, self.mask_y * scale),
            radius=1 * scale,
            color=(0, 255, 0, 255),
            thickness=1,
            parent=dlt,
            tag=self._tag("signal_point"),
        )

    def ui_update(self) -> None:
        super().ui_update()
        dpg.set_value(
            self._tag("mask_text"),
            f"mask center: ({self.mask_x}, {self.mask_y})",
        )

    def compute(self) -> None:
        udf = self.ctx.create_point_analysis(
            dataset=self.ds,
            x=self.mask_x,
            y=self.mask_y,
        ).get_udf()

        result = self.ctx.run_udf(dataset=self.ds, udf=udf, progress=True)
        result_data = np.array(result["intensity"].data.reshape(self.nav_shape))
        print("computed")
        self.result_plot.update(data=result_data)

    def render(self) -> None:
        with dpg.window(
            tag=self._tag("point_navigator"),
            label=str(self.measurement.index) + " STEM Navigator",
        ) as window:
            with dpg.group(horizontal=True):
                self.signal_plot = ImPlotElement(
                    shape=self.sig_shape,
                    tag_prefix=self.tag_prefix + "_signal_image",
                    parent_tag=self._tag("point_navigator"),
                    size_fraction=(0.5, 1),
                )
                self.signal_plot.render()

                self.result_plot = ImPlotElement(
                    shape=self.nav_shape,
                    tag_prefix=self.tag_prefix + "_result_image",
                    parent_tag=self._tag("point_navigator"),
                    size_fraction=(0.5, 1),
                )
                self.result_plot.render()

            with dpg.child_window(no_scrollbar=True), dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text(
                        f"Position: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
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
                dpg.add_button(label="Compute", callback=lambda: self.compute())
                with dpg.group():
                    dpg.add_text(
                        f"mask center: ({self.mask_x}, {self.mask_y})",
                        tag=self._tag("mask_text"),
                    )
                    navigation_element(
                        [
                            self._mask_move_up,
                            self._mask_move_left,
                            self._mask_move_right,
                            self._mask_move_down,
                        ],
                        tag=self._tag("mask_move"),
                    )

        with dpg.item_handler_registry() as handler:
            dpg.add_item_resize_handler(callback=lambda: self.update())
        dpg.bind_item_handler_registry(window, handler)
        self.update()
