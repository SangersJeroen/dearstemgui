# pyright: basic
import dearpygui.dearpygui as dpg

from dearstemgui.app_state_singleton import APP_STATE
from dearstemgui.logic.analyses import analyses_router_callback
from dearstemgui.states.app import AppState
from dearstemgui.windows.new_context import create_context_dialog
from dearstemgui.windows.open_file_dialog import open_file_dialog


class MainWindow:
    def __init__(self) -> None:
        self.app_state: AppState = APP_STATE
        dpg.create_context()
        self._setup_window()
        self.run()

    @staticmethod
    def _setup_window() -> None:
        with (
            dpg.window(tag="main_window", label="dearstemgui", no_close=True),
            dpg.menu_bar(tag="main_window_menu_bar"),
        ):
            with dpg.menu(tag="main_window_menu_file", label="File"):
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
            with dpg.menu(tag="main_window_menu_new_analyses", label="Analyses"):
                dpg.add_menu_item(
                    label="Browser",
                    user_data="browser",
                    callback=analyses_router_callback,
                )
                dpg.add_separator()
                with dpg.menu(
                    tag="main_window_menu_new_analyses_masks",
                    label="Intensity Mask",
                ):
                    dpg.add_menu_item(
                        tag="new_analyses_masks_adf",
                        label="Annular Dark-Field",
                        user_data="adf",
                        callback=analyses_router_callback,
                    )
                    dpg.add_menu_item(
                        tag="new_analyses_masks_abf",
                        label="Axial Bright-Field",
                        user_data="abf",
                        callback=analyses_router_callback,
                    )
                    dpg.add_menu_item(
                        tag="new_analyses_masks_point",
                        label="Point",
                        user_data="point",
                        callback=analyses_router_callback,
                    )
                    dpg.add_menu_item(
                        tag="new_analyses_masks_paint",
                        label="Paint",
                        user_data="paint",
                        callback=analyses_router_callback,
                    )
                dpg.add_separator()
                with dpg.menu(
                    tag="main_window_menu_analysis_mrstem",
                    label="Momentum Resolved",
                ):
                    dpg.add_menu_item(
                        tag="new_analyses_mrstem_rigid_shift",
                        label="Rigid Deflection",
                        user_data="rigid",
                        callback=analyses_router_callback,
                    )
                    dpg.add_menu_item(
                        tag="new_analyses_mrstem_com_shift",
                        label="CoM Deflection",
                        user_data="com",
                        callback=analyses_router_callback,
                    )
                dpg.add_separator()
                dpg.add_menu_item(
                    tag="new_analyses_pacbed",
                    label="PACBED",
                    user_data="pacbed",
                    callback=analyses_router_callback,
                )

    @staticmethod
    def run() -> None:
        dpg.create_viewport(title="EMPAD GUI", width=1200, height=800)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(window="main_window", value=True)
        dpg.start_dearpygui()
        dpg.destroy_context()
