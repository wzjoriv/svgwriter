"""
Ready-made content: composite shapes, paints, filters, markers, effects, presets and fonts.

Sub-packages
------------
paths
    Composite shapes (star, gear, arrow) and the ``drawing`` decorator.
patterns, gradients, filters, markers, effects
    Ready-made paints, filters, line markers and effects for any element.
preset
    Presets of your own by kind (animation, shape, pattern and more).
fonts
    Fonts from drawings: glyphs, icons and kerning written as OTF, TTF, WOFF and WOFF2.

Notes
-----
The top-level package re-exports these, so ``svg.patterns.stripes()`` and
``svg.FontBuilder`` work without this path. The group itself imports nothing.

Examples
--------
>>> from svgwriter.catalog import patterns
>>> patterns.stripes().tag
'pattern'
"""
