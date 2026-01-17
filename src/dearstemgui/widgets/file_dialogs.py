from pathlib import Path

import dearpygui.dearpygui as dpg

from dearstemgui.debug import debug_callback


def open_file_dialog() -> Path:
    if dpg.does_item_exist("file_dialog"):
        dpg.delete_item("file_dialog")

    with dpg.file_dialog(
        tag="file_dialog",
        directory_selector=False,
        show=True,
        callback=debug_callback,
        width=700,
        height=400,
        default_path=str(Path.home()),
    ):
        dpg.add_file_extension(
            extension=".xml",
        )
