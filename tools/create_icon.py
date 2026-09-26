from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
out = root / "resources" / "icon.ico"
out.parent.mkdir(parents=True, exist_ok=True)

size = 256
img = Image.new("RGBA", (size, size), (13, 17, 23, 255))
draw = ImageDraw.Draw(img)
draw.rounded_rectangle(
    (28, 38, 228, 208),
    radius=18,
    outline=(88, 166, 255, 255),
    width=10,
)
draw.line((48, 78, 208, 78), fill=(48, 54, 61, 255), width=6)
draw.polygon([(78, 112), (116, 133), (78, 154)], fill=(63, 185, 80, 255))
draw.line((126, 156, 184, 156), fill=(230, 237, 243, 255), width=8)
draw.ellipse((172, 92, 222, 142), outline=(248, 81, 73, 255), width=8)
draw.line((197, 83, 197, 151), fill=(248, 81, 73, 255), width=5)
draw.line((163, 117, 231, 117), fill=(248, 81, 73, 255), width=5)
img.save(
    out,
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(out)
