"""
Reading TikZ pictures back into a document of paths.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._constants import COMMENT_RE, PICTURE_RE
from ._reading import to_document
from ._tikz_nodes import _Context
from ._tikz_paths import _PathReader
from ._tikz_scopes import _bounds, _events, _frame, _picture_options, _Scope, _unroll
from ._tikz_styles import _definitions, _style
from ._tikz_syntax import _expand, _options, _style_table, _tokens

if TYPE_CHECKING:
    from ...document import Document

__all__ = ["read_tikz"]


def read_tikz(text: str) -> Document:
    """Read the ``\\draw``, ``\\fill``, ``\\filldraw`` and ``\\path`` commands of TikZ source as paths.

    Parameters
    ----------
    text : str
        LaTeX source holding a ``tikzpicture`` or bare TikZ commands.

    Returns
    -------
    Document
        The drawing in TeX points with y pointing down, sized to
        ``\\useasboundingbox`` when present and fitted to the content otherwise.

    Raises
    ------
    ValueError
        If *text* has no ``tikzpicture`` and no path commands.

    See Also
    --------
    svgwriter.export._vector._eps_read.read_eps : Read PostScript.

    Notes
    -----
    Reads what :func:`~svgwriter.export._vector._tikz.to_tikz` writes and
    common hand-written pictures. Coordinates are ``(x,y)`` and
    ``(angle:radius)``, absolute or ``+``/``++`` relative, unitless (scaled by
    the picture's ``x``, ``y``, ``scale``, ``xscale`` and ``yscale``, 1 cm by
    default) or with ``pt bp mm cm in pc`` units. Path operations are ``--``,
    ``|-``, ``-|``, ``.. controls .. and ..``, ``cycle``, ``rectangle``,
    ``circle``/``ellipse`` with ``(r)``, ``(a and b)`` or ``[radius=r]``.
    Options are colour names and xcolor mixes
    (``red!30!blue``), ``draw=``, ``fill=``, ``color=``, ``line width=`` and
    the named widths, ``opacity``, ``fill opacity``, ``draw opacity``,
    ``dashed``/``dotted``/``dash pattern=``, ``line cap``, ``line join``,
    ``miter limit`` and ``even odd rule``; colours come from
    ``\\definecolor`` (``RGB``, ``rgb``, ``HTML``, ``gray``, ``cmyk``) and
    ``\\colorlet``.

    Nodes (``\\node``, ``\\coordinate`` and ``node``/``coordinate`` inside a
    path) become centred ``<text>`` coloured by ``color``/``text``, with
    simple markup removed. A node sits ``at (x,y)``, at the current path
    point, or along the segment before it for ``pos=t``, ``midway``,
    ``near start`` and the like; ``above``, ``below``, ``left``, ``right``
    (with their pairs and an optional distance), ``anchor``, ``xshift`` and
    ``yshift`` place it. ``draw``/``fill`` with ``rectangle``, ``circle`` or
    ``ellipse`` paint a border sized from the text width, ``inner sep``
    (3.333pt) and ``minimum size/width/height``. Names such as ``(a)`` and
    ``(a.north)`` (compass anchors) are usable as path coordinates later.

    ``\\tikzset{name/.style={...}}``, ``/.append style``, ``\\tikzstyle`` and
    the picture's own ``name/.style`` define styles, expanded where the name is
    an option, with ``every node`` and ``every path``. ``scope`` options
    (colours, widths, ``shift``, ``xshift``, ``yshift``, ``scale``,
    ``xscale``, ``yscale``, ``rotate``) apply to the commands inside, nested.
    ``\\foreach \\x in {1,2,3}``, ``{0,...,4}``, ``{1,3,...,9}`` and
    ``\\x/\\y in {1/a,2/b}`` are unrolled by substituting the variables
    before parsing; arithmetic on them (``\\x*2``) is not evaluated.

    Macros, ``to``/``arc``/``grid`` operations, positioning libraries
    (``right=of a``), ``sloped``, node rotation and shading are not
    interpreted; a command that cannot be read is skipped.

    Examples
    --------
    >>> from svgwriter.export._vector._tikz_read import read_tikz
    >>> doc = read_tikz(r"\\begin{tikzpicture}\\fill[blue] (0,0) rectangle (1,1);\\end{tikzpicture}")
    >>> doc[0].get("fill"), round(doc[0].bounds().width, 2)
    ('#0000ff', 28.45)
    """
    text = _unroll(COMMENT_RE.sub("", text))
    events = _events(text)
    if not any(kind == "cmd" for kind, *_ in events) and PICTURE_RE.search(text) is None:
        raise ValueError("not TikZ: no tikzpicture and no \\draw, \\fill, \\filldraw or \\path command")
    picture = _picture_options(text)
    context = _Context(_definitions(text), _style_table(text, picture))
    styles = context.styles
    scopes = [_Scope(_frame(picture), _expand(_options(picture), styles))]
    every_path = _expand(styles.get("every path", []), styles)
    shapes, view = [], None
    for kind, command, options, body in events:
        if kind == "begin":
            scopes.append(scopes[-1].child(_expand(_options(options), styles)))
        elif kind == "end":
            scopes = scopes[:-1] or scopes
        else:
            pairs = scopes[-1].pairs + every_path + _expand(_options(options), styles)
            reader = _PathReader(scopes[-1].frame, context, pairs)
            try:
                ops = reader.read(_tokens(body))
            except (ValueError, IndexError, KeyError):
                continue
            if command == "useasboundingbox":
                view = _bounds(ops) or view
            elif ops:
                shapes.append(_style(command, pairs, context.colors).shape(ops))
            shapes += reader.extras
    return to_document(shapes, view)
