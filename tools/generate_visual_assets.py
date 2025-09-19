from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

IMG_DIR = Path('assets/images')
IMG_DIR.mkdir(parents=True, exist_ok=True)

COLORS = {
    'bg_top': (0x1E, 0x2A, 0x78),
    'bg_bottom': (0x14, 0x0C, 0x34),
    'accent': (0xFF, 0xD1, 0x66, 72),
    'player_fill': (0x4E, 0xCD, 0xC4, 255),
    'player_outline': (0x07, 0x3B, 0x4C, 255),
    'player_hilight': (255, 255, 255, 40),
    'ball_colors': [
        ((0xFF, 0xD1, 0x66), (255, 255, 255, 90)),
        ((0xF8, 0x96, 0x1E), (255, 255, 255, 80)),
        ((0xF3, 0x72, 0x2C), (255, 255, 255, 70)),
    ],
    'mute_fill': (0xFF, 0xD1, 0x66, 255),
    'unmute_fill': (0x06, 0xD6, 0xA0, 255),
}

def lerp_color(start, end, t):
    return tuple(int(s + (e - s) * t) for s, e in zip(start, end))

def make_background():
    size = (800, 600)
    vertical = Image.new('RGB', (1, size[1]))
    for y in range(size[1]):
        ratio = y / (size[1] - 1)
        vertical.putpixel((0, y), lerp_color(COLORS['bg_top'], COLORS['bg_bottom'], ratio))
    vertical = vertical.resize(size)

    horizontal = Image.new('RGB', (size[0], 1))
    for x in range(size[0]):
        t = x / (size[0] - 1)
        horizontal.putpixel((x, 0), lerp_color((10, 12, 42), (24, 28, 88), t))
    horizontal = horizontal.resize(size)

    bg = Image.blend(vertical, horizontal, 0.3).convert('RGBA')

    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((-200, 200, 400, 800), fill=COLORS['accent'])
    draw.ellipse((300, -250, 900, 350), fill=COLORS['accent'])
    draw.ellipse((500, 200, 1000, 700), fill=(255, 107, 107, 56))
    overlay = overlay.filter(ImageFilter.GaussianBlur(45))

    final = Image.alpha_composite(bg, overlay)
    final.save(IMG_DIR / 'bg_layer.png')


def make_player():
    size = 48
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    padding = 4
    rect = (padding, padding, size - padding, size - padding)
    draw.rounded_rectangle(rect, radius=10, fill=COLORS['player_fill'], outline=COLORS['player_outline'], width=4)

    highlight = Image.new('RGBA', img.size, (0, 0, 0, 0))
    h_draw = ImageDraw.Draw(highlight)
    h_draw.polygon([(padding + 4, padding + 4), (size - padding, padding + 12), (size - padding, padding + 4)], fill=COLORS['player_hilight'])
    h_draw.pieslice((padding + 6, padding + 6, size - padding - 2, size - padding - 2), start=200, end=300, fill=(255, 255, 255, 30))
    highlight = highlight.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, highlight)

    img.save(IMG_DIR / 'player_base.png')


def make_balls():
    diameters = [24, 32, 40]
    for (base_color, highlight_color), diameter in zip(COLORS['ball_colors'], diameters):
        size = diameter + 8
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        bbox = (4, 4, size - 4, size - 4)
        draw.ellipse(bbox, fill=base_color)

        hi = Image.new('RGBA', img.size, (0, 0, 0, 0))
        hi_draw = ImageDraw.Draw(hi)
        hi_draw.pieslice((6, 6, size // 2 + 8, size // 2 + 8), start=200, end=320, fill=highlight_color)
        hi = hi.filter(ImageFilter.GaussianBlur(3))
        img = Image.alpha_composite(img, hi)

        shadow = Image.new('RGBA', img.size, (0, 0, 0, 0))
        sh_draw = ImageDraw.Draw(shadow)
        sh_draw.ellipse((4, 4, size - 4, size - 4), outline=(0, 0, 0, 70), width=2)
        img = Image.alpha_composite(img, shadow)

        name = {24: 'ball_small.png', 32: 'ball_medium.png', 40: 'ball_large.png'}[diameter]
        img.save(IMG_DIR / name)


def make_icons():
    size = 48
    for muted in (True, False):
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        fill = COLORS['mute_fill'] if muted else COLORS['unmute_fill']
        body = [(12, 18), (22, 18), (32, 10), (32, 38), (22, 30), (12, 30)]
        draw.polygon(body, fill=fill)
        draw.line([(12, 18), (12, 30)], fill=(10, 10, 10, 120), width=3)
        if muted:
            draw.line([(10, 12), (38, 36)], fill=(255, 107, 107, 220), width=5)
            draw.line([(38, 12), (10, 36)], fill=(255, 107, 107, 220), width=5)
        else:
            draw.arc((28, 12, 44, 36), start=315, end=45, fill=(255, 255, 255, 200), width=4)
            draw.arc((24, 8, 48, 40), start=312, end=48, fill=(255, 255, 255, 120), width=3)
        name = 'icon_mute.png' if muted else 'icon_unmute.png'
        img.save(IMG_DIR / name)


def main():
    make_background()
    make_player()
    make_balls()
    make_icons()
    print('Generated visual assets in', IMG_DIR)

if __name__ == '__main__':
    main()
