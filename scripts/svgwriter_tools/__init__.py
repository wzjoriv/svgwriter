"""svgwriter's own developer commands: the W3C SVG 1.1 test suite and conformance scores.

python scripts/dev.py svgwriter fetch-suite
python scripts/dev.py svgwriter conformance [--filter shapes] [--report build/conformance.md]
python scripts/dev.py svgwriter bench [--count 100000]
"""

from __future__ import annotations

from pathlib import Path

import typer

from ._conformance import run_suite, write_report
from ._suite import SUITE_DIR, SUITE_URL, fetch

app = typer.Typer(name="svgwriter", help=__doc__, add_completion=False, no_args_is_help=True)


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
