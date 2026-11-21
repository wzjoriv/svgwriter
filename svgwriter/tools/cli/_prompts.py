"""
Prompts of ``svgwriter new``: arrow-key menus through the optional ``questionary`` package.
"""

from __future__ import annotations

import sys
from importlib.util import find_spec
from typing import Any

import click

from ...model.attributes.length import Length
from ...model.theme import THEMES
from ..project import PRESETS
from ._constants import COMMON_SIZES, CUSTOM_SIZE, KEEP_CHOICE, PRESET_COLUMN, SIZE_SEPARATOR

__all__ = ["ask_name", "ask_notebook", "ask_preset", "ask_size", "ask_theme", "has_questionary", "interactive",
           "parse_size"]


def interactive() -> bool:
    """Whether both input and output are a terminal, so prompting makes sense."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def has_questionary() -> bool:
    """Whether the optional ``questionary`` package (``pysvgwriter[cli]``) is installed."""
    return find_spec("questionary") is not None


def _answer(question: Any) -> Any:
    answer = question.ask()
    if answer is None:
        raise click.Abort()
    return answer


def parse_size(text: str) -> str | list[float | str]:
    """A size name, or ``WIDTH,HEIGHT`` (numbers or lengths such as ``50cm``) as a two-item list.

    Parameters
    ----------
    text : str
        ``"a4"``, ``"800,600"`` or ``"50cm,70cm"``.

    Returns
    -------
    str or list
        The name unchanged, or ``[width, height]`` with plain numbers as floats.

    Raises
    ------
    ValueError
        If a side is not a length.

    Examples
    --------
    >>> from svgwriter.tools.cli._prompts import parse_size
    >>> parse_size("a4"), parse_size("800,50cm")
    ('a4', [800.0, '50cm'])
    """
    if SIZE_SEPARATOR not in text:
        return text.strip()
    sides: list[float | str] = []
    for part in text.split(SIZE_SEPARATOR):
        Length.parse(part.strip())
        try:
            sides.append(float(part))
        except ValueError:
            sides.append(part.strip())
    return sides


def _valid_side(text: str) -> bool | str:
    try:
        Length.parse(text.strip())
    except ValueError as error:
        return str(error)
    return True


def ask_name() -> str:
    """Ask for the project name, which is also the folder to create."""
    import questionary

    return str(_answer(questionary.text("Project name", validate=lambda text: bool(text.strip()) or "required"))).strip()


def ask_preset() -> str:
    """Ask for a preset with arrow keys; each choice shows its description."""
    import questionary

    choices = [questionary.Choice(f"{name:<{PRESET_COLUMN}} {PRESETS.get(name).description}", name)
               for name in PRESETS.names()]
    return str(_answer(questionary.select("Preset", choices=choices)))


def ask_notebook() -> bool:
    """Ask whether the drawing is a script (``main.py``) or a notebook (``main.ipynb``)."""
    import questionary

    choices = [questionary.Choice("script (main.py)", False), questionary.Choice("notebook (main.ipynb)", True)]
    return bool(_answer(questionary.select("Drawing in a", choices=choices)))


def ask_theme() -> str | None:
    """Ask for a built-in theme to extend; None keeps the preset's own."""
    import questionary

    choices = [questionary.Choice(KEEP_CHOICE, KEEP_CHOICE), *(questionary.Choice(name, name) for name in THEMES.names())]
    picked = _answer(questionary.select("Theme", choices=choices))
    return None if picked == KEEP_CHOICE else picked


def ask_size() -> str | list[float | str] | None:
    """Ask for a page size: a common name, a custom width and height, or None for the preset's own."""
    import questionary

    choices = [questionary.Choice(KEEP_CHOICE, KEEP_CHOICE), *(questionary.Choice(name, name) for name in COMMON_SIZES),
               questionary.Choice(CUSTOM_SIZE, CUSTOM_SIZE)]
    picked = _answer(questionary.select("Page size", choices=choices))
    if picked != CUSTOM_SIZE:
        return None if picked == KEEP_CHOICE else picked
    width = _answer(questionary.text("Width (a number or a length such as 50cm)", validate=_valid_side))
    height = _answer(questionary.text("Height", validate=_valid_side))
    return parse_size(f"{width}{SIZE_SEPARATOR}{height}")
