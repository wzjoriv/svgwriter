# Planets explainer

A two-part explainer built from `Scene` classes:

1. **Eight planets**: the orbits drawn to scale from `assets/data/planets.csv` (Neptune's is 78 times
   Mercury's), every planet circling the Sun at its own pace.
2. **700× wider**: the Sun beside Betelgeuse, to scale, while a row of 100 Suns lines up and a rolling
   counter counts them.

What it shows:

- Scenes with SMIL presets (`fade_in`, `stagger`, the built-in `breathe` behaviour) and Python motion: the
  project's own `orbit` behaviour (`animations/orbit.py`, registered with `@svg.preset.behavior`) and an
  `update` that adds Suns and turns the counter's digit wheels (`components/counter.py`).
- Baking: the SVG and PowerPoint outputs turn the behaviours and the per-frame updates into SMIL, so the
  SVG plays in a browser like the video.
- The theme (`theme.toml`) and data read from `assets/`.

Controls: `explainer` takes the clip (`Eight planets` or `700× wider`) and a `time scale` that speeds up the orbits and the counter. They drive `svg.explore` in the notebook; the project's entry stays the two scenes, so `svgwriter build` still writes one clip each, and `svgwriter preview` shows no form for scenes.

Open the notebook, [planets-explainer.ipynb](planets-explainer.ipynb), to see the demo step by step with its pictures; run it to get a panel for the controls.

```
svgwriter preview                # every output, playing
svgwriter build                  # output/planets-explainer-<Scene>.{mp4,svg,pptx}; needs ffmpeg for MP4
svgwriter build --format gif     # without ffmpeg: a GIF per scene
python main.py                   # MP4 when ffmpeg is installed, else GIF, plus SVG and PPTX
```

PowerPoint needs the office extra: `pip install pysvgwriter[office]`.
