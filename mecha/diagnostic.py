__all__ = [
    "Diagnostic",
    "DiagnosticCollection",
    "DiagnosticLabel",
    "DiagnosticLabelContainer",
    "DiagnosticError",
    "DiagnosticRenderer",
]


from collections import deque
from dataclasses import dataclass, field, replace
from heapq import heappop, heappush
from types import TracebackType
from typing import Any, Deque, Dict, Iterator, List, Literal, Optional, Tuple, Type

from beet import Container, FormattedPipelineException
from tokenstream import UNKNOWN_LOCATION, SourceLocation, set_location

########################################################################################
# This version of the file is mostly a brain dump of code that doesn't work
# for pretty-printing fancy diagnostics. It's not hooked up to anything but
# I'm just keeping it in case I want to work on it again in the future.
########################################################################################


@dataclass(frozen=True, order=True)
class DiagnosticLabel:
    """Label that can be added to diagnostics to annotate source code."""

    text: str = field(compare=False)
    id: int = -1
    symbol: str = "-"
    location: SourceLocation = UNKNOWN_LOCATION
    end_location: SourceLocation = UNKNOWN_LOCATION

    @property
    def linespan(self) -> int:
        """Return the number of lines highlighted by the label."""
        return self.end_location.lineno - self.location.lineno + 1

    @property
    def colspan(self) -> int:
        """Return the number of columns highlighted by the label."""
        return self.end_location.colno - self.location.colno + 1


class DiagnosticLabelContainer(Container[Any, Any]):
    """Container for diagnostic labels."""

    def normalize_key(self, key: Any) -> Any:
        if isinstance(key, SourceLocation):
            return key, key

        location = getattr(key, "location", None)
        end_location = getattr(key, "end_location", None)

        if location and end_location:
            return location, end_location

        return key

    def process(self, key: Any, value: Any) -> DiagnosticLabel:
        location, end_location = key

        if not isinstance(value, DiagnosticLabel):
            if not isinstance(value, str):
                value = str(value)

            value = DiagnosticLabel(text=value)

        return set_location(replace(value, id=len(self)), location, end_location)


@dataclass
class Diagnostic(Exception):
    """Exception that can be raised to report messages."""

    level: Literal["info", "warn", "error"]
    message: str

    rule: Optional[str] = None
    hint: Optional[str] = None
    filename: Optional[str] = None
    location: SourceLocation = UNKNOWN_LOCATION
    end_location: SourceLocation = UNKNOWN_LOCATION
    labels: DiagnosticLabelContainer = field(default_factory=DiagnosticLabelContainer)

    def __str__(self) -> str:
        return self.format_message()

    def format_message(self) -> str:
        """Return the formatted message."""
        message = self.message
        if self.rule:
            message += f" ({self.rule})"
        return message

    def format_location(self) -> str:
        """Return the formatted location of the reported message."""
        if self.filename:
            location = self.filename
            if not self.location.unknown:
                location += f":{self.location.lineno}:{self.location.colno}"
        elif not self.location.unknown:
            location = f"line {self.location.lineno}, column {self.location.colno}"
            if self.hint:
                location = f'File "{self.hint}", {location}'
        elif self.hint:
            location = self.hint
        else:
            location = ""

        return location

    def with_defaults(
        self,
        rule: Optional[str] = None,
        hint: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> "Diagnostic":
        """Set default values for unspecified attributes."""
        return replace(
            self,
            rule=self.rule or rule,
            hint=self.hint or hint,
            filename=self.filename or filename,
        )


@dataclass
class DiagnosticCollection(Exception):
    """Exception that can be raised to group multiple diagnostics."""

    exceptions: List[Diagnostic] = field(default_factory=list)

    rule: Optional[str] = None
    hint: Optional[str] = None
    filename: Optional[str] = None

    def add(self, exc: Diagnostic) -> Diagnostic:
        """Add diagnostic."""
        exc = exc.with_defaults(rule=self.rule, hint=self.hint, filename=self.filename)
        self.exceptions.append(exc)
        return exc

    def extend(self, other: "DiagnosticCollection"):
        """Combine diagnostics from another collection."""
        self.exceptions.extend(other.exceptions)

    def get_all_errors(self) -> Iterator[Diagnostic]:
        """Yield all the diagnostics with a severity level of "error"."""
        for exc in self.exceptions:
            if exc.level == "error":
                yield exc

    def __enter__(self) -> "DiagnosticCollection":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        if not exc_type:
            if self.exceptions:
                raise self

    def __str__(self) -> str:
        term = (
            "error"
            if all(exc.level == "error" for exc in self.exceptions)
            else "diagnostic"
        )
        term += "s" * (len(self.exceptions) > 1)
        return f"Reported {len(self.exceptions)} {term}."


class DiagnosticError(FormattedPipelineException):
    """Wrap a collection of error diagnostics to abort the build."""

    diagnostics: DiagnosticCollection

    def __init__(self, diagnostics: DiagnosticCollection, show_details: bool = True):
        super().__init__(diagnostics)
        self.diagnostics = diagnostics

        if show_details:
            details = "\n".join(
                f"{diagnostic.format_location()}: {diagnostic.format_message()}"
                for diagnostic in diagnostics.exceptions
            )
            self.message = f"{diagnostics}\n\n{details}"
        else:
            self.message = str(diagnostics)

        self.format_cause = True


@dataclass
class DiagnosticRenderer:
    """Class responsible for pretty-printing diagnostics."""

    diagnostic: Diagnostic
    source: List[str]

    def zz(self) -> str:
        sorted_labels: Deque[DiagnosticLabel] = deque(
            sorted(
                self.diagnostic.labels.values(),
                key=lambda label: (
                    label.location.pos,
                    -label.end_location.pos,
                    label.id,
                ),
            )
        )

        children: Dict[int, List[DiagnosticLabel]] = {}
        priority_queue: List[Tuple[SourceLocation, int, DiagnosticLabel]] = []

        for label in sorted_labels:
            while priority_queue and label.location >= priority_queue[0][0]:
                _, _, previous_label = heappop(priority_queue)
                print("close", previous_label.text)
                for _, _, parent in priority_queue:
                    children[parent.id].append(previous_label)

            for _, _, parent in priority_queue:
                children[parent.id].append(label)
            heappush(priority_queue, (label.end_location, -label.id, label))
            print("open", label.text)
            children[label.id] = []

        while priority_queue:
            _, _, previous_label = heappop(priority_queue)
            print("close", previous_label.text)
            for _, _, parent in priority_queue:
                children[parent.id].append(previous_label)
        for label in sorted_labels:
            print(label.text)
            for child in children[label.id]:
                print("-", child.text)

        return "==============="

    def render(self) -> str:
        surrounding_context = 2
        labels_per_line: Dict[int, List[DiagnosticLabel]] = {}

        for label in self.diagnostic.labels.values():
            for lineno in range(label.location.lineno, label.end_location.lineno + 1):
                labels_per_line.setdefault(lineno, []).append(label)

                for i in range(1, surrounding_context + 1):
                    labels_per_line.setdefault(max(lineno - i, 1), [])
                    labels_per_line.setdefault(min(lineno + i, len(self.source)), [])

        gutter: List[str] = []
        output: List[str] = []

        for lineno, labels in sorted(labels_per_line.items()):
            labels.sort(
                key=lambda label: (
                    label.location.pos,
                    -label.end_location.pos,
                    label.id,
                ),
            )

            gutter.append("")
            output.append(self.source[lineno - 1])

            overlapping_labels: List[DiagnosticLabel] = []

            while labels:
                colno = 1

                current_gutter = ""
                current_output = ""

                priority_queue: List[Tuple[SourceLocation, int, DiagnosticLabel]] = []

                def do_open(label: DiagnosticLabel):
                    nonlocal colno, current_output
                    print("open", label.text)
                    if label.location.lineno == lineno:
                        print("start")
                        if label.end_location.lineno == lineno:
                            current_output += (label.location.colno - colno) * " "
                            colno = label.location.colno

                def do_close(label: DiagnosticLabel):
                    nonlocal colno, current_output
                    print("close", label.text)
                    if label.end_location.lineno == lineno:
                        print("end")
                        if label.location.lineno == lineno:
                            current_output += (label.end_location.colno - colno) * "^"
                            colno = label.end_location.colno

                for label in labels:
                    while priority_queue and label.location >= priority_queue[0][0]:
                        _, _, previous_label = heappop(priority_queue)
                        do_close(previous_label)

                    do_open(label)
                    heappush(priority_queue, (label.end_location, -label.id, label))

                while priority_queue:
                    _, _, previous_label = heappop(priority_queue)
                    do_close(previous_label)

                labels = overlapping_labels
                overlapping_labels = []

                gutter.append(current_gutter)
                output.append(current_output)

        for prefix, line in zip(gutter, output):
            print(prefix, line)

        return "_____-_-_-_-__-_-_---"

    def render_yee(self) -> str:
        sorted_labels: Deque[DiagnosticLabel] = deque(
            sorted(
                self.diagnostic.labels.values(),
                key=lambda label: (
                    label.location.pos,
                    -label.end_location.pos,
                    label.id,
                ),
            )
        )

        line_start = max(sorted_labels[0].location.lineno - 1, 1)
        line_end = min(sorted_labels[-1].end_location.lineno + 1, len(self.source))

        labels = {}

        priority_queue: List[Tuple[SourceLocation, int, DiagnosticLabel]] = []
        operations: List[Tuple[Literal["open", "close"], DiagnosticLabel]] = []

        for label in sorted_labels:
            while priority_queue and label.location >= priority_queue[0][0]:
                _, _, previous_label = heappop(priority_queue)
                operations.append(("close", previous_label))

            heappush(priority_queue, (label.end_location, -label.id, label))
            operations.append(("open", label))

        while priority_queue:
            _, _, previous_label = heappop(priority_queue)
            operations.append(("close", previous_label))

        print(line_start, line_end)

        for op, label in operations:
            op_lineno = (
                label.location.lineno if op == "open" else label.end_location.lineno
            )
            while lineno < op_lineno:
                self.do_line(self.source[lineno - 1], stack)
                lineno += 1
            if op == "open":
                stack.append(label)
            elif op == "close":
                for enclosing_label in reversed(stack):
                    if label is enclosing_label:
                        stack.remove(label)
                        break

        lineno = max(sorted_labels[0].location.lineno - 1, 1)
        current_gutter: List[str] = []
        current_output: List[str] = []
        output: List[str] = []
        gutter: List[str] = []
        stack: List[DiagnosticLabel] = []

        for op, label in operations:
            op_lineno = (
                label.location.lineno if op == "open" else label.end_location.lineno
            )
            while lineno < op_lineno:
                output.append(self.source[lineno - 1])
                gutter.append("")
                lineno += 1

            if op == "open":
                stack.append(label)
            elif op == "close":
                for enclosing_label in reversed(stack):
                    if label is enclosing_label:
                        output.append(label.text)
                        gutter.append("")
                        stack.remove(label)
                        break

            print(op, label.text)

        gutter_width = max(len(prefix) for prefix in gutter)
        for prefix, line in zip(gutter, output):
            print(prefix.ljust(gutter_width), line)

        return "hey______"

    def rendessr(self) -> str:
        sorted_labels: List[DiagnosticLabel] = list(self.diagnostic.labels.values())
        sorted_labels.sort(
            key=lambda label: (label.location.pos, -label.end_location.pos, label.id)
        )

        priority_queue: List[Tuple[SourceLocation, int, DiagnosticLabel]] = []

        lineno: int = 1
        current: List[str] = []
        output: List[str] = []
        gutter: List[str] = []

        for label in sorted_labels:
            while priority_queue and label.location >= priority_queue[0][0]:
                _, _, previous_label = heappop(priority_queue)
                operations.append(("close", previous_label))

            heappush(priority_queue, (label.end_location, -label.id, label))
            operations.append(("open", label))

        while priority_queue:
            _, _, previous_label = heappop(priority_queue)
            operations.append(("close", previous_label))

    def do_line(
        self,
        source: str,
        single_labels: List[DiagnosticLabel],
        multi_labels: List[DiagnosticLabel],
    ):
        print(len(single_labels), len(multi_labels), source)
