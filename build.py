# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools", "brotli"]
# ///
"""Regenerate every SVG in assets/:  uv run build.py

Each asset is written twice (-dark, -light) for <picture> theme switching.
IBM Plex Mono (OFL) is subset to the glyphs used and embedded, because GitHub
serves README SVGs as images and they can't load external fonts.

Animation rule: the t=0 frame must already show every piece of content, because
some renderers (GitHub mobile, link previews) freeze on it. Motion is decoration
on top: cursors, pulses, flowing dashes, sync packets, a shimmer.
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
GF = "https://github.com/google/fonts/raw/main/ofl/ibmplexmono/"
WEIGHTS = {400: "IBMPlexMono-Regular.ttf", 600: "IBMPlexMono-SemiBold.ttf"}

# One hue per track; pastel on dark, deeper on light.
DARK = NS(
    name="dark",
    panel="#11161d",
    bar="#161c24",
    line="#2a313c",
    fg="#e6edf3",
    muted="#8b949e",
    be="#7ee0a8",
    ml="#b9a3ff",
    da="#f2b87a",
    infra="#79c0ff",
    test="#6fd3c7",
    fe="#f0a3c4",
    lang="#c9d1d9",
    dots=("#ff6b61", "#f5c14b", "#3fc56b"),
)
LIGHT = NS(
    name="light",
    panel="#ffffff",
    bar="#f6f8fa",
    line="#d0d7de",
    fg="#1f2328",
    muted="#59636e",
    be="#1a7f37",
    ml="#8250df",
    da="#bc4c00",
    infra="#0969da",
    test="#1b7c83",
    fe="#bf3989",
    lang="#424a53",
    dots=("#ff5f57", "#e5a823", "#28c840"),
)

CSS = """.m{font-family:mono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-variant-ligatures:none}
.bk{animation:bk 1.1s steps(1) infinite}@keyframes bk{50%{opacity:0}}
.rg{transform-box:fill-box;transform-origin:center;animation:rg 2.4s ease-out infinite}
@keyframes rg{0%{transform:scale(1);opacity:.7}100%{transform:scale(3.2);opacity:0}}
.fw{animation:fw 1.1s linear infinite}@keyframes fw{to{stroke-dashoffset:-20}}
.sh{animation:sh 3.4s ease-in-out infinite}@keyframes sh{0%{transform:translateX(0)}60%,100%{transform:translateX(520px)}}
.cy{animation:cy 14s infinite}@keyframes cy{0%{opacity:0}2%,23%{opacity:1}25%,100%{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.pk{display:none}}"""


# ---------- primitives ----------


def esc(s):
    return html.escape(s, quote=False)


def T(x, y, s, size, fill, anchor=None, weight=None, attrs=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x}" y="{y}" class="m" font-size="{size}" fill="{fill}" xml:space="preserve"{a}{w}{attrs}>{esc(s)}</text>'


def S(x, y, size, parts, weight=None):
    """One line of mixed-colour text: parts = [(text, colour), ...]."""
    w = f' font-weight="{weight}"' if weight else ""
    spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in parts)
    return f'<text x="{x}" y="{y}" class="m" font-size="{size}" xml:space="preserve"{w}>{spans}</text>'


def cw(size):
    """Advance width of one Plex Mono glyph at `size` px."""
    return size * 0.6


def window(t, w, h, title, right=""):
    """Terminal window: traffic-light dots, title, tinted title bar."""
    s = f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="10" fill="{t.panel}" stroke="{t.line}" stroke-width="1.5"/>'
    s += f'<path d="M1.5 44V11A9.5 9.5 0 0 1 11 1.5H{w - 11}A9.5 9.5 0 0 1 {w - 1.5} 11V44Z" fill="{t.bar}"/>'
    s += f'<path d="M1 44H{w - 1}" stroke="{t.line}"/>'
    for i, c in enumerate(t.dots):
        s += f'<circle cx="{24 + i * 20}" cy="22.5" r="6" fill="{c}"/>'
    s += T(96, 28, title, 15, t.muted) + right
    return s


def chip(t, x, y, text, col, size=15, weight=None):
    """Tinted pill; returns (svg, width). y is the text baseline."""
    w = len(text) * cw(size) + 22
    s = (
        f'<rect x="{x}" y="{y - size - 4}" width="{w:.1f}" height="{size + 13}" rx="6" fill="{col}" '
        f'fill-opacity=".1" stroke="{col}" stroke-opacity=".5"/>'
    )
    return s + T(x + 11, y, text, size, col, weight=weight), w


def pulse(x, y, r, col):
    """Solid dot with an expanding ring."""
    return (
        f'<circle class="rg" cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{col}" stroke-width="1.5"/>'
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}"/>'
    )


# ---------- fonts ----------


def woff2(weight, chars):
    path = FONTS / WEIGHTS[weight]
    if not path.exists():
        FONTS.mkdir(exist_ok=True)
        urllib.request.urlretrieve(GF + WEIGHTS[weight], path)
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


def svg(w, h, title, desc, body, defs=""):
    chars = "".join(html.unescape(m) for m in re.findall(r">([^<]+)<", body)) + " "
    weights = [400] + ([600] if 'font-weight="600"' in body else [])
    faces = "".join(
        f"@font-face{{font-family:mono;font-weight:{wt};src:url(data:font/woff2;base64,{woff2(wt, chars)}) format('woff2')}}"
        for wt in weights
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        f"<style>{faces}{CSS}</style><defs>{defs}</defs>{body}</svg>"
    )


# ---------- assets ----------

NOW = [
    "running a human-eval study on how people catch LLM hallucinations",
    "contributing to ML infra: DeepSpeed (merged), PyTorch (open PR)",
    "building MergeLag: predicting PR merge times from GH Archive",
    "benchmarking PostgreSQL index strategies on 10M rows",
]


def hero(t):
    W, H, x = 1200, 446, 52
    focus = [
        (
            "backend",
            t.be,
            "PostgreSQL · query planning & indexing · offline-first sync · REST APIs",
        ),
        (
            "ml / ai",
            t.ml,
            "NLP · BERT pipelines · LLM agents & evaluation · open-source ML infra",
        ),
        (
            "data",
            t.da,
            "experiment design · benchmarking · BigQuery, DuckDB & Polars pipelines",
        ),
    ]
    b = window(t, W, H, "shravani@github: ~")
    b += S(x, 92, 18, [("$ ", t.be), ("whoami", t.muted)])
    b += T(x, 154, "Shravani Nikam", 58, t.fg, weight="600")
    b += S(
        x,
        196,
        22,
        [
            ("backend", t.be),
            (" · ", t.muted),
            ("machine learning", t.ml),
            (" · ", t.muted),
            ("data science", t.da),
        ],
    )
    b += T(
        x,
        228,
        "MS Computer Science · Northeastern University · Seattle, WA",
        17,
        t.muted,
    )

    rx = W - x
    b += pulse(rx - cw(17) * 12 - 16, 86, 5.5, t.be)
    b += T(rx, 92, "open to work", 17, t.fg, anchor="end", weight="600")
    b += T(rx, 118, "co-op · spring/summer 2027", 15, t.muted, anchor="end")

    b += f'<path d="M{x} 256H{W - x}" stroke="{t.line}" stroke-dasharray="4 6"/>'
    for i, (label, col, text) in enumerate(focus):
        y = 296 + i * 34
        b += T(x, y, label, 17, col, weight="600") + T(x + 130, y, text, 17, t.fg)

    # "now" ticker: one line at a time, item 0 is what a frozen first frame shows
    y, px = 410, x + cw(18) * 6
    b += S(x, y, 18, [("$ now ", t.be)])
    for k, line in enumerate(NOW):
        delay, base = 3.5 * k - 0.5, "" if k == 0 else ' opacity="0"'
        b += (
            f'<g class="cy" style="animation-delay:{delay}s"{base}>'
            + T(px, y, line, 18, t.fg)
            + f'<rect class="bk" x="{px + len(line) * cw(18) + 6}" y="{y - 15}" width="10" height="19" fill="{t.be}"/></g>'
        )
    return svg(
        W,
        H,
        "Shravani Nikam: backend, machine learning, data science",
        "MS in Computer Science at Northeastern University, Seattle. Open to a co-op in Spring/Summer 2027. "
        + " ".join(f"{label}: {text}." for label, _, text in focus)
        + " Currently: "
        + "; ".join(NOW)
        + ".",
        b,
    )


def stats(t):
    W, H, gap = 1200, 166, 16
    pw = (W - 3 * gap) / 4
    cells = [
        (
            t.ml,
            "ai/ml intern · ibm",
            "−30%",
            "avg response time after",
            "rebuilding intent classifier",
        ),
        (
            t.ml,
            "nlp paper · irjmets",
            "7k+",
            "reviews scored per aspect",
            "by a BERT pipeline",
        ),
        (
            t.be,
            "query-plan-lab",
            "28.4%",
            "less query time: 10 MB",
            "partial vs 404 MB covering",
        ),
        (
            t.infra,
            "gdg cloud co-lead",
            "200+",
            "students taught GCP;",
            "15 juniors mentored",
        ),
    ]
    b = ""
    for i, (col, head, big, l1, l2) in enumerate(cells):
        x = i * (pw + gap)
        b += f'<rect x="{x + 0.75}" y=".75" width="{pw - 1.5}" height="{H - 1.5}" rx="10" fill="{t.panel}" stroke="{t.line}" stroke-width="1.5"/>'
        b += f'<rect x="{x + 1.5}" y="1.5" width="4" height="{H - 3}" rx="2" fill="{col}"/>'
        b += T(x + 24, 34, head, 14, t.muted)
        b += T(x + 24, 92, big, 44, t.fg, weight="600")
        b += T(x + 24, 124, l1, 14, t.muted) + T(x + 24, 145, l2, 14, t.muted)
    return svg(
        W,
        H,
        "Highlights",
        "30% lower average response time after rebuilding intent classification (AI/ML intern, IBM SkillsBuild). "
        "7k+ reviews scored per aspect by a BERT pipeline (IRJMETS paper). "
        "28.4% less query time from a 10 MB partial index versus a 404 MB covering index (query-plan-lab). "
        "200+ students taught GCP and 15 juniors mentored (GDG Cloud Co-Lead).",
        b,
    )


def card(t, slug, track, col, status, desc, stack, viz, alt, defs="", live=False):
    W, H, m = 820, 476, 8  # m: transparent margin so side-by-side cards don't touch
    right = T(W - 26, 28, status, 15, t.muted, anchor="end")
    if live:
        right += pulse(W - 26 - len(status) * cw(15) - 14, 23, 4.5, col)
    b = window(t, W, H, f"~/{slug}", right)
    b += chip(t, 40, 90, track, col, 14, "600")[0]
    b += T(40, 150, slug, 42, t.fg, weight="600")
    b += T(40, 192, desc[0], 19, t.fg) + T(40, 219, desc[1], 19, t.fg)
    b += viz
    cx = 40
    for s in stack:
        c, w = chip(t, cx, 446, s, t.muted, 14)
        b += c
        cx += w + 8
    return svg(
        W + 2 * m,
        H + 2 * m,
        slug,
        alt,
        f'<g transform="translate({m} {m})">{b}</g>',
        defs,
    )


def kv(t, rows, y0, col, step=32, key_w=160):
    s = ""
    for i, (k, v) in enumerate(rows):
        y = y0 + i * step
        s += T(40, y, k, 16, col) + T(40 + key_w, y, v, 16, t.fg)
    return s


def cards(t):
    hh = kv(
        t,
        [
            ("design", "between-session random assignment"),
            ("conditions", "paired answers  vs  single answer"),
            ("measures", "accuracy · calibration · category"),
            ("integrity", "server-side scoring · RLS · no IPs"),
            ("findings", "pending — none claimed yet"),
        ],
        262,
        t.ml,
    )

    # mergelag: built stages solid with data flowing between them; planned stages dashed
    ml = ""
    stages = [
        ("GH Archive", "public events", True),
        ("BigQuery", "dry-run priced", True),
        ("features", "point-in-time", False),
        ("model", "merge time", False),
        ("digest", "weekly", False),
    ]
    bw, gap, by = 124, 30, 270
    for i, (name, cap, built) in enumerate(stages):
        x = 40 + i * (bw + gap)
        dash = "" if built else ' stroke-dasharray="5 5"'
        ml += (
            f'<rect x="{x}" y="{by}" width="{bw}" height="42" rx="6" fill="{t.da if built else "none"}" '
            f'fill-opacity=".1" stroke="{t.da if built else t.line}" stroke-width="1.5"{dash}/>'
        )
        ml += T(
            x + bw / 2, by + 27, name, 16, t.fg if built else t.muted, anchor="middle"
        )
        ml += T(x + bw / 2, by + 64, cap, 13, t.muted, anchor="middle")
        if i:
            flowing = built and stages[i - 1][2]  # only between two built stages
            cls = ' class="fw"' if flowing else ""
            ml += (
                f'<path{cls} d="M{x - gap + 4} {by + 21}H{x - 4}" '
                f'stroke="{t.da if flowing else t.line}" stroke-width="2" stroke-dasharray="{"6 4" if flowing else "2 4"}"/>'
            )
    ml += T(
        40, 380, "built: extraction · planned: features, model, digest", 15, t.muted
    )
    ml += T(
        40,
        404,
        "guards: no leakage · no unpriced query · no secrets in logs",
        15,
        t.muted,
    )

    # query-plan-lab: q1 bars with a shimmer sweeping across them
    bx, full = 250, 400
    qpl = T(40, 262, "q1 median, ms · lower is better", 15, t.muted)
    bars = ""
    for i, (label, ms, c) in enumerate(
        [("partial · 10 MB", 71.95, t.be), ("covering · 404 MB", 100.53, t.line)]
    ):
        y = 284 + i * 40
        w = full * ms / 100.53
        qpl += T(40, y + 13, label, 16, t.fg) + T(
            bx + w + 12, y + 13, f"{ms}", 16, t.fg
        )
        bars += "" if i else f'<rect x="{bx}" y="{y}" width="{w:.0f}" height="16" rx="3"/>'
        qpl += f'<rect x="{bx}" y="{y}" width="{w:.0f}" height="16" rx="3" fill="{c}"/>'
    qpl += (
        f'<g clip-path="url(#bars)"><rect class="sh" x="{bx - 160}" y="280" width="120" height="24" '
        f'fill="url(#gl)"/></g>'
    )
    qpl += T(40, 380, "GIN on the common JSONB probe: 22.5% slower", 15, t.muted)
    qpl += T(40, 404, "8 index strategies · 4 queries · 10M events", 15, t.muted)
    qpl_defs = (
        f'<clipPath id="bars">{bars}</clipPath><linearGradient id="gl" x1="0" x2="1">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" '
        f'stop-opacity="{0.35 if t.name == "dark" else 0.55}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    )

    # rhea: two offline lanes converging, with sync packets travelling along them
    rh, my = "", 324
    lanes = [
        ("phone", 288, [(200, "hlc 41.0"), (420, "hlc 57.0")], "", 0),
        (
            "laptop",
            360,
            [(300, "hlc 52.1"), (490, "hlc 57.1")],
            ' stroke-dasharray="7 6"',
            1.4,
        ),
    ]
    for name, y, dots, dash, begin in lanes:
        ly = y - 14 if name == "phone" else y + 26
        path = f"M140 {y}H560C600 {y} 600 {my} 640 {my}H760"
        rh += T(40, y + 6, name, 16, t.muted)
        rh += f'<path d="M140 {y}H560C600 {y} 600 {my} 640 {my}" fill="none" stroke="{t.line}" stroke-width="2"{dash}/>'
        for x, lab in dots:
            rh += f'<circle cx="{x}" cy="{y}" r="6" fill="{t.be}"/>' + T(
                x, ly, lab, 13, t.muted, anchor="middle"
            )
        rh += (
            f'<circle class="pk" r="4" fill="{t.be}" opacity="0">'
            f'<animateMotion dur="2.8s" begin="{begin}s" repeatCount="indefinite" path="{path}"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.08;.9;1" dur="2.8s" begin="{begin}s" repeatCount="indefinite"/></circle>'
        )
    rh += T(395, 386, "offline", 13, t.muted, anchor="middle")
    rh += f'<path d="M640 {my}H760" stroke="{t.be}" stroke-width="2"/>' + pulse(
        760, my, 7, t.be
    )
    rh += T(700, my - 14, "1 row", 14, t.be, anchor="middle")
    rh += T(40, 412, "hybrid logical clock + last-write-wins merge", 15, t.muted)

    return {
        "hallucination-hunter": card(
            t,
            "hallucination-hunter",
            "ML · EVALUATION",
            t.ml,
            "study in progress",
            (
                "Web game + human-evaluation study on whether",
                "people can spot fabricated facts in AI answers.",
            ),
            ["next.js", "typescript", "postgres", "python"],
            hh,
            "Hallucination Hunter (study in progress): a web game and human-evaluation study on whether people "
            "can spot fabricated facts in AI answers. Between-session random assignment to paired or single answers; "
            "measures accuracy, confidence calibration and per-category accuracy; scoring is server-side.",
            live=True,
        ),
        "mergelag": card(
            t,
            "mergelag",
            "ML · DATA",
            t.da,
            "phase 1a / 8",
            (
                "Predicts how long an open pull request waits to",
                "merge, and what is slowing the review queue.",
            ),
            ["python", "bigquery", "duckdb", "polars", "sqlalchemy"],
            ml,
            "MergeLag (in development): predicts pull-request merge time. Pipeline from GH Archive through priced "
            "BigQuery queries (built) to point-in-time features, a merge-time model and a weekly digest (planned), "
            "with guards against leakage, unpriced queries and secrets in logs.",
        ),
        "query-plan-lab": card(
            t,
            "query-plan-lab",
            "BACKEND · DATABASES",
            t.be,
            "shipped",
            (
                "Eight PostgreSQL 16 index strategies, four query",
                "plans, 10M rows, reproducible in two commands.",
            ),
            ["postgres 16", "docker", "python", "pandas", "matplotlib"],
            qpl,
            "query-plan-lab: eight PostgreSQL 16 index strategies on 10M rows. A 10 MB partial index ran q1 in "
            "71.95 ms versus 100.53 ms for a 404 MB covering index; GIN made the common JSONB probe 22.5% slower.",
            qpl_defs,
        ),
        "rhea": card(
            t,
            "rhea",
            "BACKEND · SYNC",
            t.be,
            "live",
            (
                "Local-first cycle tracker with partner sharing.",
                "Offline edits on two devices converge to one log.",
            ),
            ["react", "typescript", "supabase", "indexeddb"],
            rh,
            "Rhea: local-first cycle tracker with partner sharing. Edits made offline on two devices converge "
            "through a hybrid logical clock and a last-write-wins merge.",
            live=True,
        ),
    }


def log(t):
    W, x = 1200, 52
    rows = [
        (
            "2026",
            t.ml,
            "Open source · ML infrastructure",
            "DeepSpeed #8567 merged: sub_group_size docs + default fix · PyTorch #198840 open",
        ),
        (
            "current",
            t.muted,
            "MS Computer Science · Northeastern University, Seattle",
            "distributed systems · DBMS · algorithms · cloud computing",
        ),
        (
            "2025",
            t.ml,
            "Research paper · IRJMETS Vol. 07, Issue 05",
            "Unified Sentiment Analysis of Customer Reviews: aspect-level BERT over 7k+ reviews",
        ),
        (
            "2025",
            t.muted,
            "BS AI & Data Science · Savitribai Phule Pune University",
            None,
        ),
        (
            "2024",
            t.ml,
            "AI/ML Intern · CSRBOX × IBM SkillsBuild",
            "rebuilt intent classification around real traffic; average response time −30%",
        ),
        (
            "2022–25",
            t.infra,
            "Cloud Co-Lead · Google Developer Groups on Campus, Pune",
            "GCP workshops for 200+ students over three years; mentored 15 juniors",
        ),
    ]
    b, y, dx = "", 92, x + 120
    ys = []
    for i, (when, col, role, sub) in enumerate(rows):
        ys.append(y)
        b += T(x, y, when, 15, t.muted)
        b += (
            pulse(dx, y - 5, 5, col)
            if i == 0
            else f'<circle cx="{dx}" cy="{y - 5}" r="5" fill="{col}"/>'
        )
        b += T(dx + 24, y, role, 17, t.fg, weight="600")
        if sub:
            b += T(dx + 24, y + 25, sub, 15, t.muted)
        y += 68 if sub else 46
    H = y - 18
    rail = f'<path d="M{dx} {ys[0] + 4}V{ys[-1] - 14}" stroke="{t.line}" stroke-width="1.5"/>'
    return svg(
        W,
        H,
        "Experience",
        " ".join(
            f"{when}: {role}{' — ' + sub if sub else ''}."
            for when, _, role, sub in rows
        ),
        window(t, W, H, "~/experience") + rail + b,
    )


def stack(t):
    W, x = 1200, 52
    rows = [
        (
            "languages",
            t.lang,
            ["Python", "TypeScript", "SQL", "PL/pgSQL", "JavaScript"],
        ),
        (
            "backend",
            t.be,
            [
                "PostgreSQL",
                "FastAPI",
                "SQLAlchemy",
                "Alembic",
                "Pydantic",
                "Next.js",
                "Node/Express",
                "Supabase",
            ],
        ),
        (
            "ml / ai",
            t.ml,
            [
                "PyTorch",
                "DeepSpeed",
                "Hugging Face",
                "BERT",
                "spaCy",
                "LLM agents",
                "LLM evaluation",
            ],
        ),
        (
            "data",
            t.da,
            [
                "pandas",
                "Polars",
                "DuckDB",
                "NumPy",
                "BigQuery",
                "sqlglot",
                "matplotlib",
                "Parquet",
            ],
        ),
        (
            "infra",
            t.infra,
            ["Docker", "GitHub Actions", "AWS", "GCP", "Vercel", "Linux", "uv", "Make"],
        ),
        (
            "testing",
            t.test,
            ["pytest", "Vitest", "Playwright", "mypy", "Ruff", "ESLint"],
        ),
        (
            "frontend",
            t.fe,
            ["React", "Vite", "Tailwind CSS", "Electron", "Capacitor", "IndexedDB"],
        ),
    ]
    b = S(x, 88, 17, [("$ ", t.be), ("ls --color ~/stack", t.muted)])
    y = 136
    for label, col, items in rows:
        b += T(x, y, label, 16, col, weight="600")
        cx = x + 130
        for item in items:
            c, w = chip(t, cx, y, item, col, 15)
            b += c
            cx += w + 9
        y += 46
    H = y - 6
    return svg(
        W,
        H,
        "Tech stack",
        "; ".join(f"{label}: {', '.join(items)}" for label, _, items in rows),
        window(t, W, H, "~/stack") + b,
    )


def button(t, label, col):
    w, h = len(label) * cw(17) + 62, 46
    b = f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="8" fill="{t.panel}" stroke="{t.line}" stroke-width="1.5"/>'
    b += f'<circle cx="20" cy="{h / 2}" r="4.5" fill="{col}"/>'
    b += S(34, 29, 17, [(label, t.fg), (" ↗", t.muted)])
    return svg(w, h, label, f"{label} button", b)


def main():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.svg"):  # drop assets from older layouts
        f.unlink()
    for t in (DARK, LIGHT):
        files = {
            "hero": hero(t),
            "stats": stats(t),
            "log": log(t),
            "stack": stack(t),
            "btn-linkedin": button(t, "LinkedIn", t.infra),
            "btn-email": button(t, "Email", t.be),
        }
        files |= {f"card-{k}": v for k, v in cards(t).items()}
        for name, s in files.items():
            (OUT / f"{name}-{t.name}.svg").write_text(s)
    print(
        f"{len(list(OUT.glob('*.svg')))} files, {sum(f.stat().st_size for f in OUT.glob('*.svg')) // 1024} KB"
    )


if __name__ == "__main__":
    main()
