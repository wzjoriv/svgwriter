## What

<!-- One or two sentences: what changes and why. Link the issue: Closes #... -->

## Checks

- [ ] `python scripts/dev.py check` passes (ruff, tests, docs with warnings as errors)
- [ ] Stubs are current (`python scripts/dev.py stub check`)
- [ ] Rendering changes were compared visually (before / after PNG, or the W3C suite score: `python scripts/dev.py svgwriter`)
- [ ] Public API changes are reflected in `README.md` and `docs/`
- [ ] Add the `full-tests` label to run every Python version, Windows and macOS
