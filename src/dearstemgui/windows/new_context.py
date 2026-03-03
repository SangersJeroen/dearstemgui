from typing import TYPE_CHECKING

import dearpygui.dearpygui as dpg

from dearstemgui.app_state_singleton import APP_STATE

if TYPE_CHECKING:
    from dearstemgui.states.libertem_state import LibertemSate


def create_context_dialog() -> None:
    if dpg.does_item_exist("context_create_dialog"):
        dpg.delete_item("context_create_dialog")

    def _parse_inputs_create_context() -> None:
        state: LibertemSate = APP_STATE.libertem_state
        executor: str = dpg.get_value(item="context_create_executor")
        num_cpu: int = dpg.get_value("context_create_dialog_cpu")

        state.create_context(executor=executor, cpu=num_cpu)

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
            items=["dask", "delayed", "threads", "inline"],
            label="executor:",
            tag="context_create_executor",
        )
        dpg.add_button(
            label="ceate",
            callback=_parse_inputs_create_context,
        )
        with dpg.group():
            dpg.add_input_int(
                label="# CPUs:",
                min_value=1,
                max_value=12,
                default_value=2,
                tag="context_create_dialog_cpu",
            )
