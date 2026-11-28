"""
Optional libraries and external programs: finding them, reporting them, and explaining how to add them.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import shutil
import subprocess
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any

from ._constants import ENV_PREFIX, PYTHON_CAPABILITIES, TOOL_CAPABILITIES, VERSION_END, VERSION_TIMEOUT
from ._hints import install_hint

__all__ = ["Capabilities", "Capability", "available", "capabilities", "capability_of", "find_executable", "missing"]


@dataclass(frozen=True)
class Capability:
    """One optional library or external program and whether this machine has it.

    Attributes
    ----------
    name : str
        The capability (``"ffmpeg"``, ``"harfbuzz"``, ...).
    kind : {"python", "tool"}
        A Python library or an external program.
    available : bool
        Whether it can be used.
    version : str or None
        Its version, when available and known.
    path : str or None
        The executable (programs) or package folder (libraries), when available.
    purpose : str
        What svgwriter uses it for.
    hint : str
        How to install it on this OS.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.capabilities()["skia"].available
    True
    """

    name: str
    kind: str
    available: bool
    version: str | None
    path: str | None
    purpose: str
    hint: str

    def to_dict(self) -> dict[str, Any]:
        """The fields as a plain dictionary (for JSON).

        Returns
        -------
        dict of str to Any
            Every attribute by name.

        Examples
        --------
        >>> import svgwriter as svg
        >>> sorted(svg.capabilities()["skia"].to_dict())
        ['available', 'hint', 'kind', 'name', 'path', 'purpose', 'version']
        """
        return asdict(self)


class Capabilities(Mapping[str, Capability]):
    """What this machine can do: a read-only mapping of capability name to :class:`Capability`.

    Parameters
    ----------
    entries : iterable of Capability
        The checked capabilities.

    Examples
    --------
    >>> import svgwriter as svg
    >>> found = svg.capabilities()
    >>> "ffmpeg" in found and isinstance(found.missing(), list)
    True
    """

    def __init__(self, entries: list[Capability]) -> None:
        self._entries = {entry.name: entry for entry in entries}

    def __getitem__(self, name: str) -> Capability:
        return self._entries[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        marks = ", ".join(f"{name}={'yes' if entry.available else 'no'}" for name, entry in self._entries.items())
        return f"Capabilities({marks})"

    def missing(self) -> list[str]:
        """Names of the capabilities that are not available.

        Returns
        -------
        list of str
            In report order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> "skia" in svg.capabilities().missing()
        False
        """
        return [name for name, entry in self._entries.items() if not entry.available]

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Every capability as a plain dictionary, for JSON.

        Returns
        -------
        dict of str to dict
            Capability name to its fields.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.capabilities().to_dict()["skia"]["kind"]
        'python'
        """
        return {name: entry.to_dict() for name, entry in self._entries.items()}


_TOOL_OWNER = {tool: name for name, spec in TOOL_CAPABILITIES.items() for tool in spec["tools"]}


def capability_of(executable: str) -> str:
    """The capability an executable belongs to (``"dvisvgm"`` is part of ``"latex"``).

    Parameters
    ----------
    executable : str
        A program name.

    Returns
    -------
    str
        The capability name.

    Examples
    --------
    >>> from svgwriter._internal._platform import capability_of
    >>> capability_of("dot")
    'graphviz'
    """
    return _TOOL_OWNER[executable]


def find_executable(executable: str) -> str | None:
    """The path of a program, from ``SVGWRITER_<NAME>`` or ``PATH``; looked up afresh each call.

    Parameters
    ----------
    executable : str
        The program name (``"dot"``) or a path.

    Returns
    -------
    str or None
        The program, or None when it cannot be found.

    Examples
    --------
    >>> from svgwriter._internal._platform import find_executable
    >>> find_executable("no-such-program") is None
    True
    """
    override = os.environ.get(f"{ENV_PREFIX}{executable.upper()}")
    return override or shutil.which(executable)


def available(name: str) -> bool:
    """Whether capability *name* can be used now (programs are looked up afresh).

    Parameters
    ----------
    name : str
        A capability name.

    Returns
    -------
    bool
        True when every program of a tool capability is found, or the library imports.

    Examples
    --------
    >>> from svgwriter._internal._platform import available
    >>> available("skia")
    True
    """
    if name in TOOL_CAPABILITIES:
        return all(find_executable(tool) for tool in TOOL_CAPABILITIES[name]["tools"])
    return _module_spec(PYTHON_CAPABILITIES[name]["module"]) is not None


def missing(name: str, action: str, error: type[Exception] = ImportError) -> Exception:
    """The error to raise when *action* needs capability *name*, naming it and how to install it here.

    Parameters
    ----------
    name : str
        The missing capability.
    action : str
        What needed it (``"svg.explore"``, ``"video export"``).
    error : type of Exception, optional
        The exception class to build. Defaults to ImportError.

    Returns
    -------
    Exception
        An instance of *error*, ready to raise.

    Examples
    --------
    >>> from svgwriter._internal._platform import missing
    >>> str(missing("fonttools", "building fonts"))
    "building fonts needs fonttools (building and subsetting fonts); install it with: pip install 'pysvgwriter[fonts]'"
    """
    spec = TOOL_CAPABILITIES.get(name) or PYTHON_CAPABILITIES[name]
    return error(f"{action} needs {name} ({spec['purpose']}); install it with: {install_hint(name)}")


def _module_spec(module: str) -> Any:
    try:
        return importlib.util.find_spec(module)
    except (ImportError, ValueError):
        return None


def _tool_version(path: str, flags: tuple[str, ...]) -> str | None:
    try:
        done = subprocess.run([path, *flags], capture_output=True, timeout=VERSION_TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (done.stdout or done.stderr).decode("utf-8", "replace").strip()
    return text.splitlines()[0].split(VERSION_END)[0].strip() if text else None


def _check_tool(name: str) -> Capability:
    spec = TOOL_CAPABILITIES[name]
    paths = [find_executable(tool) for tool in spec["tools"]]
    found = all(paths)
    version = _tool_version(str(paths[0]), spec["version"]) if found else None
    return Capability(name, "tool", found, version, paths[0] if found else None, spec["purpose"],
                      install_hint(name))


def _check_python(name: str) -> Capability:
    spec = PYTHON_CAPABILITIES[name]
    importable = _module_spec(spec["module"])
    version = None
    if importable is not None:
        try:
            version = importlib.metadata.version(spec["distribution"])
        except importlib.metadata.PackageNotFoundError:
            version = None
    location = importable.submodule_search_locations if importable is not None else None
    path = next(iter(location), None) if location else (importable.origin if importable is not None else None)
    return Capability(name, "python", importable is not None, version, path, spec["purpose"], install_hint(name))


@lru_cache(maxsize=1)
def _checked() -> Capabilities:
    return Capabilities([*(_check_python(name) for name in PYTHON_CAPABILITIES),
                         *(_check_tool(name) for name in TOOL_CAPABILITIES)])


def capabilities(refresh: bool = False) -> Capabilities:
    """What this machine can do: optional libraries and external programs, with how to add each.

    The checks run on first call and are cached; programs are asked for their version once.

    Parameters
    ----------
    refresh : bool, optional
        Check again (after installing something). Defaults to False.

    Returns
    -------
    Capabilities
        A read-only mapping of name to :class:`Capability` (``available``, ``version``, ``path``,
        ``purpose`` and the install ``hint`` for this OS).

    See Also
    --------
    svgwriter.tools.cli.app : ``svgwriter doctor`` prints the same report.

    Examples
    --------
    >>> import svgwriter as svg
    >>> found = svg.capabilities()
    >>> found["harfbuzz"].kind
    'python'
    >>> # found["ffmpeg"].hint  -> e.g. 'winget install Gyan.FFmpeg'
    """
    if refresh:
        _checked.cache_clear()
    return _checked()
