__all__ = [
    "Mecha",
]


from contextlib import contextmanager
from dataclasses import InitVar, dataclass, field
from importlib import import_module
from typing import (
    Any,
    Callable,
    ContextManager,
    Iterator,
    Optional,
    Protocol,
    TypeVar,
    Union,
    overload,
)

from beet import Context, DataPack

T = TypeVar("T")

Fn = Union[Callable[[], Any], Callable[[T], Any]]


def export(f: T) -> T:
    yo: Any = f

    import_module(yo.__module__).__dict__.setdefault("__mecha_export__", []).append(yo)
    print(yo, yo.__name__)
    print(yo, yo.__qualname__)
    print(yo, yo.__module__)
    print(yo, yo.__dict__)
    return f


@dataclass
class Mecha:
    """Class exposing the command api."""

    target: InitVar[Union[Context, DataPack]]

    namespace: Optional[str] = None
    path: Optional[str] = None

    data_pack: DataPack = field(init=False)

    def __init_subclass__(cls, **kwargs: Any):
        print("subclass", kwargs)

    def __post_init__(self, target: Union[Context, DataPack]):
        if isinstance(target, Context):
            self.data_pack = target.data
            config = target.meta.get("mecha", {})
            namespace = config.get("namespace", target.project_name)
            path = config.get("path", "")
        else:
            self.data_pack = target
            namespace = self.data_pack.name or ""
            path = ""

        if self.namespace is None:
            self.namespace = namespace

        if self.path is None:
            self.path = path

    def resolve_path(self, path: str) -> str:
        """Resolve partial path."""
        namespace, sep, path = path.rpartition(":")

        if not namespace:
            namespace = self.namespace
        if not sep:
            path = f"{self.path}/{path}"

        return f"{namespace}:{path.strip('/')}".replace("//", "/").lower()

    def say(self, *args: str):
        print(*args)

    @overload
    def function(self, path: Optional[str] = None) -> ContextManager[str]:
        ...

    @overload
    def function(self: T, path: str, func: Fn[T]):
        ...

    @overload
    def function(self: T, func: Fn[T]):
        ...

    def function(self, arg1: Any = None, arg2: Any = None):
        print("function", arg1, arg2)
        if callable(arg1) or callable(arg2):
            return
        return self._handle_function(arg1, arg2)

    @contextmanager
    def _handle_function(self, *args: Any):
        yield ", ".join(map(str, args))

    @contextmanager
    def override(
        self,
        namespace: Optional[str] = None,
        path: Optional[str] = None,
    ):
        try:
            yield
        finally:
            pass

    def scan(self, thing: Any):
        print(thing)
        if isinstance(thing, str):
            thing = import_module(thing)
        if dct := getattr(thing, "__dict__", None):
            print(dct.get("__mecha_export__", []))
