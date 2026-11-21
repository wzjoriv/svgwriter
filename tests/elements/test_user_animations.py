from __future__ import annotations

import pytest

import svgwriter as svg


def bob(motion: svg.Motion, height: float = 8.0, dur: float = 1.0, *, begin: float = 0.0) -> None:
    motion.move_by(0, -height, dur / 2, begin=begin)
    motion.move_by(0, height, dur / 2, begin=begin + dur / 2)


@pytest.fixture
def registered():
    svg.register_animation("bob", bob)
    yield "bob"
    svg.unregister_animation("bob")


class TestRegisterAnimation:
    def test_call_and_chain(self, registered: str) -> None:
        dot = svg.circle(0, 0, 2)
        motion = dot.animate.bob(height=4, begin=1).fade_in()
        assert isinstance(motion, svg.Motion) and motion.element is dot
        tags = [child.tag for child in dot.children]
        assert tags == ["animateTransform", "animateTransform", "animate"]
        assert dot.children[1].get("begin") == "1.5s"

    def test_listed_and_documented(self, registered: str) -> None:
        assert "bob" in svg.ANIMATIONS and "bob" in dir(svg.rect().animate)
        assert svg.rect().animate.bob.__name__ == "bob"

    def test_stagger_uses_user_presets(self, registered: str) -> None:
        group = svg.Group()
        group += [svg.circle(0, 0, 1), svg.circle(5, 0, 1)]
        group.animate.stagger("bob", step=0.5, height=2)
        assert group.children[1].children[0].get("begin") == "0.5s"

    def test_snapshot_plays_it(self, registered: str) -> None:
        doc = svg.Document(20, 20)
        doc.circle(10, 10, 2).animate.bob(height=6)
        assert doc.at(0.5).root.to_string() != doc.at(0).root.to_string()

    def test_clash_with_builtin(self) -> None:
        with pytest.raises(ValueError, match="built-in"):
            svg.register_animation("spin", bob)

    def test_twice_and_bad_names(self, registered: str) -> None:
        with pytest.raises(ValueError, match="already registered"):
            svg.register_animation("bob", bob)
        for name in ("two words", "_hidden", "3d"):
            with pytest.raises(ValueError, match="identifiers"):
                svg.register_animation(name, bob)

    def test_unknown_name_suggests(self, registered: str) -> None:
        motion = svg.rect().animate
        with pytest.raises(AttributeError, match="did you mean 'bob'"):
            motion.bobb()
        with pytest.raises(AttributeError, match="did you mean 'fade_in'"):
            motion.fadein()
        assert not hasattr(motion, "nothing_like_it")

    def test_unregister_unknown(self) -> None:
        with pytest.raises(KeyError):
            svg.unregister_animation("never")
