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

## Video through ffmpeg

`render_animation` draws frames and pipes them to ffmpeg (mp4, gif, webm, mov, apng). The `update`
callback changes the document for each frame:

```python
import math

def update(document, seconds):
    ball.place(50 + 30 * math.cos(math.pi * seconds), 50 + 30 * math.sin(math.pi * seconds))

# doc.render_animation("orbit.mp4", fps=30, duration=2, renderer="skia", update=update)
```

The built-in `"skia"` renderer returns raw RGBA frames. Any callable `renderer(document, seconds)` that
returns PNG bytes or a uint8 `(H, W, 4)` array works, as does a `"module:function"` name. Missing ffmpeg
raises `FFmpegNotFoundError` before any rendering.

From the command line:

```console
$ python -m svgwriter animate scene.py -o out.mp4 --fps 30
```
