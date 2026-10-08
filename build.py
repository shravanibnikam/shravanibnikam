# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools", "brotli"]
# ///
"""Regenerate every SVG in assets/:  uv run build.py

Each asset is written twice (-dark, -light) for <picture> theme switching.
IBM Plex Mono (OFL) is subset to the glyphs used and embedded, because GitHub
serves README SVGs as images and they can't load external fonts.
Animations only ever change opacity, and content is visible at t=0, so
renderers that freeze the first frame still show everything.
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

DARK = NS(
    name="dark",
    panel="#0f1419",
    line="#262d37",
    fg="#e6edf3",
    muted="#8b949e",
    faint="#2a313b",
    be="#7ee0a8",
    ml="#b9a3ff",
    da="#f2b87a",
)
LIGHT = NS(
    name="light",
    panel="#ffffff",
    line="#d0d7de",
    fg="#1f2328",
    muted="#59636e",
    faint="#e1e6eb",
    be="#1a7f4b",
    ml="#6e40c9",
    da="#a85a00",
)

CSS = """.m{font-family:mono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-variant-ligatures:none}
.bk{animation:bk 1.1s steps(1) infinite}@keyframes bk{50%{opacity:0}}
.pu{animation:pu 2.4s ease-in-out infinite}@keyframes pu{50%{opacity:.25}}
@media (prefers-reduced-motion:reduce){.bk,.pu{animation:none}}"""


# ---------- primitives ----------


def esc(s):
    return html.escape(s, quote=False)


def T(x, y, s, size, fill, anchor=None, weight=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x}" y="{y}" class="m" font-size="{size}" fill="{fill}"{a}{w}>{esc(s)}</text>'


def S(x, y, size, parts, anchor=None):
    """One line of mixed-colour text: parts = [(text, colour), ...]."""
    a = f' text-anchor="{anchor}"' if anchor else ""
    spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in parts)
    return f'<text x="{x}" y="{y}" class="m" font-size="{size}" xml:space="preserve"{a}>{spans}</text>'


def cw(size):
    """Advance width of one Plex Mono glyph at `size` px."""
    return size * 0.6


def window(t, w, h, title, right=""):
    """Rounded panel with three muted dots and a title — the only chrome used."""
    s = f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="12" fill="{t.panel}" stroke="{t.line}" stroke-width="1.5"/>'
    for i in range(3):
        s += f'<circle cx="{26 + i * 18}" cy="22" r="5" fill="{t.faint}"/>'
    s += T(92, 27, title, 15, t.muted)
    if right:
        s += right
    s += f'<path d="M1 44H{w - 1}" stroke="{t.line}" stroke-width="1"/>'
    return s


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


def svg(t, w, h, title, desc, body):
    chars = "".join(html.unescape(m) for m in re.findall(r">([^<]+)<", body)) + " "
    weights = [400] + ([600] if 'font-weight="600"' in body else [])
    faces = "".join(
        f"@font-face{{font-family:mono;font-weight:{wt};src:url(data:font/woff2;base64,{woff2(wt, chars)}) format('woff2')}}"
        for wt in weights
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        f"<style>{faces}{CSS}</style>"
        f'<defs><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<circle cx="1.5" cy="1.5" r="1.1" fill="{t.faint}"/></pattern></defs>{body}</svg>'
    )


# ---------- assets ----------


def hero(t):
    W, H, x = 1200, 452, 52
    b = window(t, W, H, "shravani@seattle: ~")
    b += f'<rect x="2" y="45" width="{W - 4}" height="{H - 47}" rx="10" fill="url(#dots)"/>'
    b += S(x, 98, 18, [("$ ", t.be), ("whoami", t.muted)])
    b += T(x, 164, "Shravani Nikam", 60, t.fg, weight="600")
    b += S(
        x,
        210,
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
        244,
        "MS CS @ Northeastern University, Seattle · graduating Dec 2027",
        18,
        t.muted,
    )

    # availability, top right
    rx = W - x
    b += f'<circle class="pu" cx="{rx - cw(17) * 12 - 14}" cy="92" r="5.5" fill="{t.be}"/>'
    b += T(rx, 98, "open to work", 17, t.fg, anchor="end", weight="600")
    b += T(rx, 124, "co-op Spring/Summer 2027", 15, t.muted, anchor="end")
    b += T(rx, 146, "full-time from Jan 2028", 15, t.muted, anchor="end")

    b += f'<path d="M{x} 280H{W - x}" stroke="{t.line}" stroke-dasharray="4 6"/>'
    rows = [
        (
            "backend",
            t.be,
            "PostgreSQL · indexing & query plans · offline-first sync · REST APIs",
        ),
        (
            "ml / ai",
            t.ml,
            "NLP · BERT pipelines · LLM evaluation · open-source ML infra",
        ),
        (
            "data",
            t.da,
            "experiment design · benchmarking · BigQuery pipelines · pandas",
        ),
    ]
    for i, (label, col, text) in enumerate(rows):
        y = 326 + i * 36
        b += T(x, y, label, 18, col, weight="600") + T(x + 140, y, text, 18, t.fg)
    b += S(x, 432, 18, [("$ ", t.be)])
    b += f'<rect class="bk" x="{x + cw(18) * 2}" y="417" width="10" height="19" fill="{t.be}"/>'
    return svg(
        t,
        W,
        H,
        "Shravani Nikam: backend, machine learning, data science",
        "MS in Computer Science at Northeastern University, Seattle, graduating December 2027. "
        "Open to a co-op in Spring/Summer 2027 and full-time from January 2028. "
        "Backend: PostgreSQL, indexing and query plans, offline-first sync, REST APIs. "
        "ML/AI: NLP, BERT pipelines, LLM evaluation, open-source ML infrastructure. "
        "Data: experiment design, benchmarking, BigQuery pipelines, pandas.",
        b,
    )


def stats(t):
    W, H, gap = 1200, 168, 16
    pw = (W - 3 * gap) / 4
    cells = [
        (
            t.ml,
            "ml · ibm skillsbuild",
            "−30%",
            "avg response time, intent",
            "classification rebuild",
        ),
        (
            t.ml,
            "nlp · irjmets paper",
            "7k+",
            "reviews scored per aspect",
            "by a BERT pipeline",
        ),
        (
            t.be,
            "backend · query-plan-lab",
            "28.4%",
            "less query time: 10 MB",
            "partial vs 404 MB index",
        ),
        (t.da, "oss · ml infra", "2 PRs", "DeepSpeed (merged)", "PyTorch (open)"),
    ]
    b = ""
    for i, (col, head, big, l1, l2) in enumerate(cells):
        x = i * (pw + gap)
        b += f'<rect x="{x + 0.75}" y=".75" width="{pw - 1.5}" height="{H - 1.5}" rx="12" fill="{t.panel}" stroke="{t.line}" stroke-width="1.5"/>'
        b += f'<circle cx="{x + 26}" cy="33" r="4.5" fill="{col}"/>' + T(
            x + 40, 38, head, 14, t.muted
        )
        b += T(x + 22, 96, big, 46, t.fg, weight="600")
        b += T(x + 22, 128, l1, 15, t.muted) + T(x + 22, 150, l2, 15, t.muted)
    return svg(
        t,
        W,
        H,
        "Highlights",
        "30% lower average response time after rebuilding intent classification (AI/ML intern, IBM SkillsBuild). "
        "7k+ reviews scored per aspect by a BERT pipeline (IRJMETS paper). "
        "28.4% less query time from a 10 MB partial index versus a 404 MB covering index (query-plan-lab). "
        "Two open-source pull requests to ML infrastructure: DeepSpeed (merged) and PyTorch (open).",
        b,
    )


def card(t, slug, track, col, status, desc, stack, viz, alt):
    W, H, m = 820, 476, 8  # m: transparent margin so side-by-side cards don't touch
    b = window(t, W, H, f"~/{slug}", T(W - 26, 27, status, 15, t.muted, anchor="end"))
    tw = len(track) * cw(14) + 24
    b += f'<rect x="40" y="70" width="{tw}" height="28" rx="6" fill="none" stroke="{col}" stroke-width="1.5"/>'
    b += T(40 + tw / 2, 89, track, 14, col, anchor="middle", weight="600")
    b += T(40, 154, slug, 44, t.fg, weight="600")
    b += T(40, 196, desc[0], 20, t.fg) + T(40, 224, desc[1], 20, t.fg)
    b += viz
    b += T(40, 446, " · ".join(stack), 16, t.muted)
    return svg(
        t, W + 2 * m, H + 2 * m, slug, alt, f'<g transform="translate({m} {m})">{b}</g>'
    )


def cards(t):
    # hallucination-hunter: spot the fabrication
    hh = T(40, 272, "which answer contains a fabrication?", 17, t.muted)
    pre = "B  The Eiffel Tower opened in "
    for i, txt in enumerate(["A  The Eiffel Tower opened in 1889.", pre]):
        y = 288 + i * 48
        hh += f'<rect x="40" y="{y}" width="740" height="38" rx="6" fill="none" stroke="{t.ml if i else t.line}" stroke-width="1.5"/>'
        if i:
            hh += S(56, y + 25, 18, [(txt, t.fg), ("1901", t.ml), (".", t.fg)])
            hh += T(764, y + 25, "fabricated", 15, t.ml, anchor="end", weight="600")
        else:
            hh += S(56, y + 25, 18, [(txt, t.fg)])
    hh += T(
        40,
        404,
        "measures accuracy · confidence calibration · paired vs single",
        15,
        t.muted,
    )

    # mergelag: pipeline, solid = built, dashed = planned
    ml = ""
    stages = [
        ("GH Archive", "public events", True),
        ("BigQuery", "dry-run priced", True),
        ("features", "point-in-time", False),
        ("model", "merge time", False),
        ("digest", "weekly", False),
    ]
    bw, gap = 124, 30
    for i, (name, cap, built) in enumerate(stages):
        x = 40 + i * (bw + gap)
        dash = "" if built else ' stroke-dasharray="5 5"'
        ml += f'<rect x="{x}" y="270" width="{bw}" height="42" rx="6" fill="none" stroke="{t.da if built else t.line}" stroke-width="1.5"{dash}/>'
        ml += T(x + bw / 2, 297, name, 16, t.fg if built else t.muted, anchor="middle")
        ml += T(x + bw / 2, 334, cap, 13, t.muted, anchor="middle")
        if i:
            ml += f'<path d="M{x - gap + 6} 291H{x - 6}" stroke="{t.line}" stroke-width="1.5"/>'
    ml += T(
        40,
        380,
        "guards: no leakage · no unpriced query · no secrets in logs",
        15,
        t.muted,
    )

    # query-plan-lab: q1 bars
    bx, full = 250, 400
    qpl = T(40, 272, "q1 median, ms · lower is better", 15, t.muted)
    for i, (label, ms, c) in enumerate(
        [("partial · 10 MB", 71.95, t.be), ("covering · 404 MB", 100.53, t.line)]
    ):
        y = 292 + i * 38
        w = full * ms / 100.53
        qpl += T(40, y + 13, label, 17, t.fg)
        qpl += f'<rect x="{bx}" y="{y}" width="{w:.0f}" height="16" rx="3" fill="{c}"/>'
        qpl += T(bx + w + 12, y + 13, f"{ms}", 17, t.fg)
    qpl += T(40, 384, "GIN on the common JSONB probe: 22.5% slower", 15, t.muted)

    # rhea: two offline lanes converging
    rh = ""
    for name, y, dots, dash in [
        ("phone", 284, [(200, "hlc 41.0"), (420, "hlc 57.0")], ""),
        (
            "laptop",
            350,
            [(300, "hlc 52.1"), (490, "hlc 57.1")],
            ' stroke-dasharray="7 6"',
        ),
    ]:
        ly = y - 14 if name == "phone" else y + 26
        rh += T(40, y + 6, name, 17, t.muted)
        rh += f'<path d="M140 {y}H560C600 {y} 600 317 640 317" fill="none" stroke="{t.line}" stroke-width="2"{dash}/>'
        for x, lab in dots:
            rh += f'<circle cx="{x}" cy="{y}" r="6" fill="{t.be}"/>' + T(
                x, ly, lab, 13, t.muted, anchor="middle"
            )
    rh += T(395, 376, "offline", 13, t.muted, anchor="middle")
    rh += f'<path d="M640 317H760" stroke="{t.be}" stroke-width="2"/><circle cx="760" cy="317" r="8" fill="{t.be}"/>'
    rh += T(700, 303, "1 row", 14, t.be, anchor="middle")
    rh += T(
        780, 404, "hybrid logical clock + last-write-wins", 15, t.muted, anchor="end"
    )

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
            "can spot fabricated facts in AI answers; measures accuracy, confidence calibration, and paired versus "
            "single judgments.",
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
            ["python 3.12", "bigquery", "github actions", "uv"],
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
            ["postgres 16", "docker", "python", "matplotlib"],
            qpl,
            "query-plan-lab: eight PostgreSQL 16 index strategies on 10M rows. A 10 MB partial index ran q1 in "
            "71.95 ms versus 100.53 ms for a 404 MB covering index; GIN made the common JSONB probe 22.5% slower.",
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
        ),
    }


def log(t):
    W, x = 1200, 52
    rows = [
        (
            "2026",
            t.da,
            "Open source · ML infrastructure",
            "DeepSpeed #8567 merged: sub_group_size docs + default fix · PyTorch #198840 open",
        ),
        (
            "→ 2027",
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
            t.be,
            "Cloud Co-Lead · Google Developer Groups on Campus, Pune",
            "GCP workshops for 200+ students over three years; mentored 15 juniors",
        ),
    ]
    b, y = "", 92
    for when, col, role, sub in rows:
        b += T(x, y, when, 16, t.muted)
        b += f'<circle cx="{x + 132}" cy="{y - 6}" r="4.5" fill="{col}"/>'
        b += T(x + 152, y, role, 18, t.fg, weight="600")
        if sub:
            b += T(x + 152, y + 26, sub, 16, t.muted)
        y += 70 if sub else 48
    H = y - 14
    return svg(
        t,
        W,
        H,
        "Experience",
        "2026: open-source contributions to ML infrastructure — DeepSpeed pull request 8567 merged "
        "(sub_group_size documentation and default fix), PyTorch pull request 198840 open. "
        "Through December 2027: MS Computer Science, Northeastern University, Seattle. "
        "2025: research paper in IRJMETS Vol. 07 Issue 05, Unified Sentiment Analysis of Customer Reviews, "
        "aspect-level BERT over 7k+ reviews. 2025: BS AI and Data Science, Savitribai Phule Pune University. "
        "2024: AI/ML Intern, CSRBOX × IBM SkillsBuild; rebuilt intent classification, average response time "
        "down 30%. 2022–2025: Cloud Co-Lead, Google Developer Groups on Campus, Pune; GCP workshops for 200+ "
        "students, mentored 15 juniors.",
        window(t, W, H, "experience") + b,
    )


def stack(t):
    W, x = 1200, 52
    rows = [
        (
            "backend",
            t.be,
            [
                "Python",
                "PostgreSQL",
                "SQL",
                "Docker",
                "Node/Express",
                "REST",
                "Supabase",
            ],
        ),
        ("ml / ai", t.ml, ["PyTorch", "DeepSpeed", "Hugging Face", "BERT", "spaCy"]),
        ("data", t.da, ["Pandas", "NumPy", "BigQuery", "matplotlib"]),
        (
            "cloud",
            t.muted,
            ["AWS", "GCP", "Linux", "GitHub Actions", "TypeScript", "React"],
        ),
    ]
    b, y = "", 96
    for label, col, items in rows:
        b += T(x, y, label, 18, col, weight="600")
        cx = x + 140
        for item in items:
            w = len(item) * cw(16) + 24
            b += f'<rect x="{cx}" y="{y - 22}" width="{w:.0f}" height="32" rx="6" fill="none" stroke="{t.line}" stroke-width="1.5"/>'
            b += T(cx + 12, y, item, 16, t.fg)
            cx += w + 10
        y += 52
    H = y - 18
    return svg(
        t,
        W,
        H,
        "Tech stack",
        "; ".join(f"{label}: {', '.join(items)}" for label, _, items in rows),
        window(t, W, H, "stack") + b,
    )


def button(t, label):
    w, h = len(label) * cw(18) + 64, 48
    b = f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="10" fill="{t.panel}" stroke="{t.line}" stroke-width="1.5"/>'
    b += S(22, 30, 18, [(label, t.fg), ("  ↗", t.muted)])
    return svg(t, w, h, label, f"{label} button", b)


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
            "btn-linkedin": button(t, "LinkedIn"),
            "btn-email": button(t, "Email"),
        }
        files |= {f"card-{k}": v for k, v in cards(t).items()}
        for name, s in files.items():
            (OUT / f"{name}-{t.name}.svg").write_text(s)
    print(
        f"{len(list(OUT.glob('*.svg')))} files, {sum(f.stat().st_size for f in OUT.glob('*.svg')) // 1024} KB"
    )


if __name__ == "__main__":
    main()
