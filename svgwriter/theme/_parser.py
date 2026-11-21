"""
A recursive-descent parser for theme expressions, from tokens to a small tree of nodes.

Grammar, loosest binding first::

    expression := or
    or         := and ("or" and)*
    and        := not ("and" not)*
    not        := "not" not | comparison
    comparison := sum (("<" | "<=" | ">" | ">=" | "==" | "!=") sum)?
    sum        := product (("+" | "-") product)*
    product    := unary (("*" | "/") unary)*
    unary      := "-" unary | primary
    primary    := number | text | color | reference | "true" | "false" | color name
                | function "(" expression ("," expression)* ")" | "(" expression ")"
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from typing import TypeAlias

from ..color.color import parse_color
from ._constants import (
    BOOLEAN_WORDS,
    COMPARISONS,
    EXPONENT_RE,
    EXPRESSION_CACHE_SIZE,
    LENGTH_UNIT,
    LOGIC_WORDS,
    MAX_EXPRESSION_DEPTH,
    MAX_EXPRESSION_LENGTH,
    MAX_MAGNITUDE,
    UNSUPPORTED_OPERATORS,
)
from ._functions import Value, arity
from ._lexer import ExpressionError, Token, tokenize

__all__ = ["Binary", "Call", "Literal", "Node", "Reference", "Unary", "check_magnitude", "parse"]


@dataclass(frozen=True)
class Literal:
    """A constant: number, text, color or condition."""

    value: Value


@dataclass(frozen=True)
class Reference:
    """A ``{section.name}`` reference, by its dotted path."""

    path: str


@dataclass(frozen=True)
class Unary:
    """``-operand`` or ``not operand``."""

    operator: str
    operand: Node


@dataclass(frozen=True)
class Binary:
    """An arithmetic, comparison or logic operator between two operands."""

    operator: str
    left: Node
    right: Node


@dataclass(frozen=True)
class Call:
    """A call of a function from the table, or of ``if``."""

    name: str
    arguments: tuple[Node, ...]


Node: TypeAlias = "Literal | Reference | Unary | Binary | Call"


def check_magnitude(value: float) -> float:
    """Return *value* if its size is at most ``MAX_MAGNITUDE``, else raise ExpressionError."""
    if not abs(value) <= MAX_MAGNITUDE:
        raise ExpressionError(f"number too large; the limit is {MAX_MAGNITUDE:g}")
    return value


def _describe(token: Token) -> str:
    if token.kind == "end":
        return "unexpected end of expression"
    if token.text in UNSUPPORTED_OPERATORS:
        return UNSUPPORTED_OPERATORS[token.text]
    return f"unexpected {token.text!r} at column {token.column}"


class _Parser:
    __slots__ = ("_depth", "_index", "_tokens")

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._index = 0
        self._depth = 0

    @property
    def _token(self) -> Token:
        return self._tokens[self._index]

    def _advance(self) -> Token:
        token = self._token
        self._index += 1
        return token

    def _accept(self, kind: str, *texts: str) -> Token | None:
        token = self._token
        if token.kind == kind and (not texts or token.text in texts):
            return self._advance()
        return None

    def _expect(self, kind: str) -> Token:
        token = self._accept(kind)
        if token is None:
            raise ExpressionError(_describe(self._token))
        return token

    @contextmanager
    def _nested(self) -> Generator[None, None, None]:
        self._depth += 1
        if self._depth > MAX_EXPRESSION_DEPTH:
            raise ExpressionError(f"nested deeper than {MAX_EXPRESSION_DEPTH} levels")
        try:
            yield
        finally:
            self._depth -= 1

    def whole(self) -> Node:
        node = self.expression()
        self._expect("end")
        return node

    def expression(self) -> Node:
        with self._nested():
            return self._or()

    def _or(self) -> Node:
        node = self._and()
        while self._accept("name", "or"):
            node = Binary("or", node, self._and())
        return node

    def _and(self) -> Node:
        node = self._not()
        while self._accept("name", "and"):
            node = Binary("and", node, self._not())
        return node

    def _not(self) -> Node:
        if self._accept("name", "not"):
            with self._nested():
                return Unary("not", self._not())
        return self._comparison()

    def _comparison(self) -> Node:
        node = self._sum()
        operator = self._accept("operator", *COMPARISONS)
        if operator is None:
            return node
        node = Binary(operator.text, node, self._sum())
        if self._token.text in COMPARISONS:
            raise ExpressionError(f"comparisons cannot be chained (column {self._token.column}); use and")
        return node

    def _sum(self) -> Node:
        node = self._product()
        while (operator := self._accept("operator", "+", "-")) is not None:
            node = Binary(operator.text, node, self._product())
        return node

    def _product(self) -> Node:
        node = self._unary()
        while (operator := self._accept("operator", "*", "/")) is not None:
            node = Binary(operator.text, node, self._unary())
        return node

    def _unary(self) -> Node:
        if self._accept("operator", "-"):
            with self._nested():
                return Unary("-", self._unary())
        return self._primary()

    def _primary(self) -> Node:
        token = self._advance()
        if token.kind == "number":
            return Literal(_number(token))
        if token.kind == "string":
            return Literal(token.text)
        if token.kind == "color":
            return Literal(_color(token))
        if token.kind == "reference":
            return Reference(token.text)
        if token.kind == "(":
            node = self.expression()
            self._expect(")")
            return node
        if token.kind == "name" and token.text not in LOGIC_WORDS:
            if self._token.kind == "(":
                return self._call(token)
            if token.text in BOOLEAN_WORDS:
                return Literal(BOOLEAN_WORDS[token.text])
            return Literal(_color(token))
        raise ExpressionError(_describe(token))

    def _call(self, name: Token) -> Call:
        limits = arity(name.text)
        if limits is None:
            raise ExpressionError(f"unknown function {name.text!r}")
        self._expect("(")
        arguments: list[Node] = []
        if not self._accept(")"):
            arguments.append(self.expression())
            while self._accept(","):
                arguments.append(self.expression())
            self._expect(")")
        low, high = limits
        if not low <= len(arguments) <= high:
            expected = str(low) if low == high else f"{low} to {high}"
            raise ExpressionError(f"{name.text}() takes {expected} arguments, got {len(arguments)}")
        return Call(name.text, tuple(arguments))


def _number(token: Token) -> int | float:
    if EXPONENT_RE.fullmatch(token.unit):
        raise ExpressionError(f"exponent notation is not allowed at column {token.column}")
    if token.unit not in ("", LENGTH_UNIT):
        raise ExpressionError(f"unit {token.unit!r} is not supported; write plain numbers or {LENGTH_UNIT}")
    value = float(token.text)
    check_magnitude(value)
    return int(token.text) if token.text.isdigit() else value


def _color(token: Token) -> Value:
    try:
        return parse_color(token.text)
    except ValueError:
        kind = "color" if token.kind == "color" else "name"
        raise ExpressionError(f"unknown {kind} {token.text!r} at column {token.column}") from None


@lru_cache(maxsize=EXPRESSION_CACHE_SIZE)
def parse(text: str) -> Node:
    """Parse an expression into a tree; raise ExpressionError if it is malformed or too large.

    Parameters
    ----------
    text : str
        The expression.

    Returns
    -------
    Node
        The tree's root.

    Raises
    ------
    ExpressionError
        If the text is too long, nests too deeply, holds a number too large, or is not in the grammar.

    Examples
    --------
    >>> from svgwriter.theme._parser import parse
    >>> parse("-{fonts.sizes.text} * 2")
    Binary(operator='*', left=Unary(operator='-', operand=Reference(path='fonts.sizes.text')), right=Literal(value=2))
    """
    if len(text) > MAX_EXPRESSION_LENGTH:
        raise ExpressionError(f"longer than {MAX_EXPRESSION_LENGTH} characters")
    return _Parser(tokenize(text)).whole()
