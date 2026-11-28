"""
Constants for the platform layer: operating systems, package managers, tools, extras and fonts.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "APT",
    "BREW",
    "CACHE_NAME",
    "COMMANDS",
    "DISTRO_FAMILIES",
    "DNF",
    "EMOJI_SAMPLE",
    "ENV_PREFIX",
    "FONT_DIRS",
    "GENERIC_CANDIDATES",
    "LINUX",
    "MAC_FALLBACK_FAMILIES",
    "MACOS",
    "MANAGER_OF",
    "OS_RELEASE",
    "PACMAN",
    "PYODIDE",
    "PYTHON_CAPABILITIES",
    "SUMMARY_FAMILY",
    "SUMMARY_GENERICS",
    "SYSTEM_FONTS",
    "TOOL_CAPABILITIES",
    "UNSUPPORTED_DISTROS",
    "VERSION_END",
    "VERSION_TIMEOUT",
    "WINDOWS",
    "WINGET",
    "ZYPPER",
]

WINDOWS: Final = "windows"
MACOS: Final = "macos"
LINUX: Final = "linux"
PYODIDE: Final = "pyodide"

APT: Final = "apt"
DNF: Final = "dnf"
PACMAN: Final = "pacman"
ZYPPER: Final = "zypper"
BREW: Final = "brew"
WINGET: Final = "winget"

OS_RELEASE: Final = ("/etc/os-release", "/usr/lib/os-release")
ENV_PREFIX: Final = "SVGWRITER_"
CACHE_NAME: Final = "svgwriter"
VERSION_TIMEOUT: Final = 10
VERSION_END: Final = " Copyright"

DISTRO_FAMILIES: Final = {
    "debian": APT, "ubuntu": APT, "linuxmint": APT, "pop": APT, "raspbian": APT,
    "fedora": DNF, "rhel": DNF, "centos": DNF, "rocky": DNF, "almalinux": DNF,
    "arch": PACMAN, "manjaro": PACMAN, "endeavouros": PACMAN,
    "suse": ZYPPER, "opensuse": ZYPPER, "opensuse-tumbleweed": ZYPPER, "opensuse-leap": ZYPPER, "sles": ZYPPER,
}
"""``/etc/os-release`` ``ID`` / ``ID_LIKE`` words and the package manager of that family."""

UNSUPPORTED_DISTROS: Final = {"alpine": "skia-python ships no musllinux wheels, so Alpine (musl) is unsupported"}

MANAGER_OF: Final = {WINDOWS: WINGET, MACOS: BREW}

COMMANDS: Final = {
    APT: "sudo apt install {}",
    DNF: "sudo dnf install {}",
    PACMAN: "sudo pacman -S {}",
    ZYPPER: "sudo zypper install {}",
    BREW: "brew install {}",
    WINGET: "winget install {}",
}

TOOL_CAPABILITIES: Final = {
    "ffmpeg": {
        "tools": ("ffmpeg",), "version": ("-version",), "purpose": "video export and reading",
        "packages": {APT: "ffmpeg", DNF: "ffmpeg-free", PACMAN: "ffmpeg", ZYPPER: "ffmpeg-7", BREW: "ffmpeg",
                     WINGET: "Gyan.FFmpeg"},
        "url": "https://ffmpeg.org/download.html",
    },
    "latex": {
        "tools": ("latex", "dvisvgm"), "version": ("--version",), "purpose": "svg.latex with real TeX",
        "packages": {APT: "texlive-latex-extra dvisvgm",
                     DNF: "texlive-scheme-basic texlive-standalone texlive-dvisvgm",
                     PACMAN: "texlive-basic texlive-latexextra texlive-binextra",
                     ZYPPER: "texlive-latex texlive-standalone texlive-dvisvgm",
                     BREW: "--cask mactex-no-gui", WINGET: "MiKTeX.MiKTeX"},
        "url": "https://tug.org/texlive/",
    },
    "mermaid": {
        "tools": ("mmdc",), "version": ("--version",), "purpose": "Mermaid diagrams beyond flowcharts",
        "packages": {APT: "nodejs npm", DNF: "nodejs npm", PACMAN: "nodejs npm", ZYPPER: "nodejs-default npm-default",
                     BREW: "node", WINGET: "OpenJS.NodeJS"},
        "then": "npm install -g @mermaid-js/mermaid-cli",
        "url": "https://github.com/mermaid-js/mermaid-cli",
    },
    "graphviz": {
        "tools": ("dot",), "version": ("-V",), "purpose": "Graphviz DOT diagrams",
        "packages": {APT: "graphviz", DNF: "graphviz", PACMAN: "graphviz", ZYPPER: "graphviz", BREW: "graphviz",
                     WINGET: "Graphviz.Graphviz"},
        "url": "https://graphviz.org/download/",
    },
    "plantuml": {
        "tools": ("plantuml",), "version": ("-version",), "purpose": "PlantUML diagrams",
        "packages": {APT: "plantuml", DNF: "plantuml", PACMAN: "plantuml", ZYPPER: "plantuml", BREW: "plantuml"},
        "url": "https://plantuml.com/download",
    },
    "d2": {
        "tools": ("d2",), "version": ("--version",), "purpose": "D2 diagrams",
        "packages": {BREW: "d2", WINGET: "Terrastruct.D2"},
        "url": "https://d2lang.com/tour/install",
    },
    "inkscape": {
        "tools": ("inkscape",), "version": ("--version",), "purpose": "the Inkscape extension",
        "packages": {APT: "inkscape", DNF: "inkscape", PACMAN: "inkscape", ZYPPER: "inkscape",
                     BREW: "--cask inkscape", WINGET: "Inkscape.Inkscape"},
        "url": "https://inkscape.org/release/",
    },
}
"""External programs: executables (each ``SVGWRITER_<NAME>`` overrides PATH), version flag and packages."""

PYTHON_CAPABILITIES: Final = {
    "skia": {"module": "skia", "distribution": "skia-python", "purpose": "geometry, text and rendering",
             "pip": "skia-python"},
    "harfbuzz": {"module": "uharfbuzz", "distribution": "uharfbuzz", "purpose": "text shaping", "pip": "uharfbuzz"},
    "lcms2": {"module": "lcms2", "distribution": "python-lcms2", "purpose": "ICC colour profiles",
              "pip": "python-lcms2"},
    "fonttools": {"module": "fontTools", "distribution": "fonttools", "purpose": "building and subsetting fonts",
                  "pip": "'pysvgwriter[fonts]'"},
    "brotli": {"module": "brotli", "distribution": "brotli", "purpose": "woff2 fonts", "pip": "'pysvgwriter[fonts]'"},
    "ipywidgets": {"module": "ipywidgets", "distribution": "ipywidgets", "purpose": "svg.explore in notebooks",
                   "pip": "'pysvgwriter[widget]'"},
    "matplotlib": {"module": "matplotlib", "distribution": "matplotlib", "purpose": "plots and mathtext",
                   "pip": "'pysvgwriter[plot]'"},
    "ziamath": {"module": "ziamath", "distribution": "ziamath", "purpose": "svg.latex without TeX",
                "pip": "'pysvgwriter[math]'"},
    "office": {"module": "pptx", "distribution": "python-pptx", "purpose": "PowerPoint, Word and Excel export",
               "pip": "'pysvgwriter[office]'"},
    "notebook": {"module": "nbclient", "distribution": "nbclient", "purpose": "notebook projects",
                 "pip": "'pysvgwriter[notebook]'"},
    "questionary": {"module": "questionary", "distribution": "questionary", "purpose": "arrow-key prompts",
                    "pip": "'pysvgwriter[cli]'"},
}
"""Python libraries: import name, distribution (for the version), purpose and what to pip install."""

SYSTEM_FONTS: Final = {
    APT: "libegl1 libgl1 libfontconfig1 fonts-dejavu-core fonts-noto-color-emoji",
    DNF: "mesa-libEGL mesa-libGL fontconfig dejavu-sans-fonts dejavu-serif-fonts dejavu-sans-mono-fonts google-noto-color-emoji-fonts",
    PACMAN: "libglvnd fontconfig ttf-dejavu noto-fonts-emoji",
    ZYPPER: "Mesa-libEGL1 Mesa-libGL1 fontconfig dejavu-fonts noto-coloremoji-fonts",
}
"""Linux system libraries skia loads and a baseline of fonts, per package manager."""

GENERIC_CANDIDATES: Final = {
    "sans-serif": ("Arial", "Helvetica", "Liberation Sans", "Arimo", "DejaVu Sans", "Noto Sans"),
    "serif": ("Times New Roman", "Georgia", "Times", "Liberation Serif", "DejaVu Serif", "Noto Serif"),
    "monospace": ("Consolas", "Courier New", "Menlo", "Monaco", "Liberation Mono", "DejaVu Sans Mono",
                  "Noto Sans Mono", "Courier"),
    "cursive": ("Comic Sans MS", "Segoe Script", "Apple Chancery", "URW Chancery L"),
    "fantasy": ("Impact", "Papyrus", "Luminari"),
}
"""Concrete families tried for each CSS generic family, Windows faces first, then macOS, then Linux."""

MAC_FALLBACK_FAMILIES: Final = (
    "Helvetica Neue", "Arial Unicode MS", "PingFang SC", "Hiragino Sans", "Apple SD Gothic Neo",
    "Kohinoor Devanagari", "Kohinoor Bangla", "Geeza Pro", "Noto Nastaliq Urdu", "Thonburi", "Apple Color Emoji",
)
"""Families searched first for a missing glyph on macOS, where skia's character matching is unusable."""

SUMMARY_GENERICS: Final = ("sans-serif", "serif", "monospace")
SUMMARY_FAMILY: Final = "sans-serif"
EMOJI_SAMPLE: Final = "😀"

FONT_DIRS: Final = {
    WINDOWS: ("%WINDIR%/Fonts", "%LOCALAPPDATA%/Microsoft/Windows/Fonts"),
    MACOS: ("/System/Library/Fonts", "/Library/Fonts", "~/Library/Fonts"),
    LINUX: ("/usr/share/fonts", "/usr/local/share/fonts", "~/.local/share/fonts", "~/.fonts"),
    PYODIDE: (),
}
"""Where each operating system keeps installed fonts (variables and ``~`` expanded on use)."""
