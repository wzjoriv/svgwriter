from __future__ import annotations

import pytest

import svgwriter as svg


def bob(motion: svg.Motion, *, height: float = 8.0, dur: float = 1.0, begin: float = 0.0) -> svg.Motion:
    motion.move_by(0, -height, dur / 2, begin=begin)
    return motion.move_by(0, height, dur / 2, begin=begin + dur / 2)


@pytest.fixture
def registered():
    assert svg.preset.animation(bob) is bob
    yield "bob"
    svg.preset.animation.unregister("bob")


class TestAnimationPreset:
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
        assert "bob" in svg.preset.animation.list() and "bob" in dir(dot.animate)
        assert dot.animate.bob.__name__ == "bob" and svg.preset.animation.get("bob") is bob

    def test_builtins_are_listed(self) -> None:
        names = svg.preset.animation.list()
        assert {"fade_in", "spin", "bounce", "morph"} <= set(names)
        assert not {"apply", "stagger"} & set(names)

    def test_named_decorator(self) -> None:
        @svg.preset.animation(name="hop")
        def jump(motion: svg.Motion, *, height: float = 2.0) -> svg.Motion:
            return motion.move_by(0, -height)

        try:
            assert callable(jump)
            assert svg.rect(0, 0, 1, 1).animate.hop().element.children[0].tag == "animateTransform"
        finally:
            svg.preset.animation.unregister("hop")

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
            svg.preset.animation(name="bad")(function)
        assert "bad" not in svg.preset.animation.list()

    def test_var_keyword_allowed(self) -> None:
        svg.preset.animation(name="forward")(lambda motion, **timing: motion.fade_in(**timing))
        svg.preset.animation.unregister("forward")

    def test_taken_names_name_their_owner(self, registered: str) -> None:
        with pytest.raises(ValueError, match=r"'spin' is already registered by svgwriter\..*spin \(built in\)"):
            svg.preset.animation(name="spin")(bob)
        with pytest.raises(ValueError, match=r"'bob' is already registered by .*bob; pass replace=True"):
            svg.preset.animation(bob)
        for name in ("two words", "_hidden", "3d", "apply", "stagger"):
            with pytest.raises(ValueError, match="identifiers"):
                svg.preset.animation(name=name)(bob)

    def test_replace_user_and_builtin(self, registered: str) -> None:
        def taller(motion: svg.Motion, *, height: float = 20.0) -> svg.Motion:
            return bob(motion, height=height)

        svg.preset.animation(name="bob", replace=True)(taller)
        assert svg.preset.animation.get("bob") is taller

        def slow_spin(motion: svg.Motion, *, dur: float = 9.0) -> svg.Motion:
            return svg.Motion.spin(motion, dur)

        svg.preset.animation(name="spin", replace=True)(slow_spin)
        try:
            dot = svg.circle(0, 0, 2)
            dot.animate.spin()
            assert dot.children[0].get("dur") == "9s"
        finally:
            svg.preset.animation.unregister("spin")
        dot = svg.circle(0, 0, 2)
        dot.animate.spin()
        assert dot.children[0].get("dur") != "9s"

    def test_unknown_name_suggests(self, registered: str) -> None:
        motion = svg.rect(0, 0, 1, 1).animate
        with pytest.raises(AttributeError, match="did you mean 'bob'"):
            motion.bobb()
        with pytest.raises(AttributeError, match="did you mean 'fade_in'"):
            motion.fadein()
        assert not hasattr(motion, "nothing_like_it")

    def test_unregister_unknown(self) -> None:
        with pytest.raises(KeyError, match="unknown animation"):
            svg.preset.animation.unregister("never")
        with pytest.raises(KeyError, match="built in"):
            svg.preset.animation.unregister("fade_in")
