# -*- coding: utf-8 -*-
"""
Combine fig1 panels into a single 2x2 figure using PIL (pixel-perfect).
Layout:
  [mental beeswarm]  [mental bar]
  [income beeswarm]  [income bar]
with captions below each panel.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUTDIR = r'C:\Users\sharafi\results\median'
GAP    = 20   # horizontal gap between columns (px)
ROW_GAP = 30  # vertical gap between rows (px)
CAP_H   = 38  # height reserved for caption text below each panel (px)
FONT_SIZE = 22

def crop_whitespace(img, tol=245, border=8):
    arr = np.array(img.convert('RGB'))
    mask = np.any(arr < tol, axis=2)
    rows = np.where(np.any(mask, axis=1))[0]
    cols = np.where(np.any(mask, axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return img
    r0, r1 = max(0, rows[0]-border),  min(arr.shape[0], rows[-1]+border+1)
    c0, c1 = max(0, cols[0]-border),  min(arr.shape[1], cols[-1]+border+1)
    return img.crop((c0, r0, c1, r1))

def scale_to_height(img, h):
    w = int(img.width * h / img.height)
    return img.resize((w, h), Image.LANCZOS)

# Load and crop
mnt_s = crop_whitespace(Image.open(os.path.join(OUTDIR, 'fig1_mental_summary.png')))
mnt_b = crop_whitespace(Image.open(os.path.join(OUTDIR, 'fig1_mental_bar.png')))
inc_s = crop_whitespace(Image.open(os.path.join(OUTDIR, 'fig1_income_summary.png')))
inc_b = crop_whitespace(Image.open(os.path.join(OUTDIR, 'fig1_income_bar.png')))

# Make both images in each row the same height
row1_h = max(mnt_s.height, mnt_b.height)
row2_h = max(inc_s.height, inc_b.height)
mnt_s = scale_to_height(mnt_s, row1_h)
mnt_b = scale_to_height(mnt_b, row1_h)
inc_s = scale_to_height(inc_s, row2_h)
inc_b = scale_to_height(inc_b, row2_h)

# Total canvas size
total_w = mnt_s.width + GAP + mnt_b.width
total_h = row1_h + CAP_H + ROW_GAP + row2_h + CAP_H

canvas = Image.new('RGB', (total_w, total_h), 'white')

# Paste row 1
canvas.paste(mnt_s, (0, 0))
canvas.paste(mnt_b, (mnt_s.width + GAP, 0))

# Paste row 2
row2_y = row1_h + CAP_H + ROW_GAP
canvas.paste(inc_s, (0, row2_y))
canvas.paste(inc_b, (inc_s.width + GAP, row2_y))

# Draw captions
draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("arial.ttf", FONT_SIZE)
except Exception:
    font = ImageFont.load_default()

captions = [
    # (x_center, y_top, text)
    (mnt_s.width // 2,               row1_h + 6,
     '(a) Local SHAP values of the mental health predictions'),
    (mnt_s.width + GAP + mnt_b.width // 2, row1_h + 6,
     '(b) Mean SHAP values'),
    (inc_s.width // 2,               row2_y + inc_s.height + 6,
     '(c) Local SHAP values of the income predictions.'),
    (inc_s.width + GAP + inc_b.width // 2, row2_y + inc_s.height + 6,
     '(d) Mean SHAP values'),
]

for cx, cy, text in captions:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw // 2, cy), text, fill='black', font=font)

out_path = os.path.join(OUTDIR, 'fig1_combined.png')
canvas.save(out_path, dpi=(300, 300))
print(f"Saved: {out_path}  ({canvas.width} x {canvas.height} px)")
