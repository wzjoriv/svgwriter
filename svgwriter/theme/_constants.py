"""
Constants for ``svgwriter.theme``: built-in palettes, fonts, role measures and file syntax.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "ARRAY_CHANNELS",
    "ARRAY_INTEGER_MAX",
    "BOOLEAN_WORDS",
    "BORDER_MIX",
    "BUILTIN_THEMES",
    "COLOR_FUNCTION_RE",
    "COMPARISONS",
    "CONDITIONAL",
    "DEFAULT_THEME",
    "EXPONENT_RE",
    "EXPRESSION_MARK",
    "EXPRESSION_CACHE_SIZE",
    "FILE_FONT_KEYS",
    "FILE_KEYS",
    "FONT_FAMILY",
    "FONT_SIZES",
    "FONT_TABLES",
    "FONT_WEIGHTS",
    "GEOMETRIC_FAMILY",
    "HEX_RE",
    "LENGTH_PROPERTIES",
    "HEAVY_LINE_WIDTH",
    "LENGTH_UNIT",
    "LINE_WIDTH",
    "LOGIC_WORDS",
    "MAX_ARGUMENTS",
    "MAX_EXPRESSION_DEPTH",
    "MAX_EXPRESSION_LENGTH",
    "MAX_MAGNITUDE",
    "MAX_REFERENCE_DEPTH",
    "MAX_ROUND_DIGITS",
    "MONOSPACE_FAMILY",
    "MUTED_MIX",
    "NAME_RE",
    "NUMBER_RE",
    "OPACITY_PROPERTIES",
    "OPERATORS",
    "PUNCTUATION",
    "QUOTES",
    "REFERENCE_RE",
    "UNSUPPORTED_OPERATORS",
    "SERIF_FAMILY",
    "SHADOW_ALPHA",
    "ROLE_CLASS_PREFIX",
    "ROLE_NAME_RE",
    "SHEET_THEME_NAME",
    "STYLE_ID",
    "THIN_LINE_WIDTH",
]

DEFAULT_THEME: Final = "light"
ROLE_CLASS_PREFIX: Final = "role-"
STYLE_ID: Final = "svgwriter-theme"
SHEET_THEME_NAME: Final = "document"
"""Name of the theme rebuilt from a parsed theme sheet that no registered theme writes."""
ROLE_NAME_RE: Final = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*")
REFERENCE_RE: Final = re.compile(r"\{([a-z_][a-z0-9_]*(?:\.[a-z0-9_]+)+)\}")
FILE_KEYS: Final = frozenset({"name", "extends", "palette", "fonts", "roles"})
FILE_FONT_KEYS: Final = frozenset({"family", "monospace", "sizes", "weights"})
FONT_TABLES: Final = ("sizes", "weights")
ARRAY_CHANNELS: Final = (3, 4)
ARRAY_INTEGER_MAX: Final = 255

EXPRESSION_MARK: Final = "="
MAX_EXPRESSION_LENGTH: Final = 512
MAX_EXPRESSION_DEPTH: Final = 32
MAX_REFERENCE_DEPTH: Final = 16
MAX_ARGUMENTS: Final = 16
MAX_MAGNITUDE: Final = 1_000_000.0
MAX_ROUND_DIGITS: Final = 6
EXPRESSION_CACHE_SIZE: Final = 1024
LENGTH_UNIT: Final = "px"
CONDITIONAL: Final = "if"
LOGIC_WORDS: Final = frozenset({"and", "or", "not"})
BOOLEAN_WORDS: Final = {"true": True, "false": False}
COMPARISONS: Final = frozenset({"<", "<=", ">", ">=", "==", "!="})
OPERATORS: Final = ("**", "<=", ">=", "==", "!=", "<", ">", "+", "-", "*", "/", "%")
UNSUPPORTED_OPERATORS: Final = {"**": "the power operator ** is not supported",
                                "%": "the % operator is not supported"}
QUOTES: Final = frozenset("'\"")
PUNCTUATION: Final = frozenset("(),")
NUMBER_RE: Final = re.compile(r"(\d+(?:\.\d+)?|\.\d+)([A-Za-z%][A-Za-z0-9%]*)?")
EXPONENT_RE: Final = re.compile(r"[eE]\d*")
NAME_RE: Final = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:-[A-Za-z][A-Za-z0-9_]*)*")
HEX_RE: Final = re.compile(r"#[0-9A-Za-z]+")
COLOR_FUNCTION_RE: Final = re.compile(r"(?:device-cmyk|rgba?|hsla?|hsva?|hwb|lab|lch|oklab|oklch|color)\s*\(", re.I)

FONT_FAMILY: Final = "Helvetica, Arial, sans-serif"
MONOSPACE_FAMILY: Final = "Consolas, Menlo, monospace"
SERIF_FAMILY: Final = "Georgia, 'Times New Roman', serif"
GEOMETRIC_FAMILY: Final = "Inter, system-ui, sans-serif"
FONT_SIZES: Final = {"text": 14.0, "title": 24.0, "subtitle": 18.0, "caption": 11.0}
FONT_WEIGHTS: Final = {"regular": 400, "bold": 700}

LENGTH_PROPERTIES: Final = frozenset({"font-size", "stroke-width", "stroke-dashoffset"})
OPACITY_PROPERTIES: Final = {"fill": "fill-opacity", "stroke": "stroke-opacity", "stop-color": "stop-opacity",
                              "flood-color": "flood-opacity"}
LINE_WIDTH: Final = 2.0
THIN_LINE_WIDTH: Final = 1.0
BORDER_MIX: Final = 0.7
MUTED_MIX: Final = 0.25
SHADOW_ALPHA: Final = 0.2
HEAVY_LINE_WIDTH: Final = 2.0

BUILTIN_THEMES: Final = {
    "light": {"palette": {
        "background": "#ffffff", "foreground": "#1f2933", "surface": "#f4f6f8",
        "primary": "#0f766e", "secondary": "#4f46e5", "accent": "#fbbf24",
        "success": "#15803d", "warning": "#b45309", "error": "#b91c1c",
    }},
    "dark": {"palette": {
        "background": "#111827", "foreground": "#e5e7eb", "surface": "#1f2937",
        "primary": "#99f6e4", "on_primary": "#042f2e", "secondary": "#a5b4fc", "accent": "#b45309",
        "success": "#4ade80", "warning": "#fbbf24", "error": "#f87171",
    }},
    "paper": {"palette": {
        "background": "#fbf7ef", "foreground": "#3b3128", "surface": "#f3ecdf",
        "primary": "#8c4a2f", "secondary": "#4a6670", "accent": "#c08a2d",
        "success": "#4d7c3a", "warning": "#b7791f", "error": "#9b2c2c",
    }},
    "print": {"palette": {
        "background": "#ffffff", "foreground": "#222222", "surface": "#f8f8f8", "border": "#bbbbbb",
        "muted": "#5f5f5f", "primary": "#004b8d", "secondary": "#e85d04",
        "accent": "#004b8d", "success": "#2e7d32", "warning": "#b45309", "error": "#b71c1c",
        "shadow": "#00000000",
    }, "fonts": {"family": SERIF_FAMILY}},
    "mono": {"palette": {
        "background": "#ffffff", "foreground": "#000000", "surface": "#ffffff", "border": "#000000",
        "primary": "#000000", "secondary": "#000000", "accent": "#000000",
        "success": "#000000", "warning": "#000000", "error": "#000000", "shadow": "#000000",
    }},
    "noir": {"palette": {
        "background": "#1c1b19", "foreground": "#e3e1dc", "surface": "#252422", "border": "#3c3a36",
        "primary": "#eae7dc", "secondary": "#bdb6a9", "accent": "#a4c2f4",
        "success": "#7ba97c", "warning": "#ffd166", "error": "#d17a69", "shadow": "#ffffff14",
    }},
    "brutalist": {"palette": {
        "background": "#fff9c4", "foreground": "#000000", "surface": "#ffffff", "border": "#000000",
        "primary": "#1e40ff", "on_primary": "#ffffff", "secondary": "#ef4444", "accent": "#facc15",
        "success": "#10b981", "warning": "#f59e0b", "error": "#ef4444", "shadow": "#000000",
    }, "fonts": {"family": GEOMETRIC_FAMILY, "weights": {"regular": 500, "bold": 800}},
       "roles": {"box": {"stroke-width": HEAVY_LINE_WIDTH}, "outline": {"stroke-width": HEAVY_LINE_WIDTH}}},
    "dracula": {"palette": {
        "background": "#282a36", "foreground": "#f8f8f2", "surface": "#44475a",
        "primary": "#bd93f9", "secondary": "#ff79c6", "accent": "#8be9fd",
        "success": "#50fa7b", "warning": "#ffb86c", "error": "#ff5555",
    }},
    "alucard": {"palette": {
        "background": "#fffbeb", "foreground": "#1f1f1f", "surface": "#f5efd5", "muted": "#6c664b",
        "primary": "#036a96", "secondary": "#a3144d", "accent": "#644ac9",
        "success": "#14710a", "warning": "#846e15", "error": "#cb3a2a",
    }},
    "one-dark": {"palette": {
        "background": "#282c34", "foreground": "#abb2bf", "surface": "#21252b", "muted": "#9da5b4",
        "primary": "#61afef", "secondary": "#c678dd", "accent": "#56b6c2",
        "success": "#98c379", "warning": "#e5c07b", "error": "#e06c75",
    }},
    "one-light": {"palette": {
        "background": "#fafafa", "foreground": "#383a42", "surface": "#ffffff", "border": "#dcdfe4",
        "primary": "#4078f2", "on_primary": "#000000", "secondary": "#a626a4", "accent": "#c18401",
        "success": "#50a14f", "warning": "#c18401", "error": "#e45649",
    }},
}
