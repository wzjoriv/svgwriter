"""Sphinx configuration for the svgwriter docs: ``python scripts/dev.py docs`` or ``sphinx-build docs docs/_build/html``."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "docs" / "_ext"))

import svgwriter  # noqa: E402

project = "svgwriter"
author = "Josue N Rivera"
copyright = "2026, Josue N Rivera"
release = svgwriter.__version__
version = ".".join(release.split(".")[:2])

DOCS_CHANNEL = os.environ.get("SVGWRITER_DOCS_CHANNEL", "dev")
DOCS_BASE_URL = "https://wzjoriv.github.io/svgwriter"
REPO_URL = "https://github.com/wzjoriv/svgwriter"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
    "snippet_images",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "signature"
autodoc_typehints_format = "short"
add_module_names = False
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_rtype = False
napoleon_use_ivar = True
suppress_warnings = ["ref.python", "ref.class", "ref.obj", "ref.func", "ref.meth", "ref.mod", "ref.attr",
                     "ref.data", "ref.exc", "autodoc"]
nitpicky = False

intersphinx_mapping = (
    {"python": ("https://docs.python.org/3", None), "numpy": ("https://numpy.org/doc/stable", None)}
    if os.environ.get("SPHINX_INTERSPHINX", "1") != "0"
    else {}
)

myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3

html_theme = "furo"
html_title = f"svgwriter {release}"
html_static_path = ["_static"]
html_logo = "_static/logo/logo.svg"
html_favicon = "_static/logo/favicon.ico"
html_css_files = ["custom.css"]
templates_path = ["_templates"]
html_context = {
    "docs_channel": DOCS_CHANNEL,
    "docs_base_url": DOCS_BASE_URL,
    "docs_release": release,
}
html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "versions.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/scroll-end.html",
    ],
}
html_theme_options = {
    "navigation_with_keys": True,
    "source_repository": REPO_URL,
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {"color-brand-primary": "#0f766e", "color-brand-content": "#0f766e"},
    "dark_css_variables": {"color-brand-primary": "#5eead4", "color-brand-content": "#99f6e4"},
}
if DOCS_CHANNEL == "dev":
    html_theme_options["announcement"] = (
        f'Development docs for the next release. <a href="{DOCS_BASE_URL}/stable/">Stable docs</a>.'
    )

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "friendly"
pygments_dark_style = "monokai"
