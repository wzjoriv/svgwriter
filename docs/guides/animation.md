# Animation

## SMIL in the document

Every SVG 1.1 animation element is available (`animate`, `set`, `animateMotion`, `animateTransform`,
`animateColor`) and is written as SMIL for browsers to play:

```python
import svgwriter as svg

doc = svg.Document(100, 100)
ball = doc.circle(20, 50, 10, fill="tomato")
ball.append(svg.Animate(attribute_name="cx", from_=20, to=80, dur="2s", repeat_count="indefinite"))
doc.save("ball.svg")
```

## Presets

`element.animate` adds ready-made SMIL animations and chains:

```python
logo = svg.circle(50, 50, 20, fill="teal")
logo.animate.fade_in(0.5).spin(2, begin=0.5)
```

| Group | Presets |
|---|---|
| Appear / disappear | `show(at=)`, `hide(at=)` (at once), `fade_in`, `fade_out`, `draw` (stroke draws on), `wipe(side)`, `typewriter` (text) |
| Create | `create` (outline draws on, then the fill fades in), `uncreate` (the reverse), `write` (text character by character, a group child by child) |
| Motion | `move_by(dx, dy)`, `move_to(x, y)`, `slide_in(side)`, `follow(path)`, `bounce`, `shake` |
| Turn, scale and skew | `rotate(angle)`, `scale(factor)` (or `(sx, sy)`), `skew(x=, y=)`, `spin(turns=)`, `grow`, `shrink`, `pulse` (about the element's anchor, or `about=(x, y)`) |
| Color and any attribute | `blink`, `color_cycle(colors)`, `tween(attribute, start, end)` |
| Shape | `morph(target)` (a `<path>` turning into any shape, contours matched by `interpolate`) |
| Groups | `stagger(preset, step=)` (each child starts `step` seconds after the last) |

Every preset takes `dur` and `begin` in seconds, `repeat` (a count or `"indefinite"`) and keeps its end
state unless `freeze=False`. They are plain SMIL, so they play in browsers and in `doc.at(t)`, video,
animated GIF, APNG and WebP.

The transform presets are relative and add up: each starts from wherever the element is, after its
own transform and any earlier preset, so `el.animate.rotate(30).rotate(30, begin=1)` ends at 60
degrees. They pivot like the static methods: `el.rotate(30)` and `el.animate.rotate(30)` both turn
about `el.anchor` (the bounding-box centre unless set), and `about=(x, y)` takes a point in parent
coordinates (local ones with `local=True`). `move_by` measures along the parent's axes unless
`local=True`.

`about=` also takes a name, read on the element's own box so it moves and resizes with the element:
`"center"`, `"top"`, `"bottom"`, `"left"`, `"right"`, `"top_left"`, `"top_right"`, `"bottom_left"`,
`"bottom_right"` (the names of `BBox.point`), `"origin"` for the local `(0, 0)` and, on text,
`"baseline"` for the start of the first baseline. The same names set the anchor itself, so every later
transform and preset pivots there; an unknown name raises `ValueError` listing the valid ones:

```python
door = svg.rect(20, 20, 30, 60, fill="sienna")
door.animate.rotate(-30, about="left")        # swings on its hinge
needle = svg.rect(48, 20, 4, 40, fill="crimson", anchor="bottom")
needle.rotate(45)                              # turns about its base
needle.animate.spin(4, repeat="indefinite")    # and so does the animation
```

```python
card = svg.rect(20, 20, 60, 30, fill="slateblue")
card.animate.rotate(90).scale(1.5, begin=1).skew(x=20, begin=2).move_by(40, 0, begin=3)
```

`create`, `uncreate` and `write` animate `stroke-dasharray`/`stroke-dashoffset` and `fill-opacity`.
A shape without a stroke is drawn with its fill color, every contour of a shape draws at once, and
`write` starts each character a little before the previous one finishes:

```python
title = svg.text("Hello", x=10, y=60, font_size=48, fill="tomato")
title.animate.write(1.5)
badge = svg.circle(50, 50, 30, fill="teal")
badge.animate.create(1).uncreate(1, begin=3)
```

## Presets of your own

A reusable animation is a typed function decorated with `@svg.preset.animation`. Its first positional
parameter is the element's `Motion` (what `el.animate` returns), every option is keyword-only with a
default, and it returns the motion so calls chain:

```python
@svg.preset.animation
def bob(motion: svg.Motion, *, height: float = 8, dur: float = 1, begin: float = 0,
        ease: svg.EaseLike | None = None) -> svg.Motion:
    """Rise by *height* and come back down."""
    half = dur / 2
    return motion.move_by(0, -height, half, begin=begin, ease=ease).move_by(0, height, half, begin=begin + half,
                                                                            ease=ease)


dot = svg.circle(20, 40, 6, fill="teal")
dot.animate.apply(bob, height=12).fade_out(begin=1)   # typed: editors complete and check the options
dot.animate.bob(begin=2)                              # by name, like the built-in presets
row = svg.Group()
row += [svg.circle(20 + 20 * index, 80, 6) for index in range(4)]
row.animate.stagger("bob", step=0.2, height=6)
print(svg.preset.list("animation")[-1])
svg.preset.unregister("animation", "bob")
```

The shape is checked when the function is decorated, so a mistake fails at once with a `TypeError`
showing the expected signature. Returning None is accepted too; `apply` returns the motion either way.
`@svg.preset.animation(name="hop")` registers under another name. A taken name raises `ValueError` naming
the function that owns it, built-in presets included; `replace=True` replaces one on purpose (a
replacement can still call the original as `svg.Motion.spin(motion, ...)`), and unregistering the
replacement brings the built-in back. `svg.preset.list("animation")` lists the built-in presets and
yours, and an unknown name in `el.animate.<name>` raises `AttributeError` suggesting the closest ones.
`Motion.apply` also runs functions that are not registered at all.

In a [project](projects.md), presets live in the `animations/` folder and are registered when it is
imported.

## Easing

Every preset with a duration (all but `show` and `hide`), and `Animate`, `AnimateTransform`, `AnimateColor` and `AnimateMotion`, takes `ease=`: a
timing curve for the whole animation. The named curves are the standard cubic béziers:

| `ease=` | Control points `(x1, y1, x2, y2)` | Feel |
|---|---|---|
| `"linear"` (default) | `(0, 0, 1, 1)` | constant speed |
| `"ease"` | `(0.25, 0.1, 0.25, 1)` | quick start, long gentle stop |
| `"ease-in"` | `(0.42, 0, 1, 1)` | starts slowly |
| `"ease-out"` | `(0, 0, 0.58, 1)` | stops slowly |
| `"ease-in-out"` | `(0.42, 0, 0.58, 1)` | slow at both ends |
| `"step-start"`, `"step-end"`, `("steps", n)` | | jumps instead of gliding |

```python
box = doc.rect(10, 10, 20, 20, fill="teal")
box.animate.move_to(180, 20, dur=1, ease="ease-in-out")
box.animate.fade_in(0.5, ease=(0.2, 0.9, 0.3, 1.0))         # a custom bézier
```

Any Python function from time to progress works too, overshoot included:

```python
def back_out(t):
    return 1 + 2.7 * (t - 1) ** 3 + 1.7 * (t - 1) ** 2

box.animate.slide_in("left", ease=back_out)
```

The curve covers the whole timeline, so a preset with several `values` (`bounce`, `shake`, `pulse`,
`color_cycle`) moves through all of them along the one curve. Béziers are written as SMIL
`calcMode="spline"` with exact `keySplines` (one piece of the curve per value interval), steps as
`calcMode="discrete"`, and a function is sampled into 24 to 60 `values` at even times (more where it
bends more) played linearly; `svg.Ease(curve)(t)` evaluates any of them.

## Playing SMIL

`doc.at(seconds)` returns a static copy with every animation applied at that moment, so SMIL can be
inspected, rasterized or exported frame by frame, and `render_animation` plays it without an `update`
callback. It covers `animate`, `set`, `animateColor`, `animateTransform` and `animateMotion` with clock
timing, repeats, `fill="freeze"`, `values`/`keyTimes`, every `calcMode` (discrete, linear, paced and
spline with `keySplines`), `keyPoints` and `additive="sum"`, so frames match what browsers play.

```python
frame = doc.at(1.0)          # the ball halfway along
```

Saving keeps the animation where the format can play it: `.svg` and `.svgz` keep the SMIL elements,
and `.gif` becomes an animated GIF of the whole animation (`fps=`, `duration=`, `loop=`; no ffmpeg
needed); `.png` and `.webp` become APNG and animated WebP with `animate=True`. Other still formats show one moment, chosen with `time=`:
`doc.save("end.png", time=2.0)`.

## Python updates and SMIL together

A scene or `render_animation` can drive the same drawing from Python (`update`) and from SMIL. For each
frame at time `t`:

1. `update(t)` runs first and changes the document;
2. SMIL is then applied at `t` on a copy of the result (`doc.at(t)`), and that copy is drawn.

Python and SMIL on different attributes simply combine. On the same attribute SMIL wins, since it is
applied last, unless the animation has `additive="sum"`, which adds to whatever `update` set (every
transform preset is additive, so `update` can move an element that a preset is spinning). The
duration defaults to the end of the last SMIL animation. An `.svg` file keeps only the SMIL, as Python
does not run in a browser; video, GIF, APNG and WebP exports include both.

```python
class Drift(svg.Scene):
    width, height, fps = 120, 120, 24     # duration: 2 s, the last SMIL end

    def build(self, doc):
        self.dot = doc.circle(60, 60, 10, fill="gold")
        self.dot.animate.fade_in(0.5).tween("r", 10, 30, 2)

    def update(self, seconds):
        self.dot.cx = 30 + 30 * seconds   # Python moves it
        self.dot.r = 5                    # ignored: the r tween wins

drift = Drift()
drift.update(1.0)
frame = drift.document.at(1.0)            # cx 60 from Python, r 20 from SMIL, fully faded in
```

## Video through ffmpeg

`render_animation` draws frames and pipes them to ffmpeg (mp4, gif, webm, mov, apng; a `.png` path
writes numbered frames). The `update` callback changes the document for each frame:

```python
import math

def update(document, seconds):
    ball.place(50 + 30 * math.cos(math.pi * seconds), 50 + 30 * math.sin(math.pi * seconds))

# doc.render_animation("orbit.mp4", fps=30, duration=2, renderer="skia", update=update)
```

The built-in `"skia"` renderer returns raw RGBA frames. Any callable `renderer(document, seconds)` that
returns PNG bytes or a uint8 `(H, W, 4)` array works, as does a `"module:function"` name. Missing ffmpeg
raises `FFmpegNotFoundError` before any rendering.

## Scenes

A `svg.Scene` subclass is one animation: class attributes set `width`, `height`, `fps`, `duration` and
`renderer` (defaults 640 by 360, 30 fps, the SMIL length, `"skia"`), `build(doc)` draws into an empty
document of that size once, and `update(seconds)` sets the state for each frame. SMIL animations in
the drawing play as well, so a scene can use presets, Python, or both.

```python
class Pulse(svg.Scene):
    width, height, fps, duration = 120, 120, 24, 2.0

    def build(self, doc):
        doc.rect(0, 0, 120, 120, fill="midnightblue")
        self.dot = doc.circle(60, 60, 10, fill="gold")
        self.dot.animate.fade_in(0.5)

    def update(self, seconds):
        self.dot.r = 10 + 30 * seconds / self.duration

pulse = Pulse()
still = pulse.render(1.0)        # PNG bytes of the frame at 1 s
frames = list(pulse.frames())    # 48 frames, not encoded
# pulse.save()                   # Pulse.mp4; or save("pulse.gif"), save("pulse.png") for numbered frames
```

`build` receives the document rather than returning one, so the size is declared once, as class
attributes, and `build` holds only drawing code. It runs when the scene is created; keep the elements
that `update` changes on `self`. `update` gets absolute time, so frames can be drawn in any order. In a
notebook a scene displays as its animated SVG. `svg.Scene(doc)` animates an existing document as it is.

A file can hold any number of scenes. A class whose name starts with `_` is skipped, so a shared base
class stays out of the list. `svg.video.load_scenes` returns them, and the command line renders them:

```console
$ python -m svgwriter animate scenes.py --list            # print the scene names
$ python -m svgwriter animate scenes.py                   # every scene to <Name>.mp4
$ python -m svgwriter animate scenes.py Intro Outro --format gif
$ python -m svgwriter animate scenes.py:Intro -o intro.webm
$ python -m svgwriter animate mypackage.scenes:Intro      # an importable module
$ python -m svgwriter render scenes.py Intro --time 1.5   # one frame to Intro.png
```

`--fps`, `--duration` and `--renderer` override the scene's settings. An `.svg` file is accepted too and
plays its SMIL. See `examples/13_scenes.py`.

## Tweening and morphing

`svg.interpolate(a, b, t)` returns the value a fraction `t` of the way from `a` to `b`: numbers, points,
colors, matrices (rotation, scale and skew blended separately, turning the short way), path data and
whole elements. Elements of the same kind blend their attributes and transform; different shapes morph
as outlines, and paint blends along the way. Outlines pair with outlines and holes with holes, nearest
first; a contour without a partner grows from (or shrinks to) its centre, so a `B` with two holes can
become a ring with one. Each pair is resampled to the same number of points, keeping sharp corners, and
started where the points have least distance to travel, so the in-between shapes do not twist.

```python
start = svg.Polygon.regular(50, 50, 40, 5, fill="gold")
end = svg.circle(50, 50, 30, fill="teal")
frames = [svg.interpolate(start, end, i / 10) for i in range(11)]
print(frames[5].tag, frames[5].get("fill"))
```

In an `update` callback this gives morphs and tweens per frame, for instance
`doc[0] = svg.interpolate(start, end, time / duration)`.

Attribute values inside elements that cannot blend (keywords such as `none`, font names, lists of different
lengths) switch halfway, as SMIL does. Called directly on two values it cannot blend, `interpolate` raises
`TypeError`. Teach it a new type with `svg.register_interpolator`:

```python
class Weight(int):
    pass

svg.register_interpolator(Weight, lambda a, b, t: Weight(round(a + (b - a) * t, -2)))
print(svg.interpolate(Weight(400), Weight(700), 0.5))
svg.unregister_interpolator(Weight)
```

## Video in

`svgwriter.video.Video(path)` reads a video lazily through ffmpeg: `video[i]` is frame `i` as an
`<image>`, `video.at(seconds)` the frame shown at that time, and iterating streams every frame as a
numpy array. Mix footage with vector animation in `update`:

```python
from svgwriter.video import Video

# clip = Video("footage.mp4")
# backdrop = doc.add(clip[0])
# def update(document, seconds):
#     backdrop.color = clip.at(seconds).color
```

