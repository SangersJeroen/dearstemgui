from typing import Callable, Literal
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


class RangeSelector:
    BAR_Y = 30
    HANDLE_RADIUS = 6
    MIN_GAP = 0.001  # minimum value gap

    def __init__(
        self,
        update_callback: Callable[..., None],
        vmax: float,
        vmin: float,
        parent_tag: str,
        unique_prefix: str,
    ) -> None:
        self.vmax = vmax
        self.vmin = vmin

        self.cmin = vmin
        self.cmax = vmax

        self.width = 1.0
        self.bar_width = 1.0
        self.dragging: Literal["min", "max", "none"] = "none"

        self.parent_tag = parent_tag
        self.unique_prefix = unique_prefix

        self.update_callback = update_callback

    # ------------------------------------------------------------------ tags

    def _tag(self, name: str) -> str:
        return f"{self.unique_prefix}{name}"

    # ------------------------------------------------------------------ mapping

    def value_to_x(self, v: float) -> float:
        return (v - self.vmin) / (self.vmax - self.vmin) * self.bar_width

    def x_to_value(self, x: float) -> float:
        return self.vmin + (x / self.bar_width) * (self.vmax - self.vmin)

    @property
    def min_pos(self) -> float:
        return self.value_to_x(self.cmin)

    @property
    def max_pos(self) -> float:
        return self.value_to_x(self.cmax)

    # ------------------------------------------------------------------ logic

    def set_limits(self, vmin: float | None, vmax: float | None):
        print("setting limits")
        if vmin is not None:
            self.vmin = vmin
        if vmax is not None:
            self.vmax = vmax
        self.cmin = max(self.cmin, self.vmin)
        self.cmax = min(self.cmax, self.vmax)
        self.update()

    # ------------------------------------------------------------------ mouse

    def _mouse_x_local(self) -> float:
        mx, _ = dpg.get_mouse_pos()
        x0, _ = dpg.get_item_rect_min(self._tag("_drawlist"))
        return mx - x0

    def mouse_down(self, sender, app_data):
        x = self._mouse_x_local()

        if abs(x - self.min_pos) < self.HANDLE_RADIUS * 2:
            self.dragging = "min"
        elif abs(x - self.max_pos) < self.HANDLE_RADIUS * 2:
            self.dragging = "max"

    def mouse_up(self, sender, app_data):
        self.dragging = "none"

    def mouse_drag(self, sender, app_data):
        if self.dragging == "none":
            return

        x = max(0.0, min(self.bar_width, self._mouse_x_local()))
        value = self.x_to_value(x)

        if self.dragging == "min":
            self.cmin = min(value, self.cmax - self.MIN_GAP)
        else:
            self.cmax = max(value, self.cmin + self.MIN_GAP)
        self.update()
        self.update_callback()

    # ------------------------------------------------------------------ drawing

    def update(self):
        self.width = max(1.0, dpg.get_item_rect_size(self.parent_tag)[0])
        width = self.width
        self.bar_width = width * 0.8 - 20
        bar_width = self.bar_width
        dpg.set_item_width(self._tag("_drawlist"), width * 0.8)
        dpg.set_item_width(self._tag("_slider_window"), width * 0.9)

        dpg.delete_item(self._tag("_drawlist"), children_only=True)

        # background
        dpg.draw_line(
            (0, self.BAR_Y),
            (bar_width, self.BAR_Y),
            color=(150, 150, 150),
            thickness=4,
            parent=self._tag("_drawlist"),
        )

        # active range
        dpg.draw_line(
            (self.min_pos, self.BAR_Y),
            (self.max_pos, self.BAR_Y),
            color=(100, 180, 255),
            thickness=6,
            parent=self._tag("_drawlist"),
        )

        # handles
        for x in (self.min_pos, self.max_pos):
            dpg.draw_circle(
                (x, self.BAR_Y),
                self.HANDLE_RADIUS,
                fill=(255, 255, 255),
                color=(0, 0, 0),
                parent=self._tag("_drawlist"),
            )

        # label
        dpg.draw_text(
            (10, 5),
            f"Range: {self.cmin:.2f} – {self.cmax:.2f}",
            size=14,
            parent=self._tag("_drawlist"),
        )

    # ------------------------------------------------------------------ public

    def render(self):
        width, _ = dpg.get_item_rect_size(self.parent_tag)

        with dpg.child_window(
            tag=self._tag("_slider_window"),
            width=width * 0.9,
            height=80,
            no_scrollbar=True,
        ):
            dpg.add_drawlist(
                width=width * 0.9 - 20,
                height=60,
                tag=self._tag("_drawlist"),
            )

        with dpg.item_handler_registry(tag=self._tag("_handlers")):
            dpg.add_item_clicked_handler(callback=self.mouse_down)
            dpg.add_item_deactivated_handler(callback=self.mouse_up)
            dpg.add_item_active_handler(callback=self.mouse_drag)

        dpg.bind_item_handler_registry(
            self._tag("_drawlist"),
            self._tag("_handlers"),
        )
        self.update()


class ImPlotElement(object):
    def __init__(
        self,
        shape: tuple[int, int],
        tag_prefix: str,
        parent_tag: str,
        size_fraction: tuple[float, float] = (1.0, 1.0),
    ) -> None:
        super().__init__()

        self.data: np.ndarray = np.zeros(shape)
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

        self.range_slider: RangeSelector = RangeSelector(
            update_callback=self.update_texture,
            vmax=1e6,
            vmin=0,
            parent_tag=self.draw_list_tag + "_child",
            unique_prefix=self.draw_list_tag + "_slider",
        )

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
            self.range_slider.cmin = 0.0
            self.range_slider.cmax = self.data.max()
            self.range_slider.set_limits(0.0, self.data.max())
        else:
            self.range_slider.cmin = 1.0
            self.range_slider.cmax = np.log(self.data.max() + 1)
            self.range_slider.set_limits(1.0, np.log(self.data.max() + 1))
        self.log = not self.log
        self.range_slider.update()
        self.update()

    def _reset_slider(self):
        self.range_slider.cmin = self.data.min()
        self.range_slider.cmax = self.data.max()
        self.range_slider.vmin = self.data.min()
        self.range_slider.vmax = self.data.max()
        self.range_slider.update()

    def render(self):
        width, height = dpg.get_item_rect_size(self.parent_tag)
        with dpg.child_window(no_scrollbar=True, tag=self.draw_list_tag + "_child"):
            with dpg.drawlist(width=width, height=width, tag=self.draw_list_tag):
                pass
            dpg.add_button(label="toggle log", callback=self._toggle_log, pos=(0, 0))
            self.range_slider.render()

    def normalize(self, data: np.ndarray) -> np.ndarray:
        norm_data = np.log(data + 1) if self.log else data

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
        self.range_slider.update()
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
        return
