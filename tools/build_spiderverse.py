#!/usr/bin/env python3
"""Generate Spider-Verse themed GitHub profile SVG assets.

Uses verified repository metadata only. AstraSOC stays labelled PRIVATE.
Hero portrait is the real photo cutout (assets/portrait.png), not ASCII.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONTS = ROOT / "fonts" / "spider"

# Palette
RED = "#E62429"
NAVY = "#071426"
MID = "#102A50"
BLUE = "#168BFF"
WHITE = "#F5F7FA"
VIOLET = "#7047D7"
MUTED = "#9fb0c8"
LINE = "rgba(245,247,250,0.12)"


def b64_font(name: str) -> str:
    return base64.b64encode((FONTS / name).read_bytes()).decode("ascii")


def font_css() -> str:
    faces = [
        ("Bebas Neue", "normal", "400", "BebasNeue-Regular.woff"),
        ("Space Grotesk", "normal", "400", "SpaceGrotesk-Regular.woff"),
        ("Playfair Display", "italic", "800", "PlayfairDisplay-Italic.woff"),
        ("JetBrains Mono", "normal", "400", "JetBrainsMono-Regular.woff"),
    ]
    out = []
    for fam, style, weight, file in faces:
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64_font(file)}) format('woff')}}"
        )
    return "".join(out)


FONT_CSS = font_css()
# Cards stay light: GitHub camo cannot share one font file across SVGs, so only
# cinematic sections embed WOFF. Cards use close system fallbacks.
FONT_FALLBACK = (
    "text,tspan{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}"
    ".mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}"
    ".display{font-family:Impact,Haettenschweiler,Arial Narrow Bold,sans-serif}"
    ".serif{font-family:Georgia,'Times New Roman',serif;font-style:italic}"
)


def write(path: Path, svg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)
    print(f"wrote {path.relative_to(ROOT)} ({len(svg)} bytes)")


def web_paths(cx: float = 600, cy: float = 300, scale: float = 1.0) -> str:
    return f'''<g stroke="{WHITE}" stroke-width="{0.7 * scale}" fill="none" opacity="0.35">
  <path d="M{cx} {cy}L{cx-600} {cy-300}M{cx} {cy}L{cx-300} {cy-300}M{cx} {cy}L{cx} {cy-300}M{cx} {cy}L{cx+300} {cy-300}M{cx} {cy}L{cx+600} {cy-300}"/>
  <path d="M{cx} {cy}L{cx-600} {cy}M{cx} {cy}L{cx+600} {cy}M{cx} {cy}L{cx-600} {cy+300}M{cx} {cy}L{cx} {cy+300}M{cx} {cy}L{cx+600} {cy+300}"/>
  <circle cx="{cx}" cy="{cy}" r="{90 * scale}"/><circle cx="{cx}" cy="{cy}" r="{190 * scale}"/>
  <circle cx="{cx}" cy="{cy}" r="{300 * scale}"/>
</g>'''


def skyline(y: float = 380, width: float = 620) -> str:
    """NYC silhouette under the typography column only — never crosses the portrait."""
    return f'''<g fill="#0b1d3a" opacity="0.95">
  <path d="M0 {y+80}V{y}h30v-30h22v40h24V{y-50}h18v-20h12v20h16v50h26v-70h20v-18h10v18h20v70h28v-45h30v-38h18v83h26V{y-70}h22V{y-95}h8V{y-110}h4v15h8v25h22v70h30v-40h22v-30h26v70h22V{y-60}h18v50h30v-85h14v-16h6v16h14v85h26v-45h30v55h22v-70h30v-22h18v92h28v-40h22v{y+80-(y-40)}H0z"/>
</g>
<line x1="0" y1="{y+74}" x2="{width}" y2="{y+74}" stroke="{RED}" stroke-width="2"/>'''


def portrait_data_uri() -> tuple[str, int, int]:
    """Load the transparent photo cutout for embedding in hero.svg."""
    from PIL import Image

    path = ASSETS / "portrait.png"
    if not path.exists():
        raise SystemExit("assets/portrait.png missing — run Segment cutout first")
    with Image.open(path) as im:
        w, h = im.size
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}", w, h


def build_hero() -> None:
    """Hero with real photo cutout (no ASCII). Frame matches portrait aspect."""
    data_uri, src_w, src_h = portrait_data_uri()
    width, height = 1180, 600
    # Right column slot; frame aspect tracks the cutout so the photo fills it.
    slot_x, slot_y = 640, 36
    slot_w, slot_h = 500, 548
    aspect = src_w / src_h
    # Prefer full height; shrink width to portrait aspect and center in the slot.
    panel_h = slot_h
    panel_w = min(slot_w, panel_h * aspect)
    if panel_w / panel_h < aspect:
        panel_w = slot_w
        panel_h = panel_w / aspect
    panel_x = slot_x + (slot_w - panel_w) / 2
    panel_y = slot_y + (slot_h - panel_h) / 2
    # Near-flush fit inside the rim (2px breathing room).
    pad = 2
    avail_w, avail_h = panel_w - pad * 2, panel_h - pad * 2
    scale = min(avail_w / src_w, avail_h / src_h)
    img_w, img_h = src_w * scale, src_h * scale
    img_x = panel_x + (panel_w - img_w) / 2
    img_y = panel_y + (panel_h - img_h) / 2

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Harshith Subrahmanyam Kakumanu — Cybersecurity and AI/ML Engineer">
<title>Harshith Subrahmanyam Kakumanu — Spider-Verse profile hero</title>
<style>
{FONT_CSS}
</style>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0.85" y2="1">
    <stop offset="0" stop-color="#071426"/><stop offset=".55" stop-color="{NAVY}"/><stop offset="1" stop-color="{MID}"/>
  </linearGradient>
  <radialGradient id="glowB" cx="78%" cy="36%" r="52%"><stop offset="0" stop-color="{BLUE}" stop-opacity=".28"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
  <radialGradient id="glowR" cx="94%" cy="88%" r="48%"><stop offset="0" stop-color="{RED}" stop-opacity=".26"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>
  <radialGradient id="stage" cx="50%" cy="42%" r="62%">
    <stop offset="0" stop-color="#1a3a62" stop-opacity="1"/>
    <stop offset="1" stop-color="#0c1c34" stop-opacity="1"/>
  </radialGradient>
  <linearGradient id="sur" x1="0" y1="0" x2="1" y2="0">
    <stop offset=".08" stop-color="{RED}"/><stop offset=".48" stop-color="#ff7a7e"/><stop offset=".95" stop-color="{BLUE}"/>
  </linearGradient>
  <linearGradient id="panelEdge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#2a4a78"/><stop offset="1" stop-color="#142840"/>
  </linearGradient>
  <clipPath id="pslot"><rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="{panel_h}" rx="4"/></clipPath>
</defs>
<rect width="{width}" height="{height}" fill="url(#bg)"/>
<rect width="{width}" height="{height}" fill="url(#glowB)"/>
<rect width="{width}" height="{height}" fill="url(#glowR)"/>
<!-- web (no letterbox bars) -->
<g opacity="0.32" transform="translate(220 -20)">{web_paths(900, 200, 0.85)}</g>
{skyline(470, 620)}
<!-- particles -->
<circle cx="150" cy="160" r="2" fill="{WHITE}" opacity=".5"/>
<circle cx="500" cy="120" r="1.5" fill="{WHITE}" opacity=".4"/>
<circle cx="860" cy="400" r="2.5" fill="{BLUE}" opacity=".5"/>
<!-- integrated nav / branding -->
<text x="40" y="34" font-family="'Bebas Neue', Impact, sans-serif" font-size="24" letter-spacing="2" fill="{WHITE}">H<tspan fill="{RED}">/</tspan>SK</text>
<text x="742" y="32" font-family="'JetBrains Mono', monospace" font-size="11" letter-spacing="2.4" fill="{MUTED}">ORIGIN</text>
<text x="848" y="32" font-family="'JetBrains Mono', monospace" font-size="11" letter-spacing="2.4" fill="{MUTED}">POWERS</text>
<text x="956" y="32" font-family="'JetBrains Mono', monospace" font-size="11" letter-spacing="2.4" fill="{MUTED}">MULTIVERSE</text>
<text x="1090" y="32" font-family="'JetBrains Mono', monospace" font-size="11" letter-spacing="2.4" fill="{MUTED}">ACTIVITY</text>
<line x1="40" y1="44" x2="1140" y2="44" stroke="{WHITE}" stroke-opacity="0.08"/>
<!-- left copy — tighter rhythm -->
<text x="40" y="74" font-family="'JetBrains Mono', monospace" font-size="11" letter-spacing="2.8" fill="{MUTED}"><tspan fill="{RED}">●</tspan> TITLE SEQUENCE · SCENE 01</text>
<line x1="40" y1="92" x2="84" y2="92" stroke="{RED}" stroke-width="2"/>
<text x="96" y="96" font-family="'JetBrains Mono', monospace" font-size="12" letter-spacing="2.8" fill="{BLUE}">CYBERSECURITY &amp; AI/ML ENGINEER</text>
<!-- Glitch name via offset duplicates (SVG text-shadow is unreliable on GitHub) -->
<text x="43" y="182" font-family="'Bebas Neue', Impact, sans-serif" font-size="78" letter-spacing="1" fill="{RED}" opacity="0.55">HARSHITH</text>
<text x="37" y="182" font-family="'Bebas Neue', Impact, sans-serif" font-size="78" letter-spacing="1" fill="{BLUE}" opacity="0.55">HARSHITH</text>
<text x="40" y="182" font-family="'Bebas Neue', Impact, sans-serif" font-size="78" letter-spacing="1" fill="{WHITE}">HARSHITH</text>
<text x="43" y="258" font-family="'Bebas Neue', Impact, sans-serif" font-size="78" letter-spacing="1" fill="{RED}" opacity="0.45">SUBRAHMANYAM</text>
<text x="37" y="258" font-family="'Bebas Neue', Impact, sans-serif" font-size="78" letter-spacing="1" fill="{BLUE}" opacity="0.45">SUBRAHMANYAM</text>
<text x="40" y="258" font-family="'Bebas Neue', Impact, sans-serif" font-size="78" letter-spacing="1" fill="{WHITE}">SUBRAHMANYAM</text>
<text x="40" y="332" font-family="'Playfair Display', Georgia, serif" font-style="italic" font-weight="800" font-size="56" fill="url(#sur)">Kakumanu</text>
<text x="40" y="380" font-family="'Space Grotesk', system-ui, sans-serif" font-size="15" fill="#dce6f4">Building at the intersection of cryptography,</text>
<text x="40" y="402" font-family="'Space Grotesk', system-ui, sans-serif" font-size="15" fill="#dce6f4">AI/ML and full-stack security engineering.</text>
<polygon points="40,434 158,434 150,466 32,466" fill="{RED}"/>
<text x="54" y="456" font-family="'JetBrains Mono', monospace" font-size="12" letter-spacing="1.5" fill="{WHITE}">GITHUB →</text>
<!-- portrait frame — real photo cutout, transparent background -->
<rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="{panel_h}" rx="4" fill="url(#panelEdge)"/>
<g clip-path="url(#pslot)">
  <rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="{panel_h}" fill="url(#stage)"/>
  <image href="{data_uri}" xlink:href="{data_uri}" x="{img_x:.1f}" y="{img_y:.1f}" width="{img_w:.1f}" height="{img_h:.1f}" preserveAspectRatio="xMidYMid meet"/>
  <rect x="{panel_x}" y="{panel_y}" width="14" height="{panel_h}" fill="{BLUE}" opacity="0.12"/>
  <rect x="{panel_x + panel_w - 14}" y="{panel_y}" width="14" height="{panel_h}" fill="{RED}" opacity="0.10"/>
</g>
<!-- rim accents (blue left / red right) -->
<rect x="{panel_x}" y="{panel_y}" width="5" height="{panel_h}" fill="{BLUE}" opacity="0.95"/>
<rect x="{panel_x + panel_w - 5}" y="{panel_y}" width="5" height="{panel_h}" fill="{RED}" opacity="0.95"/>
<rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="3" fill="{BLUE}" opacity="0.55"/>
<rect x="{panel_x}" y="{panel_y + panel_h - 3}" width="{panel_w}" height="3" fill="{RED}" opacity="0.45"/>
</svg>'''
    write(ASSETS / "hero.svg", svg)


def section_banner(path: Path, tag: str, title: str, accent: str = RED, width: int = 1180, height: int = 120) -> None:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>{FONT_FALLBACK}</style>
<rect width="{width}" height="{height}" fill="{NAVY}"/>
<text class="mono" x="40" y="42" font-size="12" letter-spacing="3" fill="{BLUE}">{escape(tag)}</text>
<text class="display" x="40" y="96" font-size="52" fill="{WHITE}">{escape(title)}</text>
<rect x="40" y="{height - 8}" width="64" height="3" fill="{accent}"/>
</svg>'''
    write(path, svg)


def build_origin() -> None:
    # Verified: GCET affiliation via public college-related repos; project span from public READMEs.
    # Specific CTF/TryHackMe/cert ranks from the design reference are included as the author-supplied
    # profile facts in the uploaded reference; education years likewise. No invented extras.
    width, height = 1180, 420
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Origin Story">
<title>Origin Story</title>
<style>{FONT_CSS}</style>
<defs>
  <pattern id="ht" width="9" height="9" patternUnits="userSpaceOnUse">
    <circle cx="1.2" cy="1.2" r="1.1" fill="{WHITE}" opacity="0.06"/>
  </pattern>
</defs>
<rect width="{width}" height="{height}" fill="{NAVY}"/>
<rect width="{width}" height="{height}" fill="url(#ht)"/>
<text x="48" y="48" font-family="'JetBrains Mono', monospace" font-size="12" letter-spacing="3" fill="{BLUE}"><tspan fill="{RED}" font-weight="700">01</tspan> / CHAPTER ONE</text>
<text x="48" y="120" font-family="'Bebas Neue', Impact, sans-serif" font-size="64" fill="{WHITE}">ORIGIN</text>
<text x="250" y="120" font-family="'Playfair Display', Georgia, serif" font-style="italic" font-weight="800" font-size="52" fill="{RED}">Story</text>
<text x="48" y="180" font-family="'Space Grotesk', system-ui, sans-serif" font-size="16" fill="#cdd8e8">Computer Science and Engineering student specializing in Cyber Security</text>
<text x="48" y="206" font-family="'Space Grotesk', system-ui, sans-serif" font-size="16" fill="#cdd8e8">at Geethanjali College of Engineering and Technology. Coursework includes</text>
<text x="48" y="232" font-family="'Space Grotesk', system-ui, sans-serif" font-size="16" fill="#cdd8e8">cryptography. Outside class I build with blockchain/Web3 tooling and compete in CTFs.</text>
<text x="48" y="272" font-family="'Space Grotesk', system-ui, sans-serif" font-size="16" fill="#cdd8e8">Projects span post-quantum cryptography tooling, privacy-preserving voting,</text>
<text x="48" y="298" font-family="'Space Grotesk', system-ui, sans-serif" font-size="16" fill="#cdd8e8">network traffic analysis, AI analytics platforms and full-stack systems.</text>
<!-- fact strip — from author design reference -->
<line x1="48" y1="330" x2="51" y2="380" stroke="{BLUE}" stroke-width="3"/>
<text x="64" y="348" font-family="'JetBrains Mono', monospace" font-size="10" letter-spacing="2" fill="{RED}">EDUCATION</text>
<text x="64" y="370" font-family="'Space Grotesk', system-ui, sans-serif" font-size="14" fill="#cdd8e8">B.Tech CSE (Cyber Security) · GCET</text>
<line x1="420" y1="330" x2="423" y2="380" stroke="{BLUE}" stroke-width="3"/>
<text x="436" y="348" font-family="'JetBrains Mono', monospace" font-size="10" letter-spacing="2" fill="{RED}">FOCUS</text>
<text x="436" y="370" font-family="'Space Grotesk', system-ui, sans-serif" font-size="14" fill="#cdd8e8">Cryptography · AI/ML · Security engineering</text>
<line x1="820" y1="330" x2="823" y2="380" stroke="{BLUE}" stroke-width="3"/>
<text x="836" y="348" font-family="'JetBrains Mono', monospace" font-size="10" letter-spacing="2" fill="{RED}">BUILD</text>
<text x="836" y="370" font-family="'Space Grotesk', system-ui, sans-serif" font-size="14" fill="#cdd8e8">FastAPI · React · Python · TypeScript</text>
</svg>'''
    write(ASSETS / "origin.svg", svg)


def power_card(filename: str, num: str, title: str, blurb: str, evidence: str, color: str, icon: str) -> None:
    w, h = 360, 260
    ev1, ev2 = (evidence.split("\n") + [""])[:2]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>{FONT_FALLBACK}</style>
<defs><clipPath id="c"><polygon points="0,0 334,0 360,26 360,260 0,260"/></clipPath></defs>
<rect width="{w}" height="{h}" fill="{NAVY}"/>
<g clip-path="url(#c)">
  <rect width="{w}" height="{h}" fill="{MID}" fill-opacity="0.55"/>
  <rect width="{w}" height="3" fill="{color}"/>
  <text class="mono" x="24" y="36" font-size="11" letter-spacing="2" fill="{color}">{escape(num)}</text>
  <g transform="translate(24 48)" stroke="{color}" fill="none" stroke-width="2.4">{icon}</g>
  <text class="display" x="24" y="130" font-size="34" fill="{WHITE}">{escape(title)}</text>
  <text x="24" y="160" font-size="13" fill="{MUTED}">{escape(blurb)}</text>
  <line x1="24" y1="180" x2="336" y2="180" stroke="{WHITE}" stroke-opacity="0.12" stroke-dasharray="4 6"/>
  <text class="mono" x="24" y="208" font-size="11" fill="#cdd8e8">{escape(ev1)}</text>
  <text class="mono" x="24" y="228" font-size="11" fill="#cdd8e8">{escape(ev2)}</text>
</g>
</svg>'''
    write(ASSETS / "powers" / filename, svg)


def build_powers() -> None:
    # Evidence tied to verified repos / stacks only (no invented %).
    power_card(
        "cybersecurity.svg", "PWR—01", "Cybersecurity",
        "Offensive and defensive security practice.",
        "AstraSOC · NetScope traffic analysis\nCTF tooling · GCET CTF resources",
        RED,
        '<path d="M24 4l16 6v12c0 11-7 18-16 22C15 40 8 33 8 22V10z"/><path d="M17 24l5 5 9-10"/>',
    )
    power_card(
        "artificial-intelligence.svg", "PWR—02", "Artificial Intelligence",
        "Applied AI platforms and product surfaces.",
        "StatPlay AI studio · Retensa churn platform\nCryptoNex optional AI explanation layer",
        BLUE,
        '<circle cx="24" cy="24" r="6"/><path d="M24 4v10M24 34v10M4 24h10M34 24h10M10 10l7 7M31 31l7 7M38 10l-7 7M17 31l-7 7"/>',
    )
    power_card(
        "machine-learning.svg", "PWR—03", "Machine Learning",
        "Experimentation and analytics pipelines.",
        "StatPlay · DuckDB + scikit-learn studio\nRetensa retention modelling",
        VIOLET,
        '<circle cx="10" cy="12" r="4"/><circle cx="10" cy="36" r="4"/><circle cx="38" cy="24" r="4"/><circle cx="24" cy="24" r="4"/><path d="M14 12l6 10M14 36l6-10M28 24h6"/>',
    )
    power_card(
        "full-stack.svg", "PWR—04", "Full-Stack Dev",
        "Frontends, APIs and deployment.",
        "CryptoNex · React + FastAPI\nRTGS · TypeScript + Supabase",
        BLUE,
        '<path d="M16 14L6 24l10 10M32 14l10 10-10 10M28 8L20 40"/>',
    )
    power_card(
        "cryptography.svg", "PWR—05", "Cryptography",
        "Applied crypto and crypto-agility tooling.",
        "CryptoNex · post-quantum migration\nCRP-PBL · CryptoVote classroom voting",
        RED,
        '<rect x="9" y="21" width="30" height="21" rx="3"/><path d="M15 21v-6a9 9 0 0118 0v6"/><circle cx="24" cy="31" r="3"/>',
    )
    power_card(
        "network-security.svg", "PWR—06", "Network Security",
        "Traffic analysis and recon tooling.",
        "NetScope · Scapy + PySide6 sniffer\nAlert rules · PCAP export/replay",
        VIOLET,
        '<circle cx="24" cy="8" r="4"/><circle cx="8" cy="38" r="4"/><circle cx="40" cy="38" r="4"/><path d="M24 12L10 34M24 12l14 22M12 38h24"/>',
    )


def project_card(filename: str, universe: str, name: str, blurb: str, chips: list[str],
                 gradient_defs: str, art: str, fill_id: str, private: bool = False) -> None:
    w, h = 560, 320
    priv = ""
    if private:
        priv = f'''<g>
  <rect x="430" y="22" width="104" height="28" fill="{NAVY}" stroke="{BLUE}"/>
  <text class="mono" x="482" y="41" text-anchor="middle" font-size="11" letter-spacing="2" fill="{BLUE}">PRIVATE</text>
</g>'''
    words = blurb.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if len(trial) > 52:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    lines = lines[:4]
    blurb_svg = "".join(
        f'<text x="26" y="{118 + i * 20}" font-size="14" fill="rgba(245,247,250,0.92)">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    chip_svg = []
    x = 26
    for c in chips[:6]:
        cw = 12 + len(c) * 7.2
        chip_svg.append(
            f'<rect x="{x}" y="250" width="{cw:.0f}" height="22" fill="rgba(7,20,38,0.55)" stroke="rgba(245,247,250,0.35)"/>'
            f'<text class="mono" x="{x + 8}" y="265" font-size="11" fill="{WHITE}">{escape(c)}</text>'
        )
        x += cw + 6
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(name)}{' (private)' if private else ''}">
<title>{escape(name)}</title>
<style>{FONT_FALLBACK}</style>
<defs>{gradient_defs}</defs>
<rect width="{w}" height="{h}" fill="url(#{fill_id})"/>
{art}
{priv}
<text class="mono" x="26" y="40" font-size="11" letter-spacing="2.4" fill="{WHITE}" fill-opacity="0.85">{escape(universe)}</text>
<text class="display" x="26" y="92" font-size="48" fill="{WHITE}">{escape(name)}</text>
{blurb_svg}
{''.join(chip_svg)}
</svg>'''
    write(ASSETS / "projects" / filename, svg)


def build_projects() -> None:
    project_card(
        "project-cryptonex.svg",
        "UNIVERSE · QUANTUM-SAFE",
        "CryptoNex",
        "Post-quantum cryptography migration and crypto-agility platform with multi-phase static analysis, CBOM, CI policy and migration planning.",
        ["Python", "FastAPI", "SQLAlchemy", "React", "TypeScript"],
        f'<linearGradient id="g1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4a0b10"/><stop offset="1" stop-color="{RED}"/></linearGradient>',
        f'''<g fill="none" stroke="{WHITE}" stroke-opacity=".16" stroke-width="1.2">
          <path d="M430 40l40 23v46l-40 23-40-23V63z"/><path d="M500 90l40 23v46l-40 23-40-23v-46z"/>
        </g>
        <text x="300" y="300" font-family="'JetBrains Mono', monospace" font-size="12" fill="{WHITE}" fill-opacity=".25">RSA → ML-KEM · ECDSA → ML-DSA</text>''',
        "g1",
    )
    project_card(
        "project-astrasoc.svg",
        "UNIVERSE · SOC-ORBIT",
        "AstraSOC",
        "AI-powered SOC platform with threat intelligence and incident-response automation. Dockerized FastAPI/TypeScript split.",
        ["TypeScript", "Python", "Docker", "FastAPI"],
        f'<radialGradient id="g2" cx="80%" cy="20%" r="75%"><stop offset="0" stop-color="#0f3a78"/><stop offset="1" stop-color="#050d1a"/></radialGradient>',
        f'''<g fill="none" stroke="{BLUE}" stroke-opacity=".4">
          <circle cx="450" cy="150" r="40"/><circle cx="450" cy="150" r="80"/><circle cx="450" cy="150" r="120"/>
          <path d="M450 150L540 70" stroke-opacity=".9" stroke-width="2"/>
        </g>
        <circle cx="510" cy="96" r="4" fill="{RED}"/>''',
        "g2",
        private=True,
    )
    project_card(
        "project-statplay.svg",
        "UNIVERSE · DATA-VERSE",
        "StatPlay",
        "Multi-sport performance analytics — dataset discovery, DuckDB exploration and ML experiment studio.",
        ["Python", "TypeScript", "DuckDB", "FastAPI"],
        f'<linearGradient id="g3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1c0f45"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>',
        f'''<g stroke="{WHITE}" stroke-opacity=".18" fill="none">
          <path d="M40 280V80M40 280h340"/><path d="M40 220h340M40 160h340" stroke-dasharray="3 6"/>
          <path d="M60 240Q130 120 190 190T330 80" stroke-opacity=".45" stroke-width="2"/>
        </g>''',
        "g3",
    )
    project_card(
        "project-netscope.svg",
        "UNIVERSE · PACKET-WEB",
        "NetScope",
        "Desktop network packet sniffer and traffic analyzer with live capture, alerts and PCAP export.",
        ["Python", "PySide6", "Scapy"],
        f'<linearGradient id="g4" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#04182e"/><stop offset="1" stop-color="{BLUE}"/></linearGradient>',
        f'''<g stroke="{WHITE}" stroke-opacity=".35" fill="none">
          <path d="M300 70L400 130L360 230L460 280M400 130L470 60"/>
        </g>
        <g fill="{WHITE}" fill-opacity=".7">
          <circle cx="300" cy="70" r="5"/><circle cx="400" cy="130" r="7"/><circle cx="360" cy="230" r="5"/><circle cx="470" cy="60" r="4"/>
        </g>''',
        "g4",
    )
    project_card(
        "project-rtgs.svg",
        "UNIVERSE · LIVE-LEDGER",
        "RTGS",
        "Citizen grievance portal — DecodeX final project with FastAPI backend and Supabase-backed React UI.",
        ["TypeScript", "FastAPI", "Supabase", "PLpgSQL"],
        f'<linearGradient id="g5" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0c1a36"/><stop offset=".55" stop-color="#2a1250"/><stop offset="1" stop-color="{RED}"/></linearGradient>',
        f'''<g stroke="{WHITE}" stroke-opacity=".22" stroke-width="1.5">
          <path d="M240 70h190M240 120h190M240 170h190M240 220h190"/>
        </g>
        <g fill="{RED}" fill-opacity=".75">
          <rect x="250" y="64" width="40" height="12"/><rect x="330" y="114" width="60" height="12"/>
          <rect x="280" y="164" width="30" height="12"/><rect x="360" y="214" width="50" height="12"/>
        </g>''',
        "g5",
    )


def build_technology() -> None:
    # Only stacks evidenced across showcased / related public repos.
    cats = [
        ("Languages", ["Python", "TypeScript", "JavaScript", "SQL", "PLpgSQL"]),
        ("Frameworks & Backend", ["React", "FastAPI", "SQLAlchemy", "Vite", "pytest"]),
        ("Data & AI/ML", ["DuckDB", "scikit-learn", "Plotly", "arq"]),
        ("Security & Networking", ["Scapy", "PySide6", "Docker"]),
        ("Web3", ["ethers.js", "Solidity"]),
        ("Dev & Deploy", ["Git", "Docker Compose", "Supabase"]),
    ]
    # campus-reputation evidences ethers.js; CRP/CryptoVote are python; Solidity from campus if present - ethers.js is in campus-reputation description. Solidity - reference had it; campus-reputation is React dApp with ethers.js - Solidity may be used. I'll only include ethers.js for Web3 unless we verify Solidity files.
    cats[4] = ("Web3", ["ethers.js"])  # verified via campus-reputation description

    width, height = 1180, 420
    boxes = []
    positions = [(40, 100), (410, 100), (780, 100), (40, 255), (410, 255), (780, 255)]
    for (title, pills), (bx, by) in zip(cats, positions):
        pill_parts = []
        px, py = bx + 16, by + 48
        for p in pills:
            pw = 14 + len(p) * 7.4
            if px + pw > bx + 340:
                px = bx + 16
                py += 32
            pill_parts.append(
                f'<rect x="{px}" y="{py}" width="{pw:.0f}" height="26" fill="rgba(245,247,250,0.05)" stroke="rgba(245,247,250,0.12)"/>'
                f'<text x="{px + 8}" y="{py + 17}" font-family="\'JetBrains Mono\', monospace" font-size="12" fill="{WHITE}">{escape(p)}</text>'
            )
            px += pw + 8
        boxes.append(f'''<g>
  <rect x="{bx}" y="{by}" width="340" height="140" fill="rgba(16,42,80,0.28)" stroke="rgba(245,247,250,0.12)"/>
  <rect x="{bx}" y="{by}" width="36" height="3" fill="{RED}"/>
  <text x="{bx + 16}" y="{by + 32}" font-family="'Bebas Neue', Impact, sans-serif" font-size="22" fill="{BLUE}">{escape(title)}</text>
  {''.join(pill_parts)}
</g>''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Technology Arsenal">
<title>Technology Arsenal</title>
<style>{FONT_FALLBACK}</style>
<rect width="{width}" height="{height}" fill="{NAVY}"/>
<text x="40" y="36" font-family="'JetBrains Mono', monospace" font-size="12" letter-spacing="3" fill="{BLUE}"><tspan fill="{RED}" font-weight="700">04</tspan> / GEAR</text>
<text x="40" y="78" font-family="'Bebas Neue', Impact, sans-serif" font-size="40" fill="{WHITE}">TECHNOLOGY ARSENAL</text>
{''.join(boxes)}
</svg>'''
    write(ASSETS / "technology.svg", svg)


def build_github_stats(public_repos: int, followers: int, stars: int) -> None:
    width, height = 1180, 220
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub overview">
<title>GitHub overview</title>
<style>{FONT_CSS}</style>
<rect width="{width}" height="{height}" fill="{NAVY}"/>
<text x="40" y="40" font-family="'JetBrains Mono', monospace" font-size="12" letter-spacing="3" fill="{BLUE}"><tspan fill="{RED}" font-weight="700">05</tspan> / TELEMETRY</text>
<text x="40" y="78" font-family="'Bebas Neue', Impact, sans-serif" font-size="40" fill="{WHITE}">GITHUB ACTIVITY</text>
<!-- verified counters only -->
<g>
  <rect x="40" y="110" width="260" height="90" fill="rgba(16,42,80,0.55)" stroke="{LINE}"/>
  <text x="60" y="160" font-family="'Bebas Neue', Impact, sans-serif" font-size="44" fill="{WHITE}">{public_repos}</text>
  <text x="60" y="184" font-family="'JetBrains Mono', monospace" font-size="11" letter-spacing="2" fill="{MUTED}">PUBLIC REPOS</text>
</g>
<g>
  <rect x="320" y="110" width="260" height="90" fill="rgba(16,42,80,0.55)" stroke="{LINE}"/>
  <text x="340" y="160" font-family="'Bebas Neue', Impact, sans-serif" font-size="44" fill="{WHITE}">{followers}</text>
  <text x="340" y="184" font-family="'JetBrains Mono', monospace" font-size="11" letter-spacing="2" fill="{MUTED}">FOLLOWERS</text>
</g>
<g>
  <rect x="600" y="110" width="260" height="90" fill="rgba(16,42,80,0.55)" stroke="{LINE}"/>
  <text x="620" y="160" font-family="'Bebas Neue', Impact, sans-serif" font-size="44" fill="{WHITE}">{stars}</text>
  <text x="620" y="184" font-family="'JetBrains Mono', monospace" font-size="11" letter-spacing="2" fill="{MUTED}">STARS (OWNED)</text>
</g>
<g>
  <rect x="880" y="110" width="260" height="90" fill="rgba(16,42,80,0.55)" stroke="{LINE}"/>
  <text x="900" y="150" font-family="'Space Grotesk', system-ui, sans-serif" font-size="14" fill="#cdd8e8">Live cards below</text>
  <text x="900" y="172" font-family="'Space Grotesk', system-ui, sans-serif" font-size="14" fill="#cdd8e8">refresh from GitHub.</text>
  <text x="900" y="192" font-family="'JetBrains Mono', monospace" font-size="10" fill="{MUTED}">NO SAMPLE FIGURES</text>
</g>
</svg>'''
    write(ASSETS / "github-stats.svg", svg)


def build_github_activity() -> None:
    """Language mix from showcased public repos only — verified byte totals."""
    langs = [
        ("Python", 738923 + 321137 + 251362 + 169774, RED),
        ("TypeScript", 21340 + 294203 + 214345, BLUE),
        ("JavaScript", 8259 + 150848, VIOLET),
        ("PLpgSQL", 14547, MUTED),
        ("CSS/HTML", 2111 + 361 + 11541 + 1723 + 788, WHITE),
    ]
    # Note: these are showcased-project languages, not whole-account. Label clearly.
    total = sum(v for _, v, _ in langs) or 1
    width, height = 1180, 200
    bars = []
    x = 40
    max_w = 1100
    for name, val, color in langs:
        w = max(8, max_w * val / total)
        bars.append(f'<rect x="{x:.1f}" y="110" width="{w:.1f}" height="18" fill="{color}" opacity="0.85"/>')
        bars.append(
            f'<text x="{x + 4:.1f}" y="150" font-family="\'JetBrains Mono\', monospace" font-size="11" fill="{MUTED}">{escape(name)}</text>'
        )
        x += w
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Showcased project language mix">
<title>Showcased project language mix</title>
<style>{FONT_FALLBACK}</style>
<rect width="{width}" height="{height}" fill="{NAVY}"/>
<text x="40" y="40" font-family="'Bebas Neue', Impact, sans-serif" font-size="28" fill="{WHITE}">SHOWCASED LANGUAGE MIX</text>
<text x="40" y="68" font-family="'JetBrains Mono', monospace" font-size="11" fill="{MUTED}">BYTE SHARE ACROSS CRYPTONEX · STATPLAY · NETSCOPE · RTGS (PUBLIC)</text>
{''.join(bars)}
<text x="40" y="180" font-family="'Space Grotesk', system-ui, sans-serif" font-size="13" fill="#cdd8e8">Contribution graphs and streaks load from live GitHub services when available.</text>
</svg>'''
    write(ASSETS / "github-activity.svg", svg)


def build_nav() -> None:
    width, height = 1180, 56
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Profile navigation">
<title>H/SK navigation</title>
<style>{FONT_FALLBACK}</style>
<rect width="{width}" height="{height}" fill="{NAVY}"/>
<text class="display" x="40" y="36" font-size="26" letter-spacing="2" fill="{WHITE}">H<tspan fill="{RED}">/</tspan>SK</text>
<text class="mono" x="700" y="34" font-size="11" letter-spacing="2.5" fill="{MUTED}">ORIGIN</text>
<text class="mono" x="820" y="34" font-size="11" letter-spacing="2.5" fill="{MUTED}">POWERS</text>
<text class="mono" x="940" y="34" font-size="11" letter-spacing="2.5" fill="{MUTED}">MULTIVERSE</text>
<text class="mono" x="1080" y="34" font-size="11" letter-spacing="2.5" fill="{MUTED}">ACTIVITY</text>
</svg>'''
    write(ASSETS / "nav.svg", svg)


def build_footer() -> None:
    width, height = 1180, 320
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Every system is a web. I read the threads.">
<title>Closing — Every system is a web</title>
<style>{FONT_CSS}</style>
<defs>
  <radialGradient id="fr" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="{RED}" stop-opacity=".25"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>
  <radialGradient id="fb" cx="50%" cy="100%" r="55%"><stop offset="0" stop-color="{BLUE}" stop-opacity=".28"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
</defs>
<rect width="{width}" height="{height}" fill="{NAVY}"/>
<rect width="{width}" height="{height}" fill="url(#fr)"/>
<rect width="{width}" height="{height}" fill="url(#fb)"/>
{web_paths(590, 160, 0.7)}
<text x="590" y="60" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="12" letter-spacing="3" fill="{BLUE}"><tspan fill="{RED}" font-weight="700">06</tspan> / END CREDITS</text>
<text x="590" y="140" text-anchor="middle" font-family="'Bebas Neue', Impact, sans-serif" font-size="52" fill="{WHITE}">EVERY SYSTEM IS A WEB.</text>
<text x="590" y="200" text-anchor="middle" font-family="'Playfair Display', Georgia, serif" font-style="italic" font-weight="800" font-size="42" fill="{RED}">I read the threads.</text>
<polygon points="470,240 590,240 582,274 462,274" fill="{RED}"/>
<text x="480" y="264" font-family="'JetBrains Mono', monospace" font-size="12" letter-spacing="1.5" fill="{WHITE}">GITHUB →</text>
<polygon points="610,240 760,240 752,274 602,274" fill="{BLUE}"/>
<text x="622" y="264" font-family="'JetBrains Mono', monospace" font-size="12" letter-spacing="1.5" fill="{WHITE}">BACK TO TOP ↑</text>
</svg>'''
    write(ASSETS / "footer.svg", svg)


def build_powers_banner() -> None:
    section_banner(ASSETS / "powers-banner.svg", "02 / ABILITIES", "MY SUPERPOWERS", BLUE)


def build_projects_banner() -> None:
    section_banner(ASSETS / "projects-banner.svg", "03 / FIVE UNIVERSES", "PROJECT MULTIVERSE", RED)


def main() -> None:
    build_nav()
    build_hero()
    build_origin()
    build_powers_banner()
    build_powers()
    build_projects_banner()
    build_projects()
    build_technology()
    build_github_stats(public_repos=22, followers=2, stars=2)
    build_github_activity()
    build_footer()


if __name__ == "__main__":
    main()
