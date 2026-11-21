from __future__ import annotations

import pytest

import svgwriter as svg


def bob(motion: svg.Motion, *, height: float = 8.0, dur: float = 1.0, begin: float = 0.0) -> svg.Motion:
    motion.move_by(0, -height, dur / 2, begin=begin)
    return motion.move_by(0, height, dur / 2, begin=begin + dur / 2)


@pytest.fixture
def registered():
    assert svg.animation(bob) is bob
    yield "bob"
    svg.unregister_animation("bob")


class TestAnimationDecorator:
    def test_apply_without_registering(self) -> None:
        dot = svg.circle(0, 0, 2)
        motion = dot.animate.apply(bob, height=4, begin=1).fade_in()
        assert isinstance(motion, svg.Motion) and motion.element is dot
        assert [child.tag for child in dot.children] == ["animateTransform", "animateTransform", "animate"]
        assert dot.children[1].get("begin") == "1.5s"

    def test_none_return_still_chains(self) -> None:
        def quiet(motion: svg.Motion, *, dx: float = 1.0) -> None:
            motion.move_by(dx, 0)

        dot = svg.circle(0, 0, 2)
        assert dot.animate.apply(quiet).element is dot

    def test_by_name(self, registered: str) -> None:
        dot = svg.circle(0, 0, 2)
        assert dot.animate.bob(height=4).element is dot and len(dot.children) == 2
        assert "bob" in svg.ANIMATIONS and "bob" in dir(dot.animate)
        assert dot.animate.bob.__name__ == "bob"

    def test_named_decorator(self) -> None:
        @svg.animation(name="hop")
        def jump(motion: svg.Motion, *, height: float = 2.0) -> svg.Motion:
            return motion.move_by(0, -height)

        try:
            assert "hop" in svg.ANIMATIONS and callable(jump)
            assert svg.rect().animate.hop().element.children[0].tag == "animateTransform"
        finally:
            svg.unregister_animation("hop")

    def test_stagger_uses_user_presets(self, registered: str) -> None:
        group = svg.Group()
        group += [svg.circle(0, 0, 1), svg.circle(5, 0, 1)]
        group.animate.stagger("bob", step=0.5, height=2)
        assert group.children[1].children[0].get("begin") == "0.5s"

    def test_snapshot_plays_it(self) -> None:
        doc = svg.Document(20, 20)
        doc.circle(10, 10, 2).animate.apply(bob, height=6)
        assert doc.at(0.5).root.to_string() != doc.at(0).root.to_string()

    @pytest.mark.parametrize("function", [
        lambda: None,
        lambda motion, height=2: motion,
        lambda motion, *, height: motion,
        lambda motion, *more: motion,
    ])
    def test_signature_checked(self, function) -> None:
        with pytest.raises(TypeError, match="animation 'bad'"):
            svg.animation(name="bad")(function)
        assert "bad" not in svg.ANIMATIONS

    def test_var_keyword_allowed(self) -> None:
        svg.animation(name="forward")(lambda motion, **timing: motion.fade_in(**timing))
        svg.unregister_animation("forward")

    def test_clash_twice_and_bad_names(self, registered: str) -> None:
        with pytest.raises(ValueError, match="built-in"):
            svg.animation(name="spin")(bob)
        with pytest.raises(ValueError, match="already registered"):
            svg.animation(bob)
        for name in ("two words", "_hidden", "3d"):
            with pytest.raises(ValueError, match="identifiers"):
                svg.animation(name=name)(bob)

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
