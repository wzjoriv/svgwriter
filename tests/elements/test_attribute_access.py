from __future__ import annotations

import pytest

import svgwriter as svg


class TestAttributeAccess:
    def test_read_write_any_presentation_attribute(self) -> None:
        r = svg.Rect(0, 0, 1, 1)
        r.stroke_linejoin = "round"
        r.fill_opacity = 0.5
        assert r.stroke_linejoin == "round" and r.get("fill-opacity") == 0.5
        assert 'stroke-linejoin="round"' in str(r)

    def test_unset_known_attribute_reads_none(self) -> None:
        assert svg.Rect().marker_end is None and svg.Circle().clip_rule is None

    def test_camel_case_and_prefixed(self) -> None:
        g = svg.LinearGradient()
        g.spread_method = "reflect"
        u = svg.Use()
        u.xlink_title = "t"
        assert g.get("spreadMethod") == "reflect" and u.get("xlink:title") == "t"

    def test_reserved_words_use_trailing_underscore(self) -> None:
        blur = svg.FeGaussianBlur()
        blur.in_ = "SourceGraphic"
        assert blur.get("in") == "SourceGraphic" and blur.in_ == "SourceGraphic"

    def test_method_name_clash_uses_underscore(self) -> None:
        t = svg.Text("Hi", rotate=[10, 20])
        assert callable(t.rotate) and t.rotate_ is not None
        t.rotate_ = 5
        assert t.get("rotate") == 5

    def test_none_removes_and_del(self) -> None:
        r = svg.Rect(fill="red")
        r.fill = None
        assert not r.has("fill")
        r.stroke_dashoffset = 3
        del r.stroke_dashoffset
        assert not r.has("stroke-dashoffset")

    def test_typo_suggests(self) -> None:
        with pytest.raises(AttributeError, match="did you mean 'stroke_width'"):
            svg.Rect().strok_width = 2
        with pytest.raises(AttributeError, match="no attribute"):
            _ = svg.Rect().strok_width

    def test_unlisted_attribute_already_present_is_accessible(self) -> None:
        r = svg.Rect()
        r.set("data-x", 1)
        assert r.data_x == 1

    def test_web_only_rejected(self) -> None:
        with pytest.raises((AttributeError, ValueError)):
            svg.Rect().onclick = "x"


class TestKeywordChecking:
    def test_typo_in_constructor_suggests(self) -> None:
        with pytest.raises(TypeError, match="did you mean 'stroke_width'"):
            svg.Rect(strok_width=2)
        with pytest.raises(AttributeError):
            svg.circle(fil="red")

    def test_custom_attributes_stay_possible(self) -> None:
        r = svg.Rect(data_role="x", aria_label="box", attrs={"my-attr": 1})
        assert r.get("data-role") == "x" and r.get("aria-label") == "box" and r.get("my-attr") == 1

    def test_shortcuts_check_too(self) -> None:
        with pytest.raises(TypeError, match="did you mean 'opacity'"):
            svg.Document(10, 10).rect(0, 0, 1, 1, opactiy=0.5)


class TestReferences:
    def test_url_and_iri_point_at_the_element(self) -> None:
        g = svg.LinearGradient(id="g")
        assert g.url.svg_value() == "url(#g)" and g.iri.svg_value() == "#g"
        assert svg.Rect().url.svg_value().startswith("url(#rect")

    def test_href_reads_an_xlink_elements_own_link(self) -> None:
        track = svg.Path("M0 0 L1 1", id="track")
        mpath = svg.MPath(track)
        assert str(mpath.href) == "#track" and mpath.id is None
        use = svg.Use()
        use.href = track
        assert str(use.get("xlink:href")) == "#track"
        assert svg.Image("photo.png").href == "photo.png"


class TestDeterministicIds:
    @staticmethod
    def build() -> svg.Document:
        doc = svg.Document(10, 10)
        doc.rect(0, 0, 5, 5, fill=svg.LinearGradient.horizontal("red", "blue"))
        doc.circle(5, 5, 2).clip(svg.circle(5, 5, 1))
        return doc

    def test_same_document_twice_in_one_process_is_identical(self) -> None:
        first, second = self.build().to_string(), self.build().to_string()
        assert first == second and 'id="linearGradient1"' in first and 'id="clipPath1"' in first

    def test_references_follow_renames(self) -> None:
        doc = self.build()
        gradient = doc.defs[0]
        gradient.id = "sky"
        assert 'fill="url(#sky)"' in doc.to_string()

    def test_clone_added_to_the_same_document_gets_a_new_id(self) -> None:
        doc = self.build()
        copy = doc.defs[0].clone()
        doc.defs += copy
        assert copy.id != doc.defs[0].id and len({e.id for e in doc.defs}) == len(doc.defs)

    def test_explicit_ids_are_kept(self) -> None:
        doc = svg.Document(10, 10)
        doc.rect(0, 0, 1, 1, fill=svg.LinearGradient(id="mine"))
        assert 'id="mine"' in doc.to_string()
