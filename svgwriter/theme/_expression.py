"""
Theme expressions: deciding which text values are expressions, and evaluating them.

Evaluation walks the parsed tree with a fixed set of operators and the functions of
``_functions.FUNCTIONS``; nothing in an expression reaches Python's ``eval``, attributes or imports.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

from ..color.color import Color
from ._constants import (
    CALL_RE,
    COMPARISONS,
    CONDITIONAL,
    CSS_TEXT_FUNCTIONS,
    EXPONENT_RE,
    EXPRESSION_CACHE_SIZE,
    LOGIC_OPERATORS,
    MAX_EXPRESSION_LENGTH,
    OPERAND_TOKENS,
    UNTOKENIZED_STARTS,
)
from ._errors import ThemeError
from ._functions import FUNCTIONS, Value, arity, kind
from ._lexer import ExpressionError, Token, tokenize
from ._parser import Binary, Call, Literal, Node, Reference, Unary, check_magnitude, parse

__all__ = ["Lookup", "evaluate", "is_expression"]

Lookup = Callable[[str], object]
"""Resolves a reference path such as ``"palette.primary"`` to its value."""


def _computes(tokens: list[Token]) -> bool:
    if [t.kind for t in tokens] == ["reference", "end"] or (tokens[0].kind, tokens[0].text) == ("name", "not"):
        return True
    for index, token in enumerate(tokens):
        if token.kind == "name" and token.text in LOGIC_OPERATORS:
            return True
        if token.kind == "number" and EXPONENT_RE.fullmatch(token.unit):
            return True
        if token.kind != "operator":
            continue
        binary = index > 0 and tokens[index - 1].kind in OPERAND_TOKENS
        if binary or tokens[index + 1].kind != "number":
            return True
    return False


@lru_cache(maxsize=EXPRESSION_CACHE_SIZE)
def is_expression(text: str) -> bool:
    """Whether a text value is an expression rather than plain text with ``{references}``.

    It is one when it is a lone reference, calls a function (any call-like name other than a CSS
    function such as ``url`` or a color function), starts with ``(`` or ``not``, puts an operator
    between two values, or writes a number with an exponent. Text longer than the expression limit,
    and text that starts like a call, a reference or quoted text but holds characters outside the language,
    count too, so they are rejected rather than written out.

    Parameters
    ----------
    text : str
        The value.

    Returns
    -------
    bool
        True for an expression.

    Examples
    --------
    >>> from svgwriter.theme._expression import is_expression
    >>> is_expression("readable({palette.primary})"), is_expression("{fonts.sizes.text} * 1.5")
    (True, True)
    >>> is_expression("1px solid {palette.border}"), is_expression("Georgia, serif"), is_expression("-2px")
    (False, False, False)
    """
    source = text.strip()
    if len(source) > MAX_EXPRESSION_LENGTH or source.startswith("("):
        return True
    call = CALL_RE.match(source)
    if call is not None and call.group(1).lower() in CSS_TEXT_FUNCTIONS:
        return False
    if call is not None and (arity(call.group(1)) is not None or not call.group(1).isalpha()):
        return True
    try:
        tokens = tokenize(source)
    except ExpressionError:
        return call is not None or source[:1] in UNTOKENIZED_STARTS
    return call is not None and tokens[0].kind == "name" or _computes(tokens)


def _number(value: Value, operator: str) -> float:
    if kind(value) != "number":
        raise ExpressionError(f"{operator} needs numbers, got {kind(value)}")
    return value  # type: ignore[return-value]


def _condition(value: Value, operator: str) -> bool:
    if not isinstance(value, bool):
        raise ExpressionError(f"{operator} needs conditions, got {kind(value)}")
    return value


def _arithmetic(operator: str, left: float, right: float) -> float:
    if operator == "+":
        return left + right
    if operator == "-":
        return left - right
    if operator == "*":
        return left * right
    if right == 0:
        raise ExpressionError("division by zero")
    return left / right


def _compare(operator: str, left: Value, right: Value) -> bool:
    if operator in ("==", "!="):
        if kind(left) != kind(right):
            raise ExpressionError(f"cannot compare {kind(left)} with {kind(right)}")
        return (left == right) == (operator == "==")
    first, second = _number(left, operator), _number(right, operator)
    if operator == "<":
        return first < second
    if operator == "<=":
        return first <= second
    if operator == ">":
        return first > second
    return first >= second


class _Evaluator:
    __slots__ = ("_lookup",)

    def __init__(self, lookup: Lookup) -> None:
        self._lookup = lookup

    def run(self, node: Node) -> Value:
        if isinstance(node, Literal):
            return node.value
        if isinstance(node, Reference):
            return self._reference(node.path)
        if isinstance(node, Unary):
            operand = self.run(node.operand)
            if node.operator == "not":
                return not _condition(operand, "not")
            return -_number(operand, "-")
        if isinstance(node, Binary):
            return self._binary(node)
        return self._call(node)

    def _reference(self, path: str) -> Value:
        value = self._lookup(path)
        if isinstance(value, (bool, int, float, str, Color)):
            return value
        raise ExpressionError(f"{{{path}}} is not a number, text or color")

    def _binary(self, node: Binary) -> Value:
        if node.operator in ("and", "or"):
            left = _condition(self.run(node.left), node.operator)
            if left == (node.operator == "or"):
                return left
            return _condition(self.run(node.right), node.operator)
        left, right = self.run(node.left), self.run(node.right)
        if node.operator in COMPARISONS:
            return _compare(node.operator, left, right)
        result = _arithmetic(node.operator, _number(left, node.operator), _number(right, node.operator))
        return check_magnitude(result)

    def _call(self, node: Call) -> Value:
        if node.name == CONDITIONAL:
            test = _condition(self.run(node.arguments[0]), f"{CONDITIONAL}()")
            return self.run(node.arguments[1 if test else 2])
        arguments = [self.run(argument) for argument in node.arguments]
        try:
            return FUNCTIONS[node.name].call(arguments)
        except ExpressionError as error:
            raise ExpressionError(f"{node.name}(): {error}") from None
        except (ArithmeticError, TypeError, ValueError) as error:
            raise ExpressionError(f"{node.name}(): {error}") from None


def evaluate(text: str, lookup: Lookup, where: str) -> Value:
    """Evaluate the expression *text*, resolving references with *lookup*.

    Parameters
    ----------
    text : str
        The expression.
    lookup : callable
        Takes a reference path such as ``"palette.primary"`` and returns its value, raising
        ThemeError if it names nothing.
    where : str
        The key path of the value, such as ``"palette.on_primary"``, for messages.

    Returns
    -------
    bool or int or float or str or Color
        The value.

    Raises
    ------
    ThemeError
        If the expression is malformed, too large, or fails; the message starts with *where*.

    Examples
    --------
    >>> from svgwriter.theme._expression import evaluate
    >>> evaluate("max({fonts.sizes.text} * 1.5, 12)", lambda path: 14.0, "roles.badge.font-size")
    21.0
    """
    try:
        return _Evaluator(lookup).run(parse(text.strip()))
    except ExpressionError as error:
        raise ThemeError(f"{where}: {error}") from None
    except RecursionError:
        raise ThemeError(f"{where}: nested too deeply") from None
