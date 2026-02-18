from typing import Any, Literal
from functools import partial

from dearstemgui.app_state_singleton import APP_STATE
from dearstemgui.widgets.haadf_udf_navigator import HAADFNavigator
from dearstemgui.widgets.measurement_dialog import measurement_selector
from dearstemgui.logic.measurement import EMPAD_Measurements


def analyses_router_callback(
    sender: str | Literal[0], app_data: Any, user_data: str
) -> None:

    match user_data:
        case 'adf':
            instancer = HAADFNavigator
        case _:
            print(user_data)

    launch_callback = partial(instancer, ctx=APP_STATE.libertem_state.context, tag_suffix='')
    measurement = measurement_selector(launch_callback)

