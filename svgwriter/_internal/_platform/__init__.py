"""
The platform layer: operating system, Linux distribution, external programs, optional libraries and fonts.

Everything that differs between Windows, macOS, Linux distributions and Pyodide lives here; the rest of
the library asks this package instead of checking ``sys.platform`` or ``shutil.which`` itself.
"""

from __future__ import annotations

from ._capabilities import (
    Capabilities,
    Capability,
    available,
    capabilities,
    capability_of,
    find_executable,
    missing,
)
from ._fonts import (
    FontSummary,
    fallback_families,
    font_dirs,
    font_summary,
    generic_candidates,
    scans_fallback,
)
from ._hints import install_hint, system_packages_hint
from ._system import System, cache_dir, distro_system, open_browser, parse_os_release, system, temp_dir

__all__ = [
    "Capabilities",
    "Capability",
    "FontSummary",
    "System",
    "available",
    "cache_dir",
    "capabilities",
    "capability_of",
    "distro_system",
    "fallback_families",
    "find_executable",
    "font_dirs",
    "font_summary",
    "generic_candidates",
    "install_hint",
    "missing",
    "open_browser",
    "parse_os_release",
    "scans_fallback",
    "system",
    "system_packages_hint",
    "temp_dir",
]
