from libertem.common.buffers import BufferWrapper
from typing import Mapping
from dearstemgui.widgets.live_texture_plotter import LiveImPlotElement
from dearstemgui.widgets.texture_plotter import ImPlotElement
import dearpygui.dearpygui as dpg
from libertem.api import Context
import numpy as np

from jtools.comtools.libertemudf import ComputePACBED
from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets import navigation_element
from dearstemgui.windows.analyses.abf_udf_navigator import ABFNavigator


class PACBEDCompute(ABFNavigator):
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        super().__init__(measurement, ctx, tag_suffix)
        self.tag_prefix: str = str(measurement.index) + "_" + "ds_pacbed_"
        self.tag_suffix: str = "_" + tag_suffix

        self.area_width: int = 1
        self.area_height: int = 1

    def update_signal(self) -> None:
        super().update_signal()

    def compute(self) -> None:
        udf = ComputePACBED()
        roi = np.zeros(self.nav_shape, dtype=bool)
        roi[
            self.mask_y : self.mask_y + self.area_height,
            self.mask_x : self.mask_x + self.area_width,
        ] = True

        live_plots = [
            LiveImPlotElement(
                dataset=self.ds,
                udf=udf,
                channel=("pacbed", lambda x: x),
                update_callback=self.result_plot.update,
            )
        ]

        result: Mapping[str, BufferWrapper] = self.ctx.run_udf(
            dataset=self.ds, udf=udf, plots=live_plots, roi=roi, progress=True
        )
        result_data = np.array(result["pacbed"])
        self.measurement.pacbed = result_data
        self.result_plot.update(data=result_data)

    def ui_update(self) -> None:
        # super().ui_update()
        dpg.set_value(
            self._tag("mask_text"),
            f"ROI UL Corner: ({self.mask_x}, {self.mask_y})",
        )
        dpg.set_value(
            item=self._tag("size_text"),
            value=f"Width x Height: {self.area_width} x {self.area_height}",
        )

    def update(self) -> None:
        if self.measurement.abf is not None:
            im = self.measurement.abf
        elif self.measurement.adf is not None:
            im = self.measurement.adf
        else:
            print("err")
        self.signal_plot.update(im)
        self.update_mask()

    def _height_inc(self) -> None:
        if self.area_height + 1 < self.nav_shape[0]:
            self.area_height += 1
        self.update_mask()
        self.ui_update()

    def _height_dec(self) -> None:
        if self.area_height - 1 > 0:
            self.area_height -= 1
        self.update_mask()
        self.ui_update()

    def _width_inc(self) -> None:
        if self.area_width + 1 < self.nav_shape[1]:
            self.area_width += 1
        self.update_mask()
        self.ui_update()

    def _width_dec(self) -> None:
        if self.area_width - 1 > 0:
            self.area_width -= 1
        self.update_mask()
        self.ui_update()

    def update_mask(self) -> None:
        dlt = self.signal_plot.draw_list_tag
        scale: float = self.signal_plot.scale_x
        if dpg.does_item_exist(self._tag("rec_roi")):
            dpg.delete_item(self._tag("rec_roi"))

        dpg.draw_rectangle(
            pmin=(self.mask_x * scale, self.mask_y * scale),
            pmax=(
                (self.mask_x + self.area_width) * scale,
                (self.mask_y + self.area_height) * scale,
            ),
            color=(0, 255, 0, 255),
            thickness=2,
            parent=dlt,
            tag=self._tag("rec_roi"),
        )

    def render(self) -> None:
        with dpg.window(
            tag=self._tag("pacbed_navigator"),
            label=str(self.measurement.index) + " PACBED Compute",
        ) as window:
            with dpg.group(horizontal=True):
                self.signal_plot = ImPlotElement(
                    shape=self.nav_shape,
                    tag_prefix=self.tag_prefix + "_nav_image",
                    parent_tag=self._tag("pacbed_navigator"),
                    size_fraction=(0.5, 1),
                )
                self.signal_plot.render()

                self.result_plot = ImPlotElement(
                    shape=self.sig_shape,
                    tag_prefix=self.tag_prefix + "_sig_image",
                    parent_tag=self._tag("pacbed_navigator"),
                    size_fraction=(0.5, 1),
                )
                self.result_plot.render()

            with dpg.child_window(no_scrollbar=True), dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text(
                        f"ROI UL Corner: ({self.mask_x}, {self.mask_y})",
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
                with dpg.group():
                    dpg.add_text(
                        f"Width x Height: {self.area_width} x {self.area_height}",
                        tag=self._tag("size_text"),
                    )
                    navigation_element(
                        [
                            self._height_inc,
                            self._width_dec,
                            self._width_inc,
                            self._height_dec,
                        ],
                        tag=self._tag("width_move"),
                    )
                dpg.add_button(label="Compute", callback=lambda: self.compute())

        with dpg.item_handler_registry() as handler:
            dpg.add_item_resize_handler(callback=lambda: self.update())
        dpg.bind_item_handler_registry(window, handler)

        self.update()
