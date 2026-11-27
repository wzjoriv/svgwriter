from pathlib import Path

import pytest

STATIC = Path(__file__).parents[2] / "docs" / "_static"


@pytest.mark.parametrize("path", sorted(STATIC.rglob("*.gif")), ids=lambda path: path.name)
def test_committed_gifs_decode(path: Path) -> None:
    image = pytest.importorskip("PIL.Image")
    sequence = pytest.importorskip("PIL.ImageSequence")
    with image.open(path) as gif:
        frames = [frame.convert("RGBA").size for frame in sequence.Iterator(gif)]
    assert frames and len(set(frames)) == 1
