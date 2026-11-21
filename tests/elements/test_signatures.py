from __future__ import annotations

import inspect

import pytest

import svgwriter as svg
from svgwriter.model.attributes.names import PRESENTATION_ATTRIBUTES, py_name
from svgwriter.model.elements import Element, PresentationAttributes
from svgwriter.model.elements._behavior._presentation import PresentationKeywords

ELEMENTS = sorted(
    (cls for cls in Element._registry.values() if cls.__module__.startswith("svgwriter.model.elements.")),
    key=lambda cls: cls.__name__,
)
KEYWORD_KINDS = (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)


def _keywords(function: object) -> set[str]:
    return {p.name for p in inspect.signature(function).parameters.values() if p.kind in KEYWORD_KINDS} - {"self"}


def _expected(cls: type) -> set[str]:
    """Every keyword the attribute groups (the ``__init__`` of each base) accept, plus `PresentationKeywords`."""
    names: set[str] = set()
    for base in cls.__mro__[1:]:
        if "__init__" in base.__dict__ and base.__module__.startswith("svgwriter."):
            names |= _keywords(base.__dict__["__init__"])
    if issubclass(cls, PresentationAttributes):
        names |= set(PresentationKeywords.__annotations__)
    return names


@pytest.mark.parametrize("cls", ELEMENTS, ids=lambda cls: cls.__name__)
def test_every_element_lists_its_attributes(cls: type) -> None:
    assert "__init__" in cls.__dict__, f"{cls.__name__} has no generated __init__"
    parameters = inspect.signature(cls).parameters
    missing = _expected(cls) - set(parameters)
    assert not missing, f"{cls.__name__} does not list {sorted(missing)}"
    assert any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters.values())
    assert all(p.annotation is not inspect.Parameter.empty for p in parameters.values())


def test_presentation_keywords_complete_the_presentation_attributes() -> None:
    named = _keywords(PresentationAttributes.__init__)
    extra = set(PresentationKeywords.__annotations__)
    assert not named & extra
    assert named | extra == {py_name(name) for name in PRESENTATION_ATTRIBUTES}


def test_lowercase_aliases_share_the_signature() -> None:
    assert svg.text is svg.Text and inspect.signature(svg.text) == inspect.signature(svg.Text)
    assert {"x", "y", "font_size", "fill", "font_style", "class_", "t"} <= set(inspect.signature(svg.text).parameters)
    assert list(inspect.signature(svg.rect).parameters)[:4] == ["x", "y", "width", "height"]


@pytest.mark.parametrize(
    "cls", [c for c in ELEMENTS if issubclass(c, PresentationAttributes)], ids=lambda cls: cls.__name__
)
def test_listed_keywords_reach_the_attributes(cls: type) -> None:
    sizes = {"Rect": (0, 0, 1, 1), "Circle": (0, 0, 1), "Ellipse": (0, 0, 1, 1)}.get(cls.__name__, ())
    element = cls(*sizes, font_style="italic", fill="red", id="e", data_note="kept")
    assert element.get("font-style") == "italic" and element.get("fill") == "red"
    assert element.id == "e" and element.get("data-note") == "kept"


def test_listed_keywords_keep_their_conversions() -> None:
    text = svg.Text("Hi", x=[1, 2], decoration="underline", class_=["a", "b"], letter_spacing=2)
    assert str(text) == '<text x="1 2" letter-spacing="2" text-decoration="underline" class="a b">Hi</text>'
    use = svg.Use("#a", 1, 2, fill="red")
    assert list(use.attributes.items()) == [("x", 1), ("y", 2), ("xlink:href", "#a"), ("fill", "red")]
