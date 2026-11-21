"""svgwriter's own developer commands: the W3C SVG 1.1 test suite, conformance scores and generated code.

python scripts/dev.py svgwriter fetch-suite
python scripts/dev.py svgwriter conformance [--filter shapes] [--report build/conformance.md]
python scripts/dev.py svgwriter bench [--count 100000]
python scripts/dev.py svgwriter gallery
python scripts/dev.py svgwriter formats [--format pdf --format tikz] [--out build/formats]
python scripts/dev.py svgwriter signatures write|check
python scripts/dev.py svgwriter demo-notebooks build|check
"""

from __future__ import annotations

from pathlib import Path

import typer

from ._conformance import run_suite, write_report
from ._demo_notebooks import app as demo_notebooks
from ._suite import SUITE_DIR, SUITE_URL, fetch

app = typer.Typer(name="svgwriter", help=__doc__, add_completion=False, no_args_is_help=True)
app.add_typer(demo_notebooks, name="demo-notebooks")


@app.command()
def gallery() -> None:
    """Render the README gallery: each example's picture and each demo's tile as a PNG (animations as GIF).

    Example pictures go to docs/_static/examples, demo tiles to docs/_static/demos.
    """
    from ._gallery import build_demos, build_gallery

    for path in [*build_gallery(), *build_demos()]:
        typer.echo(f"wrote {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}")


@app.command("fetch-suite")
def fetch_suite(url: str = typer.Option(SUITE_URL, help="Archive URL."),
                target: Path = typer.Option(SUITE_DIR, help="Where to unpack (git-ignored).")) -> None:
    """Download and unpack the W3C SVG 1.1 Second Edition test suite (about 15 MB)."""
    fetch(url, target)
    typer.echo(f"suite ready in {target}")


@app.command()
def conformance(
    suite: Path = typer.Option(SUITE_DIR, help="Suite folder with svg/ and png/."),
    filter: str = typer.Option("", help="Glob or substring of test names."),
    report: Path | None = typer.Option(None, help="Write a Markdown report here."),
    failures: bool = typer.Option(False, help="Print failing tests."),
) -> None:
    """Score round-trip fidelity and rendering against the W3C SVG 1.1 suite."""
    if not (suite / "svg").is_dir():
        typer.echo("suite missing; run: python scripts/dev.py svgwriter fetch-suite", err=True)
        raise typer.Exit(2)
    outcomes = run_suite(suite, filter, echo=typer.echo if failures else None)
    for kind in ("roundtrip", "render"):
        scored = [o for o in outcomes if o.status(kind) != "skipped"]
        passed = sum(o.status(kind) == "pass" for o in scored)
        typer.echo(f"{kind:9}: {passed}/{len(scored)} passed ({100.0 * passed / max(len(scored), 1):.1f}%)")
    if report is not None:
        write_report(outcomes, report)
        typer.echo(f"wrote {report}")


@app.command()
def bench(count: int = typer.Option(100_000, help="Elements in the large-tree benchmarks."),
          figures: int = typer.Option(100, help="Documents in the batch benchmarks.")) -> None:
    """Time building, writing, parsing, geometry, rendering and exporting."""
    from ._bench import run

    for timing in run(count, figures):
        typer.echo(f"{timing.name:34} {timing.seconds * 1000:9.1f} ms {timing.per_item_us:10.2f} us/item")


@app.command()
def formats(format: list[str] = typer.Option([], help="Format names; every format that writes when omitted."),
            out: Path = typer.Option(Path("build/formats"), help="Where to write the sheets and scores.")) -> None:
    """Export the feature drawing to every format, render each export and round trip, and score them."""
    from ._formats import audit, feature_drawing, write_report

    reference, results = audit(feature_drawing(), format or None)
    for path in write_report(reference, results, out):
        typer.echo(f"wrote {path}")
    typer.echo((out / "scores.md").read_text(encoding="utf-8"))


@app.command()
def signatures(action: str = typer.Argument(..., help="write: regenerate; check: fail when stale.")) -> None:
    """Generate every element class's typed __init__ from its attribute groups, or check the generated code is current."""
    from ._signatures import check, write

    if action == "write":
        for path in write():
            typer.echo(f"wrote {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}")
    elif action == "check":
        stale = check()
        for path in stale:
            typer.echo(f"stale: {path}", err=True)
        if stale:
            typer.echo("run: python scripts/dev.py svgwriter signatures write", err=True)
            raise typer.Exit(1)
        typer.echo("element signatures are current")
    else:
        raise typer.BadParameter("use write or check", param_hint="ACTION")
