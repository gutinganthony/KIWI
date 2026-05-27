import cairosvg

# Shared palette
NAVY = "#1a2744"
GOLD = "#c9a84c"
WHITE = "white"
DARK = "#0f1923"

def make_svg(content, w, h, bg=None):
    bg_rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{bg_rect}{content}</svg>'

def save(svg_str, filename, scale=2):
    path = f"/home/user/KIWI/personal/branding/{filename}"
    cairosvg.svg2png(bytestring=svg_str.encode(), write_to=path, scale=scale)
    print(f"Saved: {path}")

# ── Concept A: 魚形K線 ────────────────────────────────────────────────────────
svg_a = make_svg("""
  <!-- Fish body -->
  <path d="M 60 60 Q 110 30 160 60 Q 110 90 60 60" fill="none" stroke="#1a2744" stroke-width="2.5"/>
  <!-- Tail -->
  <path d="M 60 60 L 38 42 M 60 60 L 38 78" stroke="#1a2744" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Eye -->
  <circle cx="148" cy="55" r="3.5" fill="#c9a84c"/>
  <!-- Divider -->
  <line x1="185" y1="28" x2="185" y2="92" stroke="#ddd" stroke-width="1"/>
  <!-- Title -->
  <text x="205" y="58" font-family="Georgia, serif" font-size="30" fill="#1a2744" letter-spacing="3">摸魚記</text>
  <text x="207" y="76" font-family="Georgia, serif" font-size="9" fill="#c9a84c" letter-spacing="3.5">PRIVATE  MARKET  LETTER</text>
""", 420, 120, bg="#faf9f7")

save(svg_a, "logo-A-fish-kline.png")

# ── Concept B: 印章風格 ───────────────────────────────────────────────────────
svg_b = make_svg("""
  <circle cx="160" cy="160" r="138" fill="none" stroke="#c9a84c" stroke-width="2"/>
  <circle cx="160" cy="160" r="128" fill="none" stroke="#c9a84c" stroke-width="0.7" stroke-dasharray="4 4"/>
  <text x="160" y="140" text-anchor="middle" font-family="Georgia, serif" font-size="58" fill="#c9a84c" letter-spacing="5">摸魚</text>
  <line x1="80" y1="158" x2="240" y2="158" stroke="#c9a84c" stroke-width="1" opacity="0.5"/>
  <text x="160" y="202" text-anchor="middle" font-family="Georgia, serif" font-size="42" fill="#c9a84c" letter-spacing="8">記</text>
  <path id="arc" d="M 40 160 A 120 120 0 0 0 280 160" fill="none"/>
  <text font-family="Georgia, serif" font-size="11" fill="#c9a84c" letter-spacing="3" opacity="0.6">
    <textPath href="#arc" startOffset="10%">PRIVATE  ·  MARKET  ·  LETTER</textPath>
  </text>
""", 320, 320, bg=DARK)

save(svg_b, "logo-B-seal.png")

# ── Concept C: 極簡字標 ───────────────────────────────────────────────────────
svg_c = make_svg("""
  <line x1="40" y1="28" x2="440" y2="28" stroke="#c9a84c" stroke-width="1.2"/>
  <text x="40" y="88" font-family="Georgia, serif" font-size="54" fill="white" letter-spacing="10">摸魚記</text>
  <line x1="40" y1="104" x2="440" y2="104" stroke="#c9a84c" stroke-width="1.2"/>
  <text x="42" y="122" font-family="Georgia, serif" font-size="10" fill="#c9a84c" letter-spacing="6">PRIVATE  MARKET  LETTER</text>
""", 480, 148, bg=NAVY)

save(svg_c, "logo-C-wordmark.png")

# ── Concept D: 圖標＋字標 ─────────────────────────────────────────────────────
svg_d = make_svg("""
  <!-- Fish body top -->
  <path d="M 50 76 Q 96 36 142 76" fill="none" stroke="#1a2744" stroke-width="3" stroke-linecap="round"/>
  <!-- Fish body bottom -->
  <path d="M 50 76 Q 96 116 142 76" fill="none" stroke="#1a2744" stroke-width="3" stroke-linecap="round"/>
  <!-- Tail -->
  <path d="M 50 76 L 24 56 M 50 76 L 24 96" stroke="#1a2744" stroke-width="3" stroke-linecap="round"/>
  <!-- Eye -->
  <circle cx="132" cy="71" r="4" fill="#c9a84c"/>
  <!-- K-line inside fish -->
  <path d="M 64 88 L 80 66 L 96 73 L 116 54" fill="none" stroke="#c9a84c" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" opacity="0.75"/>
  <!-- Divider -->
  <line x1="168" y1="30" x2="168" y2="122" stroke="#e0ddd8" stroke-width="1.2"/>
  <!-- Text -->
  <text x="190" y="84" font-family="Georgia, serif" font-size="38" fill="#1a2744" letter-spacing="4">摸魚記</text>
  <text x="192" y="104" font-family="Georgia, serif" font-size="9.5" fill="#c9a84c" letter-spacing="4">PRIVATE  MARKET  LETTER</text>
""", 480, 152, bg="#faf9f7")

save(svg_d, "logo-D-icon-wordmark.png")

# ── Avatar versions (圓形頭像) ────────────────────────────────────────────────

# Avatar: Seal
svg_av_seal = make_svg("""
  <circle cx="150" cy="150" r="148" fill="#0f1923"/>
  <circle cx="150" cy="150" r="118" fill="none" stroke="#c9a84c" stroke-width="1.5"/>
  <circle cx="150" cy="150" r="110" fill="none" stroke="#c9a84c" stroke-width="0.5" stroke-dasharray="3 3"/>
  <text x="150" y="132" text-anchor="middle" font-family="Georgia, serif" font-size="44" fill="#c9a84c" letter-spacing="4">摸魚</text>
  <line x1="72" y1="148" x2="228" y2="148" stroke="#c9a84c" stroke-width="0.8" opacity="0.5"/>
  <text x="150" y="186" text-anchor="middle" font-family="Georgia, serif" font-size="34" fill="#c9a84c" letter-spacing="8">記</text>
""", 300, 300)
save(svg_av_seal, "avatar-seal.png")

# Avatar: Fish icon
svg_av_fish = make_svg("""
  <circle cx="150" cy="150" r="148" fill="#1a2744"/>
  <g transform="translate(150,150)">
    <path d="M -62 0 Q 0 -46 62 0" fill="none" stroke="white" stroke-width="4" stroke-linecap="round"/>
    <path d="M -62 0 Q 0 46 62 0" fill="none" stroke="white" stroke-width="4" stroke-linecap="round"/>
    <path d="M -62 0 L -84 -18 M -62 0 L -84 18" stroke="white" stroke-width="4" stroke-linecap="round"/>
    <circle cx="52" cy="-7" r="5.5" fill="#c9a84c"/>
    <path d="M -30 14 L -10 -8 L 10 0 L 34 -20" fill="none" stroke="#c9a84c" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>
  </g>
""", 300, 300)
save(svg_av_fish, "avatar-fish.png")

print("\nAll done! Files saved to personal/branding/")
