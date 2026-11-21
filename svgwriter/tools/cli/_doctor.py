"""
``doctor``: what works on this machine, what is missing and how to add it.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import click

from ..._internal import _platform
from ._constants import DOCTOR_COLUMNS, DOCTOR_FEW_FAMILIES, DOCTOR_MARKS, JSON_INDENT

__all__ = ["add_doctor_command", "doctor_report"]


def doctor_report() -> dict[str, Any]:
    """The doctor report: system, capabilities and fonts, as plain data.

    Returns
    -------
    dict of str to Any
        ``python``, ``system`` (OS, distribution, package manager, support), ``system_packages``
        (the Linux command for skia's libraries and baseline fonts, else None), ``capabilities`` and
        ``fonts``.

    Examples
    --------
    >>> from svgwriter.tools.cli._doctor import doctor_report
    >>> sorted(doctor_report())
    ['capabilities', 'fonts', 'python', 'system', 'system_packages']
    """
    from ... import __version__

    found = _platform.system()
    return {
        "python": {"version": sys.version.split()[0], "executable": sys.executable, "svgwriter": __version__},
        "system": {"os": found.os, "distro": found.distro, "name": found.name, "manager": found.manager,
                   "unsupported": found.unsupported},
        "system_packages": _platform.system_packages_hint(found),
        "capabilities": _platform.capabilities(refresh=True).to_dict(),
        "fonts": _platform.font_summary().to_dict(),
    }


def _table(report: dict[str, Any]) -> list[str]:
    system, fonts = report["system"], report["fonts"]
    lines = [f"svgwriter {report['python']['svgwriter']} on Python {report['python']['version']}, "
             f"{system['name']} ({system['os']}, {system['manager'] or 'no known package manager'})"]
    if system["unsupported"]:
        lines.append(f"unsupported: {system['unsupported']}")
    name_width, version_width = DOCTOR_COLUMNS
    for entry in report["capabilities"].values():
        if entry["available"]:
            detail = (entry["version"] or "")[:version_width]
        else:
            detail = f"missing ({entry['purpose']}): {entry['hint']}"
        lines.append(f"  {DOCTOR_MARKS[entry['available']]} {entry['name']:<{name_width}} {detail}".rstrip())
    resolved = ", ".join(f"{generic} -> {family or 'none'}" for generic, family in fonts["resolved"].items())
    lines.append(f"fonts: {fonts['families']} families; {resolved}")
    if report["system_packages"] and (fonts["families"] < DOCTOR_FEW_FAMILIES or not fonts["resolved"]["emoji"]):
        lines.append(f"  add system fonts and skia's libraries: {report['system_packages']}")
    return lines


@click.command(help="Show what works on this machine, what is missing and how to install it on this OS.")
@click.option("--json", "as_json", is_flag=True, help="machine-readable output")
def doctor(as_json: bool) -> None:
    """Print the doctor report as a table, or as JSON with ``--json``."""
    report = doctor_report()
    if as_json:
        click.echo(json.dumps(report, indent=JSON_INDENT, ensure_ascii=False))
        return
    for line in _table(report):
        click.echo(line)


def add_doctor_command(app: click.Group) -> None:
    """Register ``doctor``.

    Parameters
    ----------
    app : click.Group
        The command line application.

    Examples
    --------
    >>> from svgwriter.tools.cli import app
    >>> "doctor" in app.commands
    True
    """
    app.add_command(doctor)
