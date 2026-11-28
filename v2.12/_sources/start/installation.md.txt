# Installation

```console
$ pip install pysvgwriter
```

The package installs as `pysvgwriter` and imports as `svgwriter`:

```python
import svgwriter as svg
```

svgwriter needs Python 3.10 or newer; everything else it needs installs with it. (The core
dependencies are skia-python for drawing and text, numpy, uharfbuzz for text shaping, tomlkit, click and
python-lcms2 for colour profiles.)
Nothing else is needed at runtime.

Optional extras:

- **cli** for arrow-key prompts in `svgwriter new` (preset, script or notebook, theme, page size) through
  [questionary](https://questionary.readthedocs.io/):

  ```console
  $ pip install "pysvgwriter[cli]"
  ```

  Without it, `svgwriter new` asks for the preset with a numbered menu.

- **office** for PowerPoint, Word and Excel files (read and write) through python-pptx, python-docx and
  openpyxl:

  ```console
  $ pip install "pysvgwriter[office]"
  ```

- **widget** for {doc}`notebook panels <../guides/widgets>` (`svg.explore`) through ipywidgets:

  ```console
  $ pip install "pysvgwriter[widget]"
  ```

  Controls, sweeps and the controls of `svgwriter preview` work without it.

Optional external programs, found on `PATH` or through `SVGWRITER_<NAME>` (for example
`SVGWRITER_FFMPEG=/opt/ffmpeg/bin/ffmpeg`):

- **ffmpeg** for {doc}`video export <../guides/scenes-and-video>`. Without it, `render_animation` raises
  `FFmpegNotFoundError` before doing any work.
- **LaTeX** with **dvisvgm** for `svg.latex` with real TeX (otherwise Ziamath or matplotlib's mathtext).
- **Graphviz** (`dot`), the **Mermaid CLI** (`mmdc`), **PlantUML** and **D2** for diagram files.

## Check a machine

```console
$ svgwriter doctor
```

prints what is installed, what is missing and the command that adds each missing piece on this OS,
plus the installed font families and what `sans-serif`, `serif`, `monospace` and emoji resolve to
(see {doc}`../reference/cli`). Every "needs X" error names the same command.

## Per operating system

svgwriter draws text with the system's fonts, so the fonts installed decide what `sans-serif`, emoji,
Devanagari, Arabic or CJK text looks like. Each generic family tries common faces in order (Arial,
Helvetica, Liberation Sans, Arimo, DejaVu Sans, Noto Sans for `sans-serif`), and characters a font
lacks fall back to any installed font that has them.

### Windows

Wheels need nothing else; Windows ships Arial, Times New Roman, Consolas, Segoe UI Emoji and fonts for
most scripts. Optional programs through winget:

```console
> winget install Gyan.FFmpeg
> winget install MiKTeX.MiKTeX
> winget install Graphviz.Graphviz
> winget install OpenJS.NodeJS   # then: npm install -g @mermaid-js/mermaid-cli
```

### macOS

Wheels need nothing else; macOS ships Helvetica, Times, Menlo, Apple Color Emoji and fonts for most
scripts. Optional programs through Homebrew:

```console
$ brew install ffmpeg graphviz node
$ brew install --cask mactex-no-gui
$ npm install -g @mermaid-js/mermaid-cli
```

### Debian and Ubuntu (apt)

skia needs EGL, GL and fontconfig; slim images have no fonts at all, so add a baseline:

```console
$ sudo apt install libegl1 libgl1 libfontconfig1 fonts-dejavu-core fonts-noto-color-emoji
$ sudo apt install ffmpeg graphviz texlive-latex-extra dvisvgm
```

`fonts-noto-core`, `fonts-noto-cjk` and `fonts-liberation2` add more scripts and metric-compatible
Arial and Times faces.

### Fedora, RHEL and derivatives (dnf)

```console
$ sudo dnf install mesa-libEGL mesa-libGL fontconfig dejavu-sans-fonts dejavu-serif-fonts dejavu-sans-mono-fonts google-noto-color-emoji-fonts
$ sudo dnf install ffmpeg-free graphviz texlive-scheme-basic texlive-standalone texlive-dvisvgm
```

### Arch Linux (pacman)

```console
$ sudo pacman -S libglvnd fontconfig ttf-dejavu noto-fonts-emoji
$ sudo pacman -S ffmpeg graphviz texlive-basic texlive-latexextra texlive-binextra
```

### openSUSE (zypper)

```console
$ sudo zypper install Mesa-libEGL1 Mesa-libGL1 fontconfig dejavu-fonts noto-coloremoji-fonts
$ sudo zypper install ffmpeg-7 graphviz texlive-latex texlive-standalone texlive-dvisvgm
```

### Alpine and other musl distributions

Unsupported: skia-python ships no musllinux wheels, so svgwriter cannot be installed there until it
does. Use a glibc-based image (`debian:stable-slim`, `python:3.13-slim`).

### Pyodide

skia-python has no Pyodide build yet, so svgwriter does not run in the browser; external programs are
never available there.

For a development install, see {doc}`../contributing`.
