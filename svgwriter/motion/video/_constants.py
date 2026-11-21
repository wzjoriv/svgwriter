"""
Constants for ``svgwriter.motion.video``: defaults, tables and patterns.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "BAKE_DIGITS",
    "BAKE_DISCRETE",
    "BAKE_DOCUMENTS",
    "BAKE_HIDDEN",
    "BAKE_INITIAL",
    "BAKE_PARTS",
    "BAKE_PLACEHOLDER",
    "BAKE_TOLERANCE",
    "BAKE_VISIBILITY",
    "BAKE_VISIBLE",
    "BREATHE_AMOUNT",
    "BREATHE_PERIOD",
    "CHANNELS",
    "CHANNEL_MAX",
    "DEGREES_PER_TURN",
    "DURATION_RE",
    "EVEN_PAD",
    "FFMPEG",
    "FPS_RE",
    "FRAME_PATTERN",
    "FRAME_SUFFIX",
    "GIF_FILTER",
    "HOVER_HEIGHT",
    "HOVER_PERIOD",
    "OUTPUTS",
    "PNG_SIGNATURE",
    "PNG_SIZE_OFFSET",
    "RGBA_CHANNELS",
    "RGBA_DTYPE",
    "SCENE_FORMAT",
    "SCENE_HEIGHT",
    "SCENE_RENDERER",
    "SCENE_RUN_NAME",
    "SCENE_SCRIPT",
    "SCENE_SVG",
    "SCENE_WIDTH",
    "SECONDS_PER_HOUR",
    "SECONDS_PER_MINUTE",
    "STDERR_TAIL",
    "STREAM_RE",
    "TIMECOUNT_RE",
    "TIME_SCALE",
    "WIGGLE_ANGLE",
    "WIGGLE_PERIOD",
]

FFMPEG: Final = "ffmpeg"
STDERR_TAIL: Final = 2000
EVEN_PAD: Final = "pad=ceil(iw/2)*2:ceil(ih/2)*2"
GIF_FILTER: Final = "split[a][b];[a]palettegen=reserve_transparent=1[p];[b][p]paletteuse"
OUTPUTS: Final = {
    ".mp4": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", EVEN_PAD, "-movflags", "+faststart"],
    ".m4v": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", EVEN_PAD],
    ".mov": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", EVEN_PAD],
    ".webm": ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p"],
    ".gif": ["-filter_complex", GIF_FILTER, "-loop", "0"],
    ".apng": ["-plays", "0", "-f", "apng"],
    ".png": ["-start_number", "0", "-f", "image2"],
}

TIMECOUNT_RE: Final = re.compile(r"^\s*([+-]?\d*\.?\d+)\s*(ms|s|min|h)?\s*$")
TIME_SCALE: Final = {"ms": 0.001, "s": 1.0, "min": 60.0, "h": 3600.0, None: 1.0}
SECONDS_PER_MINUTE: Final = 60.0
SECONDS_PER_HOUR: Final = 3600.0


PNG_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"
PNG_SIZE_OFFSET: Final = 16
RGBA_CHANNELS: Final = 4
RGBA_DTYPE: Final = "uint8"

CHANNELS: Final = 4
CHANNEL_MAX: Final = 255.0
STREAM_RE: Final = re.compile(r"Stream #\S+.*?Video:.*?(\d{2,5})x(\d{2,5})")
FPS_RE: Final = re.compile(r"(\d+(?:\.\d+)?) (?:fps|tbr)")
DURATION_RE: Final = re.compile(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)")

SCENE_WIDTH: Final = 640.0
SCENE_HEIGHT: Final = 360.0
SCENE_RENDERER: Final = "skia"
SCENE_FORMAT: Final = "mp4"
SCENE_RUN_NAME: Final = "__scene__"
SCENE_SCRIPT: Final = ".py"
SCENE_SVG: Final = ".svg"
FRAME_SUFFIX: Final = ".png"
FRAME_PATTERN: Final = "{stem}_%04d{suffix}"
WIGGLE_ANGLE: Final = 6.0
WIGGLE_PERIOD: Final = 0.5
HOVER_HEIGHT: Final = 4.0
HOVER_PERIOD: Final = 2.0
BREATHE_AMOUNT: Final = 0.05
BREATHE_PERIOD: Final = 2.0
BAKE_TOLERANCE: Final = 0.01
BAKE_DIGITS: Final = 6
BAKE_DOCUMENTS: Final = frozenset({".svg", ".svgz", ".html", ".htm", ".pptx"})
BAKE_DISCRETE: Final = frozenset({
    "class", "id", "role", "href", "xlink:href", "font-family", "text-anchor", "dominant-baseline", "display",
    "visibility", "fill-rule", "clip-rule", "stroke-linecap", "stroke-linejoin", "clip-path", "mask", "filter",
    "marker-start", "marker-mid", "marker-end", "font-weight", "font-style", "preserveAspectRatio",
})
BAKE_VISIBILITY: Final = "visibility"
BAKE_HIDDEN: Final = "hidden"
BAKE_VISIBLE: Final = "visible"
BAKE_PLACEHOLDER: Final = "\x00"
BAKE_PARTS: Final = (("translate", (0.0, 0.0)), ("rotate", (0.0,)), ("skewX", (0.0,)), ("scale", (1.0, 1.0)))
DEGREES_PER_TURN: Final = 360.0
BAKE_INITIAL: Final = {
    "class": "", "display": "inline", "visibility": "visible", "stroke-dasharray": "none", "font-weight": "normal",
    "font-style": "normal", "text-anchor": "start", "fill-rule": "nonzero", "clip-rule": "nonzero",
    "stroke-linecap": "butt", "stroke-linejoin": "miter", "clip-path": "none", "mask": "none", "filter": "none",
    "marker-start": "none", "marker-mid": "none", "marker-end": "none",
}
