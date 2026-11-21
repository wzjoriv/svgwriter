from __future__ import annotations

import shutil
import struct
import subprocess
import zlib
from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter import video
from svgwriter.cli import main
from svgwriter.video import _ffmpeg
from svgwriter.video.frames import to_frame

FFMPEG = shutil.which("ffmpeg")
needs_ffmpeg = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg is not on PATH")
WIDTH, HEIGHT = 16, 12


def png(width: int, height: int, rgba: tuple[int, int, int, int]) -> bytes:
    """A solid-color PNG built with the standard library."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    row = b"\x00" + bytes(rgba) * width
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(row * height)) + chunk(b"IEND", b"")


class FakeArray:
    """Minimal stand-in for a NumPy RGBA array."""

    def __init__(self, width: int, height: int, value: int, dtype: str = "uint8", channels: int = 4) -> None:
        self.shape = (height, width, channels)
        self.dtype = dtype
        self._data = bytes([value]) * (width * height * channels)

    def tobytes(self) -> bytes:
        return self._data


def solid_png(document: svg.Document, seconds: float) -> bytes:
    """Renderer used by the CLI test through ``module:function``."""
    return png(WIDTH, HEIGHT, (int(255 * min(seconds, 1.0)), 0, 0, 255))


def gray_array(document: svg.Document, seconds: float) -> FakeArray:
    return FakeArray(WIDTH, HEIGHT, int(200 * min(seconds, 1.0)))


def _doc() -> svg.Document:
    doc = svg.Document(WIDTH, HEIGHT)
    doc.circle(8, 6, 3, fill="red")
    return doc


class TestFrames:
    def test_frame_times(self) -> None:
        assert video.frame_times(4, 1) == [0, 0.25, 0.5, 0.75]
        assert len(video.frame_times(30, 0.5)) == 15
        assert video.frame_times(10, 0.01) == [0]
        with pytest.raises(ValueError, match="fps"):
            video.frame_times(0, 1)
        with pytest.raises(ValueError, match="duration"):
            video.frame_times(1, 0)

    def test_png_frames(self) -> None:
        frame = to_frame(3, 0.1, png(5, 7, (0, 0, 0, 255)))
        assert (frame.index, frame.width, frame.height, frame.png) == (3, 5, 7, True)
        assert to_frame(0, 0, bytearray(png(2, 2, (1, 2, 3, 4)))).png

    def test_array_frames(self) -> None:
        frame = to_frame(0, 0, FakeArray(4, 3, 9))
        assert (frame.width, frame.height, frame.png, len(frame.data)) == (4, 3, False, 48)

    @pytest.mark.parametrize(
        ("data", "error", "match"),
        [
            (b"not a png", TypeError, "not a PNG"),
            (FakeArray(4, 3, 0, channels=3), ValueError, "shape"),
            (FakeArray(4, 3, 0, dtype="float32"), ValueError, "uint8"),
            ("text", TypeError, "expected PNG bytes or an RGBA array"),
        ],
    )
    def test_bad_frames(self, data: object, error: type[Exception], match: str) -> None:
        with pytest.raises(error, match=match):
            to_frame(0, 0, data)  # type: ignore[arg-type]


class TestRenderers:
    def test_resolve(self) -> None:
        assert video.resolve_renderer(solid_png) is solid_png
        assert callable(video.resolve_renderer("skia"))
        assert video.resolve_renderer("tests.video.test_video:gray_array") is gray_array
        with pytest.raises(ValueError, match="no renderer given"):
            video.resolve_renderer(None)
        with pytest.raises(ValueError, match="unknown renderer"):
            video.resolve_renderer("nope")
        with pytest.raises(TypeError, match="not callable"):
            video.resolve_renderer("tests.video.test_video:WIDTH")

    def test_register(self) -> None:
        @video.register_renderer("test-solid")
        def render(document: svg.Document, seconds: float) -> bytes:
            return solid_png(document, seconds)

        assert video.resolve_renderer("test-solid") is render
        assert svg.register_renderer is video.register_renderer
        video.unregister_renderer("test-solid")

    def test_iter_frames_and_update(self) -> None:
        seen: list[float] = []
        frames = list(video.iter_frames(_doc(), 4, 1, solid_png, update=lambda doc, t: seen.append(t)))
        assert [f.seconds for f in frames] == seen == [0, 0.25, 0.5, 0.75]

    def test_duration_from_smil(self) -> None:
        doc = _doc()
        assert video.animation_duration(doc) is None
        with pytest.raises(ValueError, match="duration"):
            list(video.iter_frames(doc, 4, None, solid_png))
        circle = doc.root.find(svg.Circle)
        assert circle is not None
        circle.append(svg.Animate(attribute_name="r", from_=3, to=5, dur=1.5, begin=0.5))
        circle.append(svg.Animate(attribute_name="cx", dur="500ms"))
        circle.append(svg.Animate(attribute_name="cy", dur="indefinite"))
        assert video.animation_duration(doc) == 2.0
        assert len(list(video.iter_frames(doc, 2, None, solid_png))) == 4


class TestFFmpegMissing:
    def test_no_op_error_before_rendering(self, tmp_path: Path) -> None:
        calls: list[float] = []

        def renderer(document: svg.Document, seconds: float) -> bytes:
            calls.append(seconds)
            return solid_png(document, seconds)

        target = tmp_path / "out.mp4"
        with pytest.raises(svg.FFmpegNotFoundError, match="Nothing was rendered"):
            _doc().render_animation(target, 10, 1, renderer, ffmpeg="definitely-not-ffmpeg-xyz")
        assert calls == [] and not target.exists()

    def test_output_arguments(self) -> None:
        assert "libx264" in _ffmpeg.output_args("a.MP4")
        assert any("palettegen" in arg for arg in _ffmpeg.output_args("a.gif"))
        assert _ffmpeg.output_args("a.mkv") == []

    def test_mixed_frame_sizes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        frames = [to_frame(0, 0, png(2, 2, (0, 0, 0, 255))), to_frame(1, 0.1, png(3, 2, (0, 0, 0, 255)))]
        checked = _ffmpeg._checked(iter(frames[1:]), frames[0])
        next(checked)
        with pytest.raises(ValueError, match="frame 1 is 3x2"):
            next(checked)

    def test_no_frames(self) -> None:
        with pytest.raises(ValueError, match="no frames"):
            _ffmpeg.encode([], "x.mp4", 10, executable="ffmpeg")


@needs_ffmpeg
class TestEncoding:
    @pytest.mark.parametrize("suffix", [".mp4", ".gif", ".webm"])
    def test_png_frames_encode(self, tmp_path: Path, suffix: str) -> None:
        target = tmp_path / f"anim{suffix}"
        written = _doc().render_animation(target, fps=8, duration=0.5, renderer=solid_png)
        assert written == target and target.stat().st_size > 0

    def test_png_path_writes_numbered_frames(self, tmp_path: Path) -> None:
        written = video.render_animation(_doc(), tmp_path / "intro.png", 4, 0.75, gray_array)
        assert written.name == "intro_%04d.png"
        assert sorted(p.name for p in tmp_path.glob("intro_*.png")) == ["intro_0000.png", "intro_0001.png", "intro_0002.png"]

    def test_rgba_frames_encode(self, tmp_path: Path) -> None:
        target = tmp_path / "gray.mp4"
        video.render_animation(_doc(), target, 5, 1, gray_array)
        assert target.stat().st_size > 0

    def test_ffmpeg_failure_is_reported(self, tmp_path: Path) -> None:
        with pytest.raises(video.FFmpegError, match="ffmpeg exited"):
            video.render_animation(_doc(), tmp_path / "missing-dir" / "x.mp4", 5, 0.4, solid_png)

    def test_renderer_error_stops_ffmpeg(self, tmp_path: Path) -> None:
        def broken(document: svg.Document, seconds: float) -> bytes:
            if seconds > 0:
                raise RuntimeError("boom")
            return solid_png(document, seconds)

        with pytest.raises(RuntimeError, match="boom"):
            video.render_animation(_doc(), tmp_path / "x.mp4", 5, 1, broken)

    def test_render_frame(self, tmp_path: Path) -> None:
        target = tmp_path / "skia.gif"
        doc = _doc()
        dot = doc.root.find(svg.Circle)
        assert dot is not None

        def grow(document: svg.Document, seconds: float) -> None:
            dot.r = 2 + 4 * seconds

        doc.render_animation(target, 6, 0.5, "skia", update=grow)
        probe = subprocess.run([FFMPEG or "ffmpeg", "-i", str(target)], capture_output=True, text=True)
        assert "gif" in probe.stderr


SCENE = '''
import svgwriter as svg

class Grow(svg.Scene):
    width, height, fps, duration = 16, 12, 4, 1.0
    renderer = "tests.video.test_video:solid_png"

    def build(self, doc):
        self.dot = doc.circle(8, 6, 3)

    def update(self, seconds):
        self.dot.r = 3 + seconds

class Fade(Grow):
    pass
'''


@pytest.fixture
def script(tmp_path: Path) -> Path:
    path = tmp_path / "scenes.py"
    path.write_text(SCENE, encoding="utf-8")
    return path


class TestAnimateCommand:
    def test_list(self, script: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["animate", str(script), "--list"]) == 0
        assert capsys.readouterr().out.split() == ["Grow", "Fade"]
        assert main(["animate", f"{script}:Fade", "--list"]) == 0
        assert capsys.readouterr().out.split() == ["Fade"]

    def test_bad_scene(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        empty = tmp_path / "empty.py"
        empty.write_text("x = 1\n", encoding="utf-8")
        assert main(["animate", str(empty)]) == 1
        assert "defines no svgwriter.Scene" in capsys.readouterr().err

    def test_out_needs_one_scene(self, script: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["animate", str(script), "-o", "x.gif"]) == 1
        assert "2 scenes" in capsys.readouterr().err

    def test_missing_ffmpeg(self, script: Path, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["animate", str(script), "Grow", "--ffmpeg", "no-such-ffmpeg-xyz"])
        assert code == 1 and "was not found" in capsys.readouterr().err

    @needs_ffmpeg
    def test_animate_every_scene(self, script: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                 capsys: pytest.CaptureFixture[str]) -> None:
        monkeypatch.chdir(tmp_path)
        assert main(["animate", str(script), "--format", "gif", "--fps", "6"]) == 0
        assert capsys.readouterr().out.split() == ["Grow.gif", "Fade.gif"]
        assert (tmp_path / "Grow.gif").stat().st_size > 0 and (tmp_path / "Fade.gif").stat().st_size > 0

    @needs_ffmpeg
    def test_animate_named_to_file(self, script: Path, tmp_path: Path) -> None:
        target = tmp_path / "out.gif"
        assert main(["animate", str(script), "Fade", "--out", str(target)]) == 0
        assert target.stat().st_size > 0


class TestRenderAndOutlineCommands:
    def test_render(self, script: Path, tmp_path: Path) -> None:
        target = tmp_path / "frame.png"
        assert main(["render", str(script), "Grow", "-o", str(target), "--at", "0.5", "--scale", "2", "--background", "white"]) == 0
        assert target.read_bytes().startswith(b"\x89PNG")

    def test_render_every_scene_and_svg(self, script: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert main(["render", str(script)]) == 0
        assert (tmp_path / "Grow.png").exists() and (tmp_path / "Fade.png").exists()
        _doc().save(tmp_path / "pic.svg")
        assert main(["render", "pic.svg"]) == 0
        assert (tmp_path / "pic.png").read_bytes().startswith(b"\x89PNG")

    def test_render_unknown_name(self, script: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["render", str(script), "Nope"]) == 1
        assert "'Nope'" in capsys.readouterr().err

    def test_outline(self, tmp_path: Path) -> None:
        target = tmp_path / "hi.svg"
        assert main(["outline", "Hi", "--size", "20", "-o", str(target)]) == 0
        doc = svg.Document.open(target)
        path = doc.root.find(svg.Path)
        assert path is not None and path.bounds().x >= 3.9


def test_scene_at_combines_behaviors_update_and_smil() -> None:
    class Mixed(svg.Scene):
        width, height = 20, 20

        def build(self, doc):
            self.box = doc.rect(0, 0, 1, 1)
            self.dot = doc.circle(0, 5, 1)
            self.dot.append(svg.Animate(attribute_name="cx", from_=0, to=10, dur=2))
            self.spun = self.attach(doc.rect(5, 5, 2, 2), lambda element, seconds: element.set("x", 5 + seconds))

        def update(self, seconds):
            self.box.width = 1 + seconds

    moment = Mixed().at(1)
    box, dot, spun = moment.root[-3:]
    assert (box.get("width"), float(dot.get("cx")), spun.get("x")) == (2, 5.0, 6)
