from typing import override
import dearpygui.dearpygui as dpg
from libertem.api import Context, DataSet
import numpy as np

from dearstemgui.widgets.mrstem_navigator import MRSTEMNavigator


class HAADFNavigator(MRSTEMNavigator):
    def __init__(self, ds: DataSet, ctx: Context, tag_suffix: str) -> None:
        super().__init__(ds, ctx, tag_suffix)
        self.tag_prefix: str = 'ds_haadf_'

    @override
    def _setup_textures(self) -> None:
        super()._setup_textures()
        with dpg.texture_registry():
            result_data = np.zeros((*self.nav_shape, 4), dtype=np.float32)
            result_data[:, :, 3] = 1.0
            dpg.add_raw_texture(
                width=self.nav_shape[1],
                height=self.nav_shape[0],
                default_value=result_data.flatten(),
                format=dpg.mvFormat_Float_rgba,
                tag=self._tag("result_texture")
            )

