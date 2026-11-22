"""
How to install a missing capability on a given system.
"""

from __future__ import annotations

from ._constants import COMMANDS, PYODIDE, PYTHON_CAPABILITIES, SYSTEM_FONTS, TOOL_CAPABILITIES
from ._system import System, system

__all__ = ["install_hint", "system_packages_hint"]


def install_hint(name: str, on: System | None = None) -> str:
    """The command (or page) that installs capability *name* on *on*.

    Parameters
    ----------
    name : str
        A capability name (``"ffmpeg"``, ``"latex"``, ``"harfbuzz"``, ...).
    on : System, optional
        The target system. Defaults to the running one.

    Returns
    -------
    str
        A shell command for this OS and package manager, ``pip install ...`` for Python libraries,
        or the download page when no package is known.

    Raises
    ------
    KeyError
        If *name* is not a known capability.

    Examples
    --------
    >>> from svgwriter._internal._platform import System, install_hint
    >>> install_hint("graphviz", System("linux", "arch", "Arch Linux", "pacman", None))
    'sudo pacman -S graphviz'
    >>> install_hint("fonttools", System("windows", None, "Windows 11", "winget", None))
    "pip install 'pysvgwriter[fonts]'"
    """
    on = on or system()
    if name in PYTHON_CAPABILITIES:
        return f"pip install {PYTHON_CAPABILITIES[name]['pip']}"
    spec = TOOL_CAPABILITIES[name]
    if on.os == PYODIDE:
        return f"not available in Pyodide ({spec['url']})"
    package = spec["packages"].get(on.manager or "")
    if package is None:
        return f"see {spec['url']}" + (f", then {spec['then']}" if "then" in spec else "")
    command = COMMANDS[on.manager or ""].format(package)
    return f"{command}, then {spec['then']}" if "then" in spec else command


def system_packages_hint(on: System | None = None) -> str | None:
    """The command that installs skia's system libraries and baseline fonts on a Linux distribution.

    Parameters
    ----------
    on : System, optional
        The target system. Defaults to the running one.

    Returns
    -------
    str or None
        The command, or None outside Linux or for an unknown package manager.

    Examples
    --------
    >>> from svgwriter._internal._platform import System, system_packages_hint
    >>> system_packages_hint(System("linux", "debian", "Debian", "apt", None)).split()[:3]
    ['sudo', 'apt', 'install']
    """
    on = on or system()
    packages = SYSTEM_FONTS.get(on.manager or "")
    return COMMANDS[on.manager or ""].format(packages) if packages else None
