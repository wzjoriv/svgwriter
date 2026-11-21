"""Notebooks of the demo projects: each demo's ``main.py`` cells, run with pictures, saved as ``<name>.ipynb``.

The cells come from the shared devkit notebooks tool. The project's own ``__main__`` cell is replaced by cells
that apply the demo's theme up front, offer ``svg.interact`` on the demo's controls, show a few stills for
other control values and show every output as SVG, built from a quick copy of the demo.
"""

from __future__ import annotations

import ast
import json
import shutil
import tempfile
from pathlib import Path
from typing import Annotated, Any

import tomlkit
import typer
from devkit.config import section
from devkit.notebooks import DEFAULT_KERNEL, DEFAULT_TIMEOUT, _dump, _execute, _sources, notebook_of
from devkit.paths import shown

__all__ = ["app", "controlled", "demo_names", "notebook_path", "notebook_text", "stale"]

ROOT = Path(__file__).resolve().parents[2]
DEMOS = ROOT / "demos"
MANIFEST = "svgwriter.toml"
SCRIPT = "main.py"
ENTRY_GUARD = "if __name__ =="
SKIPPED = ("output", "__pycache__", ".ipynb_checkpoints")
CONTROLS_DECORATOR = "controls"
WIDGET_MIME = "application/vnd.jupyter.widget-view+json"
QUICK_SVG = {"planets-explainer": {"fps": 6}}
STILLS: dict[str, tuple[dict[str, Any], ...]] = {
    "blobs": ({"count": 3, "melt": 8}, {"count": 9, "melt": 24, "speed": 2.0}),
    "calculator-kit": ({"style": "glass", "accent": "#4f46e5", "shape": "pill"},
                       {"style": "brutal", "layout": "scientific 5x6", "font": "mono", "accent": "#0d9488"},
                       {"style": "soft", "layout": "compact 4x4", "shape": "circle", "accent": "#e11d48"}),
    "planets-explainer": ({"scene": "700× wider"}, {"speed": 3.0}),
    "playing-card": ({"rank": "7", "suit": "♠", "hue": 210}, {"rank": "K", "suit": "♣", "hue": 140},
                     {"rank": "A", "suit": "♦", "iridescence": 0.8, "glow": False}),
    "poster": ({"theme": "night"}, {"theme": "blueprint"}, {"hue": 120, "title": "Wave"}),
    "text-effects": ({"smoke": "ice", "metal": "neon", "wind": "glitch"},
                     {"sparks": "neon", "snow": "fire", "smoke": "snow"}),
}
SETUP = """import svgwriter as svg

project = svg.Project.load()
theme = svg.Theme.load(project.config.theme)
theme.__enter__();"""
SETUP_NOTE = "The project's theme applies to everything below, as it does when the project builds."
IMPORTS = "from IPython import display as ipy"
HELPERS = f"""import functools

{IMPORTS}


def in_project(function):
    @functools.wraps(function)
    def draw(doc, **values):
        size = project.config.size
        sheet = svg.Document(*size, theme=theme) if isinstance(size, tuple) else svg.Document(size=size, theme=theme)
        with theme:
            result = function(sheet, **values)
        return sheet if result is None else result

    return draw


def show(function, **values):
    ipy.display(ipy.SVG(data=in_project(function)(None, **values).to_string()))"""
INTERACT_NOTE = ("Every control of `{function}` becomes an input: in a running notebook (with the `widget` "
                 "extra) this panel redraws the drawing as you change them. A saved notebook cannot keep "
                 "live widgets, so the stills below show other values.")
INTERACT = "svg.interact(in_project({function}))"
STILLS_NOTE = "The same function for other control values."
STILL = "show({function}, **{values})"
SHOW_NOTE = ("`project.build` writes the outputs listed in `svgwriter.toml` (here only the SVG, which keeps "
             "animations as SMIL) and the notebook shows each one.")
SHOW = """for path in project.build(["svg"]):
    ipy.display(ipy.SVG(filename=str(path)))"""
HELP = {"help_option_names": ["-h", "--help"]}

app = typer.Typer(name="demo-notebooks", help="Jupyter notebooks of the demos, written as demos/<name>/<name>.ipynb.",
                  add_completion=False, no_args_is_help=True, context_settings=HELP)


def demo_names() -> list[str]:
    """Names of the demo projects, sorted."""
    return sorted(path.name for path in DEMOS.iterdir() if (path / MANIFEST).is_file())


def notebook_path(name: str) -> Path:
    """Where the notebook of demo *name* is saved."""
    return DEMOS / name / f"{name}.ipynb"


def controlled(name: str) -> list[str]:
    """Names of the functions of demo *name*'s ``main.py`` that declare controls with ``@svg.widgets.controls``."""
    tree = ast.parse((DEMOS / name / SCRIPT).read_text(encoding="utf-8"))
    return [node.name for node in tree.body if isinstance(node, ast.FunctionDef)
            and any(isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and call.func.attr == CONTROLS_DECORATOR for call in node.decorator_list)]


def _cell(kind: str, source: str) -> dict[str, Any]:
    cell: dict[str, Any] = {"cell_type": kind, "metadata": {}, "source": source}
    if kind == "code":
        cell.update(execution_count=None, outputs=[])
    return cell


def notebook_text(name: str) -> dict[str, Any]:
    """The notebook of demo *name* without outputs: its ``main.py`` cells plus the generated cells."""
    notebook = notebook_of((DEMOS / name / SCRIPT).read_text(encoding="utf-8"), DEFAULT_KERNEL)
    cells = [cell for cell in notebook["cells"]
             if not (cell["cell_type"] == "code" and cell["source"].startswith(ENTRY_GUARD))]
    cells[1:1] = [_cell("markdown", SETUP_NOTE), _cell("code", SETUP)]
    functions = controlled(name)
    if functions:
        function = functions[0]
        cells += [_cell("markdown", INTERACT_NOTE.format(function=function)),
                  _cell("code", f"{HELPERS}\n\n\n{INTERACT.format(function=function)}"),
                  _cell("markdown", STILLS_NOTE)]
        cells += [_cell("code", STILL.format(function=function, values=values)) for values in STILLS[name]]
    cells += [_cell("markdown", SHOW_NOTE), _cell("code", SHOW if functions else f"{IMPORTS}\n\n{SHOW}")]
    for index, cell in enumerate(cells):
        cell["id"] = f"cell-{index}"
    notebook["cells"] = cells
    return notebook


def _without_widgets(notebook: dict[str, Any]) -> None:
    """Drop outputs that are live widgets, which a saved notebook cannot keep."""
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell["outputs"] = [output for output in cell["outputs"] if WIDGET_MIME not in output.get("data", {})]


def _quick_copy(name: str, folder: Path) -> Path:
    """Copy demo *name* into *folder* with small SVG animation settings where it animates, and return the copy."""
    root = folder / name
    shutil.copytree(DEMOS / name, root, ignore=shutil.ignore_patterns(*SKIPPED))
    manifest = root / MANIFEST
    document = tomlkit.parse(manifest.read_text(encoding="utf-8"))
    if name in QUICK_SVG:
        document["outputs"]["svg"] = QUICK_SVG[name]
        manifest.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def stale() -> list[Path]:
    """Notebooks that are missing or whose cells differ from their demo's ``main.py``."""
    found = []
    for name in demo_names():
        target = notebook_path(name)
        have = _sources(json.loads(target.read_text(encoding="utf-8"))) if target.is_file() else None
        if have != _sources(notebook_text(name)):
            found.append(target)
    return found


@app.command()
def build(names: Annotated[list[str] | None, typer.Argument(help="Only these demos.")] = None,
          no_run: Annotated[bool, typer.Option("--no-run", help="Write the cells without running them.")] = False) -> None:
    """Write demos/<name>/<name>.ipynb for each demo, run in a quick copy of the demo so the outputs are saved."""
    chosen = [name for name in demo_names() if not names or name in names]
    drop = (section("notebooks") or {}).get("drop", [])
    for name in chosen:
        notebook = notebook_text(name)
        if not no_run:
            with tempfile.TemporaryDirectory(prefix="demo-nb-") as work:
                notebook = _execute(notebook, _quick_copy(name, Path(work)), DEFAULT_TIMEOUT, DEFAULT_KERNEL, drop)
            _without_widgets(notebook)
        target = notebook_path(name)
        target.write_text(_dump(notebook), encoding="utf-8", newline="\n")
        typer.echo(f"wrote {shown(target)}")
    typer.echo(f"{len(chosen)} notebook(s) built")


@app.command()
def check() -> None:
    """Exit 1 when a demo's notebook is missing or its cells differ from main.py (outputs are not compared)."""
    found = stale()
    for path in found:
        typer.echo(f"stale: {shown(path)}", err=True)
    if found:
        typer.echo(f"{len(found)} notebook(s) out of date: run `svgwriter demo-notebooks build`", err=True)
        raise typer.Exit(1)
    typer.echo("demo notebooks up to date")
