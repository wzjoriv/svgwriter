"""
The operating system, its Linux distribution and package manager, browser, temp and cache folders.
"""

from __future__ import annotations

import os
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ._constants import (
    CACHE_NAME,
    DISTRO_FAMILIES,
    LINUX,
    MACOS,
    MANAGER_OF,
    OS_RELEASE,
    PYODIDE,
    UNSUPPORTED_DISTROS,
    WINDOWS,
)

__all__ = ["System", "cache_dir", "distro_system", "open_browser", "parse_os_release", "system", "temp_dir"]


@dataclass(frozen=True)
class System:
    """The operating system svgwriter runs on.

    Attributes
    ----------
    os : {"windows", "macos", "linux", "pyodide"}
        The operating system family; Emscripten builds such as Pyodide are ``"pyodide"``.
    distro : str or None
        The Linux distribution ``ID`` from ``/etc/os-release`` (``"fedora"``), else None.
    name : str
        A readable name: ``PRETTY_NAME`` on Linux, else the OS family and release.
    manager : str or None
        The package manager for install hints (``apt``, ``dnf``, ``pacman``, ``zypper``, ``brew``,
        ``winget``), or None when unknown.
    unsupported : str or None
        Why this system cannot run svgwriter, or None.

    Examples
    --------
    >>> from svgwriter._internal._platform import System
    >>> System("linux", "fedora", "Fedora Linux 41", "dnf", None).manager
    'dnf'
    """

    os: str
    distro: str | None
    name: str
    manager: str | None
    unsupported: str | None


def parse_os_release(text: str) -> dict[str, str]:
    """The ``KEY=value`` pairs of an ``os-release`` file, quotes removed.

    Parameters
    ----------
    text : str
        The file's contents.

    Returns
    -------
    dict of str to str
        Each key and its unquoted value.

    Examples
    --------
    >>> from svgwriter._internal._platform import parse_os_release
    >>> parse_os_release('ID=fedora\\nPRETTY_NAME="Fedora Linux 41"\\n')
    {'ID': 'fedora', 'PRETTY_NAME': 'Fedora Linux 41'}
    """
    pairs = {}
    for line in text.splitlines():
        key, equals, value = line.strip().partition("=")
        if equals and not key.startswith("#"):
            pairs[key] = value.strip().strip("'\"")
    return pairs


def distro_system(release: dict[str, str]) -> System:
    """The Linux :class:`System` described by parsed ``os-release`` fields.

    Parameters
    ----------
    release : dict of str to str
        Output of :func:`parse_os_release`.

    Returns
    -------
    System
        Its distribution, package manager (from ``ID``, then ``ID_LIKE``) and support status.

    Examples
    --------
    >>> from svgwriter._internal._platform._system import distro_system
    >>> distro_system({"ID": "linuxmint", "ID_LIKE": "ubuntu debian"}).manager
    'apt'
    """
    distro = release.get("ID", "").lower() or None
    words = [word.lower() for word in (release.get("ID", ""), *release.get("ID_LIKE", "").split()) if word]
    manager = next((DISTRO_FAMILIES[word] for word in words if word in DISTRO_FAMILIES), None)
    unsupported = next((UNSUPPORTED_DISTROS[word] for word in words if word in UNSUPPORTED_DISTROS), None)
    return System(LINUX, distro, release.get("PRETTY_NAME") or distro or LINUX, manager, unsupported)


@lru_cache(maxsize=1)
def system() -> System:
    """The operating system this process runs on, read once.

    Returns
    -------
    System
        OS family, Linux distribution and package manager.

    Examples
    --------
    >>> from svgwriter._internal._platform import system
    >>> system().os in ("windows", "macos", "linux", "pyodide")
    True
    """
    import platform

    if sys.platform == "emscripten":
        return System(PYODIDE, None, f"Pyodide ({platform.release()})", None, None)
    if sys.platform == "win32":
        return System(WINDOWS, None, f"Windows {platform.release()}", MANAGER_OF[WINDOWS], None)
    if sys.platform == "darwin":
        return System(MACOS, None, f"macOS {platform.mac_ver()[0]}", MANAGER_OF[MACOS], None)
    for candidate in OS_RELEASE:
        path = Path(candidate)
        if path.is_file():
            return distro_system(parse_os_release(path.read_text(encoding="utf-8", errors="replace")))
    return System(LINUX, None, platform.system() or LINUX, None, None)


def open_browser(url: str) -> bool:
    """Open *url* in the default web browser.

    Parameters
    ----------
    url : str
        The page to open.

    Returns
    -------
    bool
        Whether a browser was started; False in Pyodide or with no browser available.

    Examples
    --------
    >>> from svgwriter._internal._platform import open_browser
    >>> # open_browser("http://127.0.0.1:8000")
    """
    if system().os == PYODIDE:
        return False
    try:
        return webbrowser.open(url)
    except webbrowser.Error:
        return False


def temp_dir() -> Path:
    """The folder for temporary files (``TMPDIR``, ``TEMP`` or the system default).

    Returns
    -------
    Path
        An existing writable folder.

    Examples
    --------
    >>> from svgwriter._internal._platform import temp_dir
    >>> temp_dir().is_dir()
    True
    """
    return Path(tempfile.gettempdir())


def cache_dir() -> Path:
    """svgwriter's per-user cache folder for this OS (not created).

    ``%LOCALAPPDATA%\\svgwriter\\Cache`` on Windows, ``~/Library/Caches/svgwriter`` on macOS and
    ``$XDG_CACHE_HOME/svgwriter`` (``~/.cache/svgwriter``) elsewhere.

    Returns
    -------
    Path
        The folder.

    Examples
    --------
    >>> from svgwriter._internal._platform import cache_dir
    >>> cache_dir().name in ("Cache", "svgwriter")
    True
    """
    family = system().os
    if family == WINDOWS:
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / CACHE_NAME / "Cache"
    if family == MACOS:
        return Path.home() / "Library" / "Caches" / CACHE_NAME
    if family == PYODIDE:
        return temp_dir() / CACHE_NAME
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / CACHE_NAME
