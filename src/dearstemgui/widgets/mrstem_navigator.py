import dearpygui.dearpygui as dpg
from libertem.api import Context, DataSet
from libertem.udf.raw import PickUDF
import numpy as np


class MRSTEMNavigator:
    def __init__(self, ds: DataSet, ctx: Context, tag_suffix: str) -> None:
        self.tag_suffix: str = tag_suffix

        self.ds: DataSet = ds
        self.ctx: Context = ctx

        self.nav_shape: tuple[int, int] = ds.shape.nav
        self.sig_shape: tuple[int, int] = ds.shape.sig
        self.nav_pos: tuple[int, int] = (0, 0)

        self.vmax: float = np.inf
        self.plot_log: bool = False

        with dpg.texture_registry():
            signal_data = np.zeros((*self.sig_shape, 4), dtype=np.float32)
            signal_data[:, :, 3] = 1.0
            dpg.add_raw_texture(
                width=self.sig_shape[1],
                height=self.sig_shape[0],
                default_value=signal_data.flatten(),
                format=dpg.mvFormat_Float_rgba,
                tag=f"signal_texture_{self.tag_suffix}",
            )

    def _move_up(self) -> None:
        if self.nav_pos[0] > 0:
            self.nav_pos = (self.nav_pos[0] - 1, self.nav_pos[1])
        self.update_signal()

    def _move_down(self) -> None:
        if self.nav_pos[0] < self.nav_shape[0] - 1:
            self.nav_pos = (self.nav_pos[0] + 1, self.nav_pos[1])
        self.update_signal()

    def _move_left(self) -> None:
        if self.nav_pos[1] > 0:
            self.nav_pos = (self.nav_pos[0], self.nav_pos[1] - 1)
        self.update_signal()

    def _move_right(self) -> None:
        if self.nav_pos[1] < self.nav_shape[1] - 1:
            self.nav_pos = (self.nav_pos[0], self.nav_pos[1] + 1)
        self.update_signal()

    def _toggle_log(self) -> None:
        self.plot_log = not self.plot_log
        self.update_signal()

    def update_signal(self) -> None:
        roi = np.zeros(self.nav_shape, dtype=bool)
        roi[self.nav_pos[0], self.nav_pos[1]] = True

        pick_udf = PickUDF()
        result = self.ctx.run_udf(dataset=self.ds, udf=pick_udf, roi=roi)
        signal_data = np.array(result["intensity"].data[0].reshape(self.sig_shape))

        if self.plot_log:
            signal_data = np.log(signal_data - signal_data.min() + 1)

        self.vmax = float(dpg.get_value(f"vmax_{self.tag_suffix}"))
        signal_data = np.where(signal_data > self.vmax, self.vmax, signal_data)

        signal_norm = (signal_data - signal_data.min()) / (
            signal_data.max() - signal_data.min() + 1e-10
        )
        signal_rgba = np.zeros((*self.sig_shape, 4), dtype=np.float32)
        signal_rgba[:, :, 0] = signal_norm  # R
        signal_rgba[:, :, 1] = signal_norm  # G
        signal_rgba[:, :, 2] = signal_norm  # B
        signal_rgba[:, :, 3] = 1.0  # A
        dpg.set_value(f"signal_texture_{self.tag_suffix}", signal_rgba.flatten())
        dpg.set_value(
            f"position_text_{self.tag_suffix}",
            f"Position: ({self.nav_pos[0]}, {self.nav_pos[1]})",
        )

    def render(self) -> None:
        with dpg.window(tag=f"stem_navigator_{self.tag_suffix}"):
            dpg.add_text(
                f"Postition: ({self.nav_pos[0]}, {self.nav_pos[1]})",
                tag=f"position_text_{self.tag_suffix}",
            )
            dpg.add_image(
                texture_tag=f"signal_texture_{self.tag_suffix}",
            )
            dpg.add_button(label="up", callback=self._move_up)
            dpg.add_button(label="down", callback=self._move_down)
            dpg.add_button(label="left", callback=self._move_left)
            dpg.add_button(label="right", callback=self._move_right)
            dpg.add_button(label="log", callback=self._toggle_log)
            dpg.add_input_float(
                tag=f"vmax_{self.tag_suffix}",
                label="vmax",
                default_value=self.vmax,
                step=1_000,
            )
        self.update_signal()
