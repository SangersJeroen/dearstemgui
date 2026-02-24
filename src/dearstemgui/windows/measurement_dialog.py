from typing import Callable
import dearpygui.dearpygui as dpg
from dearstemgui.app_state_singleton import APP_STATE
from dearstemgui.windows.open_file_dialog import open_file_dialog


def measurement_selector(launch_callback: Callable) -> None:
    if dpg.does_item_exist("measurement_selector"):
        dpg.delete_item("measurement_selector")

    def close_dialog():
        index = dpg.get_value("measurement_selector_options")
        measurement = APP_STATE.loaded_measurements[int(index)]
        widget = launch_callback(measurement) 
        widget.render()
        dpg.delete_item("measurement_selector")

    def refresh() -> None:
        dpg.configure_item(
            "measurement_selector_options",
            items=[str(k) for k in APP_STATE.loaded_measurements],
        )

    def update_select_label(sender, app_data):
        dpg.configure_item("measurement_select_continue", label=f"Select {app_data}")

    def open_and_refresh() -> None:
        open_file_dialog()

    with dpg.window(tag="measurement_selector", label="Select or Create Measurement"):
        dpg.add_button(
            label="Load New File",
            tag="measurement_selector_load_new",
            callback=open_and_refresh,
        )
        dpg.add_listbox(
            tag="measurement_selector_options",
            items=[str(k) for k in APP_STATE.loaded_measurements],
            callback=update_select_label,
        )
        dpg.add_button(
            tag='measurement_select_continue',
            label=f"Select {dpg.get_value('measurement_selector_options')}",
            callback=close_dialog,
        )
        dpg.add_button(callback=refresh, label="Refresh")
