# Conformance

svgwriter is measured against the W3C SVG 1.1 Second Edition test suite (526 files):

```console
$ python scripts/dev.py svgwriter fetch-suite
$ python scripts/dev.py svgwriter conformance --report build/conformance/report.md
```

**Round-trip fidelity: 429 / 430.** Each file is parsed, written back, and both versions are rendered
by skia; the pictures must match. The one difference is a namespace test where skia ignores XML
namespaces and svgwriter's output is the correct one. Four files skia cannot read are excluded.

**Rendering: 289 / 434 (67 %)** against the reference PNGs. A test passes when at most 1 % of its
pixels differ. The suite's `$Revision$` label and `DRAFT` watermark are bookkeeping, often newer than
the reference PNG, so they are not compared; animated tests are drawn once their animations have
settled, the state the references show.

| Chapter | Passed | Total |
| --- | ---: | ---: |
| animate | 55 | 74 |
| color | 3 | 6 |
| conform | 1 | 2 |
| coords | 24 | 28 |
| filters | 18 | 42 |
| fonts | 3 | 17 |
| imp | 0 | 1 |
| linking | 9 | 12 |
| masking | 13 | 17 |
| metadata | 1 | 1 |
| painting | 25 | 31 |
| paths | 19 | 19 |
| pservers | 22 | 33 |
| render | 3 | 8 |
| shapes | 22 | 22 |
| struct | 36 | 48 |
| styling | 7 | 17 |
| text | 27 | 54 |
| types | 1 | 2 |

Many of the remaining misses differ by 1-5 % in text: the suite sets its labels in its own SVG font,
which svgwriter draws with the nearest installed sans-serif face.

## Out of scope

These parts of SVG 1.1 are not supported, so their tests are skipped or expected to fail:

- **Scripting and the SVG DOM**: `<script>`, event attributes and the `svgdom` tests.
- **Interactivity**: event-based animation begins (`click`, `mouseover`), `cursor`, links followed by a
  viewer, and tests whose reference shows the state after a user action.
- **`foreignObject`** and the `extend` chapter.
- **SVG fonts** (`<font>`, `<glyph>`, `<font-face>` with an SVG source, `altGlyph`): text uses installed
  and registered OpenType fonts.
- **Colour profiles** (`color-profile`, ICC colours).
