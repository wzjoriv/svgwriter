from __future__ import annotations

import re
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BLOCK = re.compile(r"```python\n(.*?)```", re.S)
PAGES = sorted(
    page for page in [*(ROOT / "docs").rglob("*.md"), ROOT / "README.md"]
    if "_build" not in page.parts and BLOCK.search(page.read_text(encoding="utf-8"))
)


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_python_blocks_run(page: Path, tmp_path, monkeypatch) -> None:
    blocks = BLOCK.findall(page.read_text(encoding="utf-8"))
    monkeypatch.chdir(tmp_path)
    sample = ROOT / "tests" / "export" / "data" / "sample.excalidraw"
    (tmp_path / "sketch.excalidraw").write_bytes(sample.read_bytes())
    namespace: dict[str, object] = {"__name__": "__docs__"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for index, block in enumerate(blocks):
            try:
                exec(compile(block, f"{page.name}[{index}]", "exec"), namespace)
            except Exception as exc:
                raise AssertionError(f"block {index} of {page.name} failed: {exc!r}\n{block}") from exc
