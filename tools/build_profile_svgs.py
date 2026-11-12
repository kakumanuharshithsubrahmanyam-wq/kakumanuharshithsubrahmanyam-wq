#!/usr/bin/env python3
"""Generate the light-themed GitHub profile SVG assets.

Fonts are inlined as base64 WOFF so GitHub's camo proxy can still render them.
Project card copy is limited to verified repository descriptions and language bytes.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONTS = ROOT / "fonts"

# Soft blue → indigo → pastel violet
BLUE = "#3b6ef6"
INDIGO = "#5b5bd6"
VIOLET = "#8b7fd4"
INK = "#111827"
MUTED = "#6b7280"
SOFT = "#9ca3af"
CARD = "#f7f7f5"
LINE = "#e8e8e4"
WHITE = "#ffffff"


def font_face(family: str, style: str, weight: str, filename: str) -> str:
    data = base64.b64encode((FONTS / filename).read_bytes()).decode("ascii")
    return (
        f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};"
        f"src:url(data:font/woff;base64,{data}) format('woff')}}"
    )


FONT_CSS = "".join([
    font_face("Instrument Serif", "normal", "400", "Instrument_Serif_normal_400.woff"),
    font_face("Instrument Serif", "italic", "400", "Instrument_Serif_italic_400.woff"),
    font_face("Geist", "normal", "400", "Geist_normal_400.woff"),
    font_face("Geist Mono", "normal", "400", "Geist_Mono_normal_400.woff"),
])


def write(path: Path, svg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)
    print(f"wrote {path.relative_to(ROOT)} ({len(svg)} bytes)")


def lang_bar(langs: dict[str, int], x: float, y: float, width: float, height: float = 6) -> str:
    total = sum(langs.values()) or 1
    palette = [BLUE, INDIGO, VIOLET, "#94a3b8", "#cbd5e1"]
    parts = []
    cursor = x
    for i, (name, bytes_) in enumerate(langs.items()):
        w = width * bytes_ / total
        if w < 0.5:
            continue
        parts.append(
            f'<rect x="{cursor:.2f}" y="{y}" width="{w:.2f}" height="{height}" '
            f'rx="2" fill="{palette[i % len(palette)]}"/>'
        )
        cursor += w
    return "\n".join(parts)


def extract_portrait_glyphs(portrait_svg: str):
    """Parse glyph rows with their original coordinates from ascii-portrait.svg."""
    view = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', portrait_svg)
    if not view:
        raise SystemExit("ascii-portrait.svg is missing a viewBox")
    src_w, src_h = float(view.group(1)), float(view.group(2))
    font = re.search(r'font-size="([0-9.]+)"', portrait_svg)
    src_font = float(font.group(1)) if font else 7.2
    rows = []
    for m in re.finditer(
        r'style="animation-delay:([0-9.]+)s"[^>]*x="([^"]+)" y="([^"]+)" '
        r'textLength="([^"]+)"[^>]*>(.*?)</text>',
        portrait_svg,
        flags=re.S,
    ):
        rows.append({
            "delay": float(m.group(1)),
            "x": float(m.group(2)),
            "y": float(m.group(3)),
            "text_length": float(m.group(4)),
            "line": m.group(5),
        })
    return src_w, src_h, src_font, rows


def build_hero() -> None:
    portrait = (ASSETS / "ascii-portrait.svg").read_text()
    src_w, src_h, src_font, rows = extract_portrait_glyphs(portrait)
    # Fit the full bust into the right half, preserving row spacing so arms remain.
    width = 1180
    height = 500
    pad_x = 548
    pad_y = 18
    pad_right = 22
    pad_bottom = 18
    avail_w = width - pad_x - pad_right
    avail_h = height - pad_y - pad_bottom
    scale = min(avail_w / src_w, avail_h / src_h)
    font_size = src_font * scale
    # Center the scaled portrait inside the right panel.
    offset_x = pad_x + (avail_w - src_w * scale) / 2
    offset_y = pad_y + (avail_h - src_h * scale) / 2

    text_rows = []
    for i, row in enumerate(rows):
        x = offset_x + row["x"] * scale
        y = offset_y + row["y"] * scale
        text_length = row["text_length"] * scale
        d = 0.35 + i * 0.008
        text_rows.append(
            f'<text class="pr" style="animation-delay:{d:.3f}s" xml:space="preserve" '
            f'x="{x:.2f}" y="{y:.2f}" textLength="{text_length:.2f}" '
            f'lengthAdjust="spacing">{row["line"]}</text>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Harshith Subrahmanyam Kakumanu. Cybersecurity and AI/ML engineer.">
<title>Harshith Subrahmanyam Kakumanu — Cybersecurity &amp; AI/ML Engineer</title>
<style>
{FONT_CSS}
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.28}}}}
@keyframes nudgeup{{0%,100%{{transform:none}}50%{{transform:translate(3px,-3px)}}}}
.r{{opacity:0;animation:rise .75s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}}
.f{{opacity:0;animation:fade .85s ease-out both}}
.pr{{opacity:0;animation:fade .55s ease-out both}}
.live{{animation:pulse 1.6s ease-in-out infinite}}
.nu{{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}}
@media (prefers-reduced-motion: reduce){{.r,.f,.pr,.live,.nu{{animation:none!important;opacity:1!important;transform:none!important}}}}
</style>
<defs>
  <linearGradient id="nameShine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="520" y2="0">
    <stop offset="0" stop-color="{INK}"/>
    <stop offset=".42" stop-color="{INK}"/>
    <stop offset=".5" stop-color="{BLUE}"/>
    <stop offset=".58" stop-color="{VIOLET}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-520 0;520 0;520 0" keyTimes="0;.45;1" dur="7s" begin="1.4s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="portraitGrad" gradientUnits="userSpaceOnUse" x1="{offset_x:.1f}" y1="{offset_y:.1f}" x2="{offset_x + src_w * scale:.1f}" y2="{offset_y + src_h * scale:.1f}">
    <stop offset="0" stop-color="#1d4ed8"/>
    <stop offset=".55" stop-color="#4f46e5"/>
    <stop offset="1" stop-color="#7c3aed"/>
  </linearGradient>
</defs>
<rect width="{width}" height="{height}" rx="18" fill="{CARD}"/>
<g class="f" style="animation-delay:0.00s">
  <rect class="live" x="48" y="56" width="8" height="8" rx="2" fill="{BLUE}"/>
  <text x="66" y="63" font-family="'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" letter-spacing="1.4" fill="{MUTED}">CYBERSECURITY &amp; AI/ML ENGINEER</text>
</g>
<text class="r" style="animation-delay:0.12s" x="44" y="178" font-family="'Instrument Serif', Georgia, serif" font-size="70" letter-spacing="-1.8" fill="{INK}">Harshith</text>
<text class="r" style="animation-delay:0.24s" x="44" y="252" font-family="'Instrument Serif', Georgia, serif" font-size="70" letter-spacing="-1.8" fill="{INK}">Subrahmanyam</text>
<text class="r" style="animation-delay:0.36s" x="44" y="326" font-family="'Instrument Serif', Georgia, serif" font-style="italic" font-size="70" letter-spacing="-1.8" fill="url(#nameShine)">Kakumanu</text>
<g class="r" style="animation-delay:0.52s">
  <text x="48" y="386" font-family="Geist, system-ui, -apple-system, sans-serif" font-size="16" fill="#3a3a3c">I build post-quantum crypto tools, AI platforms,</text>
  <text x="48" y="410" font-family="Geist, system-ui, -apple-system, sans-serif" font-size="16" fill="#3a3a3c">and security systems.</text>
</g>
<g class="f" style="animation-delay:0.72s">
  <text x="48" y="458" font-family="'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" fill="{INK}">github.com/kakumanuharshithsubrahmanyam-wq</text>
  <text class="nu" x="392" y="458" font-family="'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" fill="{BLUE}">&#8599;</text>
</g>
<g fill="url(#portraitGrad)" font-size="{font_size:.3f}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
{chr(10).join(text_rows)}
</g>
</svg>
'''
    write(ASSETS / "hero.svg", svg)


def card_shell(width: int, height: int, title: str) -> tuple[str, str]:
    head = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
{FONT_CSS}
@keyframes rise{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
@keyframes draw{{from{{stroke-dashoffset:120}}to{{stroke-dashoffset:0}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
.c{{opacity:0;animation:rise .7s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}}
.f{{opacity:0;animation:fade .8s ease-out both}}
.d{{fill:none;stroke-dasharray:120;stroke-dashoffset:120;animation:draw 1.1s ease-out both}}
@media (prefers-reduced-motion: reduce){{.c,.f,.d{{animation:none!important;opacity:1!important;stroke-dashoffset:0!important;transform:none!important}}}}
</style>'''
    return head, "</svg>"


def build_focus() -> None:
    head, tail = card_shell(1100, 220, "Focus areas")
    svg = head + f'''
<rect width="1100" height="220" rx="18" fill="{CARD}"/>
<g class="c" style="animation-delay:0.05s">
  <rect x="28" y="28" width="332" height="164" rx="16" fill="{WHITE}" stroke="{LINE}"/>
  <path class="d" style="animation-delay:0.2s" d="M78 92 h40 a18 18 0 0 1 0 36 h-20" stroke="{BLUE}" stroke-width="3" stroke-linecap="round"/>
  <circle class="f" style="animation-delay:0.45s" cx="128" cy="110" r="5" fill="{VIOLET}"/>
  <text x="68" y="160" font-family="'Instrument Serif', Georgia, serif" font-size="28" fill="{INK}">Security</text>
  <text x="68" y="186" font-family="Geist, system-ui, sans-serif" font-size="13" fill="{MUTED}">Crypto, SOC tooling, packet analysis</text>
</g>
<g class="c" style="animation-delay:0.18s">
  <rect x="384" y="28" width="332" height="164" rx="16" fill="{WHITE}" stroke="{LINE}"/>
  <g class="f" style="animation-delay:0.35s" stroke="{INDIGO}" stroke-width="2.5" fill="none">
    <circle cx="448" cy="100" r="7"/><circle cx="486" cy="78" r="7"/><circle cx="486" cy="122" r="7"/>
    <path d="M455 100 L479 82 M455 100 L479 118 M486 85 L486 115"/>
  </g>
  <text x="424" y="160" font-family="'Instrument Serif', Georgia, serif" font-size="28" fill="{INK}">AI / ML</text>
  <text x="424" y="186" font-family="Geist, system-ui, sans-serif" font-size="13" fill="{MUTED}">Analytics studios, retention models</text>
</g>
<g class="c" style="animation-delay:0.31s">
  <rect x="740" y="28" width="332" height="164" rx="16" fill="{WHITE}" stroke="{LINE}"/>
  <g class="f" style="animation-delay:0.5s">
    <rect x="784" y="118" width="54" height="10" rx="2" fill="{BLUE}" opacity=".35"/>
    <rect x="792" y="100" width="54" height="10" rx="2" fill="{INDIGO}" opacity=".55"/>
    <rect x="800" y="82" width="54" height="10" rx="2" fill="{VIOLET}"/>
  </g>
  <text x="780" y="160" font-family="'Instrument Serif', Georgia, serif" font-size="28" fill="{INK}">Full-stack</text>
  <text x="780" y="186" font-family="Geist, system-ui, sans-serif" font-size="13" fill="{MUTED}">FastAPI, React, Postgres systems</text>
</g>
''' + tail
    write(ASSETS / "focus-cards.svg", svg)


def build_project(filename: str, name: str, blurb: str, stack: str,
                  langs: dict[str, int], accent: str, delay: float = 0.1,
                  badge: str | None = None) -> None:
    head, tail = card_shell(540, 210, name)
    bar = lang_bar(langs, 36, 168, 468, 7)
    badge_svg = ""
    if badge:
        badge_svg = f'''
<g class="f" style="animation-delay:{delay + 0.2:.2f}s">
  <rect x="430" y="36" width="72" height="22" rx="6" fill="#eef2ff" stroke="{LINE}"/>
  <text x="466" y="51" text-anchor="middle" font-family="'Geist Mono', ui-monospace, Menlo, monospace" font-size="10" letter-spacing="1" fill="{INDIGO}">{escape(badge)}</text>
</g>'''
    svg = head + f'''
<rect width="540" height="210" rx="18" fill="{CARD}"/>
<rect class="c" style="animation-delay:{delay:.2f}s" x="16" y="16" width="508" height="178" rx="14" fill="{WHITE}" stroke="{LINE}"/>
<circle class="f" style="animation-delay:{delay + 0.15:.2f}s" cx="48" cy="48" r="6" fill="{accent}"/>
<text class="c" style="animation-delay:{delay + 0.08:.2f}s" x="66" y="54" font-family="'Geist Mono', ui-monospace, Menlo, monospace" font-size="12" letter-spacing="1" fill="{MUTED}">{escape(stack.upper())}</text>
{badge_svg}
<text class="c" style="animation-delay:{delay + 0.16:.2f}s" x="36" y="96" font-family="'Instrument Serif', Georgia, serif" font-size="30" fill="{INK}">{escape(name)}</text>
<text class="c" style="animation-delay:{delay + 0.24:.2f}s" x="36" y="128" font-family="Geist, system-ui, sans-serif" font-size="14" fill="#3a3a3c">{escape(blurb)}</text>
<g class="f" style="animation-delay:{delay + 0.35:.2f}s">
{bar}
</g>
''' + tail
    write(ASSETS / filename, svg)


def build_stats_fallback(public_repos: int, followers: int) -> None:
    """Local always-available metrics card. Values must come from the live API."""
    head, tail = card_shell(1100, 150, "GitHub overview")
    svg = head + f'''
<rect width="1100" height="150" rx="18" fill="{CARD}"/>
<text class="f" x="48" y="42" font-family="'Geist Mono', ui-monospace, Menlo, monospace" font-size="12" letter-spacing="1.5" fill="{MUTED}">GITHUB OVERVIEW</text>
<g class="c" style="animation-delay:0.08s">
  <text x="48" y="96" font-family="'Instrument Serif', Georgia, serif" font-size="44" fill="{INK}">{public_repos}</text>
  <text x="48" y="122" font-family="Geist, system-ui, sans-serif" font-size="14" fill="{MUTED}">Public repositories</text>
</g>
<g class="c" style="animation-delay:0.18s">
  <text x="320" y="96" font-family="'Instrument Serif', Georgia, serif" font-size="44" fill="{INK}">{followers}</text>
  <text x="320" y="122" font-family="Geist, system-ui, sans-serif" font-size="14" fill="{MUTED}">Followers</text>
</g>
<g class="c" style="animation-delay:0.28s">
  <text x="520" y="88" font-family="Geist, system-ui, sans-serif" font-size="15" fill="#3a3a3c">Live badges below refresh from GitHub.</text>
  <text x="520" y="112" font-family="Geist, system-ui, sans-serif" font-size="14" fill="{MUTED}">Detailed stats cards load when the third-party service is available.</text>
</g>
''' + tail
    write(ASSETS / "stats-fallback.svg", svg)


def build_stack() -> None:
    # Only stacks evidenced across the showcased repository READMEs.
    items = [
        ("Python", BLUE),
        ("TypeScript", INDIGO),
        ("FastAPI", VIOLET),
        ("React", BLUE),
        ("Postgres", INDIGO),
        ("Docker", VIOLET),
        ("DuckDB", BLUE),
        ("Scapy", INDIGO),
    ]
    head, tail = card_shell(1100, 140, "Technology stack")
    chips = []
    x = 40
    for i, (label, color) in enumerate(items):
        w = 18 + len(label) * 8.2
        chips.append(f'''<g class="c" style="animation-delay:{0.05 + i * 0.06:.2f}s">
  <rect x="{x}" y="54" width="{w:.1f}" height="36" rx="10" fill="{WHITE}" stroke="{LINE}"/>
  <circle cx="{x + 16}" cy="72" r="4" fill="{color}"/>
  <text x="{x + 28}" y="77" font-family="'Geist Mono', ui-monospace, Menlo, monospace" font-size="13" fill="{INK}">{escape(label)}</text>
</g>''')
        x += w + 14
    svg = head + f'''
<rect width="1100" height="140" rx="18" fill="{CARD}"/>
<text class="f" x="40" y="38" font-family="'Geist Mono', ui-monospace, Menlo, monospace" font-size="12" letter-spacing="1.5" fill="{MUTED}">STACK IN ACTIVE PROJECTS</text>
{chr(10).join(chips)}
''' + tail
    write(ASSETS / "stack.svg", svg)


def build_footer() -> None:
    head, tail = card_shell(1100, 120, "Connect")
    svg = head + f'''
<rect width="1100" height="120" rx="18" fill="{CARD}"/>
<text class="c" style="animation-delay:0.05s" x="48" y="52" font-family="'Instrument Serif', Georgia, serif" font-size="28" fill="{INK}">Let's build carefully.</text>
<text class="c" style="animation-delay:0.18s" x="48" y="84" font-family="Geist, system-ui, sans-serif" font-size="15" fill="{MUTED}">Open to cybersecurity, cryptography, and applied AI/ML collaboration.</text>
<text class="f" style="animation-delay:0.3s" x="820" y="68" font-family="'Geist Mono', ui-monospace, Menlo, monospace" font-size="13" fill="{BLUE}">GitHub &#8599;</text>
''' + tail
    write(ASSETS / "footer.svg", svg)


def main() -> None:
    build_hero()
    build_focus()
    # Live public profile counters for the offline-capable stats card.
    # Keep these in sync with `gh api users/<login>` before committing.
    build_stats_fallback(public_repos=22, followers=2)
    # Verified blurbs from repository descriptions / README one-liners only.
    build_project(
        "project-cryptonex.svg",
        "CryptoNex",
        "Post-quantum cryptography migration and crypto-agility platform.",
        "Python · FastAPI · React",
        {"Python": 738923, "TypeScript": 21340, "CSS": 2111, "HTML": 361},
        BLUE,
        0.05,
    )
    build_project(
        "project-astrasoc.svg",
        "AstraSOC",
        "AI-powered SOC platform with threat intelligence and IR automation.",
        "TypeScript · Python · Docker",
        {"TypeScript": 26516, "Python": 10812, "Dockerfile": 2363, "CSS": 1213},
        INDIGO,
        0.08,
        badge="PRIVATE",
    )
    build_project(
        "project-statplay.svg",
        "StatPlay AI",
        "Multi-sport performance analytics — discovery, DuckDB, ML studio.",
        "Python · TypeScript · DuckDB",
        {"Python": 321137, "TypeScript": 294203, "CSS": 11541, "JavaScript": 8259},
        VIOLET,
        0.11,
    )
    build_project(
        "project-netscope.svg",
        "NetScope",
        "Desktop network packet sniffer and traffic analyzer.",
        "Python · PySide6 · Scapy",
        {"Python": 251362},
        BLUE,
        0.14,
    )
    build_project(
        "project-rtgs.svg",
        "RTGS",
        "Citizen grievance portal — DecodeX final project.",
        "TypeScript · FastAPI · Supabase",
        {"TypeScript": 214345, "Python": 169774, "PLpgSQL": 14547, "Shell": 5264},
        INDIGO,
        0.17,
    )
    build_stack()
    build_footer()


if __name__ == "__main__":
    main()
