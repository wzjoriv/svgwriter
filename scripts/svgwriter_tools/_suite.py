"""Downloading the W3C SVG 1.1 SE test suite."""

from __future__ import annotations

import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path

SUITE_URL = "https://www.w3.org/Graphics/SVG/Test/20110816/archives/W3C_SVG_11_TestSuite.tar.gz"
SUITE_DIR = Path("build/conformance/suite")
TIMEOUT = 120
KEEP = ("svg/", "png/", "images/", "resources/")


def fetch(url: str, target: Path) -> None:
    """Download *url* and unpack its ``svg``, ``png``, ``images`` and ``resources`` folders into *target*."""
    with tempfile.TemporaryDirectory() as tmp:
        archive_path = Path(tmp) / "suite.tar.gz"
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response, archive_path.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as archive:
            members = [m for m in archive.getmembers()
                       if m.isfile() and any(m.name.lstrip("./").startswith(k) for k in KEEP)]
            archive.extractall(target, members=members, filter="data")
