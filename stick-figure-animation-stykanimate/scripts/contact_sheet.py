"""Tile rendered frames into one image for review.  Usage: python3 contact_sheet.py <frames_dir> <out.png> [cols]"""
import glob, os, sys
from PIL import Image, ImageDraw

frames = sorted(glob.glob(os.path.join(sys.argv[1], 'f*.png')))
if not frames:
    sys.exit('no frames found')
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
w0, h0 = Image.open(frames[0]).size
w = 480 if w0 >= h0 else 320
h = round(w * h0 / w0)
rows = (len(frames) + cols - 1) // cols
sheet = Image.new('RGB', (w * cols, h * rows), 'white')
for k, f in enumerate(frames):
    im = Image.open(f).convert('RGB').resize((w, h))
    ImageDraw.Draw(im).text((6, 6), os.path.basename(f), fill=(226, 35, 38))
    sheet.paste(im, ((k % cols) * w, (k // cols) * h))
sheet.save(sys.argv[2])
print(sys.argv[2])
