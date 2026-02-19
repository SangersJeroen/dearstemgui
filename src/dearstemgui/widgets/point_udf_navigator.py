import dearpygui.dearpygui as dpg
from libertem.api import Context
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets.elements import navigation_element
from dearstemgui.widgets.mrstem_navigator import MRSTEMNavigator


class PointSignalNavigator(MRSTEMNavigator):
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        super().__init__(measurement, ctx, tag_suffix)
        self.tag_prefix: str = str(measurement.index) + "_" + "ds_haadf_"

        self.mask_x: int = self.sig_shape[1] // 2
        self.mask_y: int = self.sig_shape[0] // 2

        self.result_rgba: np.ndarray = np.zeros((*self.nav_shape, 4), dtype=np.float32)
        self.result_rgba[:, :, 3] = 1.0

    def _setup_textures(self) -> None:
        super()._setup_textures()
        with dpg.texture_registry():
            dpg.add_raw_texture(
                width=self.nav_shape[1],
                height=self.nav_shape[0],
                default_value=self.result_rgba.flatten(),
                format=dpg.mvFormat_Float_rgba,
                tag=self._tag("result_texture"),
            )

    def update_signal(self) -> None:
        super().update_signal()

    def compute(self) -> None:
        udf = self.ctx.create_point_analysis(
            dataset=self.ds,
            x=dpg.get_value(self._tag("mask_x")),
            y=dpg.get_value(self._tag("mask_y")),
        ).get_udf()

        result = self.ctx.run_udf(dataset=self.ds, udf=udf)
        result_data = np.array(result["intensity"].data.reshape(self.nav_shape))

        result_norm = (result_data - result_data.min()) / (
            result_data.max() - result_data.min() + 1e-10
        )
        result_rgba = np.zeros((*self.nav_shape, 4), dtype=np.float32)
        result_rgba[:, :, 0] = result_norm  # R
        result_rgba[:, :, 1] = result_norm  # G
        result_rgba[:, :, 2] = result_norm  # B
        result_rgba[:, :, 3] = 1.0  # A
        self.result_rgba = result_rgba
        self._push_update()

    def _push_update(self) -> None:
        super()._push_update()
        dpg.set_value(self._tag("result_texture"), self.result_rgba.flatten())

    def _update_signal(self) -> None:
        draw_list = self._tag("signal_drawlist")
        dpg.set_item_width(draw_list, dpg.get_item_width(self._tag("stem_navigator")))
        dpg.set_item_height(draw_list, dpg.get_item_width(self._tag("stem_navigator")))
        if dpg.does_item_exist(draw_list):
            dpg.delete_item(draw_list, children_only=True)

        cx = dpg.get_value(self._tag("mask_x"))
        cy = dpg.get_value(self._tag("mask_y"))

        height, width = dpg.get_item_rect_size(draw_list)

        # Only draw if we have valid dimensions
        if width <= 0 or height <= 0:
            return

        scale_x = width / self.sig_shape[1]
        scale_y = height / self.sig_shape[0]

        pmin = (0, 0)
        pmax = (width, height)

        dpg.draw_image(
            self._tag("signal_texture"),
            pmin=pmin,
            pmax=pmax,
            tag=self._tag("signal_texture_image"),
            parent=draw_list,
        )
        dpg.draw_rectangle(
            tag=self._tag("signal_dot"),
            pmin=((cx - 0.5) * scale_x, (cy - 0.5) * scale_y),
            pmax=((cx + 0.5) * scale_x, (cy + 0.5) * scale_y),
            color=(255, 0, 0, 255),
            thickness=1,
            parent=draw_list,
        )

    def _update_result(self):
        draw_list = self._tag("result_drawlist")
        dpg.set_item_width(draw_list, dpg.get_item_width(self._tag("stem_navigator")))
        dpg.set_item_height(draw_list, dpg.get_item_width(self._tag("stem_navigator")))
        if dpg.does_item_exist(draw_list):
            dpg.delete_item(draw_list, children_only=True)
        height, width = dpg.get_item_rect_size(draw_list)

        # Only draw if we have valid dimensions
        if width <= 0 or height <= 0:
            return

        pmin = (0, 0)
        pmax = (width, height)
        dpg.draw_image(
            texture_tag=self._tag("result_texture"),
            pmin=pmin,
            pmax=pmax,
            tag=self._tag("result_texture_image"),
            parent=draw_list,
        )

    def render(self) -> None:
        self._setup_textures()
        with dpg.window(
            tag=self._tag("stem_navigator"),
            label=str(self.measurement.index) + " STEM Navigator",
        ) as window:
            dpg.add_text(
                f"Postition: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
                tag=self._tag("position_text"),
            )
            with dpg.drawlist(
                width=500,
                height=500,
                tag=self._tag("signal_drawlist"),
            ) as draw_list:
                pass

            with dpg.item_handler_registry(tag=self._tag("signal_handler")) as handler:
                dpg.add_item_visible_handler(callback=lambda: self._update_signal())
                dpg.add_item_resize_handler(callback=lambda: self._update_signal())
            dpg.bind_item_handler_registry(self._tag("signal_drawlist"), handler)

            with dpg.group(horizontal=True):
                navigation_element([
                    self._move_up,
                    self._move_left,
                    self._move_right,
                    self._move_down,
                ])

                dpg.add_button(label="log", callback=self._toggle_log)
                dpg.add_input_float(
                    tag=self._tag("vmax"),
                    label="vmax",
                    default_value=self.vmax,
                    step=1_000,
                )

            dpg.add_text("ABF")
            with dpg.drawlist(
                width=500,
                height=500,
                tag=self._tag("result_drawlist"),
            ) as drawlist:
                pass

            with dpg.item_handler_registry(tag=self._tag("result_handler")) as handler:
                dpg.add_item_visible_handler(callback=lambda: self._update_result())
                dpg.add_item_resize_handler(callback=lambda: self._update_result())
            dpg.bind_item_handler_registry(self._tag("result_drawlist"), handler)

            dpg.add_input_int(
                tag=self._tag("mask_x"),
                label="mask_x",
                default_value=self.mask_x,
                min_value=0,
                max_value=self.sig_shape[1],
            )
            dpg.add_input_int(
                tag=self._tag("mask_y"),
                label="mask_y",
                default_value=self.mask_y,
                min_value=0,
                max_value=self.sig_shape[0],
            )
            dpg.add_button(label="compute", callback=self.compute)

        self.update_signal()
        self._push_update()
