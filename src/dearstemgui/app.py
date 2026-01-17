import dearpygui.dearpygui as dpg


class MainWindow:
    def __init__(self) -> None:
        dpg.create_context()
        self._setup_window()
        self.run()

    @staticmethod
    def _setup_window() -> None:
        with dpg.window(tag="main_window", label="dearstemgui", no_close=True):
            with dpg.menu_bar(tag="main_window_menu_bar"):
                with dpg.menu(tag="main_window_menu_file"):
                    dpg.add_menu_item(
                        tag="main_window_menu_file_exit",
                        label="exit",
                        callback=dpg.stop_dearpygui,
                    )

    @staticmethod
    def run() -> None:
        dpg.create_viewport(title="EMPAD GUI", width=1200, height=800)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(window="main_window", value=True)
        dpg.start_dearpygui()
        dpg.destroy_context()
