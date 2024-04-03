__all__ = [
    "AbstractNode",
    "AbstractChildren",
    "AstNode",
    "AstChildren",
    "AstRoot",
    "AstCommand",
    "AstCommandSentinel",
    "AstString",
    "AstBool",
    "AstNumber",
    "AstUUID",
    "AstCoordinate",
    "AstLiteral",
    "AstOption",
    "AstWord",
    "AstGreedy",
    "AstObjective",
    "AstObjectiveCriteria",
    "AstScoreboardOperation",
    "AstTeam",
    "AstPlayerName",
    "AstLegacyScoreboardSlot",
    "AstScoreboardSlot",
    "AstSwizzle",
    "AstAdvancementPredicate",
    "AstWildcard",
    "AstColor",
    "AstColorReset",
    "AstSortOrder",
    "AstGamemode",
    "AstHeightmap",
    "AstEntityAnchor",
    "AstTemplateRotation",
    "AstTemplateMirror",
    "AstVector2",
    "AstVector3",
    "AstJson",
    "AstJsonValue",
    "AstJsonArray",
    "AstJsonObjectKey",
    "AstJsonObjectEntry",
    "AstJsonObject",
    "AstNbt",
    "AstNbtValue",
    "AstNbtBool",
    "AstNbtList",
    "AstNbtCompoundKey",
    "AstNbtCompoundEntry",
    "AstNbtCompound",
    "AstNbtByteArray",
    "AstNbtIntArray",
    "AstNbtLongArray",
    "AstResourceLocation",
    "AstBlockState",
    "AstBlock",
    "AstItemComponent",
    "AstItem",
    "AstItemSlot",
    "AstItemSlots",
    "AstRange",
    "AstTime",
    "AstSelectorScoreMatch",
    "AstSelectorScores",
    "AstSelectorAdvancementPredicateMatch",
    "AstSelectorAdvancementMatch",
    "AstSelectorArgument",
    "AstSelector",
    "AstMessageText",
    "AstMessage",
    "AstNbtPathKey",
    "AstNbtPathSubscript",
    "AstNbtPath",
    "AstParticleParameters",
    "AstDustParticleParameters",
    "AstDustColorTransitionParticleParameters",
    "AstBlockParticleParameters",
    "AstFallingDustParticleParameters",
    "AstItemParticleParameters",
    "AstVibrationParticleParameters",
    "AstBlockMarkerParticleParameters",
    "AstParticle",
    "AstMacroLine",
    "AstMacroLineText",
    "AstMacroLineVariable",
    "COLORS",
]


import re
from dataclasses import dataclass, fields
from itertools import islice, permutations, zip_longest
from typing import (
    Any,
    ClassVar,
    Iterable,
    Iterator,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)
from uuid import UUID

from beet.core.utils import JsonDict, extra_field, required_field
from nbtlib import Byte, ByteArray, Compound, CompoundMatch, Double, Int, IntArray
from nbtlib import List as ListTag
from nbtlib import ListIndex, LongArray, NamedKey, Numeric, Path, String
from tokenstream import UNKNOWN_LOCATION, SourceLocation, set_location

from .utils import string_to_number

T = TypeVar("T")
AbstractNodeType = TypeVar("AbstractNodeType", bound="AbstractNode", covariant=True)
AstNodeType = TypeVar("AstNodeType", bound="AstNode", covariant=True)
AstLiteralType = TypeVar("AstLiteralType", bound="AstLiteral")


COLORS: Tuple[str, ...] = (
    "black",
    "dark_blue",
    "dark_green",
    "dark_aqua",
    "dark_red",
    "dark_purple",
    "gold",
    "gray",
    "dark_gray",
    "blue",
    "green",
    "aqua",
    "red",
    "light_purple",
    "yellow",
    "white",
)


@dataclass(frozen=True, slots=True)
class AbstractNode:
    """Abstract node."""

    location: SourceLocation = extra_field(default=UNKNOWN_LOCATION)
    end_location: SourceLocation = extra_field(default=UNKNOWN_LOCATION)

    def __iter__(self) -> Iterator["AbstractNode"]:
        for f in fields(self):
            attribute = getattr(self, f.name)

            if isinstance(attribute, AbstractChildren):
                yield from attribute

            if isinstance(attribute, AbstractNode):
                yield attribute

    def walk(self) -> Iterator["AbstractNode"]:
        yield self

        for f in fields(self):
            attribute = getattr(self, f.name)

            if isinstance(attribute, AbstractChildren):
                for child in attribute:  # type: ignore
                    if isinstance(child, AbstractNode):
                        yield from child.walk()

            elif isinstance(attribute, AbstractNode):
                yield from attribute.walk()

    def dump(
        self,
        prefix: str = "",
        shallow: bool = False,
        exclude: Optional[Set[str]] = None,
    ) -> str:
        """Return a pretty-printed representation of the ast."""
        return f"{prefix}{self.__class__}\n" + "\n".join(
            f"{prefix}  {f.name}:"
            + (
                "\n" + ("\n".join((f"{prefix}    {type(child)}" if shallow else child.dump(prefix + "    ", shallow, exclude)) for child in attribute) if attribute else prefix + "    <empty>")  # type: ignore
                if isinstance(attribute := getattr(self, f.name), AbstractChildren)
                else (
                    "\n"
                    + (
                        f"{prefix}    {type(attribute)}"
                        if shallow
                        else attribute.dump(prefix + "    ", shallow, exclude)
                    )
                    if isinstance(attribute, AbstractNode)
                    else f" {attribute!r}"
                )
            )
            for f in fields(self)
            if not exclude or f.name not in exclude
        )

    def emit_error(self, exc: T) -> T:
        """Add location information to invalid syntax exceptions."""
        return set_location(exc, self)


class AbstractChildren(Tuple[AbstractNodeType, ...]):
    """Abstract children."""

    def __new__(
        cls,
        children: Iterable[
            None | AbstractNodeType | "AbstractChildren[AbstractNodeType]"
        ] = (),
    ):
        children = [
            c
            for child in children
            if child is not None
            for c in (child if isinstance(child, AbstractChildren) else [child])
        ]
        return super().__new__(cls, children)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"


class AstNode(AbstractNode):
    """Base class for all ast nodes."""

    parser: ClassVar[Optional[str]] = None
    compile_hints: ClassVar[JsonDict] = {}

    def __iter__(self) -> Iterator["AstNode"]:
        return super().__iter__()  # type: ignore

    def walk(self) -> Iterator["AstNode"]:
        return super().walk()  # type: ignore


class AstChildren(AbstractChildren[AstNodeType]):
    """Specialized tuple subclass for holding multiple child ast nodes."""


@dataclass(frozen=True, slots=True)
class AstRoot(AstNode):
    """Ast root node."""

    commands: AstChildren["AstCommand"] = required_field()

    parser = "root"


@dataclass(frozen=True, slots=True)
class AstCommand(AstNode):
    """Ast command node."""

    identifier: str = required_field()
    arguments: AstChildren[AstNode] = required_field()

    parser = "command"


@dataclass(frozen=True, slots=True)
class AstCommandSentinel(AstCommand):
    """Ast command sentinel node."""

    identifier: str = "mecha:sentinel"
    arguments: AstChildren[AstNode] = AstChildren()

    parser = None


@dataclass(frozen=True, slots=True)
class AstString(AstNode):
    """Ast string node."""

    value: str = required_field()

    parser = "phrase"

    @classmethod
    def from_value(cls, value: Any) -> "AstString":
        """Return a string node from the given value."""
        return AstString(value=str(value))


@dataclass(frozen=True, slots=True)
class AstBool(AstNode):
    """Ast bool node."""

    value: bool = required_field()

    parser = "bool"

    @classmethod
    def from_value(cls, value: Any) -> "AstBool":
        """Return a bool node from the given value."""
        return AstBool(value=bool(value))


@dataclass(frozen=True, slots=True)
class AstNumber(AstNode):
    """Ast number node."""

    value: Union[int, float] = required_field()

    parser = "numeric"

    @classmethod
    def from_value(cls, value: Any) -> "AstNumber":
        """Return a number node from the given value."""
        if isinstance(value, str):
            value = string_to_number(value)
        if isinstance(value, (int, float)):
            return AstNumber(value=value)
        raise ValueError(f"Invalid number {value!r}.")


@dataclass(frozen=True, slots=True)
class AstUUID(AstNode):
    """Ast uuid node."""

    value: UUID = required_field()

    parser = "uuid"

    @classmethod
    def from_value(cls, value: Any) -> "AstUUID":
        """Return a uuid node from the given value."""
        if isinstance(value, str):
            a, b, c, d, e = value.split("-")
            value = UUID(f"{a:>08}-{b:>04}-{c:>04}-{d:>04}-{e:>012}")
        if isinstance(value, UUID):
            return AstUUID(value=value)
        raise ValueError(f"Invalid UUID {value!r}.")


@dataclass(frozen=True, slots=True)
class AstCoordinate(AstNode):
    """Coordinate ast node."""

    type: Literal["absolute", "relative", "local"] = "absolute"
    value: Union[int, float] = required_field()

    parser = "coordinate"

    @classmethod
    def from_value(cls, value: Any) -> "AstCoordinate":
        """Return a coordinate node from the given value."""
        type = "absolute"
        if isinstance(value, str):
            if value.startswith("~"):
                type = "relative"
                value = value[1:]
            elif value.startswith("^"):
                type = "local"
                value = value[1:]
            value = string_to_number(value) if value else 0
        if isinstance(value, (int, float)):
            return AstCoordinate(type=type, value=value)
        raise ValueError(f"Invalid coordinate {value!r}.")


@dataclass(frozen=True, slots=True)
class AstVector2(AstNode):
    """Vector 2 ast node."""

    x: AstCoordinate = required_field()
    y: AstCoordinate = required_field()

    @classmethod
    def from_value(cls, value: Any) -> "AstVector2":
        """Return a vector 2 node from the given value."""
        if isinstance(value, str):
            value = value.split()
        x, y = map(AstCoordinate.from_value, value)
        return AstVector2(x=x, y=y)


@dataclass(frozen=True, slots=True)
class AstVector3(AstNode):
    """Vector 3 ast node."""

    x: AstCoordinate = required_field()
    y: AstCoordinate = required_field()
    z: AstCoordinate = required_field()

    @classmethod
    def from_value(cls, value: Any) -> "AstVector3":
        """Return a vector 3 node from the given value."""
        if isinstance(value, str):
            value = value.split()
        x, y, z = map(AstCoordinate.from_value, value)
        return AstVector3(x=x, y=y, z=z)


@dataclass(frozen=True, slots=True)
class AstLiteral(AstNode):
    """Base ast node for literals."""

    value: str = required_field()

    regex: ClassVar["re.Pattern[str]"] = re.compile(r"[^#:\s]+")

    @classmethod
    def from_value(cls: Type[AstLiteralType], value: Any) -> AstLiteralType:
        """Return a literal node from a given value."""
        value = str(value)
        match = cls.regex.match(value)
        if match and match[0] == value:
            return cls(value=value)
        raise ValueError(f"Invalid {cls.parser or 'literal'} {value!r}.")


@dataclass(frozen=True, slots=True)
class AstWord(AstLiteral):
    """Ast word node."""

    parser = "word"
    regex = re.compile(r"[0-9A-Za-z_\.\+\-]+")


@dataclass(frozen=True, slots=True)
class AstOption(AstLiteral):
    """Base node for options."""

    options: ClassVar[Set[str]] = set()

    def __init_subclass__(cls):
        patterns = [
            rf"{pattern}\b" if pattern[-1].isalnum() else pattern
            for option in sorted(cls.options, key=lambda s: (-len(s), s))
            if (pattern := re.escape(option))
        ]
        cls.regex = re.compile("|".join(patterns))


@dataclass(frozen=True, slots=True)
class AstGreedy(AstLiteral):
    """Ast greedy node."""

    parser = "greedy"
    regex = re.compile(r".+")


@dataclass(frozen=True, slots=True)
class AstObjective(AstLiteral):
    """Ast objective node."""

    parser = "objective"
    regex = re.compile(r"[a-zA-Z0-9_.+-]+")


@dataclass(frozen=True, slots=True)
class AstObjectiveCriteria(AstLiteral):
    """Ast objective criteria node."""

    parser = "objective_criteria"
    regex = re.compile(r"[a-zA-Z0-9_.+-]+(?::[a-zA-Z0-9_.+-]+)?")


@dataclass(frozen=True, slots=True)
class AstScoreboardOperation(AstOption):
    """Ast scoreboard operation node."""

    parser = "scoreboard_operation"
    options = {"+=", "-=", "*=", "/=", "%=", "=", "><", "<", ">"}


@dataclass(frozen=True, slots=True)
class AstTeam(AstLiteral):
    """Ast team node."""

    parser = "team"
    regex = re.compile(r"[a-zA-Z0-9_.+-]+")


@dataclass(frozen=True, slots=True)
class AstPlayerName(AstLiteral):
    """Ast player name node."""

    parser = "player_name"
    regex = re.compile(r"(?![@*[({])\S+")


@dataclass(frozen=True, slots=True)
class AstLegacyScoreboardSlot(AstOption):
    """Ast legacy scoreboard slot node."""

    parser = "scoreboard_slot"
    options = {f"sidebar.team.{color}" for color in COLORS} | {
        "list",
        "sidebar",
        "belowName",
    }


@dataclass(frozen=True, slots=True)
class AstScoreboardSlot(AstOption):
    """Ast scoreboard slot node."""

    parser = "scoreboard_slot"
    options = {f"sidebar.team.{color}" for color in COLORS} | {
        "list",
        "sidebar",
        "below_name",
    }


@dataclass(frozen=True, slots=True)
class AstSwizzle(AstOption):
    """Ast swizzle node."""

    parser = "swizzle"
    options = (
        set("xyz")
        | set(map("".join, permutations("xyz", 2)))
        | set(map("".join, permutations("xyz", 3)))
    )


@dataclass(frozen=True, slots=True)
class AstAdvancementPredicate(AstLiteral):
    """Ast advancement predicate node."""

    parser = "advancement_predicate"
    regex = re.compile(r"[0-9A-Za-z_\.\+\-]+")


@dataclass(frozen=True, slots=True)
class AstWildcard(AstLiteral):
    """Ast wildcard node."""

    value: str = "*"

    parser = "wildcard"
    regex = re.compile(r"\*")


@dataclass(frozen=True, slots=True)
class AstColor(AstOption):
    """Ast color node."""

    parser = "color"
    options = set(COLORS)


@dataclass(frozen=True, slots=True)
class AstColorReset(AstOption):
    """Ast color reset node."""

    parser = "color_reset"
    options = {"reset"}


@dataclass(frozen=True, slots=True)
class AstSortOrder(AstOption):
    """Ast sort order node."""

    parser = "sort_order"
    options = {"nearest", "furthest", "random", "arbitrary"}


@dataclass(frozen=True, slots=True)
class AstGamemode(AstOption):
    """Ast gamemode node."""

    parser = "gamemode"
    options = {"adventure", "creative", "spectator", "survival"}


@dataclass(frozen=True, slots=True)
class AstHeightmap(AstOption):
    """Ast heightmap node."""

    parser = "heightmap"
    options = {
        "world_surface",
        "motion_blocking",
        "motion_blocking_no_leaves",
        "ocean_floor",
    }


@dataclass(frozen=True, slots=True)
class AstEntityAnchor(AstOption):
    """Ast entity anchor node."""

    parser = "entity_anchor"
    options = {"eyes", "feet"}


@dataclass(frozen=True, slots=True)
class AstTemplateRotation(AstOption):
    """Ast template rotation node."""

    parser = "template_rotation"
    options = {"180", "clockwise_90", "counterclockwise_90", "none"}


@dataclass(frozen=True, slots=True)
class AstTemplateMirror(AstOption):
    """Ast template mirror node."""

    parser = "template_mirror"
    options = {"front_back", "left_right", "none"}


@dataclass(frozen=True, slots=True)
class AstJson(AstNode):
    """Base ast node for json."""

    parser = "json"

    def evaluate(self) -> Any:
        """Return the json value."""
        raise NotImplementedError()

    @classmethod
    def from_value(cls, value: Any) -> "AstJson":
        """Create json ast nodes representing the specified json value."""
        if value is None or isinstance(value, (bool, str, int, float)):
            return AstJsonValue(value=value)
        elif isinstance(value, Mapping):
            object: Mapping[Any, Any] = value
            return AstJsonObject(
                entries=AstChildren(
                    AstJsonObjectEntry(
                        key=AstJsonObjectKey(value=str(k)),
                        value=cls.from_value(v),
                    )
                    for k, v in object.items()
                )
            )
        elif isinstance(value, Sequence):
            array: Sequence[Any] = value
            return AstJsonArray(elements=AstChildren(cls.from_value(e) for e in array))
        else:
            raise ValueError(f"Invalid json value of type {type(value)!r}.")


@dataclass(frozen=True, slots=True)
class AstJsonValue(AstJson):
    """Ast json value node."""

    value: Any = required_field()

    parser = None

    def evaluate(self) -> Any:
        return self.value


@dataclass(frozen=True, slots=True)
class AstJsonArray(AstJson):
    """Ast json array node."""

    elements: AstChildren[AstJson] = required_field()

    parser = None

    def evaluate(self) -> Any:
        return [element.evaluate() for element in self.elements]


@dataclass(frozen=True, slots=True)
class AstJsonObjectKey(AstNode):
    """Ast json object key node."""

    value: str = required_field()


@dataclass(frozen=True, slots=True)
class AstJsonObjectEntry(AstNode):
    """Ast json object entry node."""

    key: AstJsonObjectKey = required_field()
    value: AstJson = required_field()


@dataclass(frozen=True, slots=True)
class AstJsonObject(AstJson):
    """Ast json object node."""

    entries: AstChildren[AstJsonObjectEntry] = required_field()

    parser = "json"

    def evaluate(self) -> Any:
        return {entry.key.value: entry.value.evaluate() for entry in self.entries}


@dataclass(frozen=True, slots=True)
class AstNbt(AstNode):
    """Base ast node for nbt."""

    parser = "nbt"

    def evaluate(self) -> Any:
        """Return the nbt value."""
        raise NotImplementedError()

    @overload
    @classmethod
    def from_value(cls, value: Union[bool, int, float, str]) -> "AstNbtValue": ...

    @overload
    @classmethod
    def from_value(cls, value: Mapping[Any, Any]) -> "AstNbtCompound": ...

    @overload
    @classmethod
    def from_value(cls, value: Sequence[Any]) -> "AstNbtList": ...

    @overload
    @classmethod
    def from_value(cls, value: Any) -> "AstNbt": ...

    @classmethod
    def from_value(cls, value: Any) -> "AstNbt":
        """Create nbt ast nodes representing the specified value."""
        if isinstance(value, (Numeric, String)):
            return AstNbtValue(value=value)
        elif isinstance(value, bool):
            return AstNbtBool(value=Byte(1 if value else 0))
        elif isinstance(value, int):
            return AstNbtValue(value=Int(value))
        elif isinstance(value, float):
            return AstNbtValue(value=Double(value))
        elif isinstance(value, str):
            return AstNbtValue(value=String(value))
        elif isinstance(value, ByteArray):
            return AstNbtByteArray(
                elements=AstChildren(cls.from_value(e) for e in value)  # type: ignore
            )
        elif isinstance(value, IntArray):
            return AstNbtIntArray(
                elements=AstChildren(cls.from_value(e) for e in value)  # type: ignore
            )
        elif isinstance(value, LongArray):
            return AstNbtLongArray(
                elements=AstChildren(cls.from_value(e) for e in value)  # type: ignore
            )
        elif isinstance(value, Mapping):
            compound: Mapping[Any, Any] = value
            return AstNbtCompound(
                entries=AstChildren(
                    AstNbtCompoundEntry(
                        key=AstNbtCompoundKey(value=str(k)),
                        value=cls.from_value(v),  # type: ignore
                    )
                    for k, v in compound.items()
                )
            )
        elif isinstance(value, Sequence):
            lst: Sequence[Any] = value
            return AstNbtList(elements=AstChildren(cls.from_value(e) for e in lst))  # type: ignore
        else:
            raise ValueError(f"Invalid nbt value of type {type(value)!r}.")


@dataclass(frozen=True, slots=True)
class AstNbtValue(AstNbt):
    """Ast nbt value node."""

    value: Any = required_field()

    parser = None

    def evaluate(self) -> Any:
        return self.value


@dataclass(frozen=True, slots=True)
class AstNbtBool(AstNbtValue):
    """Ast nbt bool node."""


@dataclass(frozen=True, slots=True)
class AstNbtList(AstNbt):
    """Ast nbt list node."""

    elements: AstChildren[AstNbt] = required_field()

    parser = None

    def evaluate(self) -> Any:
        return ListTag([element.evaluate() for element in self.elements])  # type: ignore


@dataclass(frozen=True, slots=True)
class AstNbtCompoundKey(AstNode):
    """Ast nbt compound key node."""

    value: str = required_field()


@dataclass(frozen=True, slots=True)
class AstNbtCompoundEntry(AstNode):
    """Ast nbt compound entry node."""

    key: AstNbtCompoundKey = required_field()
    value: AstNbt = required_field()


@dataclass(frozen=True, slots=True)
class AstNbtCompound(AstNbt):
    """Ast nbt compound node."""

    entries: AstChildren[AstNbtCompoundEntry] = required_field()

    parser = "nbt_compound"

    def evaluate(self) -> Any:
        return Compound(  # type: ignore
            {entry.key.value: entry.value.evaluate() for entry in self.entries},
        )


@dataclass(frozen=True, slots=True)
class AstNbtByteArray(AstNbt):
    """Ast nbt byte array node."""

    elements: AstChildren[AstNbt] = required_field()

    parser = None

    def evaluate(self) -> Any:
        return ByteArray([element.evaluate() for element in self.elements])  # type: ignore


@dataclass(frozen=True, slots=True)
class AstNbtIntArray(AstNbt):
    """Ast nbt int array node."""

    elements: AstChildren[AstNbt] = required_field()

    parser = None

    def evaluate(self) -> Any:
        return IntArray([element.evaluate() for element in self.elements])  # type: ignore


@dataclass(frozen=True, slots=True)
class AstNbtLongArray(AstNbt):
    """Ast nbt long array node."""

    elements: AstChildren[AstNbt] = required_field()

    parser = None

    def evaluate(self) -> Any:
        return LongArray([element.evaluate() for element in self.elements])  # type: ignore


@dataclass(frozen=True, slots=True)
class AstResourceLocation(AstNode):
    """Ast resource location node."""

    is_tag: bool = False
    namespace: Optional[str] = None
    path: str = required_field()

    parser = "resource_location_or_tag"

    @classmethod
    def from_value(cls, value: Any) -> "AstResourceLocation":
        """Create a resource location node representing the given value."""
        value = str(value)
        if is_tag := value.startswith("#"):
            value = value[1:]
        namespace, _, path = value.rpartition(":")
        return cls(is_tag=is_tag, namespace=namespace or None, path=path)

    def get_value(self) -> str:
        """Return the value of the resource location as a string."""
        prefix = "#" if self.is_tag else ""
        namespace = f"{self.namespace}:" if self.namespace else ""
        return prefix + namespace + self.path

    def get_canonical_value(self) -> str:
        """Return the canonical value of the resource location as a string."""
        prefix = "#" if self.is_tag else ""
        namespace = f"{self.namespace}:" if self.namespace else "minecraft:"
        return prefix + namespace + self.path


@dataclass(frozen=True, slots=True)
class AstBlockState(AstNode):
    """Ast block state node."""

    key: AstString = required_field()
    value: AstString = required_field()


@dataclass(frozen=True, slots=True)
class AstBlock(AstNode):
    """Ast block node."""

    identifier: AstResourceLocation = required_field()
    block_states: AstChildren[AstBlockState] = AstChildren()
    data_tags: Optional[AstNbtCompound] = None


@dataclass(frozen=True, slots=True)
class AstItemComponent(AstNode):
    """Ast item component node."""

    key: AstResourceLocation = required_field()
    value: AstNbt = required_field()


@dataclass(frozen=True, slots=True)
class AstItem(AstNode):
    """Ast item node."""

    identifier: AstResourceLocation = required_field()
    components: AstChildren[AstItemComponent] = AstChildren()
    data_tags: Optional[AstNbtCompound] = None


@dataclass(frozen=True, slots=True)
class AstItemSlot(AstOption):
    """Ast item slot node."""

    parser = "item_slot"
    options = (
        {
            "armor.chest",
            "armor.feet",
            "armor.head",
            "armor.legs",
            "contents",
            "weapon",
            "weapon.mainhand",
            "weapon.offhand",
            "player.cursor",
            "player.crafting.0",
            "player.crafting.1",
            "player.crafting.2",
            "player.crafting.3",
        }
        | {f"container.{n}" for n in range(54)}
        | {f"enderchest.{n}" for n in range(27)}
        | {f"hotbar.{n}" for n in range(9)}
        | {f"inventory.{n}" for n in range(27)}
        | {"horse.saddle", "horse.chest", "horse.armor"}
        | {f"horse.{n}" for n in range(15)}
        | {f"villager.{n}" for n in range(8)}
    )


@dataclass(frozen=True, slots=True)
class AstItemSlots(AstOption):
    """Ast item slots node."""

    parser = "item_slots"
    options = AstItemSlot.options | {
        "container.*",
        "hotbar.*",
        "inventory.*",
        "enderchest.*",
        "villager.*",
        "horse.*",
        "weapon.*",
        "armor.*",
        "player.crafting.*",
    }


@dataclass(frozen=True, slots=True)
class AstRange(AstNode):
    """Ast range node."""

    min: Optional[Union[int, float]] = required_field()
    max: Optional[Union[int, float]] = required_field()

    parser = "range"

    @property
    def exact(self) -> bool:
        """Wether the range is an exact match."""
        return self.min == self.max

    @property
    def value(self) -> Union[int, float]:
        """Return the exact value."""
        return self.min  # type: ignore

    @classmethod
    def from_value(
        cls,
        value: Union[
            str,
            int,
            float,
            Tuple[Union[int, float, str], Union[int, float, str]],
        ],
    ) -> "AstRange":
        """Create a range node from a given value."""
        if isinstance(value, (int, float)):
            return AstRange(min=value, max=value)

        if isinstance(value, tuple):
            min, max = value
            return AstRange(
                min=string_to_number(min) if isinstance(min, str) else min,
                max=string_to_number(max) if isinstance(max, str) else max,
            )

        minimum, separator, maximum = value.partition("..")

        if not separator:
            maximum = minimum

        return AstRange(
            min=string_to_number(minimum) if minimum else None,
            max=string_to_number(maximum) if maximum else None,
        )


@dataclass(frozen=True, slots=True)
class AstTime(AstNode):
    """Ast time node."""

    value: Union[int, float] = required_field()
    unit: Literal["day", "second", "tick"] = "tick"

    parser = "time"

    @classmethod
    def from_value(cls, value: Union[str, int, float]) -> "AstTime":
        """Create a time node from a given value."""
        unit = "tick"

        if isinstance(value, str):
            if value.endswith(("d", "s", "t")):
                if value[-1] == "d":
                    unit = "day"
                elif value[-1] == "s":
                    unit = "second"
                else:
                    unit = "tick"
                value = value[:-1]
            value = string_to_number(value)

        return cls(value=value, unit=unit)


@dataclass(frozen=True, slots=True)
class AstSelectorScoreMatch(AstNode):
    """Ast selector score match node."""

    key: AstObjective = required_field()
    value: AstRange = required_field()


@dataclass(frozen=True, slots=True)
class AstSelectorScores(AstNode):
    """Ast selector scores node."""

    scores: AstChildren[AstSelectorScoreMatch] = required_field()


@dataclass(frozen=True, slots=True)
class AstSelectorAdvancementPredicateMatch(AstNode):
    """Ast selector advancement predicate match node."""

    key: AstAdvancementPredicate = required_field()
    value: AstBool = required_field()


@dataclass(frozen=True, slots=True)
class AstSelectorAdvancementMatch(AstNode):
    """Ast selector advancement match node."""

    key: AstResourceLocation = required_field()
    value: Union[AstBool, AstChildren[AstSelectorAdvancementPredicateMatch]] = (
        required_field()
    )


@dataclass(frozen=True, slots=True)
class AstSelectorAdvancements(AstNode):
    """Ast selector advancements node."""

    advancements: AstChildren[AstSelectorAdvancementMatch] = required_field()


@dataclass(frozen=True, slots=True)
class AstSelectorArgument(AstNode):
    """Ast selector argument node."""

    inverted: bool = False
    key: AstString = required_field()
    value: Optional[AstNode] = required_field()


@dataclass(frozen=True, slots=True)
class AstSelector(AstNode):
    """Ast selector node."""

    variable: Literal["p", "r", "a", "e", "s"] = required_field()
    arguments: AstChildren[AstSelectorArgument] = AstChildren()

    parser = "selector"


@dataclass(frozen=True, slots=True)
class AstMessageText(AstLiteral):
    """Ast message text node."""

    value: str = required_field()
    regex = re.compile(r".+")


@dataclass(frozen=True, slots=True)
class AstMessage(AstNode):
    """Ast message node."""

    fragments: AstChildren[Union[AstMessageText, AstSelector]] = required_field()

    @classmethod
    def from_value(cls, obj: Any) -> "AstMessage":
        """Return message node from a given value."""
        return AstMessage(fragments=AstChildren([AstMessageText.from_value(obj)]))


@dataclass(frozen=True, slots=True)
class AstNbtPathKey(AstNode):
    """Ast nbt path key node."""

    value: str = required_field()


@dataclass(frozen=True, slots=True)
class AstNbtPathSubscript(AstNode):
    """Ast nbt path subscript node."""

    index: Union[None, AstNumber, AstNbtCompound] = None


@dataclass(frozen=True, slots=True)
class AstNbtPath(AstNode):
    """Ast nbt path node."""

    components: AstChildren[
        Union[AstNbtPathKey, AstNbtCompound, AstNbtPathSubscript]
    ] = required_field()

    parser = "nbt_path"

    @classmethod
    def from_value(cls, value: Any) -> "AstNbtPath":
        """Create nbt path ast nodes representing the specified value."""
        if isinstance(value, str):
            value = Path(value)  # type: ignore
        if not isinstance(value, Path):
            raise ValueError(f"Invalid nbt path value of type {type(value)!r}.")

        accessors = zip_longest(value, islice(value, 1, None))
        components: List[Union[AstNbtPathKey, AstNbtCompound, AstNbtPathSubscript]] = []

        for accessor, next_accessor in accessors:
            if isinstance(accessor, NamedKey):
                components.append(AstNbtPathKey(value=accessor.key))

            elif isinstance(accessor, ListIndex):
                index = (
                    AstNumber(value=accessor.index)
                    if isinstance(accessor.index, int)
                    else None
                )

                # Special-case for the way nbtlib.Path stores compound subscripts.
                if index is None and isinstance(next_accessor, CompoundMatch):
                    compound: Mapping[Any, Any] = next_accessor.compound
                    index = AstNbt.from_value(compound)
                    next(accessors, None)

                components.append(AstNbtPathSubscript(index=index))

            elif isinstance(accessor, CompoundMatch):
                compound: Mapping[Any, Any] = accessor.compound
                components.append(AstNbt.from_value(compound))

        if not components:
            raise ValueError("Empty nbt path not allowed.")
        return AstNbtPath(components=AstChildren(components))


@dataclass(frozen=True, slots=True)
class AstParticleParameters(AstNode):
    """Base ast node for particle parameters."""


@dataclass(frozen=True, slots=True)
class AstDustParticleParameters(AstParticleParameters):
    """Ast dust particle parameters node."""

    red: AstNumber = required_field()
    green: AstNumber = required_field()
    blue: AstNumber = required_field()
    size: AstNumber = required_field()


@dataclass(frozen=True, slots=True)
class AstDustColorTransitionParticleParameters(AstParticleParameters):
    """Ast dust color transition particle parameters node."""

    red: AstNumber = required_field()
    green: AstNumber = required_field()
    blue: AstNumber = required_field()
    size: AstNumber = required_field()
    end_red: AstNumber = required_field()
    end_green: AstNumber = required_field()
    end_blue: AstNumber = required_field()


@dataclass(frozen=True, slots=True)
class AstBlockParticleParameters(AstParticleParameters):
    """Ast block particle parameters node."""

    block: AstBlock = required_field()


@dataclass(frozen=True, slots=True)
class AstFallingDustParticleParameters(AstParticleParameters):
    """Ast falling dust particle parameters node."""

    block: AstBlock = required_field()


@dataclass(frozen=True, slots=True)
class AstItemParticleParameters(AstParticleParameters):
    """Ast item particle parameters node."""

    item: AstItem = required_field()


@dataclass(frozen=True, slots=True)
class AstVibrationParticleParameters(AstParticleParameters):
    """Ast vibration particle parameters node."""

    destination_x: AstNumber = required_field()
    destination_y: AstNumber = required_field()
    destination_z: AstNumber = required_field()
    duration: AstNumber = required_field()


@dataclass(frozen=True, slots=True)
class AstBlockMarkerParticleParameters(AstParticleParameters):
    """Ast block marker particle parameters node."""

    block: AstBlock = required_field()


@dataclass(frozen=True, slots=True)
class AstSculkChargeParticleParameters(AstParticleParameters):
    """Ast sculk charge particle parameters node."""

    angle: AstNumber = required_field()


@dataclass(frozen=True, slots=True)
class AstShriekParticleParameters(AstParticleParameters):
    """Ast shriek particle parameters node."""

    delay: AstNumber = required_field()


@dataclass(frozen=True, slots=True)
class AstParticle(AstNode):
    """Ast particle node."""

    name: AstResourceLocation = required_field()
    parameters: Optional[AstParticleParameters] = None

    parser = "particle"


@dataclass(frozen=True, slots=True)
class AstMacroLineText(AstLiteral):
    """Ast macro line text node."""

    parser = "macro_line_text"
    regex = re.compile(r"(?:[^\n$]|\$(?!\())+")


@dataclass(frozen=True, slots=True)
class AstMacroLineVariable(AstLiteral):
    """Ast macro line variable node."""

    parser = "macro_line_variable"
    regex = re.compile(r"[0-9A-Za-z_]+")


@dataclass(frozen=True, slots=True)
class AstMacroLine(AstCommandSentinel):
    """Ast macro line node."""

    parser = "macro_line"

    compile_hints = {"skip_execute_inline_single_command": True}
