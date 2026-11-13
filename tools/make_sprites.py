# -*- coding: utf-8 -*-
"""把 MC素材 整理成游戏用的贴图：统一命名、缩放、合成雪碧图、导出 base64。

- 统一缩放到 96x96（像素风用 NEAREST，避免糊）
- 素材缺失的物品用 PIL 画一个像素风图标补位
- 输出 atlas.png（单张雪碧图，减少内联体积）+ 每个图标的坐标
- 最终写 sprites.js（含 data URI 与坐标表）
"""
import base64, io, json, pathlib
from PIL import Image, ImageDraw

ROOT = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
SRC  = ROOT / 'assets' / 'MC素材'
OUT  = ROOT / 'assets' / 'sprites'
OUT.mkdir(parents=True, exist_ok=True)
CELL = 96

# 素材文件名 -> 游戏内部 key
MAP = {
    '木剑.png':'wood_sword', '石剑.png':'stone_sword', '铁剑.png':'iron_sword',
    '钻石剑.png':'diamond_sword', '三叉戟.png':'trident', '钓鱼竿.png':'fishing_rod',
    '末影珍珠.png':'ender_pearl', 'TNT.png':'tnt', '打火石.png':'flint',
    '烟花火箭.png':'firework', '不死图腾.png':'totem',
    '弩（未装填）.png':'crossbow', '弩（箭）.png':'crossbow_loaded', '弩(烟花）.png':'crossbow_firework',
    '弓.png':'bow',
    '皮革甲.jpg':'leather', '铁甲.jpg':'iron_armor', '钻石甲.jpg':'diamond_armor',
    '盾.png':'shield', '铁傀儡.jpg':'golem', '铁砧.png':'anvil', '避雷针.png':'lightning_rod',
    '腐肉.png':'flesh', '面包.jpg':'bread', '附魔金苹果.gif':'god_apple',
    '村庄.png':'village', '林地府邸.png':'mansion', '沼泽小屋.png':'witchhut',
    '沙漠神殿.png':'pyramid', '水.png':'water',
    '木进程.png':'prog_wood', '石进程.png':'prog_stone', '铁进程.png':'prog_iron',
    '钻石进程.png':'prog_diamond', '铜进程.png':'prog_copper',
}
# 补齐：素材里没有的图标
DRAW = ['fist', 'potion', 'potion_heal', 'potion_str', 'potion_swift',
        'arrow', 'rock', 'scissors', 'paper', 'star', 'heart', 'coin']

def load(name):
    im = Image.open(SRC / name)
    if getattr(im, 'n_frames', 1) > 1:       # 动画取第一帧
        im.seek(0)
    im = im.convert('RGBA')
    return im

def strip_bg(im, tol=46, passes=2, edge_tol=None):
    """去掉白/浅灰底：从四边泛洪（用较宽的 edge_tol 吃掉浅灰阴影）
       + 清除内部小块纯白（凹槽里露出的背景）"""
    w, h = im.size
    px = im.load()
    from collections import deque
    et = tol if edge_tol is None else edge_tol
    def bgish(p, t):
        r, g, b, a = p
        if a == 0: return True
        mx, mn = max(r, g, b), min(r, g, b)
        return mx >= 255-t and (mx-mn) <= t
    for _ in range(passes):
        seen = bytearray(w*h)
        q = deque()
        for x in range(w):
            for y in (0, h-1):
                if not seen[y*w+x] and bgish(px[x, y], et): seen[y*w+x] = 1; q.append((x, y))
        for y in range(h):
            for x in (0, w-1):
                if not seen[y*w+x] and bgish(px[x, y], et): seen[y*w+x] = 1; q.append((x, y))
        while q:
            x, y = q.popleft()
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 0)
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = x+dx, y+dy
                if 0 <= nx < w and 0 <= ny < h and not seen[ny*w+nx] and bgish(px[nx, ny], et):
                    seen[ny*w+nx] = 1; q.append((nx, ny))
    # 内部小块纯白（面积 < 1.5% 的纯白连通块）也清掉：这些通常是凹槽露出的背景
    limit = max(60, int(w*h*0.015))
    seen = bytearray(w*h)
    for sy in range(h):
        for sx in range(w):
            if seen[sy*w+sx] or not bgish(px[sx, sy], 18): continue
            comp = []; q = deque([(sx, sy)]); seen[sy*w+sx] = 1
            while q:
                x, y = q.popleft(); comp.append((x, y))
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny*w+nx] and bgish(px[nx, ny], 18):
                        seen[ny*w+nx] = 1; q.append((nx, ny))
            if len(comp) < limit:
                for x, y in comp:
                    r, g, b, a = px[x, y]
                    px[x, y] = (r, g, b, 0)
    return im

def edge_halo_clean(im, rings=2, tol=52):
    """缩放后清掉最外圈残留的白/灰halo（只动边缘，不碰内部高光）"""
    w, h = im.size
    px = im.load()
    def whitish(p):
        r, g, b, a = p
        if a < 40: return False
        mx, mn = max(r, g, b), min(r, g, b)
        return mx >= 255-tol and (mx-mn) <= tol
    for ring in range(rings):
        coords = []
        for i in range(ring, w-ring):
            coords.append((i, ring)); coords.append((i, h-1-ring))
        for j in range(ring, h-ring):
            coords.append((ring, j)); coords.append((w-1-ring, j))
        cleared = 0
        for x, y in coords:
            if whitish(px[x, y]):
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, 0); cleared += 1
        if cleared == 0: break
    return im

def fit(im, crop=True):
    """裁掉透明边 → 等比放进 CELLxCELL 画布（像素风用 NEAREST）"""
    if crop:
        bbox = im.getbbox()
        if bbox: im = im.crop(bbox)
    w, h = im.size
    s = CELL / max(w, h)
    nw, nh = max(1, round(w*s)), max(1, round(h*s))
    im = im.resize((nw, nh), Image.NEAREST)
    canvas = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    canvas.paste(im, ((CELL-nw)//2, (CELL-nh)//2), im)
    return edge_halo_clean(canvas)

def px(d, x, y, n, color):
    d.rectangle([x*4, y*4, (x+n)*4-1, (y+n)*4-1], fill=color)

def draw_icon(key):
    """12x12 像素网格上手绘图标（放大到 96x96）"""
    im = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    SKIN=(233,190,148,255); SKIN2=(198,152,112,255); W=(255,255,255,255)
    GOLD=(255,205,60,255); GLASS=(210,235,255,255); RED=(215,60,60,255)
    GRN=(80,200,110,255); BLU=(90,150,255,255); GRY=(160,165,175,255)
    DRK=(60,64,74,255); PUR=(170,90,220,255); BRW=(150,105,60,255)
    if key == 'fist':                      # 握拳（正面，四指 + 拇指）
        px(d, 3, 3, 6, SKIN2)              # 指根阴影
        px(d, 3, 4, 6, SKIN)
        for i in range(6):                  # 四指分缝
            px(d, 3+i, 4, 1, SKIN)
        px(d, 3, 4, 6, SKIN)
        for i in (4, 5, 6, 7):              # 指缝
            px(d, i, 5, 1, SKIN2); px(d, i, 6, 1, SKIN2)
        px(d, 3, 7, 6, SKIN)
        px(d, 2, 5, 1, SKIN2); px(d, 9, 5, 1, SKIN2)   # 手掌两侧
        px(d, 3, 8, 6, SKIN2); px(d, 4, 9, 4, SKIN2)   # 手腕
    elif key == 'paper':
        px(d, 2, 2, 8, (245,245,240,255))  # 纸张
        px(d, 2, 2, 8, (250,250,245,255))
        px(d, 2, 2, 1, (200,205,215,255)); px(d, 9, 2, 1, (200,205,215,255))
        px(d, 2, 9, 8, (200,205,215,255))
        for i in (4, 6, 8):                 # 折痕
            px(d, 3, i, 6, (205,210,220,255))
    elif key == 'arrow':
        px(d, 5, 1, 2, W); px(d, 4, 3, 4, W); px(d, 3, 4, 6, W); px(d, 5, 5, 2, BRW); px(d, 5, 7, 2, BRW); px(d, 5, 9, 2, GRY)
    elif key == 'rock':
        px(d, 3, 3, 6, GRY); px(d, 2, 4, 8, GRY); px(d, 4, 2, 4, GRY); px(d, 3, 4, 2, W); px(d, 2, 9, 8, DRK)
    elif key == 'scissors':
        px(d, 3, 1, 2, GRY); px(d, 7, 1, 2, GRY); px(d, 4, 3, 2, GRY); px(d, 6, 3, 2, GRY)
        px(d, 5, 5, 2, GRY); px(d, 4, 7, 4, GRY); px(d, 3, 9, 2, RED); px(d, 7, 9, 2, RED)
    elif key == 'star':
        px(d, 5, 1, 2, GOLD); px(d, 4, 3, 4, GOLD); px(d, 2, 4, 8, GOLD); px(d, 3, 5, 6, GOLD)
        px(d, 3, 7, 2, GOLD); px(d, 7, 7, 2, GOLD); px(d, 4, 8, 1, GOLD); px(d, 7, 8, 1, GOLD)
    elif key == 'heart':
        px(d, 2, 3, 3, RED); px(d, 7, 3, 3, RED); px(d, 2, 4, 8, RED); px(d, 3, 5, 6, RED)
        px(d, 4, 6, 4, RED); px(d, 5, 7, 2, RED); px(d, 3, 4, 2, (255,140,140,255))
    elif key == 'coin':
        px(d, 3, 2, 6, GOLD); px(d, 2, 3, 8, GOLD); px(d, 4, 4, 4, (255,240,170,255)); px(d, 2, 9, 8, (200,150,30,255))
    elif key in ('potion', 'potion_heal', 'potion_str', 'potion_swift'):
        col = {'potion_heal':RED, 'potion_str':(200,70,70,255), 'potion_swift':BLU}.get(key, GRN)
        px(d, 5, 1, 2, GRY); px(d, 4, 3, 4, GRY)
        d.rectangle([3*4, 4*4, 9*4-1, 11*4-1], fill=col, outline=GLASS)
        px(d, 4, 5, 4, tuple(min(255,c+40) for c in col[:3])+(255,))
    return im

# 需要抠掉白底/灰底的素材（这些是 jpg 或带纯色底的图）
NEED_STRIP = {'皮革甲.jpg', '铁甲.jpg', '钻石甲.jpg', '铁傀儡.jpg', '村庄.png',
              '林地府邸.png', '沼泽小屋.png', '沙漠神殿.png', '避雷针.png', '水.png'}
# 这些素材的底是浅灰（带阴影），边缘容差要放宽
WIDE_TOL = {'铁甲.jpg': 72, '钻石甲.jpg': 72, '皮革甲.jpg': 72, '铁傀儡.jpg': 68,
            '村庄.png': 60, '林地府邸.png': 60, '沼泽小屋.png': 60, '沙漠神殿.png': 60}

# ---------- 载入 / 绘制 ----------
tiles = {}
for fn, key in MAP.items():
    p = SRC / fn
    if not p.exists():
        print(f'  ! 缺少素材 {fn}')
        continue
    im = load(fn)
    if fn in NEED_STRIP:
        before = im.getbbox()
        im = strip_bg(im, edge_tol=WIDE_TOL.get(fn))
        print(f'  抠底 {fn} -> {key}  bbox {before} -> {im.getbbox()}')
    tiles[key] = fit(im)
for key in DRAW:
    if key not in tiles:
        tiles[key] = draw_icon(key)

# ---------- 合成雪碧图 ----------
keys = sorted(tiles.keys())
cols = 8
rows = (len(keys) + cols - 1) // cols
atlas = Image.new('RGBA', (cols*CELL, rows*CELL), (0, 0, 0, 0))
coords = {}
for i, k in enumerate(keys):
    cx, cy = (i % cols)*CELL, (i // cols)*CELL
    atlas.paste(tiles[k], (cx, cy), tiles[k])
    coords[k] = [cx, cy, CELL, CELL]

atlas.save(OUT / 'atlas.png')
for k, im in tiles.items():
    im.save(OUT / f'{k}.png')

buf = io.BytesIO()
atlas.save(buf, 'PNG', optimize=True)
raw = buf.getvalue()
b64 = base64.b64encode(raw).decode('ascii')
print(f'雪碧图: {atlas.size}  图标数 {len(keys)}  优化后 {len(raw)/1024:.1f} KB  base64 {len(b64)/1024:.1f} KB')

js = (
    '/* 由 tools/make_sprites.py 自动生成：MC 素材贴图（雪碧图 + 坐标 + 内联 data URI） */\n'
    'const SPRITE_SHEET = "' + b64 + '";\n'
    'const SPRITE_CELL = ' + str(CELL) + ';\n'
    'const SPRITE_POS = ' + json.dumps(coords, ensure_ascii=False) + ';\n'
)
(OUT / 'sprites.js').write_text(js, encoding='utf-8')
print('已写 assets/sprites/sprites.js')
print('图标 key:', ', '.join(keys))
