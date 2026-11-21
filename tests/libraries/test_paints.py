from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg


class TestPatterns:
    def test_theme_role_by_default_and_color_on_request(self) -> None:
        themed = svg.patterns.stripes()[0]
        assert themed.classes == ["role-pattern"] and themed.get("fill") == "black"
        assert svg.patterns.stripes(color="red")[0].get("fill") == "red"
        assert svg.patterns.stripes(role=None)[0].classes == []

    def test_follows_the_document_theme(self) -> None:
        doc = svg.Document(20, 20, theme="dark")
        doc.rect(0, 0, 20, 20, fill=svg.patterns.dots())
        assert ".role-pattern {" in doc.to_string()

    def test_lands_in_defs(self) -> None:
        doc = svg.Document(20, 20)
        doc.rect(0, 0, 20, 20, fill=svg.patterns.checker())
        assert doc.root.defs()[0].tag == "pattern"

    def test_background_and_angle(self) -> None:
        tile = svg.patterns.hatch(angle=30, background="white")
        assert tile[0].get("fill") == "white" and tile.get("patternTransform") == "rotate(30)"

    def test_noise_is_deterministic(self) -> None:
        assert str(svg.patterns.noise(seed=5)) == str(svg.patterns.noise(seed=5))
        assert str(svg.patterns.noise(seed=5)) != str(svg.patterns.noise(seed=6))


class TestGradients:
    def test_oklch_samples_keep_ends_and_stay_vivid(self) -> None:
        paint = svg.gradients.blend("red", "blue")
        assert paint[0].get("stop-color").hex == "#ff0000" and paint[-1].get("stop-color").hex == "#0000ff"
        middle = paint[len(paint.children) // 2].get("stop-color")
        assert max(middle.r, middle.g, middle.b) > 0.5

    def test_theme_gradient_follows_the_current_theme(self) -> None:
        with svg.themes.get("dark"):
            dark = svg.gradients.theme()
        assert dark[0].get("stop-color") == svg.themes.get("dark").palette.primary

    def test_angle_sets_the_direction(self) -> None:
        down = svg.gradients.blend("red", "blue", angle=90)
        assert (down.get("x1"), down.get("y1"), down.get("x2"), down.get("y2")) == (0.5, 0.0, 0.5, 1.0)

    def test_mesh_rejects_extra_corners(self) -> None:
        with pytest.raises(ValueError, match="up to 4"):
            svg.gradients.mesh(*["red"] * 5)


class TestMarkers:
    @pytest.mark.parametrize("name", svg.markers.__all__)
    def test_sized_by_stroke_and_oriented(self, name: str) -> None:
        marker = getattr(svg.markers, name)(3)
        assert marker.get("orient") == "auto" and marker.get("markerWidth") == 3
        assert marker.get("markerUnits") is None

    def test_head_follows_the_theme(self) -> None:
        head = svg.markers.arrow()[0]
        assert head.classes == ["role-arrow-head"] and head.get("fill") == "black"
        doc = svg.Document(20, 20, theme="dark")
        doc.path("M0 0 L10 10", stroke="white", marker_end=svg.markers.arrow())
        assert ".role-arrow-head { fill:#e5e7eb" in doc.to_string()


class TestFilters:
    def test_drop_shadow_is_a_valid_graph(self) -> None:
        shadow = svg.filters.drop_shadow(3, 3, 2, "navy", 0.4, id="shadow")
        results = {p.get("result") for p in shadow.primitives if p.has("result")}
        inputs = ({p.get("in") for p in shadow.iter() if p.has("in")}
                  | {p.get("in2") for p in shadow.iter() if p.has("in2")})
        assert inputs <= results | {svg.StandardInput.SOURCE_ALPHA, svg.StandardInput.SOURCE_GRAPHIC}

    def test_shadow_color_follows_the_theme(self) -> None:
        doc = svg.Document(20, 20, theme="dark")
        doc.rect(0, 0, 10, 10, filter=svg.filters.drop_shadow())
        assert ".role-filter-shadow { flood-color:" in doc.to_string()

    def test_long_shadow_covers_its_length(self) -> None:
        offsets = [p for p in svg.filters.long_shadow(angle=0, length=10) if p.tag == "feOffset"]
        assert sum(p.get("dx") for p in offsets) == pytest.approx(10)

    def test_goo_bridges_nearby_shapes(self) -> None:
        doc = svg.Document(80, 40)
        with doc.group() as blobs:
            doc.circle(28, 20, 9, fill="teal")
            doc.circle(52, 20, 9, fill="teal")
        plain = np.asarray(doc.rasterize())
        blobs.filter = svg.filters.goo(8)
        gooey = np.asarray(doc.rasterize())
        assert plain[20, 40, 3] == 0 and gooey[20, 40, 3] > 0


def test_assigning_a_shortcut_name_sets_the_attribute() -> None:
    group = svg.group(svg.circle(0, 0, 1))
    group.filter = svg.filters.blur()
    group.clip_path = svg.ClipPath(svg.rect(0, 0, 1, 1))
    assert group.get("filter").element.tag == "filter" and group.get("clip-path").element.tag == "clipPath"
    assert callable(group.filter)
