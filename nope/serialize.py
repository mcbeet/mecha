from typing import Protocol


class Serializable(Protocol):
    def serialize(self) -> str:
        ...
