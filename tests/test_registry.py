from __future__ import annotations

import warnings
from importlib import metadata

import pytest

import svgwriter as svg
from svgwriter._internal._registry import Registry
from svgwriter.formats._format import FORMATS


def _points(*items: tuple[str, str]) -> list[metadata.EntryPoint]:
    return [metadata.EntryPoint(name, value, "svgwriter.widget") for name, value in items]


class TestRegistry:
    def test_decorator_forms_and_lookups(self) -> None:
        widgets: Registry[object] = Registry("widget")

        @widgets.register
        def knob() -> None: ...

        @widgets(name="slider")
        def anything() -> None: ...

        widgets.register(len, name="count")
        assert widgets.list() == ["knob", "slider", "count"] and widgets.get("slider") is anything
        assert "knob" in widgets and len(widgets) == 3 and "count" in repr(widgets)
        assert widgets.unregister("count") is len and "count" not in widgets

    def test_taken_names_and_replacements(self) -> None:
        widgets: Registry[object] = Registry("widget")
        widgets.add_builtin("knob", print)
        with pytest.raises(ValueError, match=r"widget 'knob' is already registered by builtins.print \(built in\)"):
            widgets.register(len, name="knob")
        widgets.register(len, name="knob", replace=True)
        assert widgets.get("knob") is len
        widgets.unregister("knob")
        assert widgets.get("knob") is print
        with pytest.raises(KeyError, match="built in; replace it"):
            widgets.unregister("knob")

    def test_unknown_names(self) -> None:
        widgets: Registry[object] = Registry("widget")
        widgets.register(print, name="slider")
        with pytest.raises(svg.errors.UnknownNameError, match="unknown widget 'slidr'; did you mean 'slider'") as raised:
            widgets.get("slidr")
        assert isinstance(raised.value, KeyError) and isinstance(raised.value, ValueError)
        assert str(raised.value).startswith("unknown")
        with pytest.raises(TypeError, match="has no name"):
            widgets.register(3)

    def test_builtins_load_lazily(self) -> None:
        loaded = []
        widgets: Registry[object] = Registry("widget", lambda: loaded.append(widgets.register(print, name="knob")))
        assert not loaded
        assert widgets.list() == ["knob"] and widgets.state() == {}
        with pytest.raises(KeyError, match="built in"):
            widgets.unregister("knob")

    def test_entry_points(self, monkeypatch: pytest.MonkeyPatch) -> None:
        widgets: Registry[object] = Registry("widget")
        points = _points(("count", "builtins:len"), ("broken", "no_such_module:thing"))
        monkeypatch.setattr(metadata, "entry_points", lambda group: points if group == widgets.group else [])
        assert widgets.group == "svgwriter.widget"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert widgets.get("count") is len
            assert widgets.list() == ["count"] and widgets.find("missing") is None
        assert len(caught) == 1 and "widget plugin 'broken'" in str(caught[0].message)

    def test_builtin_lookups_skip_entry_points(self, monkeypatch: pytest.MonkeyPatch) -> None:
        widgets: Registry[object] = Registry("widget")
        widgets.add_builtin("knob", print)
        monkeypatch.setattr(metadata, "entry_points", pytest.fail)
        assert widgets.get("knob") is print

    def test_every_registry_has_the_same_methods(self) -> None:
        registries = [*svg.preset.KINDS.values(), svg.themes, FORMATS, svg.renderers, svg.project.presets]
        for registry in registries:
            assert isinstance(registry, Registry) and registry.group == f"svgwriter.{registry.kind}" or \
                registry is svg.project.presets
            names = registry.list()
            assert names and registry.get(names[0]) is not None or registry is svg.preset.font
        assert svg.project.presets.group == "svgwriter.project_preset"


def test_top_level_typos_suggest() -> None:
    with pytest.raises(AttributeError, match="did you mean 'circle'"):
        svg.circel  # noqa: B018
