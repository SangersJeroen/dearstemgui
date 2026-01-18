import dearpygui.dearpygui as dpg
import numpy as np


class TexturePlotter:
    def __init__(self, width: int, height: int, tag: str) -> None:
        self.width = width
        self.height = height
        self.tag = tag
        self.rgba: np.ndarray = np.zeros((height, width, 4), dtype=np.float32)
        self.rgba[:, :, 3] = 1.0

    def setup_texture(self) -> None:
        with dpg.texture_registry():
            dpg.add_raw_texture(
                width=self.width,
                height=self.height,
                default_value=self.rgba.flatten(),
                format=dpg.mvFormat_Float_rgba,
                tag=self.tag,
            )

    def update(self, data: np.ndarray) -> None:
        data_norm = (data - data.min()) / (data.max() - data.min() + 1e-10)
        self.rgba[:, :, 0] = data_norm
        self.rgba[:, :, 1] = data_norm
        self.rgba[:, :, 2] = data_norm
        self.rgba[:, :, 3] = 1.0

    def push_update(self) -> None:
        dpg.set_value(self.tag, self.rgba.flatten())
