from PIL import Image, ImageDraw, ImageFont

size = 256
img = Image.new('RGB', (size, size), (30, 58, 95))
draw = ImageDraw.Draw(img)

# Cercle extérieur
margin = size//8
draw.ellipse([margin, margin, size-margin, size-margin],
             outline=(244, 208, 63), width=size//20)

# Texte "DB"
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf", size//3)
except:
    font = ImageFont.load_default()
text = "DB"
bbox = draw.textbbox((0,0), text, font=font)
tw = bbox[2]-bbox[0]
th = bbox[3]-bbox[1]
x = (size - tw)//2
y = (size - th)//2 - size//16
draw.text((x, y), text, fill=(255,255,255), font=font)

# Ligne
line_y = y + th + size//12
draw.rectangle([size//4, line_y, 3*size//4, line_y+size//20], fill=(244,208,63))

img.save("logo.png")
print("Icône logo.png créée")
