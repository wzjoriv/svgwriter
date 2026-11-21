"""
Constants for ``svgwriter.project``: file names, manifest keys, defaults and the preview page.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

__all__ = [
    "ANIMATED_FORMATS",
    "BAKED_FORMATS",
    "BUILTIN_PRESETS",
    "CELL_MARKER",
    "DEFAULT_ENTRY",
    "DEFAULT_FORMATS",
    "DEFAULT_GIF_FPS",
    "DEFAULT_NOTEBOOK_OBJECT",
    "DEFAULT_OUTPUT",
    "DEFAULT_PORT",
    "DOT_PREFIX",
    "FONT_FOLDER",
    "FORM_SCRIPT",
    "FORM_STYLE",
    "GALLERY_STYLE",
    "FONT_SUFFIXES",
    "HEADLESS_ENV",
    "IMAGE_TYPES",
    "KERNEL",
    "KEEPS_ANIMATION",
    "KILOBYTE",
    "MAIN_GUARD",
    "MANIFEST",
    "MARKDOWN_TAG",
    "NBFORMAT",
    "NBFORMAT_MINOR",
    "NOTEBOOK_SUFFIX",
    "NOTEBOOK_TIMEOUT",
    "OUTPUT_KEYS",
    "PLACEHOLDERS",
    "POLL_SECONDS",
    "POST_MILLISECONDS",
    "PREVIEW_CELLS",
    "PROJECT_KEYS",
    "PYPROJECT",
    "PYPROJECT_TABLE",
    "RELOAD_MILLISECONDS",
    "RELOAD_SCRIPT",
    "TEMPLATES",
    "THEME_FILE",
    "TEMPLATE_SUFFIX",
    "TOP_KEYS",
    "VIDEO_FORMATS",
    "VIDEO_TYPES",
    "WATCH_IGNORED",
]

MANIFEST: Final = "svgwriter.toml"
THEME_FILE: Final = "theme.toml"
PYPROJECT: Final = "pyproject.toml"
PYPROJECT_TABLE: Final = ("tool", "svgwriter")

TOP_KEYS: Final = frozenset({"project", "outputs"})
PROJECT_KEYS: Final = frozenset({"name", "entry", "size", "theme", "fonts"})
OUTPUT_KEYS: Final = frozenset({"formats", "directory"})

DEFAULT_ENTRY: Final = "main:build"
DEFAULT_NOTEBOOK_OBJECT: Final = "build"
DEFAULT_FORMATS: Final = ("svg", "png")
DEFAULT_OUTPUT: Final = "output"
FONT_FOLDER: Final = "assets/fonts"
FONT_SUFFIXES: Final = frozenset({".ttf", ".otf", ".ttc"})
NOTEBOOK_SUFFIX: Final = ".ipynb"
NOTEBOOK_TIMEOUT: Final = 600
HEADLESS_ENV: Final = "SVGWRITER_PROJECT_HEADLESS"
MAIN_GUARD: Final = 'if __name__ == "__main__":'
CELL_MARKER: Final = "# %%"
MARKDOWN_TAG: Final = "[markdown]"
NBFORMAT: Final = 4
NBFORMAT_MINOR: Final = 5
KERNEL: Final = "python3"
PREVIEW_CELLS: Final = (
    ("markdown", "Every output of the project, as `svgwriter build` writes it: animations play here. "
                 "`project.build()` writes the files to `output/`."),
    ("code", "project = svg.Project.load()\nproject.preview()"),
)

KEEPS_ANIMATION: Final = frozenset({"svg", "svgz", "html", "pptx", "gif"})
ANIMATED_FORMATS: Final = frozenset({"gif"})
BAKED_FORMATS: Final = KEEPS_ANIMATION - ANIMATED_FORMATS
VIDEO_FORMATS: Final = frozenset({"mp4", "webm", "mov", "apng"})
DEFAULT_GIF_FPS: Final = 15.0

IMAGE_TYPES: Final = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
                      ".webp": "image/webp", ".bmp": "image/bmp", ".svg": "image/svg+xml"}
VIDEO_TYPES: Final = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime"}

TEMPLATES: Final = Path(__file__).resolve().parent / "templates"
BUILTIN_PRESETS: Final = {
    "blank": ("A canvas with a title, a component and an animation; SVG and PNG", None),
    "poster": ("An A4 page drawn in millimetres with a chart from a CSV file; PDF, SVG and PNG", "blank"),
    "slides": ("A 16:9 deck with one function per slide and slide animations; PowerPoint and PDF", "blank"),
    "animation": ("A Scene class with SMIL presets and per-frame updates; GIF and animated SVG", "blank"),
}
PLACEHOLDERS: Final = {"project_name": "{{ project_name }}", "preset": "{{ preset }}"}
TEMPLATE_SUFFIX: Final = "-tpl"
DOT_PREFIX: Final = "dot-"

DEFAULT_PORT: Final = 8000
POLL_SECONDS: Final = 0.5
RELOAD_MILLISECONDS: Final = 700
WATCH_IGNORED: Final = frozenset({"output", ".git", "__pycache__", ".ipynb_checkpoints", ".venv"})
KILOBYTE: Final = 1024
GALLERY_STYLE: Final = (
    ".svgwriter-preview{display:flex;flex-wrap:wrap;gap:16px;font-family:system-ui,sans-serif}"
    ".svgwriter-preview h3{flex-basis:100%;margin:0}"
    ".svgwriter-preview figure{margin:0;max-width:100%;display:flex;flex-direction:column;gap:6px}"
    ".svgwriter-preview img,.svgwriter-preview video{max-width:min(100%,640px);max-height:480px;"
    "border:1px solid #d4d4d8;background:repeating-conic-gradient(#f4f4f5 0 25%,#fff 0 50%) 0 0/16px 16px}"
    ".svgwriter-preview figcaption{font-size:13px;color:#3f3f46}"
)
RELOAD_SCRIPT: Final = (
    "<script>window.shown={version};setInterval(async()=>{{try{{const r=await fetch('/version');"
    "if(Number(await r.text())!==window.shown)location.reload()}}catch(e){{}}}},{interval});</script>"
)
POST_MILLISECONDS: Final = 120
FORM_STYLE: Final = (
    ".svgwriter-controls{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px 20px;"
    "font:13px system-ui,sans-serif;margin:0 0 16px;padding:12px;border:1px solid #e4e4e7;border-radius:8px}"
    ".svgwriter-controls .field{display:flex;align-items:center;gap:8px}"
    ".svgwriter-controls .name{min-width:88px;color:#3f3f46}"
    ".svgwriter-controls input[type=range]{flex:1;min-width:0}"
    ".svgwriter-controls output{min-width:48px;text-align:right;color:#71717a;font-variant-numeric:tabular-nums}"
    ".svgwriter-controls .segmented{display:inline-flex;border:1px solid #d4d4d8;border-radius:6px;overflow:hidden}"
    ".svgwriter-controls .segmented label{padding:3px 10px;cursor:pointer;border-left:1px solid #d4d4d8}"
    ".svgwriter-controls .segmented label:first-child{border-left:0}"
    ".svgwriter-controls .segmented input{display:none}"
    ".svgwriter-controls .segmented label:has(input:checked){background:#18181b;color:#fff}"
    ".svgwriter-controls .chip{display:inline-block;width:16px;height:16px;border-radius:3px;vertical-align:middle}"
    ".svgwriter-controls .field:has(.segmented,select,input[type=checkbox],input[type=color]) output{display:none}"
    ".svgwriter-error{color:#b91c1c;white-space:pre-wrap;font-size:12px}"
)
FORM_SCRIPT: Final = (
    "<script>(()=>{const form=document.querySelector('.svgwriter-controls');let timer;"
    "const read=f=>{const k=f.dataset.kind,inputs=[...f.querySelectorAll('input,select')];"
    "if(k==='number')return Number(inputs[0].value);"
    "if(k==='pair')return inputs.map(i=>Number(i.value)).sort((a,b)=>a-b);"
    "if(k==='bool')return inputs[0].checked;if(k==='text')return inputs[0].value;"
    "const s=f.querySelector('select');"
    "if(k==='indices')return [...s.selectedOptions].map(o=>Number(o.value));"
    "return Number(s?s.value:f.querySelector('input:checked').value)};"
    "const send=async()=>{const values={};form.querySelectorAll('.field').forEach(f=>values[f.dataset.name]=read(f));"
    "const r=await fetch('/values',{method:'POST',headers:{'Content-Type':'application/json'},"
    "body:JSON.stringify(values)});const d=await r.json();if(d.version!==undefined)window.shown=d.version;"
    "if(d.outputs!==undefined)document.getElementById('svgwriter-outputs').innerHTML=d.outputs;"
    "for(const[n,t]of Object.entries(d.readouts||{})){const o=form.querySelector(`.field[data-name=\"${n}\"] output`);"
    "if(o)o.textContent=t}};"
    "const later=()=>{clearTimeout(timer);timer=setTimeout(send,{delay})};"
    "form.addEventListener('input',later);form.addEventListener('change',later);"
    "form.addEventListener('submit',e=>e.preventDefault())})();</script>"
)
