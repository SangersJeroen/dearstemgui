import dearpygui.dearpygui as dpg

from dearstemgui.app_state_singleton import APP_STATE
from dearstemgui.states.libertem_state import LibertemSate


def create_context_dialog() -> None:
    if dpg.does_item_exist("context_create_dialog"):
        dpg.delete_item("context_create_dialog")

    def _parse_inputs_create_context() -> None:
        state: LibertemSate = APP_STATE.libertem_state
        executor: str = dpg.get_value(item="context_create_executor")

        state.create_context(executor=executor)

    with dpg.window(
        label="context create",
        tag="context_create_dialog",
        show=True,
        no_resize=True,
        no_title_bar=False,
        no_scrollbar=True,
        no_collapse=False,
    ):
        dpg.add_combo(
            items=["dask", "delayed", "threads"],
            label="executor:",
            tag="context_create_executor",
        )
        dpg.add_button(label="ceate", callback=_parse_inputs_create_context)
