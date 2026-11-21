# svgwriter extensions for Inkscape

Three effects under **Extensions > svgwriter** (Inkscape 1.2 or newer):

| Extension | What it does |
| --- | --- |
| **Run svgwriter Code** | Runs Python code on the open drawing. `doc` is the drawing as an `svgwriter.Document`, `svg` is the `svgwriter` module, `selection` lists the selected objects and `math` is imported. Supports Live preview. |
| **Save with svgwriter** | Saves the drawing through svgwriter to another format: PowerPoint with animations, Word, PDF, TikZ, EPS, G-code, HPGL, DXF, HTML, PNG, animated GIF, WebP, Excalidraw. |
| **Apply svgwriter Theme** | Styles objects that carry svgwriter roles with a built-in theme or a `theme.toml`, and can give the selection a role first. |

## Install

1. **Copy the files.** Copy every `.inx` and `.py` file from this folder (or from the
   `svgwriter-inkscape.zip` release asset) into a folder inside Inkscape's user extensions
   folder, for example `extensions/svgwriter/`. Inkscape shows the folder's location under
   **Edit > Preferences > System > User extensions**. Restart Inkscape.

2. **Give the extensions a Python with svgwriter.** svgwriter needs Python 3.10 or newer
   with binary packages (skia-python, numpy, uharfbuzz). Pick one of these:

   - **Use your own Python (recommended).** Install svgwriter into a Python of your own:

     ```console
     python -m pip install pysvgwriter
     ```

     Then tell Inkscape to run extensions with it. Close Inkscape and add a
     `python-interpreter` attribute to the `extensions` group in Inkscape's
     `preferences.xml` (its folder is shown under **Edit > Preferences > System > User
     preferences**):

     ```xml
     <group id="extensions" python-interpreter="C:\Users\me\venvs\svg\Scripts\python.exe" />
     ```

     Inkscape's own extensions keep working as long as that Python also has `lxml`,
     `numpy` and `inkex` (`python -m pip install inkex`).

   - **Keep Inkscape's Python for everything else.** Set the environment variable
     `SVGWRITER_PYTHON` to a Python that has svgwriter installed. The svgwriter extensions
     start under Inkscape's Python, notice svgwriter is missing and run themselves again
     with that Python; other extensions are unaffected.

   - **Install into Inkscape's Python.** On Linux and macOS, where Inkscape uses the system
     or a regular Python, `python3 -m pip install --user pysvgwriter` for that Python is
     enough. The Python bundled with Inkscape on Windows has no `pip` and cannot load
     skia-python, so use one of the options above there.

   If svgwriter cannot be found, the extensions say so in Inkscape's error dialog.

## Run svgwriter Code

The box runs Python with the same access to your computer as Inkscape, so run only code
you wrote or trust. Write ordinary svgwriter code, as in a script:

```python
doc["star"].rotate(30)
doc["Logo"].scale(1.5)
for circle in doc.root.find_all(svg.Circle):
    circle.r *= 2

doc.text("Hello", x=20, y=20, id="title", font_size=8)
doc["title"].animate.typewriter(dur=2)
```

- Elements are found by id or by their Inkscape label (`doc["Logo"]`).
- Animations are written as SMIL inside the drawing. Inkscape shows the first frame,
  keeps them when it saves, and **Save with svgwriter** exports them (PowerPoint, GIF,
  HTML).
- Text is measured with svgwriter's own font fallback: generic families (`sans-serif`,
  `serif`, `monospace`) resolve to fonts installed on Windows, macOS or Linux, and a
  missing family falls back with a warning instead of an error.
- Errors appear in Inkscape's error dialog with the line that raised them; warnings are
  listed after the drawing is updated.
- Inkscape passes the text box on one line with newlines written as `\n`; the extension
  turns them back into line breaks, so write `"\\n"` for a backslash-n inside a string,
  or use the **Or run a .py file** field for longer scripts.

## Save with svgwriter

Choose a file and a format (or leave **From the file extension**). The options field takes
`name=value` pairs passed to the exporter, for example `dpi=300` for PNG or
`feed=1200, cut_z=-1` for G-code. The drawing in Inkscape is not changed.

## Apply svgwriter Theme

Objects with svgwriter roles (`box`, `shape`, `accent`, `text`, `title`, `line`, ...) take
the colours and fonts of the chosen theme. Type a role name to give the selected objects
that role first.

## Developing

The scripts follow Inkscape's extension protocol without needing `inkex`: Inkscape calls
`python <script>.py --param=value ... <drawing.svg>` and reads the new drawing from standard
output. Run them the same way to try them out:

```console
python svgwriter_script.py "--code=doc['star'].rotate(30)" drawing.svg > out.svg
```
