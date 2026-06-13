from PIL import Image, ImageDraw
img = Image.open("assets/retro_gui.png")
draw = ImageDraw.Draw(img)

# Title bar text
draw.rectangle([350, 150, 750, 190], fill=(45, 45, 45))

# Prompt path text
draw.rectangle([190, 330, 850, 380], fill=(30, 30, 30))

img.save("assets/retro_gui.png")
