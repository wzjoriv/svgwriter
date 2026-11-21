"""
Constants for ``svgwriter.project``: file names, manifest keys, defaults and the preview page.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

__all__ = [
    "ANIMATED_FORMATS",
    "BAKED_FORMATS",
    "BUILTIN_PRESETS",
    "CELL_MARKER",
    "DEFAULT_ENTRY",
    "DEFAULT_FORMATS",
    "DEFAULT_GIF_FPS",
    "DEFAULT_NOTEBOOK_OBJECT",
    "DEFAULT_OUTPUT",
    "DEFAULT_PORT",
    "DOT_PREFIX",
    "FONT_FOLDER",
    "GALLERY_STYLE",
    "FONT_SUFFIXES",
    "HEADLESS_ENV",
    "IMAGE_TYPES",
    "KERNEL",
    "KEEPS_ANIMATION",
    "KILOBYTE",
    "MAIN_GUARD",
    "MANIFEST",
    "MARKDOWN_TAG",
    "NBFORMAT",
    "NBFORMAT_MINOR",
    "NOTEBOOK_SUFFIX",
    "NOTEBOOK_TIMEOUT",
    "OUTPUT_KEYS",
    "PLACEHOLDERS",
    "POLL_SECONDS",
    "PREVIEW_CELLS",
    "PROJECT_KEYS",
    "PYPROJECT",
    "PYPROJECT_TABLE",
    "RELOAD_MILLISECONDS",
    "RELOAD_SCRIPT",
    "TEMPLATES",
    "TEMPLATE_SUFFIX",
    "TOP_KEYS",
    "VIDEO_FORMATS",
    "VIDEO_TYPES",
    "WATCH_IGNORED",
]

MANIFEST: Final = "svgwriter.toml"
PYPROJECT: Final = "pyproject.toml"
PYPROJECT_TABLE: Final = ("tool", "svgwriter")

TOP_KEYS: Final = frozenset({"project", "outputs"})
PROJECT_KEYS: Final = frozenset({"name", "entry", "size", "theme", "fonts"})
OUTPUT_KEYS: Final = frozenset({"formats", "directory"})

DEFAULT_ENTRY: Final = "main:build"
DEFAULT_NOTEBOOK_OBJECT: Final = "build"
DEFAULT_FORMATS: Final = ("svg", "png")
DEFAULT_OUTPUT: Final = "output"
FONT_FOLDER: Final = "assets/fonts"
FONT_SUFFIXES: Final = frozenset({".ttf", ".otf", ".ttc"})
NOTEBOOK_SUFFIX: Final = ".ipynb"
NOTEBOOK_TIMEOUT: Final = 600
HEADLESS_ENV: Final = "SVGWRITER_PROJECT_HEADLESS"
MAIN_GUARD: Final = 'if __name__ == "__main__":'
CELL_MARKER: Final = "# %%"
MARKDOWN_TAG: Final = "[markdown]"
NBFORMAT: Final = 4
NBFORMAT_MINOR: Final = 5
KERNEL: Final = "python3"
PREVIEW_CELLS: Final = (
    ("markdown", "Every output of the project, as `svgwriter build` writes it: animations play here. "
                 "`project.build()` writes the files to `output/`."),
    ("code", "project = svg.Project.load()\nproject.preview()"),
)

KEEPS_ANIMATION: Final = frozenset({"svg", "svgz", "html", "pptx", "gif"})
ANIMATED_FORMATS: Final = frozenset({"gif"})
BAKED_FORMATS: Final = KEEPS_ANIMATION - ANIMATED_FORMATS
VIDEO_FORMATS: Final = frozenset({"mp4", "webm", "mov", "apng"})
DEFAULT_GIF_FPS: Final = 15.0

IMAGE_TYPES: Final = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
                      ".webp": "image/webp", ".bmp": "image/bmp", ".svg": "image/svg+xml"}
VIDEO_TYPES: Final = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime"}

TEMPLATES: Final = Path(__file__).resolve().parent / "templates"
BUILTIN_PRESETS: Final = {
    "blank": ("A canvas with a title, a component and an animation; SVG and PNG", None),
    "poster": ("An A4 page drawn in millimetres with a chart from a CSV file; PDF, SVG and PNG", "blank"),
    "slides": ("A 16:9 deck with one function per slide and slide animations; PowerPoint and PDF", "blank"),
    "animation": ("A Scene class with SMIL presets and per-frame updates; GIF and animated SVG", "blank"),
}
PLACEHOLDERS: Final = {"project_name": "{{ project_name }}", "preset": "{{ preset }}"}
TEMPLATE_SUFFIX: Final = "-tpl"
DOT_PREFIX: Final = "dot-"

DEFAULT_PORT: Final = 8000
POLL_SECONDS: Final = 0.5
RELOAD_MILLISECONDS: Final = 700
WATCH_IGNORED: Final = frozenset({"output", ".git", "__pycache__", ".ipynb_checkpoints", ".venv"})
KILOBYTE: Final = 1024
GALLERY_STYLE: Final = (
    ".svgwriter-preview{display:flex;flex-wrap:wrap;gap:16px;font-family:system-ui,sans-serif}"
    ".svgwriter-preview h3{flex-basis:100%;margin:0}"
    ".svgwriter-preview figure{margin:0;max-width:100%;display:flex;flex-direction:column;gap:6px}"
    ".svgwriter-preview img,.svgwriter-preview video{max-width:min(100%,640px);max-height:480px;"
    "border:1px solid #d4d4d8;background:repeating-conic-gradient(#f4f4f5 0 25%,#fff 0 50%) 0 0/16px 16px}"
    ".svgwriter-preview figcaption{font-size:13px;color:#3f3f46}"
)
RELOAD_SCRIPT: Final = (
    "<script>const shown={version};setInterval(async()=>{{try{{const r=await fetch('/version');"
    "if(Number(await r.text())!==shown)location.reload()}}catch(e){{}}}},{interval});</script>"
)
