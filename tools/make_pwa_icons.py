# -*- coding: utf-8 -*-
"""
生成 PWA 图标（方块猜拳战场）
  等距 Minecraft 草方块 + 底部三色猜拳小方块，暗色背景，纯 PIL 绘制、可重复生成
输出：icon-192.png / icon-512.png / icon-maskable-512.png / apple-touch-icon-180.png
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE) if os.path.basename(HERE) == 'tools' else HERE

BG      = (14, 17, 22)
PANEL   = (27, 33, 48)
LINE    = (46, 56, 80)
GRASS   = (110, 200, 96)
GRASS_D = (78, 150, 68)
DIRT    = (138, 96, 62)
DIRT_D  = (104, 71, 45)
AMBER   = (240, 195, 74)
BLUE    = (92, 200, 255)
MINT    = (110, 231, 168)

S = 1024                      # 先画大的，最后缩小到目标尺寸（抗锯齿）
def sc(*pts):                 # 相对坐标 -> 像素
    return [(p[0] * S, p[1] * S) for p in pts]

def draw_icon(size, maskable=False):
    img = Image.new('RGBA', (S, S), BG)
    d = ImageDraw.Draw(img)

    # 背景：柔和径向（大圆 + 模糊模拟）
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-S * 0.25, -S * 0.45, S * 1.05, S * 0.75], fill=(35, 48, 78, 255))
    gd.ellipse([S * 0.35, -S * 0.5, S * 1.4, S * 0.5], fill=(58, 42, 66, 200))
    img = Image.alpha_composite(img, glow.filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(S // 12)))
    d = ImageDraw.Draw(img)

    # maskable 版本要留安全区：整图缩到 78%
    k = 0.78 if maskable else 1.0
    def pts(P):
        cx, cy = S / 2, S / 2
        return [((x - cx) * k + cx, (y - cy) * k + cy) for (x, y) in P]

    cx, cy = 0.5, 0.455
    w = 0.30          # 半个宽
    h = 0.17          # 顶面半高
    body = 0.29       # 侧面高度

    top  = pts(sc((cx, cy - h - 0.02), (cx + w, cy - 0.02), (cx, cy + h - 0.02), (cx - w, cy - 0.02)))
    left = pts(sc((cx - w, cy - 0.02), (cx, cy + h - 0.02), (cx, cy + h - 0.02 + body), (cx - w, cy - 0.02 + body)))
    right= pts(sc((cx + w, cy - 0.02), (cx, cy + h - 0.02), (cx, cy + h - 0.02 + body), (cx + w, cy - 0.02 + body)))

    # 描边 + 三面
    d.polygon(left,  fill=DIRT_D, outline=LINE)
    d.polygon(right, fill=DIRT,   outline=LINE)
    d.polygon(top,   fill=GRASS_D, outline=LINE)

    # 顶面草皮高光（内缩一圈）
    d.polygon(pts(sc((cx, cy - h + 0.03), (cx + w * 0.82, cy + 0.0), (cx, cy + h - 0.04), (cx - w * 0.82, cy + 0.0))),
              fill=GRASS)

    # 侧面草边（泥土上方的一条绿）
    d.polygon(pts(sc((cx - w, cy - 0.02), (cx, cy + h - 0.02), (cx, cy + h + 0.05), (cx - w, cy + 0.05))),
              fill=(96, 172, 80))
    d.polygon(pts(sc((cx + w, cy - 0.02), (cx, cy + h - 0.02), (cx, cy + h + 0.05), (cx + w, cy + 0.05))),
              fill=(84, 152, 70))

    # 底部三个猜拳小方块（石头/剪刀/布）
    y0, sq, gap = 0.848, 0.062, 0.030
    step = 2 * sq + gap
    xs = [cx - step, cx, cx + step]
    for x, col in zip(xs, (MINT, AMBER, BLUE)):
        d.rounded_rectangle([(x - sq) * S * 1.0 * (1 if not maskable else 1),
                             (y0 - sq) * S,
                             (x + sq) * S,
                             (y0 + sq) * S], radius=S * 0.016, fill=col, outline=LINE)
    img = img.resize((size, size), Image.LANCZOS)
    return img.convert('RGB')

def main():
    targets = [
        ('icon-192.png', 192, False),
        ('icon-512.png', 512, False),
        ('icon-maskable-512.png', 512, True),
        ('apple-touch-icon-180.png', 180, False),
    ]
    for name, size, maskable in targets:
        p = os.path.join(OUT, name)
        draw_icon(size, maskable).save(p, 'PNG', optimize=True)
        print('wrote', name, size, os.path.getsize(p), 'bytes')

if __name__ == '__main__':
    main()
