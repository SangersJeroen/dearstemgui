import dearpygui.dearpygui as dpg
from .range_selector import RangeSelector
import numpy as np


class ImPlotElement(object):
    def __init__(
        self,
        shape: tuple[int, int],
        tag_prefix: str,
        parent_tag: str,
        size_fraction: tuple[float, float] = (1.0, 1.0),
    ) -> None:
        super().__init__()

        self.data: np.ndarray = np.random.random(size=shape)
        self.size_w_fraction: float = size_fraction[0]
        self.size_h_fraction: float = size_fraction[1]

        self.sig_width: int = shape[1]
        self.sig_height: int = shape[0]

        self.log: bool = False

        self.im_rgba = np.zeros((self.sig_height, self.sig_width, 4), dtype=np.float32)
        self.im_rgba[:, :, 3] = 1.0
        self.scale_x = 1.0
        self.scale_y = 1.0

        self.texture_tag: str = tag_prefix + "_texture"
        self.draw_list_tag: str = tag_prefix + "_drawlist"
        self.parent_tag: str = parent_tag

        self.range_slider: RangeSelector

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
            self.range_slider.set_limits(self.data.min(), self.data.max())
        else:
            self.range_slider.set_limits(
                1, np.log(self.data.max() - self.data.min() + 1)
            )
        self.log = not self.log
        self._reset_slider()
        self.range_slider.update()
        self.update()

    def _reset_slider(self):
        self.range_slider.cmin = self.data.min()
        self.range_slider.cmax = self.data.max()
        self.range_slider.set_limits(
            vmin=int(self.data.min()), vmax=int(self.data.max())
        )
        self.update()

    def render(self):
        width, height = dpg.get_item_rect_size(self.parent_tag)
        with dpg.child_window(no_scrollbar=True, width=width, height=width):
            with (
                dpg.collapsing_header(
                    label="Image Options", tag=self.draw_list_tag + "_child"
                ),
            ):
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="toggle log",
                        callback=self._toggle_log,
                        tag=self.draw_list_tag + "_log",
                    )
                    dpg.add_button(
                        label="reset",
                        callback=self._reset_slider,
                    )
                self.range_slider = RangeSelector(
                    update_callback=self.update_texture,
                    tag=self.draw_list_tag + "_slider",
                    parent_tag=self.draw_list_tag + "_child",
                    init_range=(0, 1e5),
                    width_fraction=0.8,
                )
            with dpg.drawlist(width=width, height=width, tag=self.draw_list_tag):
                pass

        self.update()

    def normalize(self, data: np.ndarray) -> np.ndarray:
        norm_data = np.log(data - data.min() + 1) if self.log else data

        norm_data = np.where(
            norm_data > self.range_slider.cmax, self.range_slider.cmax, norm_data
        )
        norm_data = np.where(
            norm_data < self.range_slider.cmin, self.range_slider.cmin, norm_data
        )

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

        width *= self.size_w_fraction
        height *= self.size_h_fraction

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

        self.scale_x = width / self.sig_width
        self.scale_y = height / self.sig_height

        texture_min = (0, 10)
        texture_max = (width, width)

        dpg.draw_image(
            texture_tag=self.texture_tag,
            pmin=texture_min,
            pmax=texture_max,
            parent=draw_list_tag,
        )
