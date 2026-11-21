"""Inkscape effect: style the drawing with an svgwriter theme.

Elements carrying svgwriter roles (``role-*`` classes) take the colours and
fonts of a built-in theme or of a ``theme.toml``; the selection can be given a
role first.
"""

from __future__ import annotations

from pathlib import Path

from svgwriter_extension import fail, load, parser, reported_warnings, require_svgwriter, selected, write

__all__ = ["main"]


def main(argv: list[str] | None = None) -> None:
    """Apply ``--theme`` (or ``--theme-file``) and print the restyled drawing."""
    require_svgwriter()
    import svgwriter

    arguments = parser("Apply an svgwriter theme to an Inkscape drawing.")
    arguments.add_argument("--theme", default="light", help="a built-in theme name")
    arguments.add_argument("--theme-file", default="", dest="theme_file", help="a theme.toml, used instead of --theme")
    arguments.add_argument("--role", default="", help="give the selected objects this role first")
    options, _ = arguments.parse_known_args(argv)
    doc = load(options.input_file)
    try:
        if options.theme_file:
            theme = svgwriter.Theme.load(Path(options.theme_file).expanduser())
        else:
            theme = svgwriter.Theme.of(options.theme)
    except (ValueError, OSError, KeyError) as error:
        fail(f"could not load the theme: {error}")
    role = options.role.strip()
    if role:
        if role not in theme.roles:
            fail(f"theme {theme.name!r} has no role {role!r}; it has {', '.join(theme.roles)}")
        for element in selected(doc, options.ids):
            element.as_role(role)
    doc.theme = theme
    write(doc)


if __name__ == "__main__":
    with reported_warnings():
        main()
