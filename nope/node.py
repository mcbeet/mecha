from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

T =TypeVar("T")


@dataclass
class Operator:
    name: str = ""

    def __set_name__(self, objtype: Any, name: str):
        self.name = name.strip("_")

    def __get__(self, obj: Any, objtype: Any = None) -> Callable[..., "Expression"]:
        return lambda *args: Expression(self.name, obj, *args)


class ReversedOperator(Operator):
    def __get__(self, obj: Any, objtype: Any = None) -> Callable[..., "Expression"]:
        return lambda *args: Expression(self.name[1:], *reversed(args), obj)


class Node:
    __slots__ = ("children",)

    def __init__(self, *children: Any):
        self.children = children

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self.children}"

    # fmt: off
    __lt__        = Operator()
    __le__        = Operator()
    __eq__        = Operator()  # type: ignore
    __ne__        = Operator()  # type: ignore
    __gt__        = Operator()
    __ge__        = Operator()

    __add__       = Operator()
    __sub__       = Operator()
    __mul__       = Operator()
    __matmul__    = Operator()
    __truediv__   = Operator()
    __floordiv__  = Operator()
    __mod__       = Operator()
    __pow__       = Operator()
    __lshift__    = Operator()
    __rshift__    = Operator()
    __and__       = Operator()
    __xor__       = Operator()
    __or__        = Operator()

    __radd__      = ReversedOperator()
    __rsub__      = ReversedOperator()
    __rmul__      = ReversedOperator()
    __rmatmul__   = ReversedOperator()
    __rtruediv__  = ReversedOperator()
    __rfloordiv__ = ReversedOperator()
    __rmod__      = ReversedOperator()
    __rpow__      = ReversedOperator()
    __rlshift__   = ReversedOperator()
    __rrshift__   = ReversedOperator()
    __rand__      = ReversedOperator()
    __rxor__      = ReversedOperator()
    __ror__       = ReversedOperator()

    __getitem__   = Operator()
    __setitem__   = Operator()
    __delitem__   = Operator()

    __neg__       = Operator()
    __pos__       = Operator()
    __invert__    = Operator()
    # fmt: on


class Expression(Node):
    __slots__ = ()


class Thing(Node):
    __slots__ = ()


class NodeHandler:
    def evaluate(self, node: Any) -> Any:
        return node


class ThingHandler(NodeHandler):
    def handle
