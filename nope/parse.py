from dataclasses import InitVar, dataclass, field
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple

from tokenstream import TokenStream

from .reference import CommandTree
from .spec import CommandSpec


class CommandArgument(NamedTuple):
    name: str
    reference: CommandTree


class CommandPrototype(NamedTuple):
    """Class representing the prototype of a command."""

    identifier: str
    signature: Tuple[CommandArgument, ...]
    template: str

    def format(self, args: Iterable[Any]) -> str:
        return self.template.format(*args)


class Command(NamedTuple):
    """Class representing a command."""

    prototype: CommandPrototype
    args: List[Any]

    def __str__(self) -> str:
        return self.prototype.format(self.args)


@dataclass
class CommandParser:
    reference: CommandTree
    table: Dict[
        Tuple[str, ...],
    ]

    def parse_root(self, stream: TokenStream):
        with stream.syntax(literal=r"\w+"):
            node = ref.children
