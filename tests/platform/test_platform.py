from __future__ import annotations

import json

import pytest

import svgwriter as svg
from svgwriter._internal import _platform
from svgwriter._internal._platform import (
    System,
    distro_system,
    install_hint,
    parse_os_release,
    system_packages_hint,
)
from svgwriter.tools.cli import main

RELEASES = {
    "debian": ('ID=debian\nPRETTY_NAME="Debian GNU/Linux 13 (trixie)"\n', "apt", "sudo apt install"),
    "ubuntu": ('ID=ubuntu\nID_LIKE=debian\nPRETTY_NAME="Ubuntu 24.04 LTS"\n', "apt", "sudo apt install"),
    "fedora": ('ID=fedora\nPRETTY_NAME="Fedora Linux 41"\n', "dnf", "sudo dnf install"),
    "rocky": ('ID="rocky"\nID_LIKE="rhel centos fedora"\n', "dnf", "sudo dnf install"),
    "arch": ("ID=arch\nPRETTY_NAME=\"Arch Linux\"\n", "pacman", "sudo pacman -S"),
    "tumbleweed": ('ID="opensuse-tumbleweed"\nID_LIKE="opensuse suse"\n', "zypper", "sudo zypper install"),
}

PACKAGES = {
    "apt": {"ffmpeg": "ffmpeg", "graphviz": "graphviz", "latex": "texlive-latex-extra dvisvgm"},
    "dnf": {"ffmpeg": "ffmpeg-free", "graphviz": "graphviz", "latex": "texlive-dvisvgm"},
    "pacman": {"ffmpeg": "ffmpeg", "graphviz": "graphviz", "latex": "texlive-binextra"},
    "zypper": {"ffmpeg": "ffmpeg-7", "graphviz": "graphviz", "latex": "texlive-dvisvgm"},
}


@pytest.mark.parametrize("distro", sorted(RELEASES))
def test_distro_family_and_hints(distro: str) -> None:
    text, manager, command = RELEASES[distro]
    found = distro_system(parse_os_release(text))
    assert found.os == "linux" and found.manager == manager and found.unsupported is None
    for name, package in PACKAGES[manager].items():
        hint = install_hint(name, found)
        assert hint.startswith(command) and package in hint
    assert system_packages_hint(found).startswith(command)
    assert "fonts" in system_packages_hint(found)


def test_alpine_is_unsupported_and_unknown_distros_point_to_the_download_page() -> None:
    alpine = distro_system(parse_os_release("ID=alpine\n"))
    assert alpine.unsupported and "musl" in alpine.unsupported and alpine.manager is None
    assert install_hint("ffmpeg", alpine).startswith("see https://")
    assert system_packages_hint(alpine) is None


@pytest.mark.parametrize(("family", "manager", "expected"), [
    ("windows", "winget", "winget install Gyan.FFmpeg"),
    ("macos", "brew", "brew install ffmpeg"),
])
def test_desktop_hints(family: str, manager: str, expected: str) -> None:
    assert install_hint("ffmpeg", System(family, None, family, manager, None)) == expected


def test_pyodide_has_no_programs_and_python_hints_use_pip() -> None:
    pyodide = System("pyodide", None, "Pyodide", None, None)
    assert install_hint("graphviz", pyodide).startswith("not available in Pyodide")
    assert install_hint("ipywidgets", pyodide) == "pip install 'pysvgwriter[widget]'"


def test_mermaid_hint_installs_node_then_the_cli() -> None:
    hint = install_hint("mermaid", System("linux", "fedora", "Fedora", "dnf", None))
    assert hint == "sudo dnf install nodejs npm, then npm install -g @mermaid-js/mermaid-cli"


def test_capabilities_summary() -> None:
    found = svg.capabilities()
    assert found is svg.capabilities()
    assert found["skia"].available and found["skia"].version
    assert {"harfbuzz", "lcms2", "ffmpeg", "latex", "mermaid", "graphviz", "inkscape", "ipywidgets",
            "fonttools"} <= set(found)
    for entry in found.values():
        assert entry.hint and entry.kind in ("python", "tool")
        assert entry.available == (entry.name not in found.missing())


def test_executables_follow_the_environment(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("SVGWRITER_DOT", str(tmp_path))
    assert _platform.find_executable("dot") == str(tmp_path) and _platform.available("graphviz")


def test_missing_names_the_capability_and_the_hint() -> None:
    error = _platform.missing("graphviz", "running `dot`", RuntimeError)
    assert isinstance(error, RuntimeError)
    assert "graphviz" in str(error) and install_hint("graphviz") in str(error)


def test_doctor_table_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["doctor"]) == 0
    table = capsys.readouterr().out
    assert "skia" in table and "fonts:" in table and "sans-serif ->" in table
    assert main(["doctor", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["capabilities"]["skia"]["available"] is True
    assert report["fonts"]["families"] > 0 and set(report["fonts"]["resolved"]) == {
        "sans-serif", "serif", "monospace", "emoji"}
    assert report["system"]["os"] == _platform.system().os


def test_cache_and_temp_dirs() -> None:
    assert _platform.temp_dir().is_dir()
    assert "svgwriter" in str(_platform.cache_dir())
