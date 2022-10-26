import json
import sys
from dataclasses import dataclass, field
from typing import Any, List

from beet import Context, Function, TextFile, run_beet
from beet.core.utils import JsonDict, snake_case
from tokenstream import TokenStream

from mecha import CompilationUnit, Mecha, Parser, Reducer, Rule, rule
from mecha.ast import (
    AstAdvancementPredicate,
    AstBlock,
    AstBool,
    AstLiteral,
    AstMessage,
    AstMessageText,
    AstNode,
    AstObjective,
)
from mecha.contrib.bolt import AstIdentifier, AstTargetIdentifier
from mecha.contrib.bolt.ast import AstAttribute, AstCall


class Thing:
    scope = ("",)
    extension = ""


def thing(ctx: Context):
    ctx.data.extend_namespace.append(Thing)


@dataclass
class TokenExtractor:
    parser: Parser
    ctx: Context

    def __call__(self, stream: TokenStream) -> Any:
        node = self.parser(stream)
        tokens = []
        for t in stream.tokens:
            tokens.append(
                {
                    "type": t.type,
                    "value": t.value,
                    "start": t.location,
                    "end": t.end_location,
                }
            )

        self.ctx.meta["tokens"] = tokens

        return node


@dataclass
class TokenHighlighter(Reducer):
    tokens: List[JsonDict] = field(default_factory=list)

    @rule(AstObjective)
    def objective(self, node: AstObjective):
        self.tokens.append(
            {
                "type": "objective",
                "start": node.location.pos,
                "end": node.end_location.pos,
            }
        )


def beet_default(ctx: Context):
    mc = ctx.inject(Mecha)
    mc.spec.parsers["root"] = TokenExtractor(mc.spec.parsers["root"], ctx)
    func = Function("name = 'foo'\nsay name\nprint(''.upper())\n")
    mc.database[func] = CompilationUnit(resource_location="dummy:foo")

    # highlighter = TokenHighlighter()
    # highlighter(mc.parse(func))
    # print(highlighter.tokens)

    simple_node_types = (
        AstAdvancementPredicate,
        AstBlock,
        AstBool,
        AstLiteral,
        AstMessageText,
        AstIdentifier,
        AstTargetIdentifier,
    )
    tokens = []

    nodes: List[AstNode] = []

    node_collector = Reducer()
    node_collector.extend(Rule(nodes.append, match_types=simple_node_types))

    @rule(AstCall)
    def collect_function_calls(node: AstCall):
        if isinstance(node.value, AstAttribute):
            tokens.append(
                {
                    "type": "method_call",
                    "start": node.value.location,
                    "end": node.value.end_location,
                }
            )
        elif isinstance(node.value, AstIdentifier):
            tokens.append(
                {
                    "type": "function_call",
                    "start": node.value.location,
                    "end": node.value.end_location,
                }
            )

    node_collector.extend(collect_function_calls)

    node_collector(mc.parse(func))

    for node in nodes:
        tokens.append(
            {
                "type": node.parser or snake_case(node.__class__.__name__),
                "start": node.location,
                "end": node.end_location,
            }
        )

    print(tokens)


def grabTokens():
    with run_beet(
        {"pipeline": [__name__, "mecha"], "require": ["mecha.contrib.bolt"]}
    ) as ctx:
        return json.dumps(ctx.meta["tokens"], indent=2)


(grabTokens())
