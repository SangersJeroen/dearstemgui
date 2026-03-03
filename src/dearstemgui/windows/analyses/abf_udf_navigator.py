import dearpygui.dearpygui as dpg
from libertem.api import Context
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets import (
    ImPlotElement,
    navigation_element,
)
from dearstemgui.windows.analyses.haadf_udf_navigator import HAADFNavigator


class ABFNavigator(HAADFNavigator):
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        super().__init__(measurement, ctx, tag_suffix)
        self.tag_prefix: str = str(measurement.index) + "_" + "ds_abf_"

        self.mask_x: int = self.sig_shape[1] // 2
        self.mask_y: int = self.sig_shape[0] // 2

        self.mask_r: int = 10

        self.result_plot: ImPlotElement

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
            radius=dpg.get_value(self._tag("r_slider")) * scale,
            color=(0, 255, 0, 255),
            thickness=2,
            parent=dlt,
            tag=self._tag("mask_ri"),
        )

    def ui_update(self):
        dpg.set_value(
            self._tag("position_text"),
            f"Position: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
        )

    def compute(self) -> None:
        print(
            f"compute, {self.mask_x}, {self.mask_y}, {dpg.get_value(self._tag('r_slider'))}"
        )
        udf = self.ctx.create_ring_analysis(
            dataset=self.ds,
            cx=self.mask_x,
            cy=self.mask_y,
            ro=dpg.get_value(self._tag("r_slider")),
        ).get_udf()

        result = self.ctx.run_udf(dataset=self.ds, udf=udf)
        result_data = np.array(result["intensity"].data.reshape(self.nav_shape))
        self.result_plot.update(data=result_data)

    def render(self) -> None:
        with dpg.window(
            tag=self._tag("stem_navigator"),
            label=str(self.measurement.index) + " ABF Navigator",
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
                    size_fraction=(0.5, 1.0),
                )
                self.signal_plot.render()
                self.result_plot = ImPlotElement(
                    shape=self.nav_shape,
                    tag_prefix=self.tag_prefix + "_result_image",
                    parent_tag=self._tag("stem_navigator"),
                    size_fraction=(0.5, 1.0),
                )
                self.result_plot.render()

            with dpg.child_window(no_scrollbar=True):
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
                        dpg.add_slider_float(
                            tag=self._tag("r_slider"),
                            min_value=1,
                            max_value=100,
                            default_value=self.mask_r,
                            callback=lambda: self.update_mask(),
                        )
                        dpg.add_button(label="compute", callback=lambda: self.compute())
        with dpg.item_handler_registry() as handler:
            # dpg.add_item_visible_handler(callback=lambda: self.update())
            dpg.add_item_resize_handler(callback=lambda: self.update())
        dpg.bind_item_handler_registry(window, handler)
        self.update()
