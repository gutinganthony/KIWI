"""
摸魚記 — Final Logo Production
Direction: Water Ripple (水波紋)
Exports all Substack-ready assets
"""
import cairosvg

NAVY  = "#1a2744"
GOLD  = "#b8954a"
CREAM = "#f8f6f1"
WHITE = "#ffffff"
FONT  = "Noto Serif TC"

def save(svg, fname, scale=3):
    p = f"/home/user/KIWI/personal/branding/final/{fname}"
    cairosvg.svg2png(bytestring=svg.encode(), write_to=p, scale=scale)
    print(f"✓  {fname}")

import os
os.makedirs("/home/user/KIWI/personal/branding/final", exist_ok=True)

# ── Shared ripple helper ─────────────────────────────────────────────────────
# cx, cy = origin point; gap = spacing between arcs; stroke widths taper out
def ripple(cx, cy, r1=52, r2=82, r3=112, sw1=3.2, sw2=2.2, sw3=1.4,
           color=GOLD, dot=6):
    return f"""
  <path d="M {cx-r1} {cy} Q {cx} {cy-r1*1.18} {cx+r1} {cy}"
        fill="none" stroke="{color}" stroke-width="{sw1}" stroke-linecap="round"/>
  <path d="M {cx-r2} {cy} Q {cx} {cy-r2*1.18} {cx+r2} {cy}"
        fill="none" stroke="{color}" stroke-width="{sw2}" stroke-linecap="round" opacity="0.65"/>
  <path d="M {cx-r3} {cy} Q {cx} {cy-r3*1.18} {cx+r3} {cy}"
        fill="none" stroke="{color}" stroke-width="{sw3}" stroke-linecap="round" opacity="0.35"/>
  <circle cx="{cx}" cy="{cy}" r="{dot}" fill="{color}"/>"""


# ════════════════════════════════════════════════════════════════════════════
# 1. AVATAR — 1:1 circle, Substack profile image (400×400)
# ════════════════════════════════════════════════════════════════════════════
svg_avatar = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <circle cx="200" cy="200" r="200" fill="{NAVY}"/>
  {ripple(200, 290, r1=68, r2=106, r3=144, sw1=4.5, sw2=3.2, sw3=2, dot=7.5)}
</svg>"""
save(svg_avatar, "avatar.png")


# ════════════════════════════════════════════════════════════════════════════
# 2. LOGO HORIZONTAL — icon left, wordmark right (Substack publication logo)
# ════════════════════════════════════════════════════════════════════════════
svg_logo_dark = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="160" viewBox="0 0 600 160">
  <rect width="600" height="160" fill="{NAVY}"/>
  {ripple(80, 128, r1=48, r2=74, r3=100, sw1=3.5, sw2=2.4, sw3=1.5, dot=6)}
  <line x1="200" y1="26" x2="200" y2="134" stroke="#243557" stroke-width="1.2"/>
  <text x="224" y="96" font-family="{FONT}" font-size="50"
        fill="{WHITE}" letter-spacing="5">摸魚記</text>
  <text x="226" y="118" font-family="Liberation Serif" font-size="9"
        fill="{GOLD}" letter-spacing="6" opacity="0.8">PRIVATE  MARKET  LETTER</text>
</svg>"""
save(svg_logo_dark, "logo-horizontal-dark.png")

svg_logo_light = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="160" viewBox="0 0 600 160">
  <rect width="600" height="160" fill="{CREAM}"/>
  {ripple(80, 128, r1=48, r2=74, r3=100, sw1=3.5, sw2=2.4, sw3=1.5, dot=6)}
  <line x1="200" y1="26" x2="200" y2="134" stroke="#dedad4" stroke-width="1.2"/>
  <text x="224" y="96" font-family="{FONT}" font-size="50"
        fill="{NAVY}" letter-spacing="5">摸魚記</text>
  <text x="226" y="118" font-family="Liberation Serif" font-size="9"
        fill="{GOLD}" letter-spacing="6" opacity="0.85">PRIVATE  MARKET  LETTER</text>
</svg>"""
save(svg_logo_light, "logo-horizontal-light.png")


# ════════════════════════════════════════════════════════════════════════════
# 3. COVER BANNER — Substack header / social share (1200×400)
# ════════════════════════════════════════════════════════════════════════════
svg_cover = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="400" viewBox="0 0 1200 400">
  <rect width="1200" height="400" fill="{NAVY}"/>
  <!-- Subtle background ripples (decorative, large, faint) -->
  <path d="M 400 480 Q 600 180 800 480"
        fill="none" stroke="{GOLD}" stroke-width="1" opacity="0.08"/>
  <path d="M 300 510 Q 600 120 900 510"
        fill="none" stroke="{GOLD}" stroke-width="0.8" opacity="0.06"/>
  <path d="M 200 540 Q 600 60 1000 540"
        fill="none" stroke="{GOLD}" stroke-width="0.6" opacity="0.04"/>
  <!-- Main ripple icon, centered-left -->
  {ripple(280, 330, r1=78, r2=120, r3=162, sw1=5, sw2=3.5, sw3=2.2, dot=9)}
  <!-- Vertical rule -->
  <line x1="490" y1="100" x2="490" y2="300" stroke="#2a3d5a" stroke-width="1.5"/>
  <!-- Wordmark -->
  <text x="530" y="230" font-family="{FONT}" font-size="100"
        fill="{WHITE}" letter-spacing="10">摸魚記</text>
  <!-- Tagline -->
  <text x="534" y="272" font-family="Liberation Serif" font-size="13"
        fill="{GOLD}" letter-spacing="7" opacity="0.75">PRIVATE  MARKET  LETTER</text>
</svg>"""
save(svg_cover, "cover-banner.png", scale=2)


# ════════════════════════════════════════════════════════════════════════════
# 4. ICON SQUARE — for favicon / app icon (standalone ripple only)
# ════════════════════════════════════════════════════════════════════════════
svg_icon = f"""<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300">
  <rect width="300" height="300" fill="{NAVY}" rx="36"/>
  {ripple(150, 230, r1=58, r2=90, r3=122, sw1=4.5, sw2=3.2, sw3=2, dot=7)}
</svg>"""
save(svg_icon, "icon-square.png")

print("\n✦  All final assets saved to personal/branding/final/")
