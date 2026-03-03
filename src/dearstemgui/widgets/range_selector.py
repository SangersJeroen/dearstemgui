from collections.abc import Callable
from typing import Literal

import dearpygui.dearpygui as dpg


class RangeSelector:
    def __init__(
        self,
        update_callback: Callable[..., None],
        tag: str,
        parent_tag: str,
        init_range: tuple[float, float],
        width_fraction: float = 1,
        height: int = 40,
    ) -> None:

        self.cmin: float = init_range[0]
        self.cmax: float = init_range[1]

        self.update_callback = update_callback

        self._tag: str = tag
        self._parent_tag: str = parent_tag

        self.dragging: Literal["min", "max", "none"] = "none"

        self.width_fraction: float = width_fraction
        self.bar_width: float = 1
        self.height = height

        print(f"RangeSelector with tag: {self._tag} created")

    def value_to_pos(self, value: float) -> float:
        if self.vmax - self.vmin == 0:
            return 1.0
        return (value - self.vmin) / (self.vmax - self.vmin) * self.bar_width

    def pos_to_value(self, pos: float) -> float:
        return self.vmin + (pos / self.bar_width) * (self.vmax - self.vmin)

    @property
    def vmin(self) -> float:
        return float(dpg.get_value(self._tag + "_lower_bound"))

    @property
    def vmax(self) -> float:
        return float(dpg.get_value(self._tag + "_upper_bound"))

    @property
    def min_pos(self) -> float:
        return self.value_to_pos(self.cmin)

    @property
    def max_pos(self) -> float:
        return self.value_to_pos(self.cmax)

    def set_limits(self, vmin: float, vmax: float):
        dpg.set_value(self._tag + "_upper_bound", f"{vmax}")
        dpg.set_value(self._tag + "_lower_bound", f"{vmin}")
        self.cmin = vmin
        self.cmax = vmax
        self.update()

    def _mouse_x_local(self) -> float:
        mx, _ = dpg.get_drawing_mouse_pos()
        return mx

    def mouse_down(self, sender, app_data):
        x = self._mouse_x_local()
        print(x)

        if abs(x - self.min_pos) < 6 * 2:
            print("clicked min")
            self.dragging = "min"
        elif abs(x - self.max_pos) < 6 * 2:
            print("clicked max")
            self.dragging = "max"

    def mouse_up(self, sender, app_data):
        self.dragging = "none"

    def mouse_drag(self, sender, app_data):
        if self.dragging == "none":
            return

        x = max(0, min(self.bar_width, self._mouse_x_local()))
        value = self.pos_to_value(x)

        if self.dragging == "min":
            self.cmin = min(value, self.cmax)
        else:
            self.cmax = max(value, self.cmin)
        self.update()
        self.update_callback()

    def update(self) -> None:
        pwidth, _ = dpg.get_item_rect_size(self._parent_tag)
        width = pwidth * self.width_fraction
        self.bar_width = width - 140

        if (maxv := float(dpg.get_value(self._tag + "_upper_bound"))) < self.cmax:
            self.cmax = maxv
        if (minv := float(dpg.get_value(self._tag + "_lower_bound"))) > self.cmin:
            self.cmin = minv

        dpg.set_item_width(self._tag + "_drawlist", width - 140)
        dpg.delete_item(self._tag + "_drawlist", children_only=True)

        dpg.draw_line(
            (0, self.height / 2),
            (self.bar_width, self.height / 2),
            color=(150, 150, 150),
            thickness=4,
            parent=self._tag + "_drawlist",
        )
        dpg.draw_line(
            (self.min_pos, self.height / 2),
            (self.max_pos, self.height / 2),
            color=(180, 0, 0),
            thickness=6,
            parent=self._tag + "_drawlist",
        )
        for pos in (self.min_pos, self.max_pos):
            dpg.draw_circle(
                (pos, self.height / 2),
                6,
                fill=(180, 0, 0),
                color=(180, 0, 0),
                parent=self._tag + "_drawlist",
            )
        self.update_callback()

    def render(self):
        pwidth, _ = dpg.get_item_rect_size(self._parent_tag)
        width = pwidth * self.width_fraction
        self.bar_width = width - 140

        with dpg.group(horizontal=True):
            dpg.add_input_text(
                default_value="0",
                width=60,
                tag=self._tag + "_lower_bound",
                callback=lambda: self.update(),
            )
            dpg.add_spacer(width=10)
            dpg.add_drawlist(
                width=self.bar_width,
                height=self.height,
                tag=self._tag + "_drawlist",
            )
            dpg.add_spacer(width=10)
            dpg.add_input_text(
                default_value="1e5",
                width=60,
                tag=self._tag + "_upper_bound",
                callback=lambda: self.update(),
            )

        with dpg.item_handler_registry(tag=self._tag + "_handlers"):
            dpg.add_item_clicked_handler(callback=lambda s, a: self.mouse_down(s, a))
            dpg.add_item_deactivated_handler(callback=lambda s, a: self.mouse_up(s, a))
            dpg.add_item_active_handler(callback=lambda s, a: self.mouse_drag(s, a))

        dpg.bind_item_handler_registry(
            self._tag + "_drawlist",
            self._tag + "_handlers",
        )
        self.set_limits(vmin=self.cmin, vmax=self.cmax)
        self.update()
