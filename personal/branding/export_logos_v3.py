"""
摸魚記 logo v3 — full reset
Three completely new directions, no reference to previous work
"""
import cairosvg

NAVY  = "#1a2744"
GOLD  = "#b8954a"
CREAM = "#f8f6f1"
RED   = "#c0392b"
WHITE = "#ffffff"
FONT  = "Noto Serif TC"

def save(svg, fname, scale=3):
    p = f"/home/user/KIWI/personal/branding/{fname}"
    cairosvg.svg2png(bytestring=svg.encode(), write_to=p, scale=scale)
    print(f"✓  {fname}")


# ════════════════════════════════════════════════════════════════════════════
# CONCEPT 1 — RED SEAL (印章)
# A vermillion square seal with 摸魚 inside — traditional, luxury, iconic
# Inspired by: Hermès carré, traditional Chinese publishing seals
# Clean, zero ambiguity, perfect as avatar
# ════════════════════════════════════════════════════════════════════════════

svg1_icon = f"""<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300">
  <rect width="300" height="300" fill="#f8f6f1"/>
  <!-- Seal square -->
  <rect x="40" y="40" width="220" height="220" fill="{RED}" rx="4"/>
  <!-- Inner border -->
  <rect x="52" y="52" width="196" height="196" fill="none" stroke="{WHITE}" stroke-width="2" rx="2"/>
  <!-- 摸魚 two characters stacked -->
  <text x="150" y="138" text-anchor="middle"
        font-family="{FONT}" font-size="76" fill="{WHITE}" font-weight="400">摸</text>
  <text x="150" y="222" text-anchor="middle"
        font-family="{FONT}" font-size="76" fill="{WHITE}" font-weight="400">魚</text>
</svg>"""
save(svg1_icon, "v3-1a-seal-icon.png")

# Seal + wordmark horizontal layout
svg1_full = f"""<svg xmlns="http://www.w3.org/2000/svg" width="560" height="180" viewBox="0 0 560 180">
  <rect width="560" height="180" fill="{CREAM}"/>
  <!-- Seal -->
  <rect x="30" y="24" width="132" height="132" fill="{RED}" rx="3"/>
  <rect x="39" y="33" width="114" height="114" fill="none" stroke="{WHITE}" stroke-width="1.5" rx="1"/>
  <text x="96" y="94" text-anchor="middle" font-family="{FONT}" font-size="44" fill="{WHITE}">摸魚</text>
  <!-- Wordmark -->
  <text x="194" y="98" font-family="{FONT}" font-size="56" fill="{NAVY}" letter-spacing="2">摸魚記</text>
  <line x1="194" y1="118" x2="530" y2="118" stroke="{GOLD}" stroke-width="1.2"/>
  <text x="195" y="136" font-family="Liberation Serif" font-size="9.5"
        fill="{GOLD}" letter-spacing="5.5">PRIVATE  MARKET  LETTER</text>
</svg>"""
save(svg1_full, "v3-1b-seal-full.png")


# ════════════════════════════════════════════════════════════════════════════
# CONCEPT 2 — WATER RIPPLE
# Three expanding arcs from a single point — the act of 摸魚 (touching water)
# sends ripples outward = your insight ripples out to readers
# Simple, metaphorical, no fish cliché
# ════════════════════════════════════════════════════════════════════════════

svg2_icon = f"""<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300">
  <rect width="300" height="300" fill="{NAVY}"/>
  <!-- Three ripple arcs, bottom-center origin -->
  <!-- Innermost -->
  <path d="M 100 210 Q 150 148 200 210"
        fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round"/>
  <!-- Middle -->
  <path d="M 68 220 Q 150 120 232 220"
        fill="none" stroke="{GOLD}" stroke-width="2.2" stroke-linecap="round" opacity="0.75"/>
  <!-- Outer -->
  <path d="M 36 228 Q 150 92 264 228"
        fill="none" stroke="{GOLD}" stroke-width="1.5" stroke-linecap="round" opacity="0.45"/>
  <!-- Dot at origin — the touch point -->
  <circle cx="150" cy="224" r="5" fill="{GOLD}"/>
</svg>"""
save(svg2_icon, "v3-2a-ripple-icon.png")

svg2_full = f"""<svg xmlns="http://www.w3.org/2000/svg" width="560" height="160" viewBox="0 0 560 160">
  <rect width="560" height="160" fill="{NAVY}"/>
  <!-- Ripple icon (compact) -->
  <g transform="translate(30, 20)">
    <path d="M 36 102 Q 70 62 104 102"
          fill="none" stroke="{GOLD}" stroke-width="2.8" stroke-linecap="round"/>
    <path d="M 18 110 Q 70 46 122 110"
          fill="none" stroke="{GOLD}" stroke-width="2" stroke-linecap="round" opacity="0.7"/>
    <path d="M 2 117 Q 70 32 138 117"
          fill="none" stroke="{GOLD}" stroke-width="1.4" stroke-linecap="round" opacity="0.4"/>
    <circle cx="70" cy="114" r="4" fill="{GOLD}"/>
  </g>
  <!-- Vertical rule -->
  <line x1="196" y1="24" x2="196" y2="136" stroke="#2a3d5a" stroke-width="1.2"/>
  <!-- Text -->
  <text x="218" y="92" font-family="{FONT}" font-size="48" fill="{WHITE}" letter-spacing="4">摸魚記</text>
  <text x="220" y="114" font-family="Liberation Serif" font-size="9"
        fill="{GOLD}" letter-spacing="5.5" opacity="0.85">PRIVATE  MARKET  LETTER</text>
</svg>"""
save(svg2_full, "v3-2b-ripple-full.png")


# ════════════════════════════════════════════════════════════════════════════
# CONCEPT 3 — PURE WORDMARK (Typography-first)
# No icon at all. Let the characters carry everything.
# 摸魚  large, navy.  記  smaller, gold accent.
# Inspired by: The Economist, FT, Net Interest
# The most confident move: trust that the name is strong enough
# ════════════════════════════════════════════════════════════════════════════

svg3_light = f"""<svg xmlns="http://www.w3.org/2000/svg" width="560" height="160" viewBox="0 0 560 160">
  <rect width="560" height="160" fill="{CREAM}"/>
  <!-- Thin top rule, gold -->
  <line x1="40" y1="30" x2="520" y2="30" stroke="{GOLD}" stroke-width="1"/>
  <!-- 摸魚 large -->
  <text x="44" y="110" font-family="{FONT}" font-size="72" fill="{NAVY}" letter-spacing="4">摸魚</text>
  <!-- 記 gold accent, vertically aligned right -->
  <text x="340" y="110" font-family="{FONT}" font-size="72" fill="{GOLD}">記</text>
  <!-- Subtitle -->
  <text x="44" y="134" font-family="Liberation Serif" font-size="9.5"
        fill="{NAVY}" letter-spacing="6" opacity="0.55">PRIVATE  MARKET  LETTER</text>
  <!-- Thin bottom rule -->
  <line x1="40" y1="144" x2="520" y2="144" stroke="{GOLD}" stroke-width="1"/>
</svg>"""
save(svg3_light, "v3-3a-wordmark-light.png")

svg3_dark = f"""<svg xmlns="http://www.w3.org/2000/svg" width="560" height="160" viewBox="0 0 560 160">
  <rect width="560" height="160" fill="{NAVY}"/>
  <line x1="40" y1="30" x2="520" y2="30" stroke="{GOLD}" stroke-width="1"/>
  <text x="44" y="110" font-family="{FONT}" font-size="72" fill="{WHITE}" letter-spacing="4">摸魚</text>
  <text x="340" y="110" font-family="{FONT}" font-size="72" fill="{GOLD}">記</text>
  <text x="44" y="134" font-family="Liberation Serif" font-size="9.5"
        fill="{WHITE}" letter-spacing="6" opacity="0.45">PRIVATE  MARKET  LETTER</text>
  <line x1="40" y1="144" x2="520" y2="144" stroke="{GOLD}" stroke-width="1"/>
</svg>"""
save(svg3_dark, "v3-3b-wordmark-dark.png")


# ════════════════════════════════════════════════════════════════════════════
# AVATAR versions (Substack circle crop)
# ════════════════════════════════════════════════════════════════════════════

av_seal = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <circle cx="200" cy="200" r="200" fill="{CREAM}"/>
  <rect x="80" y="80" width="240" height="240" fill="{RED}" rx="5"/>
  <rect x="94" y="94" width="212" height="212" fill="none" stroke="{WHITE}" stroke-width="2.2" rx="2"/>
  <text x="200" y="182" text-anchor="middle" font-family="{FONT}" font-size="80" fill="{WHITE}">摸魚</text>
  <line x1="104" y1="200" x2="296" y2="200" stroke="{WHITE}" stroke-width="1" opacity="0.4"/>
  <text x="200" y="280" text-anchor="middle" font-family="{FONT}" font-size="60" fill="{WHITE}" opacity="0.9">記</text>
</svg>"""
save(av_seal, "v3-avatar-seal.png")

av_ripple = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <circle cx="200" cy="200" r="200" fill="{NAVY}"/>
  <path d="M 100 280 Q 200 160 300 280"
        fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>
  <path d="M 60 295 Q 200 130 340 295"
        fill="none" stroke="{GOLD}" stroke-width="3.5" stroke-linecap="round" opacity="0.65"/>
  <path d="M 22 308 Q 200 100 378 308"
        fill="none" stroke="{GOLD}" stroke-width="2.2" stroke-linecap="round" opacity="0.35"/>
  <circle cx="200" cy="300" r="7" fill="{GOLD}"/>
</svg>"""
save(av_ripple, "v3-avatar-ripple.png")

print("\nAll v3 logos exported.")
