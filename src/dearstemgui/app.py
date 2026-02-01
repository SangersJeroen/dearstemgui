# pyright: basic
import dearpygui.dearpygui as dpg

from dearstemgui.app_state_singleton import APP_STATE
from dearstemgui.states.app import AppState
from dearstemgui.widgets.analysis_dialog import create_new_analysis_dialog
from dearstemgui.widgets.context_dialog import create_context_dialog
from dearstemgui.widgets.file_dialogs import open_file_dialog


class MainWindow:
    def __init__(self) -> None:
        self.app_state: AppState = APP_STATE
        dpg.create_context()
        self._setup_window()
        self.run()

    @staticmethod
    def _setup_window() -> None:
        with dpg.window(tag="main_window", label="dearstemgui", no_close=True):
            with dpg.menu_bar(tag="main_window_menu_bar"):
                with dpg.menu(tag="main_window_menu_file", label="file"):
                    dpg.add_menu_item(
                        tag="main_window_menu_file_open",
                        label="open",
                        callback=open_file_dialog,
                    )
                    dpg.add_menu_item(
                        tag="main_window_menu_file_context",
                        label="context create",
                        callback=create_context_dialog,
                    )
                    dpg.add_menu_item(
                        tag="main_window_menu_file_exit",
                        label="exit",
                        callback=dpg.stop_dearpygui,
                    )
                with dpg.menu(tag="main_window_menu_analyses", label="analysis"):
                    dpg.add_menu_item(
                        tag="main_window_menu_analysis_new",
                        label="new",
                        callback=create_new_analysis_dialog,
                    )

    @staticmethod
    def run() -> None:
        dpg.create_viewport(title="EMPAD GUI", width=1200, height=800)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(window="main_window", value=True)
        dpg.start_dearpygui()
        dpg.destroy_context()
