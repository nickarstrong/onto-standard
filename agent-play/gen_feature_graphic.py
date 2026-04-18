"""
ONTO Agent · Play Store Feature Graphic Generator
Output: 1024×500 PNG, 24-bit, no alpha
"""

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 500
BG       = (24, 24, 27)       # #18181b
INK      = (244, 244, 245)    # #f4f4f5
INK2     = (212, 212, 216)    # #d4d4d8
INK3     = (161, 161, 170)    # #a1a1aa
GREEN    = (34, 197, 94)      # #22c55e
GREEN_BG = (20, 83, 45)       # darker green for bg pill
GREY     = (39, 39, 42)       # #27272a - logo circle
GRID     = (39, 39, 42)       # grid color, low opacity via blend

# ── fonts ────────────────────────────────────────────────────────
FONT_SANS_BOLD  = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FONT_SANS       = "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf"
FONT_SANS_MED   = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
FONT_MONO       = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
FONT_MONO_REG   = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"

def f(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()

# ── canvas ───────────────────────────────────────────────────────
img  = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# ── subtle grid background ───────────────────────────────────────
# 40px grid, very faint
GRID_FAINT = (34, 34, 38)
step = 40
for x in range(0, W, step):
    draw.line([(x, 0), (x, H)], fill=GRID_FAINT, width=1)
for y in range(0, H, step):
    draw.line([(0, y), (W, y)], fill=GRID_FAINT, width=1)

# ── LEFT BLOCK: Logo + Brand + Tagline ────────────────────────────

# Logo — circle + "1" (matching app)
logo_cx, logo_cy, logo_r = 90, 120, 34
draw.ellipse([logo_cx - logo_r, logo_cy - logo_r,
              logo_cx + logo_r, logo_cy + logo_r], fill=GREY)
# white "1" glyph — using simple rect strokes (matches SVG path shape)
# Original SVG path: M16 10L20 10L20 26L16 26L16 14L13 14L13 10L16 10Z (viewBox 36x36)
# Scale from 36 to 68 (2*logo_r), center at logo_cx, logo_cy
scale = (2 * logo_r) / 36
x0 = logo_cx - logo_r
y0 = logo_cy - logo_r
def pt(x, y):
    return (x0 + x * scale, y0 + y * scale)

# Polygon for "1" — 7 points from SVG path
points = [pt(16, 10), pt(20, 10), pt(20, 26), pt(16, 26),
          pt(16, 14), pt(13, 14), pt(13, 10)]
draw.polygon(points, fill=INK)

# Brand wordmark "ONTO"
font_brand = f(FONT_SANS_BOLD, 64)
draw.text((150, 85), "ONTO", font=font_brand, fill=INK)

# Hairline separator under brand
draw.line([(64, 185), (480, 185)], fill=INK3 + (), width=1)

# Tagline — 2 lines
font_tag1 = f(FONT_SANS_BOLD, 38)
font_tag2 = f(FONT_SANS, 26)
draw.text((64, 210), "Every AI answer —", font=font_tag1, fill=INK)
draw.text((64, 258), "verified, sourced, scored.", font=font_tag1, fill=GREEN)

# Sub-tagline (muted, below)
font_sub = f(FONT_SANS_MED, 20)
draw.text((64, 325), "R1–R18 · Inference-time discipline", font=font_sub, fill=INK3)

# Bottom-left small brand tag
font_brandtag = f(FONT_MONO_REG, 14)
draw.text((64, 435), "ontostandard.org", font=font_brandtag, fill=INK3)

# ── RIGHT BLOCK: Grade A Card + R bars ────────────────────────────

card_x, card_y, card_w, card_h = 605, 85, 360, 330
# card bg (slight lift from BG)
CARD_BG = (31, 31, 35)
draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                       radius=18, fill=CARD_BG,
                       outline=(55, 55, 60), width=1)

# Grade A badge (pill) centered on card top
badge_text = "Grade A · 9.4 / 10"
font_badge = f(FONT_MONO, 22)
bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
bw = bbox[2] - bbox[0]
bh = bbox[3] - bbox[1]
pad_x, pad_y = 18, 10
bx = card_x + (card_w - bw - 2 * pad_x) // 2
by = card_y + 28
# pill bg (tinted green, darker)
PILL_BG = (18, 54, 32)
PILL_BORDER = (34, 197, 94, 80)  # RGBA not used here, approximate with solid
draw.rounded_rectangle([bx, by, bx + bw + 2 * pad_x, by + bh + 2 * pad_y],
                       radius=10, fill=PILL_BG,
                       outline=(34, 197, 94), width=1)
draw.text((bx + pad_x, by + pad_y - 2), badge_text, font=font_badge, fill=GREEN)

# R bars (3 bars: R1, R4, R6 — matching welcome modal)
bars = [("R1", 1.00), ("R4", 1.00), ("R6", 1.00)]
bar_start_y = by + bh + 2 * pad_y + 42
bar_x = card_x + 36
bar_track_x = bar_x + 42
bar_track_w = card_w - 36 - 42 - 70 - 36  # room for value on right
bar_h = 8
bar_gap = 42

font_rlabel = f(FONT_MONO, 18)
font_rval   = f(FONT_MONO, 16)

for i, (label, val) in enumerate(bars):
    y = bar_start_y + i * bar_gap
    # label
    draw.text((bar_x, y - 6), label, font=font_rlabel, fill=INK3)
    # track
    track_y0 = y + 2
    track_y1 = y + 2 + bar_h
    draw.rounded_rectangle([bar_track_x, track_y0,
                            bar_track_x + bar_track_w, track_y1],
                           radius=4, fill=(39, 39, 42))
    # fill
    fill_w = int(bar_track_w * val)
    draw.rounded_rectangle([bar_track_x, track_y0,
                            bar_track_x + fill_w, track_y1],
                           radius=4, fill=GREEN)
    # value on right
    val_text = f"{val:.2f}"
    vbbox = draw.textbbox((0, 0), val_text, font=font_rval)
    vw = vbbox[2] - vbbox[0]
    draw.text((card_x + card_w - 36 - vw, y - 4), val_text,
              font=font_rval, fill=INK2)

# Card footer label
font_card_lbl = f(FONT_MONO_REG, 13)
footer_txt = "EVERY  ANSWER  ·  MEASURED"
fbbox = draw.textbbox((0, 0), footer_txt, font=font_card_lbl)
fw = fbbox[2] - fbbox[0]
draw.text((card_x + (card_w - fw) // 2, card_y + card_h - 38),
          footer_txt, font=font_card_lbl, fill=INK3)

# ── Save ─────────────────────────────────────────────────────────
out_path = "/mnt/user-data/outputs/feature-graphic-1024x500.png"
img.save(out_path, "PNG", optimize=True)
print(f"Saved: {out_path}")
print(f"Size:  {W}×{H}")
