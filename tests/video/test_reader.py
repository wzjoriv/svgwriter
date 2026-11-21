import shutil

import numpy as np
import pytest

import svgwriter as svg
from svgwriter.motion.video import Video

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


@pytest.fixture(scope="module")
def clip(tmp_path_factory):
    doc = svg.Document(32, 24)
    ball = doc.circle(4, 12, 4, fill="red")
    ball.append(svg.Animate(attribute_name="cx", from_=4, to=28, dur=1, fill="freeze"))
    path = tmp_path_factory.mktemp("video") / "ball.mp4"
    doc.render_animation(path, fps=10, duration=1, renderer="skia")
    return Video(path)


def _ball_x(frame):
    return int(np.argmin(frame[12, :, 1]))


def test_metadata_and_length(clip):
    assert (clip.width, clip.height, clip.fps, len(clip)) == (32, 24, 10, 10)


def test_frames_follow_the_animation(clip):
    assert _ball_x(clip.frame(0)) < 8 and _ball_x(clip.frame(-1)) > 20
    assert clip[3].shape == (24, 32) and clip.at(0.5).tag == "image"


def test_iteration_streams_every_frame(clip):
    frames = list(clip)
    assert len(frames) == 10 and frames[0].shape == (24, 32, 4)


def test_out_of_range(clip):
    with pytest.raises(IndexError):
        clip.frame(10)
