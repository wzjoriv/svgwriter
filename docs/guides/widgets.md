# Widgets

A drawing function with parameters becomes adjustable: `svg.explore` puts sliders, buttons and colour
pickers beside the drawing in a notebook, `svgwriter preview` shows the same controls as a form above a
project's outputs, and `svg.sweep` steps the parameters over time into an animation. All three read one
declaration, because a control is plain data.

## Controls

Declare the controls of a function with `@svg.widgets.controls`, one per parameter. Calling the function
directly still works; the controls only describe its parameters.

```python
import svgwriter as svg

@svg.widgets.controls(
    size=svg.widgets.Slider(10, 80, label="size", format="{:.0f}px"),
    color=svg.widgets.Swatches(["#0ea5e9", "#f43f5e", "#22c55e"]),
    shape=svg.widgets.Segmented(["box", "dot"]),
    outline=svg.widgets.Toggle(),
)
def badge(size=40, color="#0ea5e9", shape="box", outline=False):
    doc = svg.Document(100, 100)
    stroke = {"stroke": "black", "stroke_width": 3} if outline else {}
    if shape == "box":
        doc.rect(50 - size / 2, 50 - size / 2, size, size, fill=color, **stroke)
    else:
        doc.circle(50, 50, size / 2, fill=color, **stroke)
    return doc

badge(size=60, shape="dot")
```

| Control | Value | Input |
| --- | --- | --- |
| `Slider(min, max, step=None, value=None)` | a number (`IntSlider` for whole numbers) | a slider with a readout |
| `RangeSlider(min, max)` | a `(low, high)` pair | a slider with two handles |
| `Number(value, min=, max=)` | a typed-in number | a number field |
| `Toggle(value=False)`, `Checkbox` | `True` or `False` | a switch, a box |
| `Dropdown(options)`, `Segmented(options)` | one option | a menu, a row of buttons |
| `MultiSelect(options)` | a tuple of options | a list to pick from |
| `ColorPicker(value)` | `"#rrggbb"` (`"#rrggbbaa"` when translucent) | a colour picker |
| `Swatches(colors)` | one of the colours | colour chips |
| `Text(value)` | a string | a text field |

Options are a list, or a `{label: value}` mapping when the shown label differs from the value. Every
control takes `label=`; numeric ones also take `units=` and `format=` for the readout. A length unit
(`units="mm"`) makes the function receive a `svg.Length` in that unit. A control without a starting
`value` starts at the function's default for that parameter, else at the middle of a slider or the first
option.

Shorthands stand in for controls, as in the table below; `svg.widgets.control(spec)` shows what one
becomes.

| Shorthand | Control |
| --- | --- |
| `(0, 10)`, `(0, 1, 0.05)` | `Slider` (`IntSlider` when every number is an int) |
| `(svg.mm(0), svg.mm(20))`, `svg.mm(5)` | `Slider` in millimetres |
| `40`, `0.5` | a slider from 0 to twice the value |
| `True`, `False` | `Toggle` |
| `"#ff6347"`, a `svg.Color` | `ColorPicker` |
| any other string | `Text` |
| `["a", "b"]` | `Segmented` with up to four options, `Dropdown` with more |
| `["#f00", "#0f0"]` | `Swatches` |

```python
import svgwriter as svg

print(svg.widgets.control((0, 360)))
print(type(svg.widgets.control(["S", "M", "L", "XL", "XXL"])).__name__)   # Dropdown
print(svg.widgets.Slider(0, 1, format=".0%").text(0.25))                    # 25%
```

Values are checked: a slider refuses numbers outside its ends, an option control anything that is not an
option, with a `ValueError` naming the problem.

## Notebook panels

`svg.explore(fn)` shows the controls next to the drawing `fn(**values)` returns, a `Document` or an
element, and redraws it as they change. It needs the `widget` extra:

```console
$ pip install "pysvgwriter[widget]"
```

```python
import svgwriter as svg

view = svg.explore(badge)                       # the panel appears below the cell
view.update(size=70, color="#f43f5e")            # set values from code as well
print(view.values)
print(view.code())                               # badge(size=70.0, color='#f43f5e', shape='box', outline=False)
view.save("badge.svg")                           # the drawing for the current values
```

The panel looks like the preview page: the drawing on the left, the controls in a column on the right
(under the drawing when the cell is narrow), in the notebook's light or dark theme.

Controls given as keywords are added to declared ones (`svg.explore(fn, size=(0, 100))`); with none
at all, they are inferred from the function's keyword defaults. A function whose first parameter is not
a control, such as a project's `build(doc, ...)`, receives a new document there.

Redraws wait until the controls have been still for 80 ms (`delay=` changes it), and values drawn before
come from a cache, so moving a slider back and forth stays smooth. When the function raises, the last
drawing stays and the traceback appears under it until a change draws again. `view.document` is the
drawing for the current values and `view.error` the last traceback.

The panel itself is a *backend*: `svg.widgets.Recorder()` is one that shows nothing and remembers every
drawing, and `recorder.set(name, value)` plays an edit. It runs anywhere, for tests and scripts:

```python
import svgwriter as svg

panel = svg.widgets.Recorder()
view = svg.explore(badge, backend=panel, delay=0)
panel.set("shape", 1)                            # option controls send the option's index
print(view.values["shape"], len(panel.drawings))  # dot 2
```

## Controls in the live preview

A project's entry declares controls the same way. `svgwriter preview` shows them as a form above the
outputs; each change is posted to the local server, which rebuilds with the new values and swaps the
outputs in place. `svgwriter build` uses the starting values, and `project.build(values={...})` others.

```python
import svgwriter as svg

@svg.widgets.controls(hue=(0, 360), corners=(0, 24))
def build(doc: svg.Document, hue=200, corners=12) -> None:
    doc.rect(10, 10, 200, 120, rx=corners, fill=svg.Color.from_hsl(hue, 0.7, 0.5))
```

The form is plain HTML inputs and the server only the standard library. Editing `main.py` keeps the
values that still fit the edited controls. See {doc}`projects`.

## Sweeps

`svg.sweep(fn, param=(start, end), dur=2)` calls the function with parameters that change over time. A
pair of numbers, lengths or colours runs smoothly from one to the other, a list steps through its items,
and a control runs through its range or options; anything else is passed unchanged. The result is a
`svg.Scene`, so it saves like one:

```python
import svgwriter as svg

grow = svg.sweep(badge, size=(10, 80), color=["#0ea5e9", "#f43f5e"], dur=2, fps=12, ease="ease-in-out")
print(grow.values_at(1.0))
grow.save("badge.svg")    # baked SMIL: plays in a browser
grow.save("badge.gif")    # frame by frame, no ffmpeg needed
# grow.save("badge.mp4")  # through ffmpeg; .pptx works as well
```

Each frame redraws the function and carries the result over onto the scene's drawing: elements that
keep their place keep their identity and only take new attributes, so the baked SVG interpolates them
with a few keyframes instead of swapping whole copies. A function that returns an element gets a canvas
fitted to the content of the whole sweep.
