__all__ = [
    "CommandSpec",
]


from dataclasses import InitVar, dataclass
from typing import Dict, Optional

from beet import Context
from beet.core.utils import extra_field

from .command import CommandPrototype, generate_prototypes
from .reference import CommandTree


@dataclass
class CommandSpec:
    """Holds the command specification."""

    ctx: InitVar[Optional[Context]] = None

    reference: CommandTree = extra_field(
        default_factory=CommandTree.load_reference,
    )

    prototypes: Dict[str, CommandPrototype] = extra_field(default_factory=dict)

    def __post_init__(self, ctx: Optional[Context]):
        self.update_prototypes()

    def update_prototypes(self):
        """Update command prototypes."""
        self.prototypes = {
            proto.identifier: proto for proto in generate_prototypes(self.reference)
        }
