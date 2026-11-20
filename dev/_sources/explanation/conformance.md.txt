# Conformance

svgwriter is measured against the W3C SVG 1.1 Second Edition test suite (526 files):

```console
$ python scripts/dev.py svgwriter fetch-suite
$ python scripts/dev.py svgwriter conformance --report build/conformance/report.md
```

Scripting, DOM, interactivity and `foreignObject` tests are out of scope, as those features are.

**Round-trip fidelity: 429 / 430.** Each file is parsed, written back, and both versions are rendered
by skia; the pictures must match. The one difference is a namespace test where skia ignores XML
namespaces and svgwriter's output is the correct one. Four files skia cannot read are excluded.

**Rendering: 148 / 434** against the reference PNGs. Most misses differ by 1-3 % in the page labels, which
the suite sets in its own SVG font; the rest are features skia's renderer lacks (SMIL animation, some
filters and masks).
