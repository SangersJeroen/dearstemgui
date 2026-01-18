import dearpygui.dearpygui as dpg
from libertem.api import Context, DataSet
import numpy as np

from dearstemgui.widgets.mrstem_navigator import MRSTEMNavigator


class HAADFNavigator(MRSTEMNavigator):
    def __init__(self, ds: DataSet, ctx: Context, tag_suffix: str) -> None:
        super().__init__(ds, ctx, tag_suffix)
        self.tag_prefix: str = "ds_haadf_"

        self.mask_x: int = self.sig_shape[1] // 2
        self.mask_y: int = self.sig_shape[0] // 2
        self.mask_r: int = 10
        self.mask_ro: int = 30

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
        udf = self.ctx.create_ring_analysis(
            dataset=self.ds,
            cx=dpg.get_value(self._tag("mask_x")),
            cy=dpg.get_value(self._tag("mask_y")),
            ri=dpg.get_value(self._tag("mask_r")),
            ro=dpg.get_value(self._tag("mask_ro")),
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

    def render(self) -> None:
        self._setup_textures()
        with dpg.window(tag=self._tag("stem_navigator")):
            dpg.add_text(
                f"Postition: ({self.nav_pos[0]}, {self.nav_pos[1]})",
                tag=self._tag("position_text"),
            )
            dpg.add_image(
                texture_tag=self._tag("signal_texture"),
            )
            dpg.add_button(label="up", callback=self._move_up)
            dpg.add_button(label="down", callback=self._move_down)
            dpg.add_button(label="left", callback=self._move_left)
            dpg.add_button(label="right", callback=self._move_right)
            dpg.add_button(label="log", callback=self._toggle_log)
            dpg.add_input_float(
                tag=self._tag("vmax"),
                label="vmax",
                default_value=self.vmax,
                step=1_000,
            )
            dpg.add_text("HAADF")
            dpg.add_image(texture_tag=self._tag("result_texture"))
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
            dpg.add_input_int(
                tag=self._tag("mask_r"),
                label="mask_r",
                default_value=self.mask_r,
                min_value=0,
                max_value=self.sig_shape[0],
            )
            dpg.add_input_int(
                tag=self._tag("mask_ro"),
                label="mask_ro",
                default_value=self.mask_ro,
                min_value=0,
                max_value=self.sig_shape[0],
            )
            dpg.add_button(label="compute", callback=self.compute)

        self.update_signal()
        self._push_update()
