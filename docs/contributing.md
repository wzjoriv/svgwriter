# Contributing

Set up a development install from a clone of the repository:

```console
$ pip install -e ".[dev,test]"
```

All developer commands go through one entry point:

```console
$ python scripts/dev.py test                     # test tiers
$ python scripts/dev.py check                    # ruff, tests and the docs build
$ python scripts/dev.py docs                     # build these docs
$ python scripts/dev.py stub generate            # .pyi stubs (git-ignored; the release workflow builds the shipped ones)
$ python scripts/dev.py svgwriter conformance    # W3C SVG 1.1 suite (after: svgwriter fetch-suite)
$ python scripts/dev.py svgwriter bench          # timing of the hot paths
$ python scripts/dev.py svgwriter formats        # every export and round trip side by side, scored (build/formats)
$ python scripts/dev.py notebooks build          # example notebooks from their cell scripts
```

## Conventions

- Code lives in the `svgwriter` package; modules whose names start with `_` are private and imported only
  inside their own package. Public names are re-exported with an explicit `__all__`.
- NumPy-style docstrings with type hints, and runnable examples for public functions.
- Named constants live in `_constants.py` modules.
- Each change has tests next to the code it touches (`tests/` mirrors the package).
- One branch per change; pull requests describe the user-visible change and how it was checked.
