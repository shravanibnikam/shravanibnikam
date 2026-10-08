# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools", "brotli"]
# ///
"""Regenerate every SVG in assets/:  uv run build.py

Each asset is written twice (-dark CRT phosphor, -light greenbar printout).
Fonts (OFL) are subset to the glyphs used and embedded, because GitHub
serves README SVGs as images and they can't load external fonts.
"""

import base64
import html
import io
import logging
import re
import urllib.request
from pathlib import Path
from types import SimpleNamespace as NS

from fontTools import subset

logging.getLogger("fontTools.subset").setLevel(logging.ERROR)

ROOT = Path(__file__).parent
OUT = ROOT / "assets"
FONTS = ROOT / ".fonts"
GF = "https://github.com/google/fonts/raw/main/ofl/"
FONT_SRC = {
    "VT323-Regular.ttf": GF + "vt323/VT323-Regular.ttf",
    "IBMPlexMono-Regular.ttf": GF + "ibmplexmono/IBMPlexMono-Regular.ttf",
    "IBMPlexMono-Bold.ttf": GF + "ibmplexmono/IBMPlexMono-Bold.ttf",
}

DARK = NS(
    name="dark",
    bg="#0a0a0c",
    panel="#131317",
    line="#34343d",
    fg="#ece7da",
    dim="#8d877b",
    hi="#a6ff7a",
    amber="#ffb22e",
    pink="#ff3d7f",
    cyan="#36d8ff",
    ink=(1, 1, 1),
    band=None,
    frame="#34343d",
)
LIGHT = NS(
    name="light",
    bg="#f3efe4",
    panel="#faf7ef",
    line="#c9c2b2",
    fg="#191816",
    dim="#6a645a",
    hi="#1e7b30",
    amber="#9c5800",
    pink="#cf0f55",
    cyan="#0b7fa8",
    ink=(0.16, 0.14, 0.12),
    band="#e2ecd8",
    frame="#24221f",
)

CSS = """.d{font-family:vt,monospace}
.m{font-family:mono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-variant-ligatures:none}
.bk{animation:bk 1.1s steps(1) infinite}@keyframes bk{50%{opacity:0}}
.gl{animation:gl 4.3s infinite}.gl2{animation:gl 4.3s .15s infinite reverse}
@keyframes gl{0%,90%,100%{transform:none}91%{transform:translate(-5px,2px)}93%{transform:translate(4px,-1px)}95%{transform:translate(-2px,0)}97%{transform:translate(3px,1px)}}
.roll{animation:roll 7s linear infinite}@keyframes roll{from{transform:translateY(-140px)}to{transform:translateY(620px)}}
.fl{animation:fl 6s infinite}@keyframes fl{0%,47%,49%,72%,74%,100%{opacity:1}48%{opacity:.85}73%{opacity:.93}}
.mv{animation:mv 2.4s linear infinite}@keyframes mv{from{transform:translateX(0)}to{transform:translateX(120px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}"""


# ---------- primitives ----------


def esc(s):
    return html.escape(s, quote=False)


def T(x, y, s, size, fill, anchor=None, cls="m", weight=None, attrs=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}"{a}{w}{attrs}>{esc(s)}</text>'


def S(x, y, size, parts, cls="m", attrs=""):
    """One line of mixed-colour text: parts = [(text, colour), ...]."""
    spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in parts)
    return f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" xml:space="preserve"{attrs}>{spans}</text>'


def glow(t):
    return ' filter="url(#glow)"' if t.name == "dark" else ""


def defs(t):
    r, g, b = t.ink
    d = f"""<filter id="grain" x="0" y="0" width="1" height="1"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 {r} 0 0 0 0 {g} 0 0 0 0 {b} 2.4 0 0 0 -1.3"/><feComposite in2="SourceAlpha" operator="in"/></filter>
<filter id="stain" x="0" y="0" width="1" height="1"><feTurbulence type="fractalNoise" baseFrequency=".007" numOctaves="3" seed="4"/><feColorMatrix values="0 0 0 0 {r} 0 0 0 0 {g} 0 0 0 0 {b} 2.6 0 0 0 -1.25"/><feComposite in2="SourceAlpha" operator="in"/></filter>
<filter id="worn" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".6" numOctaves="3" seed="11" result="n"/><feColorMatrix in="n" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -4.2 0 0 0 3.3" result="m"/><feComposite in="SourceGraphic" in2="m" operator="in"/></filter>"""
    if t.name == "dark":
        d += """<filter id="glow" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<pattern id="scan" width="6" height="3" patternUnits="userSpaceOnUse"><rect width="6" height="1" fill="#000" opacity=".38"/></pattern>
<radialGradient id="vig" cx="50%" cy="50%" r="75%"><stop offset="55%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity=".6"/></radialGradient>
<linearGradient id="band" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".045"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>"""
    else:
        d += f'<pattern id="bars" width="10" height="64" patternUnits="userSpaceOnUse"><rect width="10" height="32" fill="{t.band}"/></pattern>'
    return d


def under(t, x, y, w, h, rx=0):
    """Screen background: black glass on dark, greenbar paper on light."""
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{t.bg}"/>'
    if t.name == "light":
        s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#bars)"/>'
    return s


def over(t, x, y, w, h, rx=0):
    """Grunge on top: grain + stains everywhere, scanlines/vignette/roll bar on dark."""
    box = f'x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"'
    dark = t.name == "dark"
    s = f'<rect {box} filter="url(#grain)" opacity="{0.09 if dark else 0.2}"/>'
    if not dark:  # coffee-stained paper; on glass it just reads as smudge
        s += f'<rect {box} filter="url(#stain)" opacity=".07"/>'
    if dark:
        s += f'<rect {box} fill="url(#scan)"/><rect {box} fill="url(#vig)"/>'
        s += (
            f'<clipPath id="cl"><rect {box}/></clipPath><g clip-path="url(#cl)">'
            f'<rect class="roll" x="{x}" y="{y}" width="{w}" height="120" fill="url(#band)"/></g>'
        )
    return s


def chrome(t, w, h, title, right=""):
    """Window frame + title bar shared by every panel."""
    s = f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="14" fill="{t.panel}" stroke="{t.frame}" stroke-width="2.5"/>'
    for i, c in enumerate((t.pink, t.amber, t.hi)):
        s += f'<rect x="{22 + i * 22}" y="17" width="12" height="12" fill="{c}"/>'
    s += T(100, 29, title, 17, t.dim)
    if right:
        s += T(w - 24, 29, right, 15, t.dim, anchor="end")
    s += f'<path d="M2 46H{w - 2}" stroke="{t.frame}" stroke-width="2"/>'
    return s


def screen(t, w, h, body):
    """chrome-less helper: background, content, grunge — inside a framed window."""
    x, y, iw, ih = 3, 47, w - 6, h - 50
    return under(t, x, y, iw, ih, 0) + body + over(t, x, y, iw, ih, 0)


# ---------- fonts ----------


def woff2(name, chars):
    path = FONTS / name
    if not path.exists():
        FONTS.mkdir(exist_ok=True)
        urllib.request.urlretrieve(FONT_SRC[name], path)
    opts = subset.Options()
    opts.flavor, opts.layout_features, opts.hinting, opts.name_IDs = (
        "woff2",
        [],
        False,
        [],
    )
    font = subset.load_font(str(path), opts)
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(font)
    buf = io.BytesIO()
    subset.save_font(font, buf, opts)
    return base64.b64encode(buf.getvalue()).decode()


def faces(body):
    chars = "".join(html.unescape(m) for m in re.findall(r">([^<]+)<", body)) + " "
    f = ""
    if 'class="d"' in body:
        f += f"@font-face{{font-family:vt;src:url(data:font/woff2;base64,{woff2('VT323-Regular.ttf', chars)}) format('woff2')}}"
    f += f"@font-face{{font-family:mono;font-weight:400;src:url(data:font/woff2;base64,{woff2('IBMPlexMono-Regular.ttf', chars)}) format('woff2')}}"
    if 'font-weight="700"' in body:
        f += f"@font-face{{font-family:mono;font-weight:700;src:url(data:font/woff2;base64,{woff2('IBMPlexMono-Bold.ttf', chars)}) format('woff2')}}"
    return f


def svg(t, w, h, title, desc, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        f"<style>{faces(body)}{CSS}</style><defs>{defs(t)}</defs>{body}</svg>"
    )


# ---------- assets ----------


def hero(t):
    W, H = 1200, 470
    dark = t.name == "dark"
    b = chrome(t, W, H, "tty1 — shravani@seattle: ~", "80×24 · utf-8")
    c = ""
    if not dark:  # tractor-feed holes down both edges of the printout
        for y in range(70, H - 10, 30):
            c += f'<circle cx="20" cy="{y}" r="5" fill="#d9d2c2"/><circle cx="{W - 20}" cy="{y}" r="5" fill="#d9d2c2"/>'
        c += f'<path d="M36 47V{H - 3}M{W - 36} 47V{H - 3}" stroke="{t.line}" stroke-dasharray="2 5"/>'

    x = 56
    boot = [
        "Mounted /dev/postgres16.",
        "Started distributed-systems.service.",
        "Reached target open-to-work.",
    ]
    for i, line in enumerate(boot):
        c += S(x, 90 + i * 24, 16, [("[  OK  ] ", t.hi), (line, t.dim)])

    name, ny = "SHRAVANI NIKAM", 252
    split = ' opacity=".75" style="mix-blend-mode:screen"'
    if dark:  # RGB split that twitches every few seconds
        layers = T(x - 3, ny, name, 108, t.cyan, cls="d gl", attrs=split)
        layers += T(x + 3, ny, name, 108, t.pink, cls="d gl2", attrs=split)
    else:  # print misregistration instead
        layers = T(x + 3, ny + 2, name, 108, t.pink, cls="d", attrs=' opacity=".55"')
    c += layers + T(x, ny, name, 108, t.fg, cls="d", attrs=glow(t))
    c += T(
        x,
        296,
        "backend · databases · distributed systems",
        23,
        t.amber,
        attrs=glow(t),
    )
    c += T(x, 330, "MS CS @ Northeastern University · Seattle · Dec 2027", 18, t.dim)
    c += S(x, 382, 18, [("$ ", t.hi), ("cat motto.txt", t.fg)])
    c += T(x, 408, "measure it, then believe it.", 18, t.fg)
    c += S(x, 444, 18, [("shravani@github", t.hi), (":~$ ", t.fg)])
    c += f'<rect class="bk" x="{x + 19 * 10.8 + 2}" y="429" width="11" height="19" fill="{t.hi}"/>'

    # psql panel
    px, py, pw, ph = 716, 72, 438, 360
    c += f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="6" fill="{t.bg if dark else t.panel}" stroke="{t.frame}" stroke-width="2"/>'
    c += f'<path d="M{px} {py + 32}H{px + pw}" stroke="{t.frame}" stroke-width="1.5"/>'
    c += T(px + 16, py + 22, "psql 16 — engineers", 14, t.dim)
    lx, ly, lh = px + 18, py + 62, 22
    q = [
        [("=# ", t.hi), ("EXPLAIN ANALYZE SELECT *", t.fg)],
        [("-# ", t.hi), ("  FROM engineers WHERE open_to_work;", t.fg)],
    ]
    plan = [
        [("Index Scan using idx_backend on engineers", t.amber)],
        [("  Index Cond: (stack @> '{python,postgres}')", t.fg)],
        [("  Filter: open_to_work", t.fg)],
        [("  Rows Removed by Filter: ", t.fg), ("0", t.hi)],
        [("Planning Time: ", t.dim), ("0.081 ms", t.fg)],
        [("Execution Time: ", t.dim), ("0.027 ms", t.hi)],
    ]
    for i, p in enumerate(q):
        c += S(lx, ly + i * lh, 15, p)
    for i, p in enumerate(plan):
        c += S(lx, ly + (i + 3) * lh, 15, p)
    c += T(lx, ly + 10 * lh, "(6 rows)", 15, t.dim)

    # rubber stamp
    sx, sy = 1012, 392
    stamp = (
        f'<rect x="{sx - 132}" y="{sy - 40}" width="264" height="80" rx="4" fill="none" stroke="{t.pink}" stroke-width="4"/>'
        f'<rect x="{sx - 124}" y="{sy - 32}" width="248" height="64" rx="2" fill="none" stroke="{t.pink}" stroke-width="1.5"/>'
        + T(sx, sy + 4, "OPEN TO WORK", 44, t.pink, anchor="middle", cls="d")
        + T(
            sx,
            sy + 24,
            "CO-OP 2027 · FULL-TIME 2028",
            13,
            t.pink,
            anchor="middle",
            weight="700",
        )
    )
    c += f'<g transform="rotate(-7 {sx} {sy})"><g filter="url(#worn)">{stamp}</g></g>'

    b += screen(t, W, H, f'<g class="fl">{c}</g>' if dark else c)
    return svg(
        t,
        W,
        H,
        "Shravani Nikam: backend engineer — databases, distributed systems",
        "MS in Computer Science at Northeastern University in Seattle, graduating December 2027. "
        "Open to a co-op in Spring/Summer 2027 and full-time from January 2028. "
        "Animated terminal: boot log, an EXPLAIN ANALYZE query plan, and an OPEN TO WORK stamp.",
        b,
    )


def stats(t):
    W, H, gap = 1200, 214, 16
    pw = (W - 3 * gap) / 4
    cells = [
        (
            "query-plan-lab",
            "28.4%",
            t.hi,
            ["less query time: a 10 MB", "partial index vs a 404 MB", "covering index"],
        ),
        (
            "ibm skillsbuild '24",
            "−30%",
            t.amber,
            ["avg response time after", "rebuilding intent", "classification"],
        ),
        (
            "gdg cloud '22–'25",
            "200+",
            t.cyan,
            [
                "students taught GCP;",
                "15 juniors mentored into",
                "running their own sessions",
            ],
        ),
        (
            "pg_isready",
            "OPEN",
            t.pink,
            ["co-op Spring/Summer 2027", "full-time from Jan 2028", None],
        ),
    ]
    b = ""
    for i, (unit, big, col, lines) in enumerate(cells):
        x = i * (pw + gap)
        b += f'<rect x="{x + 1.5}" y="1.5" width="{pw - 3}" height="{H - 3}" rx="12" fill="{t.panel}" stroke="{t.frame}" stroke-width="2.5"/>'
        b += under(t, x + 3, 44, pw - 6, H - 47)
        b += f'<path d="M{x + 2} 44H{x + pw - 2}" stroke="{t.frame}" stroke-width="2"/>'
        b += T(x + 18, 29, unit, 16, t.dim) + T(
            x + pw - 18, 29, f"0{i + 1}", 16, t.dim, anchor="end"
        )
        b += T(x + 18, 114, big, 76, col, cls="d", attrs=glow(t))
        for j, line in enumerate(lines):
            if line:
                b += T(x + 18, 146 + j * 22, line, 16, t.fg)
        if not lines[2]:
            b += f'<circle class="bk" cx="{x + 25}" cy="{146 + 2 * 22 - 5}" r="5" fill="{t.hi}"/>'
            b += T(x + 38, 146 + 2 * 22, "accepting connections", 16, t.hi)
        b += (
            over(t, x + 3, 44, pw - 6, H - 47)
            .replace('id="cl"', f'id="cl{i}"')
            .replace("url(#cl)", f"url(#cl{i})")
        )
    return svg(
        t,
        W,
        H,
        "Highlights",
        "28.4% less query time from a 10 MB partial index versus a 404 MB covering index (query-plan-lab). "
        "30% lower average response time after rebuilding intent classification (AI/ML intern, IBM SkillsBuild, 2024). "
        "200+ students taught GCP and 15 juniors mentored as GDG Cloud Co-Lead, 2022–2025. "
        "Open to a co-op in Spring/Summer 2027 and full-time from January 2028.",
        b,
    )


def card(t, slug, status, status_col, desc, tags, viz, alt):
    W, H = 820, 484
    b = chrome(t, W, H, f"~/{slug}")
    tw = len(status) * 9.6 + 24
    b += f'<rect x="{W - 22 - tw}" y="12" width="{tw}" height="24" fill="none" stroke="{status_col}" stroke-width="2"/>'
    b += T(W - 22 - tw / 2, 30, status, 16, status_col, anchor="middle", weight="700")
    c = T(40, 132, slug, 78, t.fg, cls="d", attrs=glow(t))
    c += T(40, 178, desc[0], 21, t.fg) + T(40, 206, desc[1], 21, t.dim)
    c += viz
    c += S(40, 456, 18, [("deps ", t.hi), (" · ".join(tags), t.dim)])
    b += screen(t, W, H, c)
    # 8px transparent margin so two cards side by side (and stacked) don't touch
    return svg(t, W + 16, H + 16, slug, alt, f'<g transform="translate(8 8)">{b}</g>')


def cards(t):
    # query-plan-lab: q1 bars
    bx, full = 250, 380
    qpl = T(40, 254, "q1 median, ms — lower is better", 17, t.dim)
    for i, (label, ms, col) in enumerate(
        [("partial · 10 MB", 71.95, t.hi), ("covering · 404 MB", 100.53, t.dim)]
    ):
        y = 274 + i * 46
        w = full * ms / 100.53
        qpl += T(40, y + 19, label, 19, t.fg)
        qpl += f'<rect x="{bx}" y="{y}" width="{w:.0f}" height="24" fill="{col}"/>'
        qpl += T(bx + w + 12, y + 19, f"{ms}", 19, col)
    qpl += S(
        40,
        394,
        19,
        [("! ", t.pink), ("GIN on the common JSONB probe: 22.5% slower", t.pink)],
    )

    # rhea: two offline lanes converging
    rh = ""
    lanes = [
        ("phone", 280, [(190, "hlc 41.0", 0.3), (420, "hlc 57.0", 0.9)]),
        ("laptop", 352, [(300, "hlc 52.1", 0.6), (480, "hlc 57.1", 1.2)]),
    ]
    for name, y, dots in lanes:
        rh += T(40, y + 6, name, 19, t.dim)
        rh += f'<path d="M140 {y}H560C600 {y} 600 316 640 316" fill="none" stroke="{t.line if t.name == "dark" else t.frame}" stroke-width="3" stroke-dasharray="{"0" if name == "phone" else "10 7"}"/>'
        for x, lab, d in dots:
            ly = y - 14 if name == "phone" else y + 28
            rh += f'<circle cx="{x}" cy="{y}" r="8" fill="{t.amber}"/>'
            rh += T(x, ly, lab, 15, t.dim, anchor="middle")
    rh += T(390, 380, "offline", 14, t.dim, anchor="middle")
    rh += f'<path d="M640 316H780" stroke="{t.hi}" stroke-width="3"/>'
    rh += f'<g class="mv"><circle cx="640" cy="316" r="4" fill="{t.hi}"/></g>'
    rh += f'<circle cx="760" cy="316" r="11" fill="{t.hi}"{glow(t)}/>'
    rh += T(700, 300, "1 row", 16, t.hi, anchor="middle")
    rh += T(780, 412, "hybrid logical clock + last-write-wins", 16, t.hi, anchor="end")

    # mergelag: invariant guards
    ml = S(40, 258, 19, [("$ ", t.hi), ("make check", t.fg)])
    guards = [
        "no pandas in first-party source",
        "no credential reaches a log",
        "no query reads payload (92.4% of bytes)",
        "no query runs unpriced",
    ]
    for i, g in enumerate(guards):
        ml += S(40, 294 + i * 31, 19, [("[PASS] ", t.hi), (g, t.fg)])

    # hallucination-hunter: spot the fabrication
    hh = T(40, 256, "which answer contains a fabrication?", 19, t.fg)
    pre = "B  The Eiffel Tower opened in "
    for i, (txt, col) in enumerate(
        [("A  The Eiffel Tower opened in 1889.", t.frame), (pre + "1901.", t.pink)]
    ):
        y = 272 + i * 52
        hh += f'<rect x="40" y="{y}" width="740" height="40" fill="none" stroke="{col}" stroke-width="{2.5 if i else 1.5}"/>'
        if i:
            hh += f'<rect x="{56 + len(pre) * 11.4 - 3}" y="{y + 7}" width="{4 * 11.4 + 6}" height="26" fill="{t.pink}" opacity=".28"/>'
            hh += T(764, y + 26, "← fabricated", 17, t.pink, anchor="end", weight="700")
        hh += T(56, y + 26, txt, 19, t.fg)
    hh += S(
        40,
        396,
        17,
        [
            ("confidence ", t.dim),
            ("[1] [2] [3] ", t.dim),
            ("[4]", t.hi),
            (" [5]", t.dim),
        ],
    )

    return {
        "query-plan-lab": card(
            t,
            "query-plan-lab",
            "SHIPPED",
            t.hi,
            (
                "Eight PostgreSQL 16 index strategies, four query",
                "plans, 10M rows, reproducible in two commands.",
            ),
            ["postgres 16", "docker", "python", "make"],
            qpl,
            "query-plan-lab: eight PostgreSQL 16 index strategies on 10M rows. A 10 MB partial index ran q1 in "
            "71.95 ms versus 100.53 ms for a 404 MB covering index; GIN made the common JSONB probe 22.5% slower.",
        ),
        "rhea": card(
            t,
            "rhea",
            "LIVE",
            t.hi,
            (
                "Local-first cycle tracker with partner sharing.",
                "Two offline devices still converge on one log.",
            ),
            ["react", "typescript", "supabase", "indexeddb"],
            rh,
            "Rhea: local-first cycle tracker with partner sharing. Edits made offline on two devices converge "
            "through a hybrid logical clock and a last-write-wins merge.",
        ),
        "mergelag": card(
            t,
            "mergelag",
            "WIP 1a/8",
            t.amber,
            (
                "Predicts how long an open PR waits to merge,",
                "and names what is actually slowing review.",
            ),
            ["python 3.12", "bigquery", "github actions", "uv"],
            ml,
            "MergeLag (in development): predicts pull-request merge time. Enforced guards: no pandas in "
            "first-party source, no credential reaches a log, no query reads payload, no query runs unpriced.",
        ),
        "hallucination-hunter": card(
            t,
            "hallucination-hunter",
            "STUDY WIP",
            t.amber,
            (
                "Can you catch the AI lying? A web game and a",
                "human-eval study on spotting fabricated facts.",
            ),
            ["next.js 16", "postgres", "supabase", "python"],
            hh,
            "Hallucination Hunter: a web game and human-evaluation study on how well people "
            "detect fabricated facts in AI answers.",
        ),
    }


def log(t):
    W = 1200
    rows = [
        (
            "2022–25",
            "gdg-cloud",
            "Cloud Co-Lead · Google Developer Groups on Campus, Pune",
            "GCP workshops for 200+ students over three years; mentored 15 juniors",
        ),
        (
            "2024",
            "ibm-intern",
            "AI/ML Intern · CSRBOX × IBM SkillsBuild · remote",
            "rebuilt intent classification around real traffic; avg response −30%",
        ),
        (
            "2025",
            "irjmets",
            "Paper · Unified Sentiment Analysis of Customer Reviews",
            "Vol. 07, Issue 05 · aspect-level BERT pipeline over 7k+ reviews",
        ),
        (
            "2025",
            "sppu",
            "BS AI & Data Science · Savitribai Phule Pune University",
            None,
        ),
        (
            "→ 2027",
            "northeastern",
            "MS Computer Science · Northeastern University, Seattle",
            "distributed systems · DBMS · algorithms · cloud computing",
        ),
    ]
    c = S(40, 92, 18, [("$ ", t.hi), ("journalctl -u shravani --no-pager", t.fg)])
    y = 138
    for date, unit, msg, sub in rows:
        c += T(40, y, date, 18, t.amber)
        c += T(150, y, unit, 18, t.hi)
        c += T(300, y, msg, 18, t.fg)
        c += T(300, y + 26, sub, 16, t.dim) if sub else ""
        y += 70 if sub else 44
    c += (
        T(40, y, "now", 18, t.pink)
        + T(150, y, "status", 18, t.pink)
        + T(
            300,
            y,
            "OPEN: co-op Spring/Summer 2027 · full-time from Jan 2028",
            18,
            t.pink,
            weight="700",
        )
        + f'<rect class="bk" x="{300 + 56 * 10.8 + 8}" y="{y - 15}" width="11" height="19" fill="{t.pink}"/>'
    )
    H = y + 40
    b = chrome(t, W, H, "journal — shravani.service") + screen(t, W, H, c)
    return svg(
        t,
        W,
        H,
        "Experience log",
        "2022–2025: Cloud Co-Lead, Google Developer Groups on Campus, Pune — GCP workshops for 200+ students, "
        "mentored 15 juniors. 2024: AI/ML Intern, CSRBOX × IBM SkillsBuild — rebuilt intent classification, "
        "average response time down 30%. 2025: paper in IRJMETS, Unified Sentiment Analysis of Customer Reviews. "
        "2025: BS AI & Data Science, Savitribai Phule Pune University. Through 2027: MS Computer Science, "
        "Northeastern University, Seattle. Open to a co-op in Spring/Summer 2027 and full-time from January 2028.",
        b,
    )


def stack(t):
    W = 1200
    rows = [
        ("core", ["Python", "PostgreSQL", "SQL", "Docker"]),
        ("backend", ["schema design", "migrations", "query optimization", "REST"]),
        ("build", ["TypeScript", "React", "Node/Express", "GitHub Actions"]),
        ("cloud", ["AWS", "GCP", "Linux", "Supabase"]),
        ("data", ["Pandas", "NumPy", "spaCy", "Hugging Face"]),
    ]
    c = S(40, 92, 18, [("$ ", t.hi), ("tree ~/loadout", t.fg)])
    y = 140
    for i, (cat, items) in enumerate(rows):
        row = T(40, y, "└──" if i == len(rows) - 1 else "├──", 18, t.dim) + T(
            92, y, cat, 18, t.amber
        )
        x = 210
        for item in items:
            w = len(item) * 10.2 + 28
            col = t.hi if cat == "core" else t.frame
            row += f'<rect x="{x}" y="{y - 23}" width="{w:.0f}" height="34" fill="{t.panel}" stroke="{col}" stroke-width="{2 if cat == "core" else 1.5}"/>'
            row += T(x + 14, y, item, 17, t.hi if cat == "core" else t.fg)
            x += w + 12
        c += row
        y += 54
    c += T(
        40,
        y + 4,
        f"{len(rows)} directories, {sum(len(r[1]) for r in rows)} files",
        16,
        t.dim,
    )
    H = y + 36
    b = chrome(t, W, H, "loadout") + screen(t, W, H, c)
    return svg(
        t,
        W,
        H,
        "Tech stack",
        "; ".join(f"{cat}: {', '.join(items)}" for cat, items in rows),
        b,
    )


def button(t, label):
    w, h, sh = len(label) * 12 + 2 * 10.8 + 48, 52, 5
    b = f'<rect x="{sh}" y="{sh}" width="{w}" height="{h}" fill="{t.pink}"/>'
    b += f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" fill="{t.panel}" stroke="{t.hi if t.name == "dark" else t.frame}" stroke-width="2.5"/>'
    b += S(22, 34, 20, [("> ", t.hi), (label, t.fg)], attrs=' font-weight="700"')
    b += f'<rect class="bk" x="{22 + (len(label) + 2) * 12 + 4}" y="36" width="12" height="3" fill="{t.hi}"/>'
    return svg(t, w + sh, h + sh, label, f"{label} button", b)


def main():
    OUT.mkdir(exist_ok=True)
    for t in (DARK, LIGHT):
        files = {
            "hero": hero(t),
            "stats": stats(t),
            "log": log(t),
            "stack": stack(t),
            "btn-linkedin": button(t, "linkedin"),
            "btn-email": button(t, "email"),
        }
        files |= {f"card-{k}": v for k, v in cards(t).items()}
        for name, s in files.items():
            (OUT / f"{name}-{t.name}.svg").write_text(s)
            print(f"{name}-{t.name}.svg  {len(s) // 1024} KB")


if __name__ == "__main__":
    main()
