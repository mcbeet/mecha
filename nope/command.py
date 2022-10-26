from typing import Any, Iterable, Iterator, List, NamedTuple, Tuple

from .reference import CommandTree


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


def generate_prototypes(
    reference: CommandTree,
    identifier: Tuple[str, ...] = (),
    args: Tuple[CommandArgument, ...] = (),
    template: Tuple[str, ...] = (),
) -> Iterator[CommandPrototype]:
    """Yield command prototypes for all the executable commands."""
    if reference.executable:
        yield CommandPrototype(":".join(identifier), args, " ".join(template))
    if reference.children:
        for name, child in reference.children.items():
            yield from generate_prototypes(
                child,
                identifier + (name,),
                args + ((name,) if child.type == "argument" else ()),
                template + (("{}",) if child.type == "argument" else (name,)),
            )
    if reference.redirect:
        identifier += ("redirect",)
        args += ("redirect",)
        template += ("{}",)
        yield CommandPrototype(":".join(identifier), args, " ".join(template))


class Command(NamedTuple):
    """Class representing a command."""

    prototype: CommandPrototype
    args: List[Any]

    def __str__(self) -> str:
        return self.prototype.format(self.args)
