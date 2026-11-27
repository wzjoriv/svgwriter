"""
Constants for ``svgwriter.tools.project``: file names, manifest keys, defaults and the preview page.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

__all__ = [
    "ANIMATED_FORMATS",
    "BACKGROUNDS",
    "BAKED_FORMATS",
    "BUILD_IDLE_SECONDS",
    "BUILTIN_PRESETS",
    "CELL_MARKER",
    "DEFAULT_ENTRY",
    "DEFAULT_FORMATS",
    "DEFAULT_GIF_FPS",
    "DEFAULT_NOTEBOOK_OBJECT",
    "DEFAULT_OUTPUT",
    "DEFAULT_PORT",
    "DISCONNECTS",
    "DOT_PREFIX",
    "FITS",
    "FONT_FOLDER",
    "FONT_SUFFIXES",
    "GALLERY_STYLE",
    "HEADLESS_ENV",
    "IMAGE_TYPES",
    "KEEPS_ANIMATION",
    "KERNEL",
    "KILOBYTE",
    "LAYOUTS",
    "MAIN_GUARD",
    "MANIFEST",
    "MARKDOWN_TAG",
    "MILLISECONDS",
    "NBFORMAT",
    "NBFORMAT_MINOR",
    "NOTEBOOK_SUFFIX",
    "NOTEBOOK_TIMEOUT",
    "OPTION_CHARACTER",
    "OPTION_PADDING",
    "OUTPUT_KEYS",
    "PAGE_SCRIPT",
    "PAGE_STYLE",
    "PAGE_TEMPLATE",
    "PLACEHOLDERS",
    "POLL_SECONDS",
    "PREVIEW_CELLS",
    "PREVIEW_DEBOUNCE_MS",
    "PREVIEW_KEYS",
    "PROJECT_KEYS",
    "PYPROJECT",
    "PYPROJECT_TABLE",
    "TEMPLATES",
    "TEMPLATE_SUFFIX",
    "THEME_FILE",
    "TOP_KEYS",
    "VERSION_POLL_MS",
    "VIDEO_FORMATS",
    "VIDEO_TYPES",
    "WATCH_IGNORED",
]

MANIFEST: Final = "svgwriter.toml"
THEME_FILE: Final = "theme.toml"
PYPROJECT: Final = "pyproject.toml"
PYPROJECT_TABLE: Final = ("tool", "svgwriter")

TOP_KEYS: Final = frozenset({"project", "outputs", "preview"})
PROJECT_KEYS: Final = frozenset({"name", "entry", "size", "theme", "fonts"})
OUTPUT_KEYS: Final = frozenset({"formats", "directory"})
PREVIEW_KEYS: Final = frozenset({"pages", "background", "layout", "fit", "port", "open", "debounce_ms", "build_on_save",
                                 "formats_on_build"})

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
OPTION_CHARACTER: Final = 1.15
OPTION_PADDING: Final = 18
POLL_SECONDS: Final = 0.5
BUILD_IDLE_SECONDS: Final = 1.0
VERSION_POLL_MS: Final = 700
PREVIEW_DEBOUNCE_MS: Final = 80
MILLISECONDS: Final = 1000
BACKGROUNDS: Final = ("checker", "light", "dark")
LAYOUTS: Final = ("auto", "right", "bottom")
FITS: Final = ("contain", "actual")
DISCONNECTS: Final = (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)
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
PAGE_TEMPLATE: Final = (
    "<!doctype html><html lang='en'><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title><style>{style}</style>"
    "<header><h1>{title}</h1><nav id='svgwriter-tabs' role='tablist' aria-label='Pages and scenes'></nav>"
    "<button type='button' id='svgwriter-build' title='Write the output files into the output folder'>"
    "Export</button></header>"
    "<main class='layout-{layout}'><section class='stage' aria-label='Drawing'>"
    "<div id='svgwriter-canvas' class='canvas fit-{fit} backdrop-{backdrop}'{backdrop_style}></div>"
    "<p id='svgwriter-status' class='status' role='status' aria-live='polite'></p>"
    "<pre id='svgwriter-error' class='error' role='alert' hidden></pre></section>"
    "<aside id='svgwriter-panel' class='panel' aria-label='Controls'{panel_hidden}>{form}</aside></main>"
    "<script id='svgwriter-state' type='application/json'>{state}</script><script>{script}</script></html>"
)
PAGE_STYLE: Final = (
    ":root{color-scheme:light dark;--bg:#f5f5f3;--panel:#ffffff;--ink:#1d1d1f;--muted:#6e6e73;--line:#e2e2de;"
    "--soft:#ececea;--accent:#3b5bdb;--on-accent:#ffffff;--danger:#b42318;--check:#e9e9e6}"
    "@media (prefers-color-scheme:dark){:root{--bg:#151517;--panel:#1d1d20;--ink:#ececef;--muted:#9b9ba3;"
    "--line:#2d2d32;--soft:#26262b;--accent:#91a7ff;--on-accent:#10121a;--danger:#ff8f85;--check:#222226}}"
    "*{box-sizing:border-box}html,body{margin:0}"
    "body{min-height:100vh;display:flex;flex-direction:column;background:var(--bg);color:var(--ink);"
    "font:14px/1.45 system-ui,-apple-system,'Segoe UI',sans-serif}"
    ":focus-visible{outline:2px solid var(--accent);outline-offset:2px}"
    "button{font:inherit;color:inherit;cursor:pointer}"
    "header{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;padding:8px 16px;background:var(--panel);"
    "border-bottom:1px solid var(--line);position:sticky;top:0;z-index:1}"
    "header h1{margin:0;font-size:15px;font-weight:600;white-space:nowrap}"
    "#svgwriter-tabs{display:flex;gap:2px;flex:1;min-width:0;overflow-x:auto;scrollbar-width:thin}"
    "@media (max-width:760px){#svgwriter-tabs{order:3;flex-basis:100%}}"
    "#svgwriter-tabs button{border:0;background:none;padding:5px 10px;border-radius:6px;color:var(--muted);"
    "white-space:nowrap;flex:none}"
    "#svgwriter-tabs button:hover{background:var(--soft)}"
    "#svgwriter-tabs button[aria-selected=true]{background:var(--soft);color:var(--ink);font-weight:500}"
    "#svgwriter-build{margin-left:auto;border:1px solid var(--accent);background:var(--accent);"
    "color:var(--on-accent);padding:5px 12px;border-radius:7px;font-weight:500;white-space:nowrap}"
    "#svgwriter-build:disabled{opacity:.6;cursor:progress}"
    "main{flex:1;display:grid;gap:16px;padding:16px;grid-template-columns:minmax(0,1fr);"
    "grid-template-rows:minmax(320px,68vh) auto}"
    "@media (min-width:900px) and (min-aspect-ratio:1/1){body:has(main.layout-auto){height:100vh}"
    "main.layout-auto{min-height:0;grid-template-columns:minmax(0,1fr) clamp(260px,26vw,360px);"
    "grid-template-rows:minmax(0,1fr)}}"
    "body:has(main.layout-right){height:100vh}"
    "main.layout-right{min-height:0;grid-template-columns:minmax(0,1fr) clamp(240px,28vw,360px);"
    "grid-template-rows:minmax(0,1fr)}"
    "body:has(.panel[hidden]){height:100vh}"
    "main:has(.panel[hidden]){min-height:0;grid-template-columns:minmax(0,1fr);grid-template-rows:minmax(0,1fr)}"
    ".stage{display:flex;flex-direction:column;gap:6px;min-width:0;min-height:0}"
    ".canvas{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;padding:24px;"
    "border-radius:12px;border:1px solid var(--line);overflow:hidden}"
    ".canvas img{display:block;filter:drop-shadow(0 1px 3px rgb(0 0 0/.12))}"
    ".fit-contain img{width:100%;height:100%;object-fit:contain}"
    ".fit-actual{overflow:auto;align-items:flex-start;justify-content:flex-start}"
    ".fit-actual img{flex:none;margin:auto}"
    ".backdrop-checker{background:repeating-conic-gradient(var(--check) 0 25%,var(--panel) 0 50%) 0 0/20px 20px}"
    ".backdrop-light{background:#ffffff}.backdrop-dark{background:#18181b}"
    ".status{margin:0;min-height:1.45em;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}"
    ".error{margin:0;padding:10px 12px;max-height:30vh;overflow:auto;border-radius:8px;white-space:pre-wrap;"
    "font:12px/1.5 ui-monospace,'Cascadia Mono',Consolas,monospace;color:var(--danger);"
    "background:color-mix(in srgb,var(--danger) 9%,transparent)}"
    ".panel{min-height:0;overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:12px;"
    "padding:4px 16px;container-type:inline-size}"
    ".svgwriter-controls{display:grid;grid-template-columns:minmax(0,1fr);column-gap:24px}"
    "@container (min-width:560px){.svgwriter-controls{grid-template-columns:repeat(2,minmax(0,1fr))}}"
    ".field{display:flex;flex-direction:column;gap:6px;padding:12px 0;border-bottom:1px solid var(--line);"
    "min-width:0}"
    ".field .head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:2px 8px}"
    ".field .name{font-weight:500;overflow-wrap:anywhere}"
    ".field output{color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}"
    ".field:has(.segmented,select,input[type=checkbox],input[type=color]) output{display:none}"
    ".field input[type=range]{width:100%;margin:0;accent-color:var(--accent)}"
    ".field select,.field input[type=text],.field input[type=number]{width:100%;padding:6px 8px;"
    "border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit;font:inherit}"
    ".field select[multiple]{min-height:5.5em}"
    ".field input[type=color]{width:44px;height:28px;padding:0 2px;border:1px solid var(--line);border-radius:7px;"
    "background:var(--bg)}"
    ".segmented{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,var(--option,4ch)),1fr));"
    "gap:2px;padding:2px;border-radius:8px;background:var(--soft)}"
    ".segmented label{position:relative;text-align:center;padding:4px 8px;border-radius:6px;cursor:pointer;"
    "color:var(--muted);white-space:nowrap}"
    ".segmented label:hover{color:var(--ink)}"
    ".segmented input{position:absolute;inset:0;opacity:0;margin:0;cursor:pointer}"
    ".segmented label:has(input:checked){background:var(--panel);color:var(--ink);"
    "box-shadow:0 1px 2px rgb(0 0 0/.15)}"
    ".segmented label:has(input:focus-visible){outline:2px solid var(--accent);outline-offset:1px}"
    ".segmented.swatches{display:flex;flex-wrap:wrap;background:none;gap:6px;padding:0}"
    ".segmented.swatches label{flex:none;padding:3px;border-radius:50%}"
    ".segmented.swatches label:has(input:checked){box-shadow:0 0 0 2px var(--ink);background:none}"
    ".chip{display:block;width:20px;height:20px;border-radius:50%;border:1px solid rgb(0 0 0/.15)}"
    ".field input[type=checkbox]{width:16px;height:16px;margin:0;accent-color:var(--accent)}"
    ".field input.switch{appearance:none;width:34px;height:20px;border-radius:10px;background:var(--line);"
    "position:relative;cursor:pointer;transition:background .15s}"
    ".field input.switch::after{content:'';position:absolute;top:2px;left:2px;width:16px;height:16px;"
    "border-radius:50%;background:#fff;box-shadow:0 1px 2px rgb(0 0 0/.3);transition:transform .15s}"
    ".field input.switch:checked{background:var(--accent)}"
    ".field input.switch:checked::after{transform:translateX(14px)}"
    ".field:has(input[type=checkbox]){flex-direction:row;align-items:center;justify-content:space-between}"
    "@media (prefers-reduced-motion:reduce){*{transition:none!important}}"
)
PAGE_SCRIPT: Final = (
    "(()=>{const $=i=>document.getElementById('svgwriter-'+i);"
    "const panel=$('panel'),canvas=$('canvas'),tabs=$('tabs'),status=$('status'),problem=$('error'),"
    "build=$('build');"
    "let state=JSON.parse($('state').textContent),form=state.form,tab=0,urls=[],sent=0,applied=0,ctl=null,timer=0;"
    "const say=t=>{status.textContent=t};"
    "const fail=t=>{problem.textContent=t||'';problem.hidden=!t};"
    "const read=f=>{const k=f.dataset.kind,inputs=[...f.querySelectorAll('input,select')];"
    "if(k==='number')return Number(inputs[0].value);"
    "if(k==='pair')return inputs.map(i=>Number(i.value)).sort((a,b)=>a-b);"
    "if(k==='bool')return inputs[0].checked;if(k==='text')return inputs[0].value;"
    "const s=f.querySelector('select');"
    "if(k==='indices')return [...s.selectedOptions].map(o=>Number(o.value));"
    "return Number(s?s.value:f.querySelector('input:checked').value)};"
    "const values=()=>{const v={};panel.querySelectorAll('.field').forEach(f=>{v[f.dataset.name]=read(f)});"
    "return v};"
    "const show=()=>{const v=state.views[tab];"
    "[...tabs.children].forEach((b,i)=>{b.setAttribute('aria-selected',String(i===tab));b.tabIndex=i===tab?0:-1;if(i===tab)b.scrollIntoView({inline:'nearest',block:'nearest'})});"
    "if(!v){canvas.replaceChildren();return}"
    "let img=canvas.querySelector('img');if(!img){img=document.createElement('img');canvas.append(img)}"
    "img.src=urls[tab];img.alt=v.name};"
    "const pick=i=>{tab=i;show();tabs.children[i]?.focus()};"
    "const apply=d=>{state={...state,...d};urls.forEach(u=>URL.revokeObjectURL(u));"
    "urls=state.views.map(v=>URL.createObjectURL(new Blob([v.svg],{type:'image/svg+xml'})));"
    "tab=Math.min(tab,Math.max(state.views.length-1,0));"
    "tabs.replaceChildren(...(state.views.length>1?state.views.map((v,i)=>{"
    "const b=document.createElement('button');b.type='button';b.setAttribute('role','tab');b.textContent=v.name;"
    "b.onclick=()=>pick(i);return b}):[]));"
    "for(const[n,t]of Object.entries(state.readouts||{})){"
    "const o=panel.querySelector(`.field[data-name=\"${CSS.escape(n)}\"] output`);if(o)o.textContent=t}"
    "fail(state.error);show();"
    "say(state.error?'Drawing failed; showing the last drawing that worked':`Rendered in ${state.ms} ms`)};"
    "tabs.addEventListener('keydown',e=>{const n=state.views.length,step={ArrowRight:1,ArrowLeft:-1}[e.key];"
    "if(step&&n){e.preventDefault();pick((tab+step+n)%n)}});"
    "const send=()=>{const my=++sent;if(ctl)ctl.abort();ctl=new AbortController();const t0=performance.now();"
    "say('Rendering\u2026');"
    "fetch('/values',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(values()),"
    "signal:ctl.signal}).then(r=>r.json()).then(d=>{if(my<=applied)return;applied=my;"
    "if(d.views===undefined){fail(d.error);say('Value not accepted');return}apply(d);"
    "if(!d.error)say(`Rendered in ${d.ms} ms \u00b7 ${Math.round(performance.now()-t0)} ms round trip`)})"
    ".catch(e=>{if(e.name!=='AbortError')say('The preview server is not answering')})};"
    "const later=()=>{clearTimeout(timer);timer=setTimeout(send,state.debounce)};"
    "panel.addEventListener('input',later);panel.addEventListener('change',later);"
    "panel.addEventListener('submit',e=>e.preventDefault());"
    "build.addEventListener('click',()=>{build.disabled=true;say('Building outputs\u2026');"
    "fetch('/build',{method:'POST'}).then(r=>r.json()).then(d=>{if(d.error){fail(d.error);say('Build failed');"
    "return}fail(state.error);say(`Wrote ${d.files.length} files in ${(d.ms/1000).toFixed(1)} s: "
    "${d.files.join(', ')}`)})"
    ".catch(()=>say('The preview server is not answering')).finally(()=>{build.disabled=false})});"
    "setInterval(()=>fetch('/version').then(r=>r.text()).then(v=>{if(Number(v)===state.version)return;"
    "return fetch('/state').then(r=>r.json()).then(d=>{if(d.form!==form){form=d.form;panel.innerHTML=form;"
    "panel.hidden=!form}apply(d)})}).catch(()=>{}),state.poll);"
    "apply(state)})();"
)
