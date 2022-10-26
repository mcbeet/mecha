from typing import Union


class CommandApi:
    def raw(self, command: str):
        pass

    def say(self, *parts: Union[str]):
        self.raw(" ".join(parts))
