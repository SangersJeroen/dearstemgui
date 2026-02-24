import dearpygui.dearpygui as dpg


def create_new_analysis_dialog():
    if dpg.does_item_exist("new_analysis_dialog"):
        dpg.delete_item("new_analysis_dialog")

    with dpg.window(label="new analysis", tag="new_analysis_dialog", pos=(400, 400)):
        pass
