from typing import Literal

from libertem.api import Context


class LibertemSate:
    def __init__(self) -> None:
        self.context: Context | None = None

    def create_context(
        self,
        executor: Literal["threads", "dask", "delayed", "inline"] = "delayed",
        cpu: int | None = None,
        gpu: int | None = None,
    ) -> Context:
        context = Context.make_with(executor_spec=executor, cpus=cpu, gpus=gpu)
        self.context = context

    def delete_context(self) -> None:
        self.context = None
