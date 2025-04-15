__all__ = [
    "Serializer",
    "FormattingOptions",
]


import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, List, Literal, Union

from beet.core.utils import required_field
from pydantic.v1 import BaseModel

from .ast import (
    AstBlock,
    AstBlockState,
    AstBool,
    AstChildren,
    AstCommand,
    AstCoordinate,
    AstItemComponent,
    AstItemPredicate,
    AstItemPredicateAlternatives,
    AstItemPredicateTestComponent,
    AstItemPredicateTestPredicate,
    AstItemRemovedDefaultComponent,
    AstItemStack,
    AstJson,
    AstLiteral,
    AstMacroLine,
    AstMacroLineText,
    AstMacroLineVariable,
    AstMessage,
    AstNbtBool,
    AstNbtByteArray,
    AstNbtCompound,
    AstNbtCompoundKey,
    AstNbtIntArray,
    AstNbtList,
    AstNbtLongArray,
    AstNbtPath,
    AstNbtPathKey,
    AstNbtPathSubscript,
    AstNbtValue,
    AstNode,
    AstNumber,
    AstParticle,
    AstParticleParameters,
    AstRange,
    AstResourceLocation,
    AstRoot,
    AstSelector,
    AstSelectorAdvancementMatch,
    AstSelectorAdvancementPredicateMatch,
    AstSelectorAdvancements,
    AstSelectorArgument,
    AstSelectorScoreMatch,
    AstSelectorScores,
    AstString,
    AstTime,
    AstUUID,
    AstVector2,
    AstVector3,
)
from .database import CompilationDatabase
from .dispatch import Visitor, rule
from .spec import CommandSpec
from .utils import NbtQuoteHelper, QuoteHelper, number_to_string

REGEX_COMMENTS = re.compile(r"^(?:(\s*#.*)|.+)", re.MULTILINE)
UNQUOTED_COMPOUND_KEY = re.compile(r"^[a-zA-Z0-9._+-]+$")


class FormattingOptions(BaseModel):
    """Formatting options."""

    layout: Literal["dense", "preserve"] = "dense"
    cmd_compact: bool = False
    nbt_compact: bool = False
    json_compact: bool = False
    json_ensure_ascii: bool = True
    json_allow_nan: bool = True
    json_sort_keys: bool = False


@dataclass
class Serializer(Visitor):
    spec: CommandSpec = required_field()
    database: CompilationDatabase = field(default_factory=CompilationDatabase)

    formatting: FormattingOptions = field(default_factory=FormattingOptions)

    regex_comments: "re.Pattern[str]" = field(default=REGEX_COMMENTS)
    quote_helper: QuoteHelper = field(
        default_factory=lambda: QuoteHelper(
            escape_sequences={
                r"\\": "\\",
                r"\f": "\f",
                r"\n": "\n",
                r"\r": "\r",
                r"\t": "\t",
            }
        )
    )
    nbt_quote_helper: QuoteHelper = field(default_factory=NbtQuoteHelper)

    def __call__(self, node: AstNode, **kwargs: Any) -> str:  # type: ignore
        result: List[str] = []

        previous_formatting = self.formatting if kwargs else None
        if previous_formatting:
            options = previous_formatting.dict()
            options.update(kwargs)
            self.formatting = FormattingOptions.parse_obj(options)

        try:
            self.invoke(node, result)
        finally:
            if previous_formatting:
                self.formatting = previous_formatting

        return "".join(result)

    def collection(
        self,
        nodes: Iterable[AstNode],
        delimitters: str,
        result: List[str],
    ) -> Iterator[AstNode]:
        """Helper for serializing collections."""
        result.append(delimitters[0])
        comma = "," if self.formatting.cmd_compact else ", "
        sep = ""
        for node in nodes:
            result.append(sep)
            sep = comma
            yield node
        result.append(delimitters[-1])

    def key_value(self, node: Any, sep: str, result: List[str]) -> Iterator[AstNode]:
        """Helper for serializing key-value pairs."""
        yield node.key
        result.append(sep)
        yield node.value

    @rule(AstNode)
    def unserializable(self, node: AstNode, result: List[str]):
        raise ValueError(f"Couldn't serialize {type(node)!r} node.")

    @rule(AstVector2)
    @rule(AstVector3)
    @rule(AstParticleParameters)
    def aggregate(self, node: AstNode, result: List[str]):
        sep = ""
        for child in node:
            result.append(sep)
            sep = " "
            yield child

    @rule(AstRoot)
    def root(self, node: AstRoot, result: List[str]):
        pos = 0
        source = (
            self.formatting.layout == "preserve"
            and self.database[self.database.current].source
        )

        for command in node.commands:
            if source:
                end_pos = max(command.location.pos, pos + 1)
                if pos > -1:
                    if fill := source[pos:end_pos]:
                        result.append(self.regex_comments.sub(r"\1", fill))
                try:
                    pos = source.index("\n", end_pos) + 1
                except ValueError:
                    pos = -1

            yield command
            result.append("\n")

        if source and pos > -1:
            if fill := source[pos:]:
                result.append(self.regex_comments.sub(r"\1", fill))

    @rule(AstCommand)
    def command(self, node: AstCommand, result: List[str]):
        prototype = self.spec.prototypes[node.identifier]
        argument_index = 0

        sep = ""
        for token in prototype.signature:
            result.append(sep)
            sep = " "

            if isinstance(token, str):
                result.append(token)
            else:
                yield node.arguments[argument_index]
                argument_index += 1

    @rule(AstLiteral)
    def literal(self, node: AstLiteral, result: List[str]):
        result.append(node.value)

    @rule(AstString)
    def string(self, node: AstString, result: List[str]):
        result.append(self.quote_helper.quote_string(node.value))

    @rule(AstBool)
    def bool(self, node: AstBool, result: List[str]):
        result.append(str(node.value).lower())

    @rule(AstNumber)
    def number(self, node: AstNumber, result: List[str]):
        result.append(number_to_string(node.value))

    @rule(AstUUID)
    def uuid(self, node: AstUUID, result: List[str]):
        result.append(str(node.value))

    @rule(AstCoordinate)
    def coordinate(self, node: AstCoordinate, result: List[str]):
        if node.type == "relative":
            result.append("~")
            if node.value == 0:
                return
        elif node.type == "local":
            result.append("^")
            if node.value == 0:
                return
        result.append(number_to_string(node.value))

    @rule(AstJson)
    def json(self, node: AstJson, result: List[str]):
        result.append(
            json.dumps(
                node.evaluate(),
                separators=(",", ":") if self.formatting.json_compact else None,
                ensure_ascii=self.formatting.json_ensure_ascii,
                allow_nan=self.formatting.json_allow_nan,
                sort_keys=self.formatting.json_sort_keys,
            )
        )

    @rule(AstNbtValue)
    def nbt_value(self, node: AstNbtValue, result: List[str]):
        if isinstance(node.value, str):
            result.append(self.nbt_quote_helper.quote_string(node.value))
        else:
            result.append(node.evaluate().snbt(compact=self.formatting.nbt_compact))

    @rule(AstNbtBool)
    def nbt_bool(self, node: AstNbtBool, result: List[str]):
        result.append("true" if node.value else "false")

    @rule(AstNbtList)
    def nbt_list(self, node: AstNbtList, result: List[str]):
        result.append("[")
        comma = "," if self.formatting.nbt_compact else ", "
        sep = ""
        for element in node.elements:
            result.append(sep)
            sep = comma
            yield element
        result.append("]")

    @rule(AstNbtCompoundKey)
    def nbt_compound_key(self, node: AstNbtCompoundKey, result: List[str]):
        if UNQUOTED_COMPOUND_KEY.match(node.value):
            result.append(node.value)
        else:
            result.append(self.nbt_quote_helper.quote_string(node.value))

    @rule(AstNbtCompound)
    def nbt_compound(self, node: AstNbtCompound, result: List[str]):
        result.append("{")
        comma, colon = (",", ":") if self.formatting.nbt_compact else (", ", ": ")
        sep = ""
        for entry in node.entries:
            result.append(sep)
            sep = comma
            yield entry.key
            result.append(colon)
            yield entry.value
        result.append("}")

    @rule(AstNbtByteArray)
    @rule(AstNbtIntArray)
    @rule(AstNbtLongArray)
    def nbt_array(
        self,
        node: Union[AstNbtByteArray, AstNbtIntArray, AstNbtLongArray],
        result: List[str],
    ):
        result.append("[")
        result.append(node.array_prefix)
        semicolon = ";" if self.formatting.nbt_compact else "; "
        result.append(semicolon)
        comma = "," if self.formatting.nbt_compact else ", "
        sep = ""
        for element in node.elements:
            result.append(sep)
            sep = comma
            yield element
        result.append("]")

    @rule(AstResourceLocation)
    def resource_location(self, node: AstResourceLocation, result: List[str]):
        result.append(node.get_value())

    @rule(AstBlockState)
    def block_state(self, node: AstBlockState, result: List[str]):
        yield from self.key_value(node, "=", result)

    @rule(AstBlock)
    def block(self, node: AstBlock, result: List[str]):
        yield node.identifier
        if node.block_states:
            yield from self.collection(node.block_states, "[]", result)
        if node.data_tags:
            yield node.data_tags

    @rule(AstItemComponent)
    def item_component(self, node: AstItemComponent, result: List[str]):
        yield from self.key_value(node, "=", result)

    @rule(AstItemRemovedDefaultComponent)
    def item_removed_default_component(
        self, node: AstItemRemovedDefaultComponent, result: List[str]
    ):
        result.append("!")
        yield node.key

    @rule(AstItemPredicateTestComponent)
    @rule(AstItemPredicateTestPredicate)
    def item_test(
        self,
        node: Union[AstItemPredicateTestComponent, AstItemPredicateTestPredicate],
        result: List[str],
    ):
        if node.inverted:
            result.append("!")

        yield node.key

        if node.value:
            result.append(
                "~" if isinstance(node, AstItemPredicateTestPredicate) else "="
            )
            yield node.value

    @rule(AstItemPredicateAlternatives)
    def item_alternatives(self, node: AstItemPredicateAlternatives, result: List[str]):
        pipe = "|" if self.formatting.cmd_compact else " | "
        sep = ""
        for test_node in node.alternatives:
            result.append(sep)
            sep = pipe
            yield test_node

    @rule(AstItemStack)
    @rule(AstItemPredicate)
    def item(self, node: Union[AstItemStack, AstItemPredicate], result: List[str]):
        yield node.identifier
        if node.arguments:
            yield from self.collection(node.arguments, "[]", result)
        if node.data_tags:
            yield node.data_tags

    @rule(AstRange)
    def range(self, node: AstRange, result: List[str]):
        if node.exact:
            result.append(number_to_string(node.value))
        else:
            if node.min is not None:
                result.append(number_to_string(node.min))
            result.append("..")
            if node.max is not None:
                result.append(number_to_string(node.max))

    @rule(AstTime)
    def time(self, node: AstTime, result: List[str]):
        result.append(number_to_string(node.value))

        if node.unit == "day":
            result.append("d")
        elif node.unit == "second":
            result.append("s")

    @rule(AstSelectorScoreMatch)
    @rule(AstSelectorAdvancementPredicateMatch)
    def selector_argument_key_value(self, node: AstNode, result: List[str]):
        yield from self.key_value(node, "=", result)

    @rule(AstSelectorScores)
    def selector_scores(self, node: AstSelectorScores, result: List[str]):
        yield from self.collection(node.scores, "{}", result)

    @rule(AstSelectorAdvancementMatch)
    def selector_advancement_match(
        self,
        node: AstSelectorAdvancementMatch,
        result: List[str],
    ):
        yield node.key
        result.append("=")
        if isinstance(node.value, AstChildren):
            yield from self.collection(node.value, "{}", result)
        else:
            yield node.value

    @rule(AstSelectorAdvancements)
    def selector_advancements(self, node: AstSelectorAdvancements, result: List[str]):
        yield from self.collection(node.advancements, "{}", result)

    @rule(AstSelectorArgument)
    def selector_argument(self, node: AstSelectorArgument, result: List[str]):
        yield node.key
        result.append("=")
        if node.inverted:
            result.append("!")
        if node.value:
            yield node.value

    @rule(AstSelector)
    def selector(self, node: AstSelector, result: List[str]):
        result.append("@")
        result.append(node.variable)
        if node.arguments:
            yield from self.collection(node.arguments, "[]", result)

    @rule(AstMessage)
    def message(self, node: AstMessage, result: List[str]):
        yield from node.fragments

    @rule(AstNbtPathKey)
    def nbt_path_key(self, node: AstNbtPathKey, result: List[str]):
        value = self.quote_helper.quote_string(node.value)
        if "." in value and not value.startswith(('"', "'")):
            value = f'"{value}"'
        result.append(value)

    @rule(AstNbtPathSubscript)
    def nbt_path_subscript(self, node: AstNbtPathSubscript, result: List[str]):
        result.append("[")
        if node.index:
            yield node.index
        result.append("]")

    @rule(AstNbtPath)
    def nbt_path(self, node: AstNbtPath, result: List[str]):
        sep = ""
        for component in node.components:
            if isinstance(component, AstNbtPathKey):
                result.append(sep)
            sep = "."
            yield component

    @rule(AstParticle)
    def particle(self, node: AstParticle, result: List[str]):
        yield node.name
        if node.parameters:
            if not isinstance(node.parameters, AstNbtCompound):
                result.append(" ")
            yield node.parameters

    @rule(AstMacroLine)
    def macro_line(self, node: AstMacroLine, result: List[str]):
        result.append("$")
        yield from node.arguments

    @rule(AstMacroLineText)
    def macro_line_text(self, node: AstMacroLineText, result: List[str]):
        result.append(node.value)

    @rule(AstMacroLineVariable)
    def macro_line_variable(self, node: AstMacroLineVariable, result: List[str]):
        result.append("$(")
        result.append(node.value)
        result.append(")")
