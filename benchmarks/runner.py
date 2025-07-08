import gc
from abc import ABC, abstractmethod
from typing import Any

import pyperf
from datasets import load_datasets


class BSONModule(ABC):
    @abstractmethod
    def encode(self, data: dict[str, Any]) -> bytes: ...

    @abstractmethod
    def decode(self, data: bytes) -> dict[str, Any]: ...


def run(module: BSONModule) -> None:
    def bench_encode(data: dict[str, Any]) -> None:
        gc.disable()
        module.encode(data)
        gc.enable()

    def bench_decode(data: bytes) -> None:
        gc.disable()
        module.decode(data)
        gc.enable()

    def bench_encode_decode(data: dict[str, Any]) -> None:
        gc.disable()
        encoded = module.encode(data)
        module.decode(encoded)
        gc.enable()

    datasets = load_datasets()
    runner = pyperf.Runner()

    for name, data in datasets.items():
        runner.bench_func(f"encode_{name}", bench_encode, data)
        runner.bench_func(f"decode_{name}", bench_decode, module.encode(data))
        runner.bench_func(f"encode_decode_{name}", bench_encode_decode, data)
