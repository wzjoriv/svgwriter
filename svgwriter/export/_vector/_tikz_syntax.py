"""
TikZ source tokenizing: balanced groups, option lists, style definitions and dimensions.
"""

from __future__ import annotations

from ._constants import (
    BRACKETS,
    DIMENSION_RE,
    MAX_STYLE_DEPTH,
    PATH_TOKEN_RE,
    TIKZSET_RE,
    TIKZSTYLE_RE,
    UNITS,
)

__all__ = ["Pair", "Point"]

Point = tuple[float, float]
Pair = tuple[str, str | None]


def _balanced(text: str, start: int) -> tuple[str, int]:
    """The text inside the bracket opening at *start*, and the index after its closer."""
    opener, closer = text[start], BRACKETS[text[start]]
    depth = 0
    for i in range(start, len(text)):
        depth += (text[i] == opener) - (text[i] == closer)
        if depth == 0:
            return text[start + 1:i], i + 1
    return text[start + 1:], len(text)


def _unbrace(text: str) -> str:
    """*text* without one pair of braces wrapping all of it."""
    text = text.strip()
    if text.startswith("{") and _balanced(text, 0)[1] == len(text):
        return text[1:-1].strip()
    return text


def _split(text: str) -> list[str]:
    """Split *text* at commas outside braces, brackets and parentheses."""
    parts, depth, current = [], 0, []
    for char in text:
        depth += (char in "{[(") - (char in "}])")
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [_unbrace(part) for part in parts if part.strip()]


def _options(text: str) -> list[Pair]:
    """``key=value`` pairs of an option list; bare keys have the value None."""
    out = []
    for part in _split(text):
        key, separator, value = part.partition("=")
        out.append((" ".join(key.split()), _unbrace(value) if separator else None))
    return out


def _expand(pairs: list[Pair], styles: dict[str, list[Pair]], depth: int = 0) -> list[Pair]:
    """*pairs* with every bare style name replaced by the options it defines."""
    out: list[Pair] = []
    for key, value in pairs:
        if value is None and key in styles and depth < MAX_STYLE_DEPTH:
            out += _expand(styles[key], styles, depth + 1)
        else:
            out.append((key, value))
    return out


def _define(table: dict[str, list[Pair]], pairs: list[Pair]) -> None:
    """Record the ``name/.style`` and ``name/.append style`` entries of *pairs* in *table*."""
    for key, value in pairs:
        name, _, kind = key.partition("/.")
        if value is None or kind not in ("style", "append style"):
            continue
        table[name] = (table.get(name, []) if kind == "append style" else []) + _options(value)


def _style_table(text: str, picture: str) -> dict[str, list[Pair]]:
    """Styles from ``\\tikzset``, ``\\tikzstyle`` and the picture's own options, by name."""
    table: dict[str, list[Pair]] = {}
    for match in TIKZSET_RE.finditer(text):
        _define(table, _options(_balanced(text, match.end() - 1)[0]))
    for match in TIKZSTYLE_RE.finditer(text):
        table[match.group(1).strip()] = _options(_balanced(text, match.end() - 1)[0])
    _define(table, _options(picture))
    return table


def _dimension(text: str) -> tuple[float, bool]:
    """A length in points and whether it carried a unit."""
    match = DIMENSION_RE.match(text)
    if match is None:
        raise ValueError(f"not a TikZ dimension: {text!r}")
    value, unit = float(match.group(1)), match.group(2)
    if unit is not None and unit not in UNITS:
        raise ValueError(f"unknown TeX unit: {unit!r}")
    return value * UNITS.get(unit or "pt", 1.0), unit is not None


def _tokens(text: str) -> list[tuple[str, str]]:
    """Path tokens: ``("coord"|"opts"|"text", body)`` for bracketed groups, else ``("op", word)``."""
    tokens, pos = [], 0
    kinds = {"(": "coord", "[": "opts", "{": "text"}
    while pos < len(text):
        match = PATH_TOKEN_RE.match(text, pos)
        if match is None or not match.group(1).strip():
            break
        word, start = match.group(1), match.start(1)
        if word in kinds:
            body, pos = _balanced(text, start)
            tokens.append((kinds[word], body))
            continue
        pos = match.end()
        tokens.append(("op", word))
    return tokens


def _length(keys: dict[str, str | None], name: str, default: float) -> float:
    """The length option *name* in points, *default* when absent or unreadable."""
    value = keys.get(name)
    try:
        return default if value is None else _dimension(value)[0]
    except ValueError:
        return default
