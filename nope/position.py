from dataclasses import dataclass
from typing import Any, ClassVar

from .node import Node


class Position(Node):
    __slots__ = ()

    # fmt: off
    X:        ClassVar["Node"]
    Y:        ClassVar["Node"]
    Z:        ClassVar["Node"]

    EAST:     ClassVar["Node"]
    UP:       ClassVar["Node"]
    SOUTH:    ClassVar["Node"]
    WEST:     ClassVar["Node"]
    DOWN:     ClassVar["Node"]
    NORTH:    ClassVar["Node"]

    LEFT:     ClassVar["Node"]
    ABOVE:    ClassVar["Node"]
    FORWARD:  ClassVar["Node"]
    RIGHT:    ClassVar["Node"]
    BELOW:    ClassVar["Node"]
    BACKWARD: ClassVar["Node"]
    # fmt: on


# fmt: off
Position.X        = Position("1 0 0")
Position.Y        = Position("0 1 0")
Position.Z        = Position("0 0 1")

Position.EAST     = Position("~1 ~ ~")
Position.UP       = Position("~ ~1 ~")
Position.SOUTH    = Position("~ ~ ~1")
Position.WEST     = -Position.EAST
Position.DOWN     = -Position.UP
Position.NORTH    = -Position.SOUTH

Position.LEFT     = Position("^1 ^ ^")
Position.ABOVE    = Position("^ ^1 ^")
Position.FORWARD  = Position("^ ^ ^1")
Position.RIGHT    = -Position.LEFT
Position.BELOW    = -Position.ABOVE
Position.BACKWARD = -Position.FORWARD
# fmt: on

class Serializer:
    def match(self, node: Node, )


class PositionSerializer(Serializer):
    def serialize(self, mc: Any, node: Node):
        if self.match()


# expression builders that are evaluated in a single point by a hot-swappable serializer (required for endermite)


class ScoreboardValue(Node):
    pass


class Expression(Node):
    pass


class Serializer:
    def serialize(self, other):
        pass


serializer = Serializer()
serializer.serialize(Position(1, 2, 3) * 9 + 1)


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    ZERO: ClassVar["Point"]


Point.ZERO = Point(0, 0)


##########################


pos = Position("~ ~ ~")


pos.abs(1, 2, 3)
pos.rel(1, 2, 3)
pos.loc(z=-2).rel(y=5)
pos.north * 7 + pos.south
pos == "dirt"
pos("~ ~78 ^8")



mc: Any = {}
with mc.function("foo"):
    mc.execute(at="@p").setblock("stone", mc.down * 1.5)
    with mc.execute("@a", at="@s", align="eyes", positioned=mc.forward * 3, facing=mc.east):
        mc.say("hello")
        mc.positioned(mc.backward).summon("sheep", mc.up * 20)
        mc.advancement_grant_everything(mc.self(predicates=["something:hello"]))
    mc.wheather_clear()
