import base64
import datetime as dt
import html
import io
import json
import os
from pathlib import Path

STATIC = os.getenv("STATIC", "0") == "1"
DATA_PATH = Path("data/contributions.json")
OUT_DIR = Path("cards")

# Duo Palette: Paper & Ink + Electric Cobalt
BG = "#F8F8F6"
SURFACE = "#FFFFFF"
BORDER = "#DFDFD8"
INK = "#121316"
MUTED = "#5C606E"
COBALT = "#1D4ED8"
COBALT_LIGHT = "#DBEAFE"
GRID_COLORS = ["#EAEAE4", "#93C5FD", "#3B82F6", "#1D4ED8", "#1E3A8A"]

ASCII_PORTRAIT = [
    "        .::----::.        ",
    "      .-==========-.      ",
    "     :==============:     ",
    "    :================:    ",
    "    :==--::::::::--==:    ",
    "    :=:  ..    ..  :=:    ",
    "    :=: [##]  [##] :=:    ",
    "    :=:  ..    ..  :=:    ",
    "    :=:     ::     :=:    ",
    "    :==:   -==-   :==:    ",
    "     :==:  '--'  :==:     ",
    "      :===------===:      ",
    "       ':========:'       ",
    "     ..--::::::::--..     ",
    "   .:================:.   ",
    "  :====================:  ",
    " :====:  <DEEPESH/> :===: ",
    " :====:  ---------- :===: ",
    " :====:   WEB·DEV   :===: ",
    " :======================: ",
    " :======================: ",
    "  '===================='  ",
]


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def build_font_css() -> str:
    font_specs = [
        ("DuoDisplay", Path("fonts/SpaceGrotesk-Bold.ttf"), "700"),
        ("DuoSans", Path("fonts/Inter-Regular.ttf"), "400"),
        ("DuoMono", Path("fonts/JetBrainsMono-Regular.ttf"), "400"),
    ]
    rules = []
    try:
        from fontTools import subset  # type: ignore

        unicodes = subset.parse_unicodes("U+0020-007E,U+00B7,U+2022,U+2192,U+2197,U+2605")
        for family, ttf_path, weight in font_specs:
            if not ttf_path.exists():
                continue
            options = subset.Options(flavor="woff", layout_features=["kern", "liga"])
            font = subset.load_font(str(ttf_path), options)
            subsetter = subset.Subsetter(options=options)
            subsetter.populate(unicodes=unicodes)
            subsetter.subset(font)
            buf = io.BytesIO()
            font.save(buf)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            rules.append(
                f"@font-face{{font-family:'{family}';font-weight:{weight};"
                f"src:url(data:font/woff;base64,{b64}) format('woff');}}"
            )
    except Exception:
        pass
    return "\n".join(rules)


FONT_CSS = build_font_css()
FONT_DISPLAY = "'DuoDisplay', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
FONT_SANS = "'DuoSans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
FONT_MONO = "'DuoMono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"


def shared_css(extra: str = "") -> str:
    motion_guard = """
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation: none !important;
        transition: none !important;
        opacity: 1 !important;
        transform: none !important;
      }
    }
    """
    if STATIC:
        static_override = """
        .anim, .bar, .cell, .row-line, .tile-wrap, .proj-wrap, .banner-wrap, .l1, .l2, .l3, .l4 {
          opacity: 1 !important;
          transform: none !important;
          animation: none !important;
        }
        """
        return f"<style>{FONT_CSS}\n{extra}\n{static_override}</style>"
    return f"<style>{FONT_CSS}\n{extra}\n{motion_guard}</style>"


def smil_countup(
    target: int,
    x: float,
    y: float,
    font_size: int,
    fill: str,
    delay: float,
    duration: float = 0.85,
    anchor: str = "start",
) -> str:
    if STATIC or target <= 0:
        return (
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" '
            f'font-family="{FONT_DISPLAY}" font-size="{font_size}" font-weight="700">{target:,}</text>'
        )

    steps = 18
    step_dur = duration / steps
    elems = []
    for i in range(steps):
        val = int(round((target * i) / steps))
        begin = delay + i * step_dur
        elems.append(
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" opacity="0" '
            f'font-family="{FONT_DISPLAY}" font-size="{font_size}" font-weight="700">{val:,}'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s" dur="{step_dur:.3f}s" fill="remove" />'
            f"</text>"
        )
    end_begin = delay + duration
    elems.append(
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" opacity="0" '
        f'font-family="{FONT_DISPLAY}" font-size="{font_size}" font-weight="700">{target:,}'
        f'<set attributeName="opacity" to="1" begin="{end_begin:.2f}s" fill="freeze" />'
        f"</text>"
    )
    return "\n".join(elems)


def render_hero(data: dict) -> str:
    w, h = 840, 250
    css = """
    @keyframes riseIn {
      from { opacity: 0; transform: translateY(14px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes typeRow {
      from { opacity: 0; }
      to   { opacity: 1; }
    }
    @keyframes pulseDot {
      0%, 100% { opacity: 1; transform: scale(1); }
      50%      { opacity: 0.35; transform: scale(1.45); }
    }
    .l1 { opacity: 0; animation: riseIn 0.55s cubic-bezier(.2,.8,.2,1) 0.05s forwards; }
    .l2 { opacity: 0; animation: riseIn 0.55s cubic-bezier(.2,.8,.2,1) 0.18s forwards; }
    .l3 { opacity: 0; animation: riseIn 0.55s cubic-bezier(.2,.8,.2,1) 0.30s forwards; }
    .l4 { opacity: 0; animation: riseIn 0.55s cubic-bezier(.2,.8,.2,1) 0.42s forwards; }
    .dot-pulse {
      transform-box: fill-box;
      transform-origin: center;
      animation: pulseDot 2.2s ease-in-out infinite;
    }
    """

    shine_anim = ""
    if not STATIC:
        shine_anim = (
            '<animateTransform attributeName="gradientTransform" type="translate" '
            'from="-1 0" to="2 0" dur="3.6s" repeatCount="indefinite" />'
        )

    portrait_rows = []
    for idx, line in enumerate(ASCII_PORTRAIT):
        delay = 0.08 + idx * 0.022
        row_style = "" if STATIC else f'style="opacity:0;animation:typeRow 0.12s linear {delay:.3f}s forwards;"'
        color = COBALT if ("DEEPESH" in line or "WEB" in line) else INK
        portrait_rows.append(
            f'<text x="615" y="{31 + idx * 8.6:.1f}" fill="{color}" font-family="{FONT_MONO}" '
            f'font-size="8.5" xml:space="preserve" class="row-line" {row_style}>{esc(line)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <defs>
    <linearGradient id="nameShine" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{INK}" />
      <stop offset="42%" stop-color="{INK}" />
      <stop offset="50%" stop-color="{COBALT}" />
      <stop offset="58%" stop-color="{INK}" />
      <stop offset="100%" stop-color="{INK}" />
      {shine_anim}
    </linearGradient>
  </defs>
  {shared_css(css)}
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="{BG}" stroke="{BORDER}" />

  <!-- Top kicker -->
  <g class="l1">
    <circle cx="38" cy="40" r="4.5" fill="{COBALT}" class="dot-pulse" />
    <text x="52" y="44" fill="{MUTED}" font-family="{FONT_MONO}" font-size="11.5" letter-spacing="1.2">
      PORTFOLIO — VOL. 01 · WEB DEVELOPER · INDIA · 2026
    </text>
  </g>

  <!-- Name with SMIL cobalt shine -->
  <g class="l2">
    <text x="34" y="106" fill="url(#nameShine)" font-family="{FONT_DISPLAY}" font-size="52" font-weight="700" letter-spacing="-1.2">
      Deepesh
    </text>
  </g>

  <!-- One-line bio -->
  <g class="l3">
    <text x="36" y="146" fill="{INK}" font-family="{FONT_SANS}" font-size="18.5" font-weight="500">
      I design and develop online stores and web apps that look sharp &amp; grow sales.
    </text>
  </g>

  <!-- Duo tag pills -->
  <g class="l4">
    <rect x="36" y="176" width="132" height="32" rx="8" fill="{COBALT}" />
    <text x="102" y="196" text-anchor="middle" fill="#FFFFFF" font-family="{FONT_MONO}" font-size="11" font-weight="700">
      PORTFOLIO ↗
    </text>

    <rect x="176" y="176" width="184" height="32" rx="8" fill="{SURFACE}" stroke="{BORDER}" />
    <text x="268" y="196" text-anchor="middle" fill="{INK}" font-family="{FONT_MONO}" font-size="11" font-weight="500">
      E-COMMERCE &amp; WEB APPS
    </text>

    <rect x="368" y="176" width="168" height="32" rx="8" fill="{COBALT_LIGHT}" stroke="{COBALT}" stroke-opacity="0.3" />
    <text x="452" y="196" text-anchor="middle" fill="{COBALT}" font-family="{FONT_MONO}" font-size="11" font-weight="600">
      AVAILABLE FOR WORK
    </text>
  </g>

  <!-- Right ASCII terminal frame -->
  <rect x="596" y="18" width="224" height="214" rx="10" fill="{SURFACE}" stroke="{BORDER}" />
  {''.join(portrait_rows)}
</svg>"""


def render_graph(data: dict) -> str:
    w, h = 840, 178
    days = data["days"][-371:]
    if days:
        first_wd = (dt.date.fromisoformat(days[0]["date"]).weekday() + 1) % 7
        padded = [{"date": "", "count": 0, "level": 0}] * first_wd + days
    else:
        padded = []

    weeks = [padded[i : i + 7] for i in range(0, len(padded), 7)][:53]
    cell = 11.5
    gap = 3.2
    start_x = 34
    start_y = 48

    css = """
    @keyframes popCell {
      0%   { opacity: 0; transform: scale(0.35); }
      75%  { opacity: 1; transform: scale(1.12); }
      100% { opacity: 1; transform: scale(1); }
    }
    .cell {
      transform-box: fill-box;
      transform-origin: center;
    }
    """

    rects = []
    for c_idx, week in enumerate(weeks):
        col_delay = 0.55 + c_idx * 0.015
        for r_idx, day in enumerate(week):
            x = start_x + c_idx * (cell + gap)
            y = start_y + r_idx * (cell + gap)
            fill = GRID_COLORS[min(4, max(0, day["level"]))]
            style = "" if STATIC else f'style="opacity:0;animation:popCell 0.35s ease-out {col_delay:.3f}s forwards;"'
            rects.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2.6" '
                f'fill="{fill}" class="cell" {style} />'
            )

    legend = []
    for lvl, color in enumerate(GRID_COLORS):
        lx = w - 118 + lvl * 15
        legend.append(f'<rect x="{lx}" y="21" width="11" height="11" rx="2.5" fill="{color}" />')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  {shared_css(css)}
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="{BG}" stroke="{BORDER}" />
  <text x="34" y="31" fill="{INK}" font-family="{FONT_MONO}" font-size="11.5" font-weight="600" letter-spacing="0.8">
    CONTRIBUTION GRAPH · LAST 52 WEEKS
  </text>
  <text x="{w - 154}" y="30" fill="{MUTED}" font-family="{FONT_MONO}" font-size="10">LESS</text>
  {''.join(legend)}
  <text x="{w - 40}" y="30" fill="{MUTED}" font-family="{FONT_MONO}" font-size="10">MORE</text>
  {''.join(rects)}
</svg>"""


def render_activity(data: dict) -> str:
    w, h = 840, 210
    months = data["months"]
    max_val = max((m["count"] for m in months), default=1) or 1
    best_idx = max(range(len(months)), key=lambda i: months[i]["count"]) if months else 0

    css = """
    @keyframes growBar {
      from { opacity: 0; transform: scaleY(0); }
      to   { opacity: 1; transform: scaleY(1); }
    }
    @keyframes popBadge {
      from { opacity: 0; transform: translateY(5px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .bar {
      transform-box: fill-box;
      transform-origin: bottom;
    }
    """

    bars = []
    chart_base_y = 166
    max_bar_h = 96
    bar_w = 28
    bar_gap = 14
    left_x = 36

    for idx, m in enumerate(months):
        bh = max(6.0, (m["count"] / max_val) * max_bar_h)
        bx = left_x + idx * (bar_w + bar_gap)
        by = chart_base_y - bh
        is_best = idx == best_idx and m["count"] > 0
        fill = COBALT if is_best else INK
        delay = 1.15 + idx * 0.045
        style = "" if STATIC else f'style="opacity:0;animation:growBar 0.55s cubic-bezier(.2,.8,.2,1) {delay:.2f}s forwards;"'
        bars.append(
            f'<rect x="{bx}" y="{by:.1f}" width="{bar_w}" height="{bh:.1f}" rx="5" fill="{fill}" class="bar" {style} />'
        )
        bars.append(
            f'<text x="{bx + bar_w/2:.1f}" y="185" text-anchor="middle" fill="{COBALT if is_best else MUTED}" '
            f'font-family="{FONT_MONO}" font-size="10" font-weight="{700 if is_best else 400}">{esc(m["label"])}</text>'
        )
        if is_best:
            badge_delay = delay + 0.35
            b_style = "" if STATIC else f'style="opacity:0;animation:popBadge 0.3s ease-out {badge_delay:.2f}s forwards;"'
            bars.append(
                f'<text x="{bx + bar_w/2:.1f}" y="{by - 7:.1f}" text-anchor="middle" fill="{COBALT}" '
                f'font-family="{FONT_MONO}" font-size="10.5" font-weight="700" {b_style}>{m["count"]}</text>'
            )

    busiest = data["busiest_day"]
    busiest_label = f"{busiest['count']} on {busiest['date'][5:]}" if busiest.get("date") else "—"

    stats = [
        ("TOTAL CONTRIBUTIONS", f"{data['total']:,}", COBALT),
        ("CURRENT STREAK", f"{data['current_streak']}d", INK),
        ("ACTIVE DAYS", f"{data['active_days']}d", INK),
        ("BUSIEST DAY", busiest_label, INK),
    ]
    stat_boxes = []
    for idx, (label, val, color) in enumerate(stats):
        col = idx % 2
        row = idx // 2
        sx = 562 + col * 128
        sy = 46 + row * 74
        stat_boxes.append(
            f'<rect x="{sx}" y="{sy}" width="118" height="62" rx="10" fill="{SURFACE}" stroke="{BORDER}" />'
            f'<text x="{sx + 12}" y="{sy + 21}" fill="{MUTED}" font-family="{FONT_MONO}" font-size="9">{label}</text>'
            f'<text x="{sx + 12}" y="{sy + 46}" fill="{color}" font-family="{FONT_DISPLAY}" font-size="20" font-weight="700">{esc(val)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  {shared_css(css)}
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="{BG}" stroke="{BORDER}" />
  <text x="36" y="30" fill="{INK}" font-family="{FONT_MONO}" font-size="11.5" font-weight="600" letter-spacing="0.8">
    MONTHLY CADENCE · PEAK IN COBALT
  </text>
  <line x1="36" y1="{chart_base_y}" x2="534" y2="{chart_base_y}" stroke="{BORDER}" stroke-width="1" />
  {''.join(bars)}
  {''.join(stat_boxes)}
</svg>"""


def render_tile(
    kicker: str,
    title: str,
    subtitle: str,
    metric: int,
    suffix: str,
    accent_bg: bool,
    delay: float,
) -> str:
    w, h = 272, 174
    card_fill = COBALT if accent_bg else BG
    stroke_fill = COBALT if accent_bg else BORDER
    text_main = "#FFFFFF" if accent_bg else INK
    text_sub = "#DBEAFE" if accent_bg else MUTED
    ring_color = "#FFFFFF" if accent_bg else COBALT

    css = f"""
    @keyframes tileSwing {{
      0%   {{ opacity: 0; transform: translateY(22px) rotate(-1.6deg); }}
      70%  {{ opacity: 1; transform: translateY(-3px) rotate(0.4deg); }}
      100% {{ opacity: 1; transform: translateY(0) rotate(0deg); }}
    }}
    @keyframes ringPulse {{
      0%   {{ opacity: 0.45; transform: scale(0.7); }}
      100% {{ opacity: 0; transform: scale(2.1); }}
    }}
    @keyframes arrowNudge {{
      0%, 100% {{ transform: translate(0, 0); }}
      50%      {{ transform: translate(3px, -3px); }}
    }}
    .tile-wrap {{
      transform-box: fill-box;
      transform-origin: center bottom;
      opacity: 0;
      animation: tileSwing 0.65s cubic-bezier(.2,.85,.25,1) {delay:.2f}s forwards;
    }}
    .ring {{
      transform-box: fill-box;
      transform-origin: center;
      animation: ringPulse 2.8s ease-out {delay + 0.5:.2f}s infinite;
    }}
    .arrow {{
      transform-box: fill-box;
      transform-origin: center;
      animation: arrowNudge 2.2s ease-in-out {delay + 0.8:.2f}s infinite;
    }}
    """

    sheen = ""
    if not STATIC:
        sheen = (
            '<animateTransform attributeName="gradientTransform" type="translate" '
            f'from="-1 0" to="2 0" begin="{delay + 1.0:.1f}s" dur="4.2s" repeatCount="indefinite" />'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <defs>
    <linearGradient id="tileSheen" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0" />
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="{0.16 if accent_bg else 0.55}" />
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
      {sheen}
    </linearGradient>
  </defs>
  {shared_css(css)}
  <g class="tile-wrap">
    <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="{card_fill}" stroke="{stroke_fill}" />
    <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="url(#tileSheen)" />

    <circle cx="{w - 28}" cy="28" r="10" fill="none" stroke="{ring_color}" stroke-width="1.5" class="ring" />
    <text x="{w - 28}" y="33" text-anchor="middle" fill="{text_main}" font-family="{FONT_MONO}" font-size="14" class="arrow">↗</text>

    <text x="20" y="31" fill="{text_sub}" font-family="{FONT_MONO}" font-size="10.5" font-weight="600" letter-spacing="1">
      {esc(kicker)}
    </text>

    {smil_countup(metric, x=20, y=88, font_size=40, fill=text_main, delay=delay + 0.15)}
    <text x="20" y="112" fill="{text_sub}" font-family="{FONT_MONO}" font-size="11">
      {esc(suffix)}
    </text>

    <text x="20" y="142" fill="{text_main}" font-family="{FONT_DISPLAY}" font-size="16" font-weight="700">
      {esc(title)}
    </text>
    <text x="20" y="159" fill="{text_sub}" font-family="{FONT_SANS}" font-size="11.5">
      {esc(subtitle)}
    </text>
  </g>
</svg>"""


def render_project_card(
    number: str,
    name: str,
    tagline: str,
    description: str,
    domain: str,
    status_label: str,
    stack: list[str],
    is_live: bool,
    delay: float,
) -> str:
    w, h = 412, 180
    pulse_color = "#10B981" if is_live else "#F59E0B"
    badge_bg = "#DCFCE7" if is_live else "#FEF3C7"
    badge_text = "#15803D" if is_live else "#B45309"
    badge_border = "#86EFAC" if is_live else "#FCD34D"

    css = f"""
    @keyframes cardRise {{
      from {{ opacity: 0; transform: translateY(16px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes pulseLive {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50%      {{ opacity: 0.35; transform: scale(1.4); }}
    }}
    .proj-wrap {{
      opacity: 0;
      animation: cardRise 0.55s cubic-bezier(.2,.8,.2,1) {delay:.2f}s forwards;
    }}
    .live-dot {{
      transform-box: fill-box;
      transform-origin: center;
      animation: pulseLive 2s ease-in-out infinite;
    }}
    """

    pills = []
    px = 22
    for item in stack:
        pw = len(item) * 6.8 + 16
        pills.append(
            f'<rect x="{px}" y="136" width="{pw:.1f}" height="24" rx="6" fill="{SURFACE}" stroke="{BORDER}" />'
            f'<text x="{px + pw/2:.1f}" y="152" text-anchor="middle" fill="{INK}" font-family="{FONT_MONO}" font-size="10">{esc(item)}</text>'
        )
        px += pw + 8

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  {shared_css(css)}
  <g class="proj-wrap">
    <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="{BG}" stroke="{BORDER}" />

    <!-- Status Badge -->
    <rect x="22" y="18" width="{len(status_label)*7.2 + 28:.1f}" height="22" rx="6" fill="{badge_bg}" stroke="{badge_border}" stroke-width="0.8" />
    <circle cx="32" cy="29" r="3.5" fill="{pulse_color}" class="live-dot" />
    <text x="41" y="33" fill="{badge_text}" font-family="{FONT_MONO}" font-size="9.5" font-weight="700" letter-spacing="0.5">
      {esc(status_label)}
    </text>

    <!-- Domain Link Pill -->
    <text x="{w - 22}" y="33" text-anchor="end" fill="{COBALT}" font-family="{FONT_MONO}" font-size="11" font-weight="600">
      {esc(domain)} ↗
    </text>

    <!-- Number + Project Title -->
    <text x="22" y="70" fill="{INK}" font-family="{FONT_DISPLAY}" font-size="22" font-weight="700">
      <tspan fill="{MUTED}" font-family="{FONT_MONO}" font-size="14" font-weight="400">{esc(number)} </tspan>{esc(name)}
    </text>

    <!-- Tagline -->
    <text x="22" y="92" fill="{COBALT}" font-family="{FONT_SANS}" font-size="12.5" font-weight="600">
      {esc(tagline)}
    </text>

    <!-- Short Description -->
    <text x="22" y="114" fill="{MUTED}" font-family="{FONT_SANS}" font-size="12">
      {esc(description)}
    </text>

    <!-- Tags Row -->
    {''.join(pills)}
  </g>
</svg>"""


def render_contact_banner() -> str:
    w, h = 840, 120
    css = """
    @keyframes bannerFade {
      from { opacity: 0; transform: translateY(12px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .banner-wrap {
      opacity: 0;
      animation: bannerFade 0.6s cubic-bezier(.2,.8,.2,1) 2.6s forwards;
    }
    """
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  {shared_css(css)}
  <g class="banner-wrap">
    <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="{SURFACE}" stroke="{BORDER}" />

    <!-- Left side: pitch -->
    <text x="32" y="32" fill="{COBALT}" font-family="{FONT_MONO}" font-size="10.5" font-weight="700" letter-spacing="1">
      GOT A STORE OR IDEA IN MIND?
    </text>
    <text x="32" y="62" fill="{INK}" font-family="{FONT_DISPLAY}" font-size="24" font-weight="700">
      Let's build yours.
    </text>
    <text x="32" y="88" fill="{MUTED}" font-family="{FONT_SANS}" font-size="13">
      From first sketch to a store taking orders — one person, start to finish.
    </text>

    <!-- Right side: Contact action badges -->
    <!-- Email (Primary CTA) -->
    <rect x="520" y="24" width="288" height="34" rx="8" fill="{COBALT}" />
    <text x="664" y="46" text-anchor="middle" fill="#FFFFFF" font-family="{FONT_MONO}" font-size="11" font-weight="600">
      ✉️ deepeshsingh2606@gmail.com ↗
    </text>

    <!-- Portfolio -->
    <rect x="520" y="66" width="288" height="34" rx="8" fill="{SURFACE}" stroke="{BORDER}" />
    <text x="664" y="88" text-anchor="middle" fill="{COBALT}" font-family="{FONT_MONO}" font-size="11" font-weight="700">
      🌐 portfolio-deepesh.lovable.app ↗
    </text>
  </g>
</svg>"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    files = {
        "hero.svg": render_hero(data),
        "tile-build.svg": render_tile(
            kicker="01 · SHIPPED",
            title="Projects Shipped",
            subtitle="E-commerce stores & interactive web apps",
            metric=6,
            suffix="TOTAL PROJECTS",
            accent_bg=True,
            delay=1.75,
        ),
        "tile-focus.svg": render_tile(
            kicker="02 · DEPLOYED",
            title="Live in Production",
            subtitle="Taking orders & serving active users",
            metric=5,
            suffix="LIVE RIGHT NOW",
            accent_bg=False,
            delay=1.90,
        ),
        "tile-ship.svg": render_tile(
            kicker="03 · PIPELINE",
            title="In Active Build",
            subtitle="Launch-ready storefronts & tools",
            metric=1,
            suffix="IN PROGRESS",
            accent_bg=False,
            delay=2.05,
        ),
        "project-posterverse.svg": render_project_card(
            number="01",
            name="POSTERVERSE",
            tagline="Art that holds the room.",
            description="Print-studio storefront for posters, polaroids & kits.",
            domain="posterverse.store",
            status_label="LIVE STORE",
            stack=["Storefront", "Catalog", "Checkout"],
            is_live=True,
            delay=2.20,
        ),
        "project-woolencraft.svg": render_project_card(
            number="02",
            name="WOOLENCRAFT",
            tagline="Woven by heart.",
            description="Artisanal shop for handmade crochet & accessories.",
            domain="woolencraft.store",
            status_label="LIVE STORE",
            stack=["Brand Identity", "Custom Orders", "Payments"],
            is_live=True,
            delay=2.35,
        ),
        "project-flowstate.svg": render_project_card(
            number="03",
            name="FLOWSTATE",
            tagline="A study sanctuary for deep work.",
            description="Pomodoro focus timer, ambient rooms & stats.",
            domain="useflowstate.vercel.app",
            status_label="LIVE WEB APP",
            stack=["Web App", "Timers & Stats", "Live Rooms"],
            is_live=True,
            delay=2.50,
        ),
        "project-constellation.svg": render_project_card(
            number="04",
            name="CONSTELLATION LYRICS",
            tagline="Synchronized music & interactive lyrics.",
            description="Audio-synced visual lyric canvas & music player.",
            domain="constellationlyrics.vercel.app",
            status_label="LIVE WEB APP",
            stack=["Web Audio", "Audio Sync", "Frontend"],
            is_live=True,
            delay=2.65,
        ),
        "project-portfolio.svg": render_project_card(
            number="05",
            name="PORTFOLIO",
            tagline="I build stores that sell.",
            description="Personal brand showcase & engineering portfolio.",
            domain="portfolio-deepesh.lovable.app",
            status_label="LIVE SITE",
            stack=["Brand Identity", "Full-Stack UI", "Showcase"],
            is_live=True,
            delay=2.80,
        ),
        "project-hapylo.svg": render_project_card(
            number="06",
            name="HAPYLO",
            tagline="Happy home. Better living.",
            description="Launch-ready store for bamboo-less dhoop sticks.",
            domain="hapylo.com",
            status_label="IN PROGRESS",
            stack=["Storefront", "Pre-Launch", "Gift Kits"],
            is_live=False,
            delay=2.95,
        ),
        "contact.svg": render_contact_banner(),
    }

    for filename, svg in files.items():
        (OUT_DIR / filename).write_text(svg, encoding="utf-8")
        print(f"Rendered cards/{filename}")


if __name__ == "__main__":
    main()
