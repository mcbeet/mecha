__all__ = [
    "CommandTree",
]


from importlib.resources import read_text
from typing import Dict, List, Optional

from beet.core.utils import JsonDict
from pydantic import BaseModel


class CommandTree(BaseModel):
    """Deserialized representation of the commands.json reference."""

    type: str
    parser: Optional[str] = None
    properties: Optional[JsonDict] = None
    executable: Optional[bool] = None
    redirect: Optional[List[str]] = None
    children: Optional[Dict[str, "CommandTree"]] = None

    class Config:
        extra = "forbid"

    @classmethod
    def load_reference(cls) -> "CommandTree":
        """Load commands.json reference."""
        return cls.parse_raw(read_text("mecha.resources", "commands.json"))

    def extend(self, other: "CommandTree") -> "CommandTree":
        """Merge children from another commands.json."""
        if other.children:
            if self.children is None:
                self.children = {}
            for name, child in other.children.items():
                if name in self.children:
                    self.children[name].extend(child)
                else:
                    self.children[name] = child
        return self


CommandTree.update_forward_refs()
