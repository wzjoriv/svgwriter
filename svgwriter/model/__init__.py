"""
The SVG object model: elements, their attributes and the values they hold.

Sub-packages
------------
attributes
    ``viewBox``, ``preserveAspectRatio``, inline styles and style sheets, IRI
    references, attribute-name mapping.
units
    Lengths, angles, quantities and unit factories (``mm``, ``inch``, ``deg``, ...).
color
    Color keywords and syntaxes and the ``<paint>`` type.
elements
    One class per SVG 1.1 element.
pathdata
    Path data: commands, parsing, serialization, arc math, ``PathBuilder``.
transform
    Affine matrices and transform lists.
layout
    Stacks and grids that place their children by size.
theme
    Palettes, fonts and role styles applied as CSS classes.
batch
    Many similar shapes made, transformed and written as numpy columns.

Notes
-----
The top-level package re-exports the public names, so ``svg.Rect`` and
``svg.Theme`` work without this path. The group itself imports nothing.

Examples
--------
>>> from svgwriter.model.color import parse_color
>>> parse_color("red").hex
'#ff0000'
"""
