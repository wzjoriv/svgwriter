"""
README gallery: run the examples and build the demos, and render their pictures to PNG (animated ones as GIF).
"""

from __future__ import annotations

import io
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

__all__ = ["DEMO_DIR", "DEMO_GALLERY", "GALLERY", "GALLERY_DIR", "DemoPicture", "Picture", "build_demos",
           "build_gallery"]

ROOT = Path(__file__).resolve().parents[2]
GALLERY_DIR = ROOT / "docs" / "_static" / "examples"
DEMO_DIR = ROOT / "docs" / "_static" / "demos"
DEMOS = ROOT / "demos"
SCALE = 2.0
SCENE_FPS = 12.0
SCENE_HOLD = 1.0


class Picture(NamedTuple):
    """One gallery picture: the example that makes it, the file it saves and how to render it.

    A picture with ``scenes`` is a GIF of those scene classes of the example played one after another.
    """

    example: str
    file: str = ""
    background: str | None = None
    padding: float = 0.0
    scenes: tuple[str, ...] = ()


GALLERY = {
    "basic_shapes": Picture("01_basic_shapes", "01_basic_shapes.svg"),
    "transforms": Picture("02_transforms_and_layout", "02_transforms_and_layout.svg"),
    "boolean_ops": Picture("03_paths_and_geometry", "03_boolean.svg"),
    "typography": Picture("04_typography", "04_typography.svg"),
    "filter_effects": Picture("05_paint_and_filters", "05_filters.svg"),
    "paths_and_markers": Picture("03_paths_and_geometry", "03_paths_pretty.svg"),
    "animation": Picture("09_animation", "09_animation.gif"),
    "math": Picture("08_math_and_diagrams", "08_math.svg"),
    "flowchart": Picture("08_math_and_diagrams", "08_flowchart.svg", background="white", padding=12),
    "lighting": Picture("05_paint_and_filters", "05_lighting.svg"),
    "scenes": Picture("13_scenes", scenes=("Title", "Bars")),
    "themes": Picture("14_themes", "14_themes.svg"),
    "powerpoint": Picture("15_powerpoint", "15_powerpoint.svg"),
    "text_effects": Picture("19_presets", "19_sentence.gif"),
    "goo": Picture("19_presets", "19_goo.gif"),
    "pattern_catalogue": Picture("19_presets", "19_patterns.svg"),
    "gradient_catalogue": Picture("19_presets", "19_gradients.svg"),
    "filter_catalogue": Picture("19_presets", "19_filters.svg"),
    "marker_catalogue": Picture("19_presets", "19_markers.svg", background="white"),
}


class DemoPicture(NamedTuple):
    """One demo tile: the demo folder, the output format and file that make it, and that format's options.

    The options replace the demo's own for the tile, so animations come out small enough for the README.
    """

    demo: str
    format: str
    file: str
    options: dict[str, float]


DEMO_GALLERY = {
    "playing-card": DemoPicture("playing-card", "png", "playing-card.png", {"scale": 1}),
    "calculator-kit": DemoPicture("calculator-kit", "png", "calculator-kit.png", {"scale": 1}),
    "text-effects": DemoPicture("text-effects", "gif", "text-effects.gif", {"fps": 8, "scale": 0.5}),
    "planets-explainer": DemoPicture("planets-explainer", "gif", "planets-explainer-Planets.gif",
                                     {"fps": 8, "scale": 0.375}),
    "blobs": DemoPicture("blobs", "gif", "blobs.gif", {"fps": 12, "scale": 0.75}),
    "poster": DemoPicture("poster", "png", "poster.png", {"dpi": 72}),
}


def build_demos(out: Path = DEMO_DIR) -> list[Path]:
    """Build each demo tile's output in a temporary copy of its project and copy it to *out* as ``<demo>.<ext>``.

    Parameters
    ----------
    out : Path, optional
        Destination folder. Defaults to ``docs/_static/demos``.

    Returns
    -------
    list of Path
        The files written, one per entry of :data:`DEMO_GALLERY`.
    """
    import tomlkit

    import svgwriter as svg

    out.mkdir(parents=True, exist_ok=True)
    written = []
    with tempfile.TemporaryDirectory(prefix="svgwriter-demos-") as work:
        for name, picture in DEMO_GALLERY.items():
            root = Path(work) / picture.demo
            if not root.exists():
                shutil.copytree(DEMOS / picture.demo, root, ignore=shutil.ignore_patterns("output", "__pycache__"))
            manifest = root / "svgwriter.toml"
            document = tomlkit.parse(manifest.read_text(encoding="utf-8"))
            document["outputs"][picture.format] = picture.options
            manifest.write_text(tomlkit.dumps(document), encoding="utf-8")
            built = {path.name: path for path in svg.Project.load(root).build([picture.format])}
            target = out / f"{name}{Path(picture.file).suffix}"
            shutil.copyfile(built[picture.file], target)
            written.append(target)
    return written


def build_gallery(out: Path = GALLERY_DIR, scale: float = SCALE) -> list[Path]:
    """Run each gallery example into a temporary folder and write its picture to *out*.

    Parameters
    ----------
    out : Path, optional
        Destination folder. Defaults to ``docs/_static/examples``.
    scale : float, optional
        Raster scale of the PNGs. Defaults to 2.

    Returns
    -------
    list of Path
        The files written: ``<name>.png``, or ``<name>.gif`` for an animated picture.
    """
    import svgwriter as svg

    out.mkdir(parents=True, exist_ok=True)
    written = []
    ran: set[str] = set()
    with tempfile.TemporaryDirectory(prefix="svgwriter-gallery-") as work:
        env = {**os.environ, "PYTHONPATH": str(ROOT)}
        for name, picture in GALLERY.items():
            if picture.scenes:
                written.append(_scenes_gif(picture, out / f"{name}.gif"))
                continue
            if picture.example not in ran:
                script = ROOT / "examples" / f"{picture.example}.py"
                subprocess.run([sys.executable, str(script)], cwd=work, env=env, check=True, capture_output=True)
                ran.add(picture.example)
            source = Path(work) / picture.file
            if source.suffix == ".gif":
                target = out / f"{name}.gif"
                shutil.copyfile(source, target)
            else:
                target = out / f"{name}.png"
                svg.Document.open(source).save(target, scale=scale, background=picture.background, padding=picture.padding)
            written.append(target)
        written.append(_readme_picture(out, Path(work), scale))
    return written


def _scenes_gif(picture: Picture, target: Path) -> Path:
    """Play *picture*'s scenes one after another, each held on its last frame, and save them as a GIF."""
    from PIL import Image

    namespace = runpy.run_path(str(ROOT / "examples" / f"{picture.example}.py"), run_name="gallery")
    frames = []
    for name in picture.scenes:
        scene = namespace[name]()
        clip = [(Image.open(io.BytesIO(frame.data)) if frame.png
                 else Image.frombytes("RGBA", (frame.width, frame.height), frame.data)).convert("RGB")
                for frame in scene.frames(fps=SCENE_FPS)]
        frames += clip + clip[-1:] * int(SCENE_FPS * SCENE_HOLD)
    frames[0].save(target, save_all=True, append_images=frames[1:], duration=round(1000 / SCENE_FPS), loop=0)
    return target


def _readme_picture(out: Path, work: Path, scale: float) -> Path:
    """Run the README's first Python block in *work* and save its ``doc`` as ``readme.png`` in *out*."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    code = text.split("```python\n", 1)[1].split("```", 1)[0]
    namespace: dict[str, object] = {}
    previous = Path.cwd()
    os.chdir(work)
    try:
        exec(compile(code, "README.md", "exec"), namespace)
    finally:
        os.chdir(previous)
    target = out / "readme.png"
    namespace["doc"].save(target, scale=scale)  # type: ignore[attr-defined]
    return target
