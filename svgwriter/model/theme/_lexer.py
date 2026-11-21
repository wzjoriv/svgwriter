"""
Tokens of theme expressions: numbers, text, colors, ``{references}``, names, operators and punctuation.
"""

from __future__ import annotations

from typing import NamedTuple

from ._constants import (
    COLOR_FUNCTION_RE,
    HEX_RE,
    NAME_RE,
    NUMBER_RE,
    OPERATORS,
    PUNCTUATION,
    QUOTES,
    REFERENCE_RE,
)

__all__ = ["ExpressionError", "Token", "tokenize"]


class ExpressionError(Exception):
    """A malformed or failing theme expression; the reason, without the key path."""


class Token(NamedTuple):
    """One token: its kind, its text, its column (from 1) and, for numbers, the unit after it."""

    kind: str
    text: str
    column: int
    unit: str = ""


def _color_function(text: str, start: int, open_at: int) -> int:
    close = text.find(")", open_at)
    nested = text.find("(", open_at)
    if close < 0 or 0 <= nested < close:
        raise ExpressionError(f"unclosed color function at column {start + 1}")
    return close + 1


def _string(text: str, start: int) -> int:
    end = text.find(text[start], start + 1)
    if end < 0:
        raise ExpressionError(f"unclosed text at column {start + 1}")
    if "\\" in text[start:end]:
        raise ExpressionError(f"escapes are not supported in text at column {start + 1}")
    return end + 1


def _token(text: str, pos: int) -> tuple[Token, int]:
    char = text[pos]
    if char in PUNCTUATION:
        return Token(char, char, pos + 1), pos + 1
    if char in QUOTES:
        end = _string(text, pos)
        return Token("string", text[pos + 1:end - 1], pos + 1), end
    if char == "{":
        match = REFERENCE_RE.match(text, pos)
        if match is None:
            raise ExpressionError(f"malformed reference at column {pos + 1}; write {{palette.name}}")
        return Token("reference", match.group(1), pos + 1), match.end()
    if (match := NUMBER_RE.match(text, pos)) is not None:
        return Token("number", match.group(1), pos + 1, match.group(2) or ""), match.end()
    if (match := COLOR_FUNCTION_RE.match(text, pos)) is not None:
        end = _color_function(text, pos, match.end())
        return Token("color", text[pos:end], pos + 1), end
    if (match := HEX_RE.match(text, pos)) is not None:
        return Token("color", match.group(), pos + 1), match.end()
    if (match := NAME_RE.match(text, pos)) is not None:
        return Token("name", match.group(), pos + 1), match.end()
    for operator in OPERATORS:
        if text.startswith(operator, pos):
            return Token("operator", operator, pos + 1), pos + len(operator)
    raise ExpressionError(f"unexpected character {char!r} at column {pos + 1}")


def tokenize(text: str) -> list[Token]:
    """Split *text* into tokens ending with an ``end`` token; raise ExpressionError on anything else.

    Parameters
    ----------
    text : str
        The expression.

    Returns
    -------
    list of Token
        The tokens.

    Raises
    ------
    ExpressionError
        On a character outside the language, an unclosed text or color function, or a bad reference.

    Examples
    --------
    >>> from svgwriter.model.theme._lexer import tokenize
    >>> [t.kind for t in tokenize("mix({palette.a}, #fff, 0.5)")]
    ['name', '(', 'reference', ',', 'color', ',', 'number', ')', 'end']
    """
    tokens: list[Token] = []
    pos = 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        token, pos = _token(text, pos)
        tokens.append(token)
    tokens.append(Token("end", "", len(text) + 1))
    return tokens
