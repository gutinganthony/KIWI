"""
摸魚記 logo v2 — fish + trend line, no K-line rectangles
Three refined concepts inspired by top newsletter branding research
"""
import cairosvg

NAVY  = "#1a2744"
GOLD  = "#c9a84c"
CREAM = "#faf8f4"
DARK  = "#0e1720"

def save(svg_str, filename, scale=3):
    path = f"/home/user/KIWI/personal/branding/{filename}"
    cairosvg.svg2png(bytestring=svg_str.encode(), write_to=path, scale=scale)
    print(f"✓  {filename}")

# ════════════════════════════════════════════════════════════════════════════
# CONCEPT A — "Brushstroke Fish"
# One single open path forming the fish silhouette, calligraphy-ink style
# The upper arc naturally rises left→right, referencing an uptrend
# ════════════════════════════════════════════════════════════════════════════
svg_A = f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="140" viewBox="0 0 480 140">
  <rect width="480" height="140" fill="{CREAM}"/>

  <!-- Fish: single open stroke, upper arc rises (tail left, nose right) -->
  <!-- Tail fork -->
  <line x1="38" y1="52" x2="62" y2="70" stroke="{NAVY}" stroke-width="2.8" stroke-linecap="round"/>
  <line x1="38" y1="88" x2="62" y2="70" stroke="{NAVY}" stroke-width="2.8" stroke-linecap="round"/>

  <!-- Body upper arc — gently rising, references uptrend -->
  <path d="M 62 70 C 80 68 110 36 160 30 C 200 25 218 36 226 44"
        fill="none" stroke="{NAVY}" stroke-width="2.8" stroke-linecap="round"/>
  <!-- Body lower arc -->
  <path d="M 62 70 C 80 72 110 96 160 100 C 200 103 218 94 226 84"
        fill="none" stroke="{NAVY}" stroke-width="2.8" stroke-linecap="round"/>
  <!-- Nose close -->
  <path d="M 226 44 C 234 52 234 76 226 84"
        fill="none" stroke="{NAVY}" stroke-width="2.8" stroke-linecap="round"/>

  <!-- Eye — gold dot -->
  <circle cx="214" cy="52" r="4.5" fill="{GOLD}"/>

  <!-- Divider -->
  <line x1="258" y1="28" x2="258" y2="112" stroke="#ddd8d0" stroke-width="1"/>

  <!-- Wordmark -->
  <text x="278" y="78" font-family="Georgia, 'Times New Roman', serif"
        font-size="36" fill="{NAVY}" letter-spacing="4">摸魚記</text>
  <text x="280" y="97" font-family="Georgia, serif"
        font-size="8.5" fill="{GOLD}" letter-spacing="5">PRIVATE  MARKET  LETTER</text>
</svg>"""
save(svg_A, "logo-v2-A-brushstroke.png")


# ════════════════════════════════════════════════════════════════════════════
# CONCEPT B — "Fish Follows the Line"
# Solid navy fish silhouette; a thin gold trend line rises above/through it
# The fish is swimming along the uptrend — visually tells the brand story
# ════════════════════════════════════════════════════════════════════════════
svg_B = f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="140" viewBox="0 0 480 140">
  <rect width="480" height="140" fill="{NAVY}"/>

  <!-- Trend line: thin gold rising line, from tail-level to above the head -->
  <path d="M 28 98 C 60 90 100 68 150 50 C 180 38 210 30 240 26"
        fill="none" stroke="{GOLD}" stroke-width="1.4" stroke-linecap="round" opacity="0.85"/>

  <!-- Fish silhouette (filled, white) swimming along the trend -->
  <!-- Upper arc -->
  <path d="M 52 80 C 72 76 108 56 152 52 C 190 48 210 56 218 64
           C 210 72 190 80 152 78 C 108 74 72 82 52 80 Z"
        fill="white" opacity="0.97"/>
  <!-- Tail (filled triangles) -->
  <polygon points="52,80 28,62 28,98" fill="white" opacity="0.97"/>

  <!-- Eye — gold -->
  <circle cx="207" cy="60" r="4" fill="{GOLD}"/>

  <!-- Vertical divider -->
  <line x1="258" y1="30" x2="258" y2="110" stroke="#2d4060" stroke-width="1"/>

  <!-- Wordmark white -->
  <text x="278" y="77" font-family="Georgia, 'Times New Roman', serif"
        font-size="34" fill="white" letter-spacing="4">摸魚記</text>
  <text x="280" y="96" font-family="Georgia, serif"
        font-size="8" fill="{GOLD}" letter-spacing="5">PRIVATE  MARKET  LETTER</text>
</svg>"""
save(svg_B, "logo-v2-B-fish-follows-line.png")


# ════════════════════════════════════════════════════════════════════════════
# CONCEPT C — "Abstract: The Fish IS the Trend"
# Ultra-minimal: a single rising bezier IS the fish
# Small tail fork at start, gold eye-dot at end
# Pure concept: you "fish" for signals in the market trend
# ════════════════════════════════════════════════════════════════════════════
svg_C = f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="140" viewBox="0 0 480 140">
  <rect width="480" height="140" fill="{CREAM}"/>

  <!-- The rising curve = fish body = trend line -->
  <path d="M 50 95 C 80 90 120 72 175 55 C 210 44 225 40 235 38"
        fill="none" stroke="{NAVY}" stroke-width="3.2" stroke-linecap="round"/>

  <!-- Tail fork — small, elegant -->
  <path d="M 50 95 L 28 80" stroke="{NAVY}" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 50 95 L 30 108" stroke="{NAVY}" stroke-width="2.6" stroke-linecap="round"/>

  <!-- Eye / head — gold filled circle at the tip -->
  <circle cx="235" cy="38" r="5.5" fill="{GOLD}"/>

  <!-- Small fin — single upward stroke from mid-body -->
  <path d="M 140 62 L 130 46" stroke="{NAVY}" stroke-width="2" stroke-linecap="round" opacity="0.6"/>

  <!-- Divider -->
  <line x1="268" y1="28" x2="268" y2="112" stroke="#e0dcd6" stroke-width="1"/>

  <!-- Wordmark -->
  <text x="288" y="76" font-family="Georgia, 'Times New Roman', serif"
        font-size="36" fill="{NAVY}" letter-spacing="4">摸魚記</text>
  <text x="290" y="96" font-family="Georgia, serif"
        font-size="8.5" fill="{GOLD}" letter-spacing="5">PRIVATE  MARKET  LETTER</text>
</svg>"""
save(svg_C, "logo-v2-C-abstract-trend-fish.png")


# ════════════════════════════════════════════════════════════════════════════
# CONCEPT D — "Seal / Stamp" — refined version of the original B
# Circular, premium, works as Substack avatar
# Fish silhouette inside the circle (negative space)
# ════════════════════════════════════════════════════════════════════════════
svg_D = f"""<svg xmlns="http://www.w3.org/2000/svg" width="320" height="320" viewBox="0 0 320 320">
  <rect width="320" height="320" fill="{DARK}"/>

  <!-- Outer ring -->
  <circle cx="160" cy="160" r="145" fill="none" stroke="{GOLD}" stroke-width="1.5"/>
  <circle cx="160" cy="160" r="136" fill="none" stroke="{GOLD}" stroke-width="0.6" stroke-dasharray="3 5" opacity="0.5"/>

  <!-- Fish inside: outline style, elegant -->
  <g transform="translate(55, 148)">
    <!-- Tail -->
    <line x1="0"  y1="0"  x2="22" y2="-16" stroke="{GOLD}" stroke-width="2.2" stroke-linecap="round"/>
    <line x1="0"  y1="0"  x2="22" y2="16"  stroke="{GOLD}" stroke-width="2.2" stroke-linecap="round"/>
    <!-- Upper body -->
    <path d="M 22 0 C 42 -4 80 -26 120 -28 C 148 -29 164 -18 170 -8"
          fill="none" stroke="{GOLD}" stroke-width="2.2" stroke-linecap="round"/>
    <!-- Lower body -->
    <path d="M 22 0 C 42 4 80 26 120 26 C 148 27 164 16 170 6"
          fill="none" stroke="{GOLD}" stroke-width="2.2" stroke-linecap="round"/>
    <!-- Nose -->
    <path d="M 170 -8 C 178 -2 178 2 170 6"
          fill="none" stroke="{GOLD}" stroke-width="2.2" stroke-linecap="round"/>
    <!-- Eye -->
    <circle cx="160" cy="-2" r="4" fill="{GOLD}"/>
  </g>

  <!-- Chinese text below -->
  <text x="160" y="220" text-anchor="middle"
        font-family="Georgia, serif" font-size="28" fill="{GOLD}" letter-spacing="10">摸魚記</text>

  <!-- Bottom arc label -->
  <path id="btmarc" d="M 30 160 A 130 130 0 0 0 290 160" fill="none"/>
  <text font-family="Georgia, serif" font-size="9" fill="{GOLD}" letter-spacing="3" opacity="0.55">
    <textPath href="#btmarc" startOffset="11%">PRIVATE  ·  MARKET  ·  LETTER</textPath>
  </text>
</svg>"""
save(svg_D, "logo-v2-D-seal.png")


# ════════════════════════════════════════════════════════════════════════════
# AVATAR — best of C on a circle (Substack profile)
# ════════════════════════════════════════════════════════════════════════════
svg_av = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <circle cx="200" cy="200" r="200" fill="{NAVY}"/>

  <!-- Rising fish / trend line centered -->
  <g transform="translate(200, 200)">
    <!-- Main body curve -->
    <path d="M -110 50 C -70 44 -20 18 40 -2 C 80 -16 108 -22 118 -24"
          fill="none" stroke="white" stroke-width="5.5" stroke-linecap="round"/>
    <!-- Tail -->
    <path d="M -110 50 L -138 28" stroke="white" stroke-width="5" stroke-linecap="round"/>
    <path d="M -110 50 L -136 70" stroke="white" stroke-width="5" stroke-linecap="round"/>
    <!-- Fin -->
    <path d="M -10 14 L -22 -10" stroke="white" stroke-width="3.5" stroke-linecap="round" opacity="0.7"/>
    <!-- Eye -->
    <circle cx="118" cy="-24" r="8" fill="{GOLD}"/>
  </g>
</svg>"""
save(svg_av, "avatar-v2-trend-fish.png")

print("\nAll v2 logos exported.")
