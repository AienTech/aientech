#!/usr/bin/env python3
"""Generates assets/terminal.svg, the animated terminal at the top of the README.

Edit the content below, then run:  python3 scripts/make_terminal.py
No dependencies. Animations are SMIL, so they play inside GitHub's <img> sandbox.
"""

import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets" / "terminal.svg"

# ---------------------------------------------------------------- content

USER, HOST = "aien", "github"

INVADER = [  # the two frames of the classic crab invader, 11x8 px
    ("..#.....#..",
     "...#...#...",
     "..#######..",
     ".##.###.##.",
     "###########",
     "#.#######.#",
     "#.#.....#.#",
     "...##.##..."),
    ("..#.....#..",
     "#..#...#..#",
     "#.#######.#",
     "###.###.###",
     "###########",
     ".#########.",
     "..#.....#..",
     ".#.......#."),
]

INFO = [  # (key, value); key=None means a raw line
    ("Name", "Aien · Āyīn · آیین"),
    ("OS", "Computer Science grad"),
    ("Kernel", "Go, JavaScript"),
    ("Arch", "Software Architecture"),
    ("Ops", "DevOps"),
    ("CPU", "Algorithms"),
    ("Blog", "aien.me"),
    ("Mail", "hi@aien.me"),
]

PLAN = [  # (mark, mark colour, text)
    ("x", "green", "build backends"),
    ("x", "green", "break games"),
    ("~", "yellow", "write down what I learn  →  aien.me"),
]

# ---------------------------------------------------------------- look

C = {
    "bg": "#0d1117", "bar": "#161b22", "border": "#30363d",
    "fg": "#c9d1d9", "dim": "#6e7681", "green": "#3fb950", "neon": "#7ee787",
    "blue": "#79c0ff", "yellow": "#e3b341", "red": "#ff7b72", "purple": "#d2a8ff",
    "cyan": "#56d4dd", "orange": "#ffa657",
}
PALETTE = ["red", "orange", "yellow", "green", "cyan", "blue", "purple", "fg"]

W = 720
FONT = 14
CW = FONT * 0.6          # monospace advance; typed text is pinned to this grid
LH = 20
PAD_X = 24
BAR_H = 34
TOP = BAR_H + 26         # baseline of the first row
INFO_COL = 29
PX = 16                  # invader pixel size

random.seed(7)           # stable output -> no noisy diffs when re-generating

# ---------------------------------------------------------------- builder

body, defs = [], []
row, t = 0, 0.4


def x_at(col):
    return PAD_X + col * CW


def y_at(r):
    return TOP + r * LH


def fmt(n):
    return f"{n:.3f}".rstrip("0").rstrip(".")


def show(begin):
    return f'<set attributeName="visibility" to="visible" begin="{fmt(begin)}s" fill="freeze"/>'


def hide(begin):
    return f'<set attributeName="visibility" to="hidden" begin="{fmt(begin)}s" fill="freeze"/>'


def spans(segments, grid_col=None):
    """segments: [(text, colour, bold)]. With grid_col, every char gets a fixed x."""
    out, col = [], grid_col
    for text, colour, bold in segments:
        attrs = f' fill="{C[colour]}"' + (' font-weight="700"' if bold else "")
        if grid_col is not None:
            xs = " ".join(fmt(x_at(col + i)) for i in range(len(text)))
            attrs += f' x="{xs}"'
            col += len(text)
        out.append(f"<tspan{attrs}>{escape(text)}</tspan>")
    return "".join(out)


def line(r, col, segments, begin):
    body.append(
        f'<text x="{fmt(x_at(col))}" y="{y_at(r)}" visibility="hidden">'
        f"{spans(segments)}{show(begin)}</text>"
    )


PROMPT = [(USER, "green", True), ("@", "dim", False), (HOST, "green", True),
          (":", "dim", False), ("~", "blue", True), ("$ ", "dim", False)]
PROMPT_LEN = sum(len(s[0]) for s in PROMPT)


def cursor(r, col, begin, blink=False):
    el = (f'<rect x="{fmt(x_at(col))}" y="{y_at(r) - FONT + 2}" width="{fmt(CW)}" '
          f'height="{FONT + 3}" fill="{C["neon"]}" visibility="hidden">{show(begin)}')
    if blink:
        el += (f'<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" '
               f'begin="{fmt(begin)}s" repeatCount="indefinite"/>')
    return el


def command(cmd, think=0.7):
    """Prompt appears, cursor idles, then cmd is typed char by char and 'entered'."""
    global row, t
    r, begin = row, t
    clip = f"clip{r}"

    # key-press times with a bit of human jitter
    times, k = [], begin + think
    for ch in cmd:
        times.append(k)
        k += random.uniform(0.045, 0.11) + (0.08 if ch in " /." else 0)
    t0, dur = times[0], times[-1] - times[0] + 0.001
    key_times = ";".join(fmt((tt - t0) / dur) for tt in times)
    widths = ";".join(fmt((i + 1) * CW) for i in range(len(cmd)))
    xs = ";".join(fmt(x_at(PROMPT_LEN + i + 1)) for i in range(len(cmd)))
    anim = f'calcMode="discrete" keyTimes="{key_times}" begin="{fmt(t0)}s" dur="{fmt(dur)}s" fill="freeze"'

    defs.append(
        f'<clipPath id="{clip}"><rect x="{fmt(x_at(PROMPT_LEN))}" y="{y_at(r) - FONT - 2}" '
        f'width="0" height="{LH + 4}"><animate attributeName="width" values="{widths}" {anim}/>'
        f"</rect></clipPath>"
    )
    body.append(
        f'<text y="{y_at(r)}" visibility="hidden">{spans(PROMPT, 0)}{show(begin)}</text>'
        f'<text y="{y_at(r)}" clip-path="url(#{clip})">{spans([(cmd, "fg", False)], PROMPT_LEN)}</text>'
    )
    enter = times[-1] + 0.35
    body.append(
        cursor(r, PROMPT_LEN, begin)
        + f'<animate attributeName="x" values="{xs}" {anim}/>{hide(enter)}</rect>'
    )
    row += 1
    t = enter + 0.12


def invader(x, y, begin, step):
    """Pixel rows are revealed top-down; the CSS in <style> then makes it march and flap."""
    frames = []
    for cls, frame in zip(("fa", "fb"), INVADER):
        rows = []
        for r, bits in enumerate(frame):
            px = "".join(
                f'<rect x="{c * PX}" y="{r * PX}" width="{PX - 2}" height="{PX - 2}" rx="2"/>'
                for c, bit in enumerate(bits) if bit == "#"
            )
            rows.append(f'<g visibility="hidden">{px}{show(begin + r * PX / LH * step)}</g>')
        frames.append(f'<g class="{cls}">{"".join(rows)}</g>')
    body.append(
        f'<g transform="translate({fmt(x)} {fmt(y)})" fill="{C["neon"]}" filter="url(#glow)">'
        f'<g class="march">{"".join(frames)}</g></g>'
    )


def output(rows, step=0.04):
    """rows: list of [(col, segments)]; each row appears a beat after the previous one."""
    global row, t
    for items in rows:
        for col, segs in items:
            line(row, col, segs, t)
        row += 1
        t += step
    t += 0.5


# ---------------------------------------------------------------- script

command("neofetch")

info_rows = [
    [(USER, "neon", True), ("@", "fg", False), (HOST, "neon", True)],
    [("-" * len(f"{USER}@{HOST}"), "dim", False)],
] + [[(f"{k + ':':<8}", "green", True), (v, "fg", False)] for k, v in INFO]
palette_row = len(info_rows) + 1

rows = [[(INFO_COL, r)] for r in info_rows] + [[], []]

block_top = y_at(row) - FONT
invader(PAD_X + 6, block_top + (len(rows) * LH - len(INVADER[0]) * PX) / 2, t, 0.04)
palette_at, palette_begin = row + palette_row, t + palette_row * 0.04
output(rows)

swatches = "".join(
    f'<rect x="{fmt(x_at(INFO_COL + i * 3))}" y="{y_at(palette_at) - FONT + 1}" '
    f'width="{fmt(CW * 3)}" height="{FONT + 2}" fill="{C[c]}"/>'
    for i, c in enumerate(PALETTE)
)
body.append(f'<g visibility="hidden">{swatches}{show(palette_begin)}</g>')

command("cat ~/.plan", think=0.9)
output([[(0, [("[", "dim", False), (m, colour, True), ("] ", "dim", False), (text, "fg", False)])]
        for m, colour, text in PLAN], step=0.12)

body.append(f'<text y="{y_at(row)}" visibility="hidden">{spans(PROMPT, 0)}{show(t)}</text>')
body.append(cursor(row, PROMPT_LEN, t, blink=True) + "</rect>")

# ---------------------------------------------------------------- render

H = y_at(row) + 26
dots = "".join(
    f'<circle cx="{20 + i * 20}" cy="{BAR_H / 2}" r="6" fill="{c}"/>'
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"])
)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title">
<title id="title">{USER}@{HOST}: neofetch. Aien (Āyīn · آیین), Computer Science grad. Go, JavaScript, software architecture, DevOps, algorithms. Builds backends, breaks games, writes at aien.me.</title>
<style>
text {{ font: {FONT}px ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace; white-space: pre; }}
.title {{ font-size: 12px; fill: {C["dim"]}; }}
.march {{ animation: march 4s steps(1) infinite; }}
.fa {{ animation: fa 1s steps(1) infinite; }}
.fb {{ opacity: 0; animation: fb 1s steps(1) infinite; }}
@keyframes march {{ 25% {{ transform: translateX({PX // 2}px); }} 50% {{ transform: translateX({PX}px); }} 75% {{ transform: translateX({PX // 2}px); }} }}
@keyframes fa {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
@keyframes fb {{ 0% {{ opacity: 0; }} 50% {{ opacity: 1; }} }}
@media (prefers-reduced-motion: reduce) {{ .march, .fa, .fb {{ animation: none; }} }}
</style>
<defs>
<filter id="glow" x="-10%" y="-40%" width="120%" height="180%">
<feGaussianBlur stdDeviation="2.4" result="blur"/>
<feComponentTransfer in="blur" result="soft"><feFuncA type="linear" slope="0.55"/></feComponentTransfer>
<feMerge><feMergeNode in="soft"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#ffffff" fill-opacity="0.025"/></pattern>
<clipPath id="window"><rect width="{W}" height="{H}" rx="10"/></clipPath>
{chr(10).join(defs)}
</defs>
<g clip-path="url(#window)">
<rect width="{W}" height="{H}" fill="{C["bg"]}"/>
<rect width="{W}" height="{BAR_H}" fill="{C["bar"]}"/>
<line x1="0" y1="{BAR_H}" x2="{W}" y2="{BAR_H}" stroke="{C["border"]}"/>
{dots}
<text class="title" x="{W / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle">{USER}@{HOST}: ~ — zsh</text>
<g xml:space="preserve">
{chr(10).join(body)}
</g>
<rect y="{BAR_H}" width="{W}" height="{H - BAR_H}" fill="url(#scan)" pointer-events="none"/>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{C["border"]}"/>
</svg>
"""

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUT.relative_to(Path.cwd()) if OUT.is_relative_to(Path.cwd()) else OUT} ({W}x{H})")
