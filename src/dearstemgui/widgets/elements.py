from typing import Callable
import dearpygui.dearpygui as dpg
import numpy as np


def navigation_element(
    callbacks: list[Callable[..., None]],
    btn_size: int = 40,
    pad: int = 10,
) -> None:

    mwidth: int = btn_size * 4 + 2 * pad
    mheight: int = btn_size * 3 + 2 * pad
    with dpg.child_window(width=mwidth, height=mheight, no_scrollbar=True):
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=btn_size + pad)
            dpg.add_button(
                label="^", callback=callbacks[0], width=btn_size, height=btn_size
            )

        with dpg.group(horizontal=True):
            dpg.add_button(
                label="<", callback=callbacks[1], width=btn_size, height=btn_size
            )
            dpg.add_spacer(width=2 * pad + btn_size)
            dpg.add_button(
                label=">", callback=callbacks[2], width=btn_size, height=btn_size
            )

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=btn_size + pad)
            dpg.add_button(
                label="v", callback=callbacks[3], width=btn_size, height=btn_size
            )


class ImPlotElement(object):
    def __init__(
        self, shape: tuple[int, int], tag_prefix: str, parent_tag: str
    ) -> None:
        super().__init__()
        self.data: np.ndarray = np.zeros(shape)

        self.sig_width: int = shape[1]
        self.sig_height: int = shape[0]

        self.vmax: float = np.inf
        self.vmin: float = 0
        self.log: bool = False

        self.im_rgba = np.zeros((self.sig_height, self.sig_width, 4), dtype=np.float32)
        self.im_rgba[:, :, 3] = 1.0
        self.scale_x = 1.0
        self.scale_y = 1.0

        self.texture_tag: str = tag_prefix + "_texture"
        self.draw_list_tag: str = tag_prefix + "_drawlist"
        self.parent_tag: str = parent_tag

        with dpg.texture_registry():
            dpg.add_raw_texture(
                width=self.sig_width,
                height=self.sig_height,
                default_value=self.im_rgba.flatten(),
                format=dpg.mvFormat_Float_rgba,
                tag=self.texture_tag,
            )

    def _toggle_log(self) -> None:
        if self.log:  # was log
            self.vmin = 0.0
            self.vmax = np.exp(self.vmax)
        else:
            self.vmin = 1.0
            self.vmax = np.log(self.vmax)
        self.log = not self.log

        self.update()

    def render(self):
        width, height = dpg.get_item_rect_size(self.parent_tag)
        with dpg.child_window(no_scrollbar=True):
            with dpg.drawlist(width=width, height=width, tag=self.draw_list_tag):
                pass
            dpg.add_button(label="toggle log", callback=self._toggle_log, pos=(0, 0))

        with dpg.item_handler_registry() as handler:
            dpg.add_item_visible_handler(callback=lambda: self.update())
            dpg.add_item_resize_handler(callback=lambda: self.update())
        dpg.bind_item_handler_registry(self.draw_list_tag, handler)

    def normalize(self, data: np.ndarray) -> np.ndarray:
        norm_data = np.where(data > self.vmax, self.vmax, data)
        norm_data = np.where(norm_data < self.vmin, self.vmin, norm_data)

        if self.log:
            norm_data = np.log(norm_data + 1)

        dmin, dmax = norm_data.min(), norm_data.max()
        norm_data = (norm_data - dmin) / (dmax - dmin + 1e-10)
        return norm_data

    def update_texture(self) -> None:
        norm_data = self.normalize(self.data)
        self.im_rgba[:, :, 0] = norm_data
        self.im_rgba[:, :, 1] = norm_data
        self.im_rgba[:, :, 2] = norm_data

        dpg.set_value(self.texture_tag, self.im_rgba.flatten())

    def update(self, data: None | np.ndarray = None) -> None:
        if data is not None:
            self.data = data
        self.update_texture()

        draw_list_tag: str = self.draw_list_tag
        width, height = dpg.get_item_rect_size(self.parent_tag)

        window_tag = dpg.get_item_parent(draw_list_tag)

        dpg.set_item_width(window_tag, width)
        dpg.set_item_height(window_tag, width)

        dpg.set_item_width(draw_list_tag, width)
        dpg.set_item_height(draw_list_tag, width)

        if dpg.does_item_exist(draw_list_tag):
            dpg.delete_item(draw_list_tag, children_only=True)

        width, height = dpg.get_item_rect_size(draw_list_tag)

        # Only draw if we have valid dimensions
        if width <= 0 or height <= 0:
            return

        texture_min = (0, 10)
        texture_max = (width, width)

        dpg.draw_image(
            texture_tag=self.texture_tag,
            pmin=texture_min,
            pmax=texture_max,
            parent=draw_list_tag,
        )
