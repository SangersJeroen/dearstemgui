from collections.abc import Callable
from pathlib import Path
import xml.etree.ElementTree as ET

from libertem.api import DataSet
import numpy as np

from dearstemgui.app_state_singleton import APP_STATE


def expand_blob(blob, attributes={}):
    if len(blob) > 0:
        for child in blob:
            expand_blob(child, attributes)
    else:
        attributes[blob.tag] = blob.attrib
        attributes[blob.tag + "_data"] = blob.text
    return attributes


def parse_xml_file(xml_file_path: Path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    parsed_xml = expand_blob(root)
    return parsed_xml


class AcquisitionParameters:
    def __init__(self) -> None:
        self.exposure_time_data: float = 0.0  # milliseconds
        self.post_exposure_time_data: float = 0.0  # milliseconds
        self.scan_resolution_x_data: int = 0  # scan pixels
        self.scan_resolution_y_data: int = 0  # scan pixels
        self.scan_center_x_data: float = 0.0  # scan pattern center [0..1] FOV
        self.scan_size_data: float = 0.0  # scan pattern size [0..1] FOV
        self.scan_center_y_data: float = 0.0  # scan pattern center [0..1] FOV
        self.center_x_data: int = 0  # sensor pixels offset
        self.center_y_data: int = 0  # sensor pixels offset
        self.scan_rotation_data: float = 0.0  # degrees
        self.spot_size_index_data: int = 0  # spot size [1..11]
        self.scale_factor_data: float = 0.0  # unkown
        self.x_data: float = 0.0  # meters
        self.y_data: float = 0.0  # meters
        self.nominal_camera_length_data: float = 0.0  # meters
        self.high_voltage_data: float = 0.0  # volts

        # Set in post_init
        self.scan_xaxis: np.ndarray
        self.scan_yaxis: np.ndarray
        self.scan_xscale: float
        self.scan_yscale: float

    @classmethod
    def from_path(cls, xml_file_path: Path):
        parsed_xml = parse_xml_file(xml_file_path)
        params = cls()
        key: str
        value: str
        for key, value in parsed_xml.items():
            if hasattr(params, key):
                cast_to = type(getattr(params, key))
                setattr(params, key, cast_to(value))
        params.__post_init__()
        return params

    def __post_init__(self) -> None:
        self.scan_xscale = self.x_data / self.scan_resolution_x_data
        self.scan_yscale = self.y_data / self.scan_resolution_y_data
        self.scan_xaxis: np.ndarray = (
            (np.arange(self.scan_resolution_x_data) + 0.5) - self.scan_center_x_data
        ) * self.scan_xscale
        self.scan_yaxis: np.ndarray = (
            (np.arange(self.scan_resolution_y_data) + 0.5) - self.scan_center_y_data
        ) * self.scan_yscale


class EMPAD_Measurements:
    def __init__(self, xml_file_path: str) -> None:
        self.acq_params: AcquisitionParameters = AcquisitionParameters.from_path(
            xml_file_path
        )
        if APP_STATE.libertem_state is None:
            raise RuntimeError("Libertem state is not initialized")

        self.index: int | None = None
        self.dataset: DataSet = APP_STATE.libertem_state.context.load(
            filetype="empad", path=xml_file_path
        )
        self.pacbed: np.ndarray | None = None
        self.adf: np.ndarray | None = None
        self.abf: np.ndarray | None = None

        # Center Reference
        self.reference_center = tuple([i / 2 for i in self.dataset.shape.sig])

        # Rigid shift signals
        self.rigid_shift_sensor_axis_0: np.ndarray | None = None
        self.rigid_shift_sensor_axis_1: np.ndarray | None = None

        # Center of mass shift signals
        self.com_shift_sensor_axis_0: np.ndarray | None = None
        self.com_shift_sensor_axis_1: np.ndarray | None = None

        # Navigation location
        self.pos_x_idx: int = 0
        self.pos_y_idx: int = 0
        self.update_nav_callbacks: list[Callable] = []

    def update_open(self) -> None:
        for callback in self.update_nav_callbacks:
            callback()

    def set_index(self, index: int) -> None:
        self.index: int = index


def main():
    path = Path(r"/home/jeroensangers/Data/acquisition_6/acquisition_6.xml")
    print(parse_xml_file(path))
    return AcquisitionParameters.from_path(path)


if __name__ == "__main__":
    params = main()
