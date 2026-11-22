"""
Tokenizer and parser for path data (the ``d`` attribute).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from ...errors import PathSyntaxError
from ._constants import ARC_FLAG_POSITIONS, ARITY, NUMBER_RE, SEPARATORS
from .commands import (
    ArcTo,
    ClosePath,
    CurveTo,
    HLineTo,
    LineTo,
    MoveTo,
    PathCommand,
    QuadTo,
    SmoothCurveTo,
    SmoothQuadTo,
    VLineTo,
)

__all__ = ["iter_commands", "parse_path"]

_COMMANDS: Final[dict[str, type[PathCommand]]] = {
    "M": MoveTo,
    "L": LineTo,
    "H": HLineTo,
    "V": VLineTo,
    "C": CurveTo,
    "S": SmoothCurveTo,
    "Q": QuadTo,
    "T": SmoothQuadTo,
    "A": ArcTo,
    "Z": ClosePath,
}



class _Scanner:
    __slots__ = ("pos", "text")

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def skip(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in SEPARATORS:
            self.pos += 1

    def at_end(self) -> bool:
        self.skip()
        return self.pos >= len(self.text)

    def peek_command(self) -> str | None:
        self.skip()
        if self.pos < len(self.text) and self.text[self.pos].upper() in _COMMANDS:
            return self.text[self.pos]
        return None

    def number(self) -> float:
        self.skip()
        match = NUMBER_RE.match(self.text, self.pos)
        if match is None:
            raise PathSyntaxError("expected a number", self.pos)
        self.pos = match.end()
        return float(match.group())

    def flag(self) -> bool:
        self.skip()
        if self.pos >= len(self.text) or self.text[self.pos] not in "01":
            raise PathSyntaxError("expected an arc flag", self.pos)
        self.pos += 1
        return self.text[self.pos - 1] == "1"


def _arguments(scanner: _Scanner, code: str) -> list[float]:
    args: list[float] = []
    for index in range(ARITY[code]):
        if code == "A" and index in ARC_FLAG_POSITIONS:
            args.append(float(scanner.flag()))
        else:
            args.append(scanner.number())
    return args


def _build(code: str, relative: bool, args: list[float]) -> PathCommand:
    cls = _COMMANDS[code]
    if code == "A":
        rx, ry, rotation, large, sweep, x, y = args
        return ArcTo(rx, ry, rotation, bool(large), bool(sweep), x, y, relative=relative)
    return cls(*args, relative=relative)  # type: ignore[call-arg]


def iter_commands(text: str) -> Iterator[PathCommand]:
    """Iterate the commands of path data text, expanding implicit repeats.

    ``M0 0 1 1`` yields a ``MoveTo`` followed by a ``LineTo``; a repeated
    ``moveto`` becomes a ``lineto`` of the same case. Empty text yields nothing.

    Parameters
    ----------
    text : str
        Path data, as in the ``d`` attribute.

    Yields
    ------
    PathCommand
        The commands in order.

    Raises
    ------
    PathSyntaxError
        If the text is malformed or does not start with a moveto.

    See Also
    --------
    parse_path : The same, collected into a list.

    Examples
    --------
    >>> from svgwriter.model.pathdata import iter_commands
    >>> [str(c) for c in iter_commands("M0 0 1 1 l2 2")]
    ['M0 0', 'L1 1', 'l2 2']
    """
    scanner = _Scanner(text)
    if scanner.at_end():
        return
    letter = scanner.peek_command()
    if letter is None or letter.upper() != "M":
        raise PathSyntaxError("path data must start with a moveto", scanner.pos)
    while not scanner.at_end():
        letter = scanner.peek_command()
        if letter is None:
            raise PathSyntaxError("expected a command", scanner.pos)
        scanner.pos += 1
        code, relative = letter.upper(), letter.islower()
        if code == "Z":
            yield ClosePath(relative=relative)
            continue
        yield _build(code, relative, _arguments(scanner, code))
        if code == "M":
            code = "L"
        while not scanner.at_end() and scanner.peek_command() is None:
            yield _build(code, relative, _arguments(scanner, code))


def parse_path(text: str) -> list[PathCommand]:
    """Parse path data text into a list of commands.

    Parameters
    ----------
    text : str
        Path data, as in the ``d`` attribute.

    Returns
    -------
    list of PathCommand
        The parsed commands.

    Raises
    ------
    PathSyntaxError
        If the text is malformed or does not start with a moveto.

    See Also
    --------
    iter_commands : Lazy version.

    Examples
    --------
    >>> from svgwriter.model.pathdata import parse_path
    >>> [str(c) for c in parse_path("M0 0 L1 1 z")]
    ['M0 0', 'L1 1', 'z']
    """
    return list(iter_commands(text))
