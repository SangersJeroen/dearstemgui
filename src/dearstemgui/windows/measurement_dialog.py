from typing import Any
from collections.abc import Callable

import dearpygui.dearpygui as dpg

from dearstemgui.app_state_singleton import APP_STATE
from dearstemgui.windows.open_file_dialog import open_file_dialog


index: int | None = None

def measurement_selector(launch_callback: Callable) -> None:

    if dpg.does_item_exist("measurement_selector"):
        dpg.delete_item("measurement_selector")

    def close_dialog() -> None:
        measurement = APP_STATE.loaded_measurements[int(index)]
        widget = launch_callback(measurement)
        widget.render()
        dpg.delete_item("measurement_selector")

    def refresh() -> None:
        measurement_selector(launch_callback=launch_callback)

    def update_select_label(sender: int | str, app_data: Any, user_data: int) -> None:
        global index
        dpg.configure_item("measurement_select_continue", label=f"Select {user_data}")
        index = int(user_data)

    def open_and_refresh() -> None:
        open_file_dialog()
        measurement_selector(launch_callback=launch_callback)

    with dpg.window(tag="measurement_selector", label="Select or Create Measurement"):
        with dpg.table(tag="measurement_selector_table"):
            dpg.add_table_column(label="index")
            dpg.add_table_column(label="name")
            dpg.add_table_column(label="folder")
            for i, k in enumerate(APP_STATE.loaded_measurements.values()):
                with dpg.table_row(label=f"{i}"):
                    dpg.add_selectable(label=f'{int(i)}', callback=update_select_label, user_data=int(i))
                    for j, key in zip(range(2), ["name", "folder"]):
                        dpg.add_selectable(label=getattr(k, key), callback=update_select_label, user_data=int(i))

        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Load New File",
                tag="measurement_selector_load_new",
                callback=open_and_refresh,
            )
            dpg.add_button(
                tag="measurement_select_continue",
                label=f"Select {dpg.get_value('measurement_selector_options')}",
                callback=close_dialog,
            )
            dpg.add_button(callback=refresh, label="Refresh")
