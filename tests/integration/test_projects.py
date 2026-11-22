"""Every project preset with a layout card, a typeface from assets/fonts and theme expressions; rebuilt after edits."""

import pytest

import svgwriter as svg
from svgwriter.tools.project import presets
from tests.ops.test_typeface import _font

CARD = '''
from pathlib import Path as _Path

_FACE = svg.Typeface.from_files(*sorted(_Path("assets/fonts").glob("*.ttf")))


def _card(doc: svg.Document, label: str = "Card") -> svg.VStack:
    text = svg.text(label, font_family=_FACE, font_size=12).as_role("text")
    card = svg.VStack(text, svg.rect(0, 0, 30, 6).as_role("edge"), gap=4, padding=6, background="surface")
    doc += card
    return card

'''
HOOKS = {
    "blank": ('    box = doc.root.get("viewBox")\n', '    box = doc.root.get("viewBox")\n    _card(doc)\n'),
    "poster": ('    box = doc.root.get("viewBox")\n', '    box = doc.root.get("viewBox")\n    _card(doc)\n'),
    "slides": ('    doc.text("Thank you"', '    _card(doc)\n    doc.text("Thank you"'),
    "animation": ("        self.bar =", "        _card(doc)\n        self.bar ="),
}
PALETTE = ('[palette]\nsurface = "=mix({palette.primary}, {palette.background}, 0.85)"\n'
           'edge_color = "=darken({palette.accent}, 0.2)"\n')
ROLES = '\n[roles.edge]\nfill = "{palette.edge_color}"\nstroke = "none"\n'


def make(tmp_path, preset):
    project = svg.Project.new(tmp_path / preset, preset)
    fonts = project.root / "assets" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    (fonts / "Card.ttf").write_bytes(_font("SvgwProjectFace"))
    theme = project.root / "theme.toml"
    text = theme.read_text(encoding="utf-8")
    text = text.replace("[palette]\n", PALETTE, 1) if "[palette]" in text else text + "\n" + PALETTE
    theme.write_text(text + ROLES, encoding="utf-8")
    main = project.root / "main.py"
    source = main.read_text(encoding="utf-8").replace("# %%\nif __name__", CARD + "\n# %%\nif __name__", 1)
    old, new = HOOKS[preset]
    main.write_text(source.replace(old, new, 1), encoding="utf-8")
    return svg.Project.load(project.root)


def test_every_preset_is_covered():
    assert set(HOOKS) == set(presets)


@pytest.mark.parametrize("preset", sorted(HOOKS))
def test_preset_builds_with_layout_font_and_theme_expressions(tmp_path, preset):
    if preset == "slides":
        pytest.importorskip("pptx")
    project = make(tmp_path, preset)
    outputs = project.build()
    assert outputs and all(path.stat().st_size for path in outputs)
    vector = [path for path in outputs if path.suffix == ".svg"]
    if vector:
        text = vector[0].read_text(encoding="utf-8")
        assert ".role-surface" in text and ".role-edge" in text and "SvgwProjectFace" in text
        main = project.root / "main.py"
        main.write_text(main.read_text(encoding="utf-8").replace('label: str = "Card"', 'label: str = "Edited"'),
                        encoding="utf-8")
        project.build()
        assert ">Edited<" in vector[0].read_text(encoding="utf-8")
