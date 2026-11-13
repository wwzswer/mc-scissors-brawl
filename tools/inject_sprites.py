# -*- coding: utf-8 -*-
"""把贴图（雪碧图 data URI）注入 index.html：
   - 在脚本开头插入 SPRITE_SHEET / SPRITE_POS
   - 在 CSS 里追加 .spr 基类
   - 在脚本里插入 sprStyle() / sprTag() / 图标映射表
可重复执行（先移除旧注入块再插）。
"""
import base64, io, json, pathlib, re
from PIL import Image

ROOT = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = ROOT / 'index.html'
SPR = ROOT / 'assets' / 'sprites'

atlas = Image.open(SPR / 'atlas.png')
buf = io.BytesIO(); atlas.save(buf, 'PNG', optimize=True)
b64 = base64.b64encode(buf.getvalue()).decode('ascii')
coords = json.loads((SPR / 'sprites.js').read_text(encoding='utf-8').split('const SPRITE_POS = ')[1].split(';\n')[0])

BEGIN = '/* ===== SPRITES:BEGIN (由 tools/inject_sprites.py 生成，勿手改) ===== */'
END   = '/* ===== SPRITES:END ===== */'

block = f"""{BEGIN}
const SPRITE_SHEET = "data:image/png;base64,{b64}";
const ATLAS_W = {atlas.size[0]}, ATLAS_H = {atlas.size[1]};
const SPRITE_POS = {json.dumps(coords, ensure_ascii=False)};
/* 物品 / 武器 / 护甲 / 建筑 / 进程 / 状态 图标 key */
const ICON = {{
  fist:'fist', flesh:'flesh', bread:'bread',
  wood_sword:'wood_sword', leather:'leather', village:'village',
  stone_sword:'stone_sword', fishing_rod:'fishing_rod', ender_pearl:'ender_pearl',
  trident:'trident', mansion:'mansion', witchhut:'witchhut',
  iron_sword:'iron_sword', flint:'flint', shield:'shield', iron_armor:'iron_armor',
  golem:'golem', anvil:'anvil', pyramid:'pyramid',
  crossbow:'crossbow', diamond_sword:'diamond_sword', firework:'firework',
  diamond_armor:'diamond_armor',
  tnt:'tnt', god_apple:'god_apple', totem:'totem',
  potion_heal:'potion_heal', potion_str:'potion_str', potion_swift:'potion_swift', potion:'potion',
  lightning_rod:'lightning_rod', bow:'bow', arrow:'arrow',
  rock:'rock', scissors:'scissors', paper:'paper', star:'star', heart:'heart', coin:'coin', water:'water',
}};
const PROG_ICON = ['fist','prog_wood','prog_stone','prog_iron','prog_diamond'];
/* 进程 -> 该级升级需要的进度点（与 UPGRADE 的 cost 对应） */
const PROG_REQ = [null, 2, 2, 3, 3];
function sprStyle(key, size){{
  const p = SPRITE_POS[key]; if(!p) return '';
  const s = size || 32, k = s / p[2];
  return `background-image:url(${{SPRITE_SHEET}});background-position:${{-p[0]*k}}px ${{-p[1]*k}}px;` +
         `background-size:${{ATLAS_W*k}}px ${{ATLAS_H*k}}px;width:${{s}}px;height:${{s}}px;`;
}}
function sprTag(key, size, cls){{
  const s = size || 32;
  return `<i class="spr ${{cls||''}}" style="${{sprStyle(key, s)}}"></i>`;
}}
function itemIcon(key){{ return ICON[key] || null; }}
{END}"""

html = IDX.read_text(encoding='utf-8')
# 移除旧注入
html = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), '', html, flags=re.S)

# 1) 脚本开头插入（在第一个 const PROG 之前）
anchor = 'const PROG = {'
assert anchor in html, '找不到注入锚点'
html = html.replace(anchor, block + '\n\n' + anchor, 1)

# 2) CSS 追加 .spr 基类
css_anchor = '.hidden{display:none !important}'
spr_css = """
/* 贴图基类（雪碧图定位由行内样式给出） */
.spr{display:inline-block;vertical-align:middle;background-repeat:no-repeat;border-radius:3px;
  image-rendering:pixelated;flex:0 0 auto}
.spr.lg{transform:translateY(-1px)}
.iconline{display:flex;align-items:center;gap:6px}
"""
if spr_css.strip() not in html:
    html = html.replace(css_anchor, css_anchor + spr_css, 1)

IDX.write_text(html, encoding='utf-8')
print(f'注入完成：贴图 {len(b64)/1024:.1f} KB(base64)，index.html 现 {len(html)/1024:.1f} KB')
print('图标 key 数:', len(coords))
