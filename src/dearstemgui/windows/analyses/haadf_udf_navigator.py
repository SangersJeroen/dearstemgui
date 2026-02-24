import dearpygui.dearpygui as dpg
from libertem.api import Context
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets import (
    ImPlotElement,
    RangeSelector,
    navigation_element,
)
from dearstemgui.windows.analyses.signal_navigator import MRSTEMNavigator


class HAADFNavigator(MRSTEMNavigator):
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        super().__init__(measurement, ctx, tag_suffix)
        self.tag_prefix: str = str(measurement.index) + "_" + "ds_haadf_"

        self.mask_x: int = self.sig_shape[1] // 2
        self.mask_y: int = self.sig_shape[0] // 2

        self.mask_r: int = 10
        self.mask_ro: int = 30

        self.result_plot: ImPlotElement
        self.result_data = np.random.random(size=self.nav_shape)

    def _mask_move_up(self) -> None:
        if self.mask_y > 0:
            self.mask_y -= 1
        self.update_mask()
        self.ui_update()

    def _mask_move_down(self) -> None:
        if self.mask_y < self.sig_shape[0] - 1:
            self.mask_y += 1
        self.update_mask()
        self.ui_update()

    def _mask_move_left(self) -> None:
        if self.mask_x > 0:
            self.mask_x -= 1
        self.update_mask()
        self.ui_update()

    def _mask_move_right(self) -> None:
        if self.mask_x < self.sig_shape[1] - 1:
            self.mask_x += 1
        self.update_mask()
        self.ui_update()

    def update_signal(self) -> None:
        super().update_signal()
        self.update_mask()

    def update_mask(self) -> None:
        dlt = self.signal_plot.draw_list_tag
        scale: float = self.signal_plot.scale_x
        for tag in [
            self._tag("mask_ri"),
            self._tag("mask_ro"),
        ]:
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)

        dpg.draw_circle(
            center=(self.mask_x * scale, self.mask_y * scale),
            radius=self.r_select.cmin * scale,
            color=(0, 255, 0, 255),
            thickness=2,
            parent=dlt,
            tag=self._tag("mask_ri"),
        )
        dpg.draw_circle(
            center=(self.mask_x * scale, self.mask_y * scale),
            radius=self.r_select.cmax * scale,
            color=(0, 255, 0, 255),
            thickness=2,
            parent=dlt,
            tag=self._tag("mask_ro"),
        )

    def compute(self) -> None:
        print(
            f"compute, {self.mask_x}, {self.mask_y}, {self.r_select.cmin}, {self.r_select.cmax}"
        )
        udf = self.ctx.create_ring_analysis(
            dataset=self.ds,
            cx=self.mask_x,
            cy=self.mask_y,
            ri=self.r_select.cmin,
            ro=self.r_select.cmax,
        ).get_udf()

        result = self.ctx.run_udf(dataset=self.ds, udf=udf)
        result_data = np.array(result["intensity"].data.reshape(self.nav_shape))
        self.result_data = result_data
        self.result_plot.update(data=result_data)

    def update_result(self) -> None:
        self.result_plot.range_slider.update()
        self.result_plot.update(self.result_data)
        dpg.draw_circle(
            (
                self.mask_x * self.result_plot.scale_x,
                self.mask_y * self.result_plot.scale_y,
            ),
            2,
            color=(180, 0, 0),
            parent=self.result_plot.draw_list_tag,
        )

    def ui_update(self):
        super().ui_update()
        dpg.set_value(
            self._tag("position_text"),
            f"Position: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
        )
        dpg.set_value(
            self._tag("mask_text"),
            f"mask center: ({self.mask_x}, {self.mask_y})",
        )

        pwidth = dpg.get_item_rect_size(self._tag("controls"))[0]
        mnav_width = dpg.get_item_rect_size(self._tag("mask_move"))[0]
        snav_width = dpg.get_item_rect_size(self._tag("sig_move"))[0]

        pwidth = max(1, pwidth)
        frac = (pwidth - mnav_width - snav_width) / pwidth
        self.r_select.width_fraction = frac
        self.r_select.update()

    def update(self) -> None:
        self.ui_update()
        self.update_signal()
        self.update_result()

    def render(self) -> None:
        with dpg.window(
            tag=self._tag("stem_navigator"),
            label=str(self.measurement.index) + " STEM Navigator",
            no_scrollbar=True,
            min_size=(800, 700),
        ) as window:
            with dpg.group(
                horizontal=True,
            ):
                self.signal_plot = ImPlotElement(
                    shape=self.sig_shape,
                    tag_prefix=self.tag_prefix + "_signal_image",
                    parent_tag=self._tag("stem_navigator"),
                    size_fraction=(0.5, 0.0),
                )
                self.signal_plot.render()
                self.result_plot = ImPlotElement(
                    shape=self.nav_shape,
                    tag_prefix=self.tag_prefix + "_result_image",
                    parent_tag=self._tag("stem_navigator"),
                    size_fraction=(0.5, 0.0),
                )
                self.result_plot.render()

            with dpg.child_window(no_scrollbar=True, tag=self._tag("controls")):
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
                        self.r_select = RangeSelector(
                            self.update_signal,
                            tag=self._tag("mask_ri"),
                            parent_tag=self._tag("stem_navigator"),
                            init_range=(0, 75),
                        )
                        dpg.add_button(label="compute", callback=self.compute)

        with dpg.item_handler_registry() as handler:
            dpg.add_item_resize_handler(callback=lambda: self.update())
        dpg.bind_item_handler_registry(window, handler)

        self.update()
