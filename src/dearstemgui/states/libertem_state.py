from typing import Literal, Optional
from libertem.api import Context


class LibertemSate:
    def __init__(self) -> None:
        self.context: Optional[Context] = None

    def create_context(
        self,
        executor: Literal["threads", "dask", "delayed"] = "delayed",
        cpu: Optional[int] = None,
        gpu: Optional[int] = None,
    ) -> Context:
        context = Context.make_with(executor_spec=executor, cpus=cpu, gpus=gpu)
        self.context = context
