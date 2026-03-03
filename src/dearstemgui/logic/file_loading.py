from libertem.api import Context
from libertem.io.dataset.empad import *

from dearstemgui.app_state_singleton import APP_STATE
from dearstemgui.logic.measurement import EMPAD_Measurements
from dearstemgui.windows.analyses.haadf_udf_navigator import HAADFNavigator
from dearstemgui.windows.analyses.signal_navigator import MRSTEMNavigator


def file_open_router(sender: str, data: dict) -> None:
    file_path: str = data["file_path_name"]
    file_name: str = file_path.rsplit("/", maxsplit=1)[-1]
    extension: str = file_path.rsplit(".", maxsplit=1)[-1]

    match extension:
        case "xml":
            ctx = APP_STATE.libertem_state.context
            if ctx is None:
                raise Exception("No context")
            ctx: Context

            new_measurement = EMPAD_Measurements(file_path)
            index = APP_STATE.add_measurement(new_measurement)
            new_measurement.index = index
