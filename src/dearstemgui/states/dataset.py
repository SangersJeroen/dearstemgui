from libertem.api import Context, DataSet


class DatasetState:
    def __init__(self, context: Context, dataset: DataSet) -> None:
        self.ds: DataSet = dataset
        self.ctx: Context = context
        self.shape: tuple[int, ...] = self.ds.shape
