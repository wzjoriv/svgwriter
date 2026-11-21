from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter.widgets import (
    Checkbox,
    ColorPicker,
    Dropdown,
    IntSlider,
    MultiSelect,
    Number,
    RangeSlider,
    Segmented,
    Slider,
    Swatches,
    Text,
    Toggle,
    control,
    controls,
    controls_of,
)


class TestInference:
    @pytest.mark.parametrize("spec, kind", [
        ((0, 10), IntSlider), ((0.0, 1.0), Slider), ((0, 10, 2), IntSlider), ((0, 1, 0.1), Slider),
        (True, Toggle), (False, Toggle), ("#ff0000", ColorPicker), ("hello", Text), ("red", Text),
        (["a", "b"], Segmented), (list("abcd"), Segmented), (list("abcde"), Dropdown),
        ({"light": 300, "bold": 700}, Segmented), (["#f00", "#0f0"], Swatches), (40, IntSlider), (0.5, Slider), (svg.mm(5), Slider),
        ((svg.mm(0), svg.mm(20)), Slider),
    ])
    def test_kinds(self, spec, kind) -> None:
        assert type(control(spec)) is kind

    def test_details(self) -> None:
        assert control((0, 10, 2)).step == 2
        assert control(40).max == 80 and control(-4).min == -8 and control(0).max == 1
        length = control(svg.mm(5))
        assert (length.min, length.max, length.units, length.initial) == (0, 10, "mm", 5)
        assert control(svg.Color(1, 0, 0)).initial == "#ff0000"
        assert control({"light": 300, "bold": 700}).initial == 300
        same = Slider(0, 1)
        assert control(same) is same and control(same, label="x").label == "x"

    def test_errors(self) -> None:
        with pytest.raises(TypeError, match="no control"):
            control(object())
        with pytest.raises(ValueError, match="min < max"):
            control((5, 1))
        with pytest.raises(ValueError, match="one unit"):
            control((svg.mm(0), svg.pt(4)))
        with pytest.raises(ValueError, match="empty"):
            control([])


class TestValidation:
    def test_slider(self) -> None:
        slider = Slider(0, 10)
        assert slider.step == pytest.approx(0.1) and slider.initial == 5.0
        assert slider.check(3) == 3.0 and isinstance(slider.check(3), float)
        for bad, error in ((11, ValueError), (-1, ValueError), ("3", TypeError), (True, TypeError),
                           (float("nan"), ValueError)):
            with pytest.raises(error):
                slider.check(bad)
        with pytest.raises(ValueError, match="step"):
            Slider(0, 1, step=0)
        with pytest.raises(ValueError, match="outside"):
            Slider(0, 1, value=2)

    def test_int_slider_and_units(self) -> None:
        ints = IntSlider(1, 12)
        assert ints.initial == 6 and ints.check(4.0) == 4
        with pytest.raises(ValueError, match="whole"):
            ints.check(4.5)
        mm = Slider(0, 10, units="mm")
        assert mm.check(svg.mm(4)) == 4.0 and str(mm.argument(4.0)) == "4mm" and mm.text(4) == "4mm"
        assert mm.code(4.0) == "svg.length(4.0, 'mm')"
        with pytest.raises(ValueError, match="in mm"):
            mm.check(svg.pt(4))
        degrees = Slider(0, 360, format="{:.0f}°")
        assert degrees.text(12.4) == "12°" and degrees.argument(5.0) == 5.0
        assert Slider(0, 9, units="items").text(3) == "3 items"

    def test_range_and_number(self) -> None:
        band = RangeSlider(0, 100)
        assert band.initial == (0.0, 100.0) and band.check([10, 20]) == (10.0, 20.0)
        assert band.text((10, 20)) == "10 – 20"
        with pytest.raises(ValueError, match="above"):
            band.check((30, 20))
        with pytest.raises(TypeError):
            band.check(5)
        assert RangeSlider(0, 10, integer=True).check((1, 2)) == (1, 2)
        count = Number(5, min=1, max=9)
        assert count.check(8) == 8 and count.initial == 5
        with pytest.raises(ValueError):
            count.check(10)
        with pytest.raises(ValueError, match="whole"):
            count.check(2.5)
        assert Number(0.5).check(2) == 2.0

    def test_choices(self) -> None:
        sizes = Dropdown({"S": 1, "M": 2})
        assert sizes.labels == ("S", "M") and sizes.values == (1, 2) and sizes.text(2) == "M"
        assert sizes.from_form(1) == 2
        for bad in (2, -1, True, "1"):
            with pytest.raises(ValueError):
                sizes.from_form(bad)
        with pytest.raises(ValueError, match="not one of"):
            sizes.check(3)
        assert Dropdown([1, True]).check(True) is True and Dropdown([1, True]).check(1) == 1
        assert Segmented(["a", "b"], value="b").starting_at("a").initial == "a"
        layers = MultiSelect(["grid", "guides"], value=["guides"])
        assert layers.initial == ("guides",) and layers.from_form([1, 0]) == ("grid", "guides")
        assert layers.text(()) == "none"
        with pytest.raises(TypeError):
            layers.check("grid")
        with pytest.raises(ValueError):
            layers.from_form(0)
        chips = Swatches(["tomato", "#0ea5e9"])
        assert chips.chips == ("#ff6347", "#0ea5e9") and chips.initial == "tomato"
        with pytest.raises(ValueError, match="colour"):
            Swatches(["tomato", "not a colour"])

    def test_toggles_colours_text(self) -> None:
        assert Toggle().initial is False and Toggle().text(True) == "on"
        with pytest.raises(TypeError):
            Checkbox().check(1)
        picker = ColorPicker("tomato")
        assert picker.initial == "#ff6347" and picker.check(svg.Color(0, 0, 1, 0.5)) == "#0000ff80"
        with pytest.raises(ValueError, match="colour"):
            picker.check("nope")
        assert Text("a").check("b") == "b" and Text().code("x") == "'x'"
        with pytest.raises(TypeError):
            Text().check(3)


class TestDeclaration:
    def test_decorator_and_defaults(self) -> None:
        @controls(hue=(0, 360), glow=False)
        def card(doc, hue=200, glow=True, other=1):
            return doc

        found = controls_of(card)
        assert list(found) == ["hue", "glow"]
        assert found["hue"].initial == 200 and found["glow"].initial is False
        assert found["hue"].label == "hue"
        assert list(controls_of(card, other=(0, 5))) == ["hue", "glow", "other"]

    def test_inferred_from_defaults(self) -> None:
        def ring(doc, size=40, color="#ff0000", note=None, weird=print):
            return doc

        assert {name: type(c) for name, c in controls_of(ring).items()} == {"size": IntSlider, "color": ColorPicker}
        assert controls_of(ring, infer=False) == {}

    def test_unknown_names(self) -> None:
        with pytest.raises(TypeError, match="no parameter radius"):
            controls(radius=(0, 1))(lambda doc: doc)
        with pytest.raises(TypeError, match="no parameter radius"):
            controls_of(lambda doc: doc, radius=(0, 1))
        assert "radius" in controls_of(lambda doc, **kw: doc, radius=(0, 1))
