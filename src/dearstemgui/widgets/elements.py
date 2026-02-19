from typing import Callable
import dearpygui.dearpygui as dpg


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
