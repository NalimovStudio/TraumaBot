from typing import TypeVar, Generic

InputData = TypeVar("InputData")
OutputData = TypeVar("OutputData")


class Interactor(Generic[InputData, OutputData]):
    def __call__(self, data: InputData) -> OutputData:
        raise NotADirectoryError
