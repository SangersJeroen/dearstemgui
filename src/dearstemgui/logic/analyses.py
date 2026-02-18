from typing import Any, Callable, Literal
from functools import partial

from libertem.api import Context

from dearstemgui.app_state_singleton import APP_STATE
from dearstemgui.widgets.abf_udf_navigator import ABFNavigator
from dearstemgui.widgets.haadf_udf_navigator import HAADFNavigator
from dearstemgui.widgets.measurement_dialog import measurement_selector
from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.widgets.mrstem_navigator import MRSTEMNavigator
from dearstemgui.widgets.point_udf_navigator import PointSignalNavigator


def analyses_router_callback(
    sender: str | Literal[0], app_data: Any, user_data: str
) -> None:

    instancer: Callable[[EMPAD_Measurements, Context, str], None]

    match user_data:
        case "adf":
            instancer = HAADFNavigator
        case "browser":
            instancer = MRSTEMNavigator
        case "abf":
            instancer = ABFNavigator
        case 'point':
            instancer = PointSignalNavigator
        case _:
            print(user_data)

    launch_callback = partial(
        instancer, ctx=APP_STATE.libertem_state.context, tag_suffix=""
    )
    measurement_selector(launch_callback)
