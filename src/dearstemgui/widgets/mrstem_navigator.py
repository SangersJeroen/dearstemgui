import dearpygui.dearpygui as dpg
from libertem.api import Context, DataSet
from libertem.udf.raw import PickUDF
import numpy as np

from dearstemgui.logic.measurement import EMPAD_Measurements


class MRSTEMNavigator:
    def __init__(
        self, measurement: EMPAD_Measurements, ctx: Context, tag_suffix: str
    ) -> None:
        self.tag_prefix: str = str(measurement.index) + "_" + "ds_nav_"
        self.tag_suffix: str = "_" + tag_suffix

        self.measurement: EMPAD_Measurements = measurement
        self.measurement.update_nav_callbacks.append(self.update_signal)
        self.ds: DataSet = measurement.dataset
        self.ctx: Context = ctx

        self.nav_shape: tuple[int, int] = self.ds.shape.nav
        self.sig_shape: tuple[int, int] = self.ds.shape.sig

        self.vmax: float = np.inf
        self.plot_log: bool = False

        self.signal_rgba: np.ndarray = np.zeros((*self.nav_shape, 4), dtype=np.float32)
        self.signal_rgba[:, :, 3] = 1.0

    def _setup_textures(self) -> None:
        with dpg.texture_registry():
            dpg.add_raw_texture(
                width=self.sig_shape[1],
                height=self.sig_shape[0],
                default_value=self.signal_rgba.flatten(),
                format=dpg.mvFormat_Float_rgba,
                tag=self._tag("signal_texture"),
            )

    def _tag(self, tag: str) -> str:
        return self.tag_prefix + tag + self.tag_suffix

    def _move_up(self) -> None:
        if self.measurement.pos_y_idx > 0:
            self.measurement.pos_y_idx -= 1
        self.measurement.update_open()

    def _move_down(self) -> None:
        if self.measurement.pos_y_idx < self.nav_shape[0] - 1:
            self.measurement.pos_y_idx += 1
        self.measurement.update_open()

    def _move_left(self) -> None:
        if self.measurement.pos_x_idx > 0:
            self.measurement.pos_x_idx -= 1
        self.measurement.update_open()

    def _move_right(self) -> None:
        if self.measurement.pos_x_idx < self.nav_shape[1] - 1:
            self.measurement.pos_x_idx += 1
        self.measurement.update_open()

    def _toggle_log(self) -> None:
        self.plot_log = not self.plot_log
        self.update_signal()

    def update_signal(self) -> None:
        roi = np.zeros(self.nav_shape, dtype=bool)
        roi[self.measurement.pos_y_idx, self.measurement.pos_x_idx] = True

        pick_udf = PickUDF()
        result = self.ctx.run_udf(dataset=self.ds, udf=pick_udf, roi=roi)
        signal_data = np.array(result["intensity"].data[0].reshape(self.sig_shape))

        if self.plot_log:
            signal_data = np.log(signal_data - signal_data.min() + 1)

        self.vmax = float(dpg.get_value(self._tag("vmax")))
        signal_data = np.where(signal_data > self.vmax, self.vmax, signal_data)

        signal_norm = (signal_data - signal_data.min()) / (
            signal_data.max() - signal_data.min() + 1e-10
        )
        signal_rgba = np.zeros((*self.sig_shape, 4), dtype=np.float32)
        signal_rgba[:, :, 0] = signal_norm  # R
        signal_rgba[:, :, 1] = signal_norm  # G
        signal_rgba[:, :, 2] = signal_norm  # B
        signal_rgba[:, :, 3] = 1.0  # A
        self.signal_rgba = signal_rgba
        self._push_update()

    def _push_update(self) -> None:
        dpg.set_value(self._tag("signal_texture"), self.signal_rgba.flatten())
        dpg.set_value(
            self._tag("position_text"),
            f"Position: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
        )

    def render(self) -> None:
        self._setup_textures()
        with dpg.window(
            tag=self._tag("stem_navigator"),
            label=str(self.measurement.index) + " Navigator",
        ):
            dpg.add_text(
                f"Position: ({self.measurement.pos_y_idx}, {self.measurement.pos_x_idx})",
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
        self.update_signal()
