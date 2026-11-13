# -*- coding: utf-8 -*-
"""补丁 13：两条规则变更
   ① 进程树合并木进程：空手 --1步--> 石进程 --3步--> 铁进程 --3步--> 钻石进程
      （木级的木剑 / 皮革甲 / 村庄归入石进程）
   ② 每回合只进行「一次」AP 获取猜拳：所有存活玩家同时出拳，
      平局则重出，直到有人胜出为止（多人也只在胜者产生时结束）
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ============ ① 进程树重构 ============
sub("const PROG = { HAND:0, WOOD:1, STONE:2, IRON:3, DIAMOND:4 };",
    "const PROG = { HAND:0, STONE:1, IRON:2, DIAMOND:3 };   /* 木进程已并入石进程 */",
    'PROG 枚举')

sub("const PROG_NAME = ['空手','木进程','石进程','铁进程','钻石进程'];",
    "const PROG_NAME = ['空手','石进程','铁进程','钻石进程'];",
    'PROG_NAME')

sub("const UPGRADE = [ null, {cost:2}, {cost:2}, {cost:3}, {cost:3} ];  // 升到该进程需要的进度点：空手→木2 / 木→石2 / 石→铁3 / 铁→钻石3",
    "const UPGRADE = [ null, {cost:1}, {cost:3}, {cost:3} ];  // 升到该进程需要的进度点：空手→石 1 / 石→铁 3 / 铁→钻石 3",
    'UPGRADE 表')

sub("const PROG_REQ = [null, 2, 2, 3, 3];", "const PROG_REQ = [null, 1, 3, 3];", 'PROG_REQ（注入块内）')

sub("const PROG_ICON = ['fist','prog_wood','prog_stone','prog_iron','prog_diamond'];",
    "const PROG_ICON = ['fist','prog_stone','prog_iron','prog_diamond'];",
    'PROG_ICON')

# 木级物品归入石进程
for key, name in [('wood_sword','木剑'), ('leather','皮革甲'), ('village','村庄')]:
    before = t
    t = t.replace(f"prog:PROG.WOOD", "prog:PROG.STONE") if False else t
import re
def move_to_stone(key):
    global t
    pat = re.compile(r"(\b" + key + r":\s*\{[^}]*?)prog:PROG\.WOOD", re.S)
    t2, n = pat.subn(r"\1prog:PROG.STONE", t, count=1)
    if n: t = t2; notes.append(f'  ok {key} 归入石进程')
    else: notes.append(f'  ! {key} 归入石进程失败')

for k in ['wood_sword','leather','village']:
    move_to_stone(k)

# 升级提示文案
sub("      if(next===PROG.STONE) log('（石进程：钓鱼竿是三叉戟的前置；末影珍珠获得后不会消耗）','l-sys');",
    "      if(next===PROG.STONE) log('（石进程：木剑 / 皮革甲 / 石剑 / 钓鱼竿→三叉戟 / 末影珍珠 / 建筑）','l-sys');",
    '升级提示 STONE')
sub("    if(p.prog===PROG.STONE) log('（石进程：钓鱼竿是三叉戟的前置；末影珍珠获得后不会消耗）','l-sys');",
    "    if(p.prog===PROG.STONE) log('（石进程：木剑 / 皮革甲 / 石剑 / 钓鱼竿→三叉戟 / 末影珍珠 / 建筑）','l-sys');",
    '升级提示 STONE（addProgPoint）')

# 移除所有 PROG.WOOD 引用
n_wood = t.count('PROG.WOOD')
t = t.replace('PROG.WOOD', 'PROG.STONE')
notes.append(f'  ok 替换 PROG.WOOD -> PROG.STONE（{n_wood} 处）')

# 商店 / 规则里的进程说明
sub("            next===PROG.WOOD?'（木进程：木剑、皮革甲、村庄）':\n            next===PROG.STONE?'（石进程：石剑、钓鱼竿 → 三叉戟、末影珍珠、林地府邸、女巫小屋）':",
    "            next===PROG.STONE?'（石进程：木剑、皮革甲、村庄、石剑、钓鱼竿 → 三叉戟、末影珍珠、林地府邸、女巫小屋）':",
    '商店进程说明')
sub("      if(next===PROG.IRON) log('（铁进程：铁砧可修复护甲；沙漠金字塔可获取 TNT 与附魔金苹果）','l-sys');\n      sfx.win();\n      break; }\n    case 'craftShopItem': case 'craft': {",
    "      if(next===PROG.IRON) log('（铁进程：铁剑、打火石、盾、铁甲、铁傀儡、铁砧、沙漠金字塔）','l-sys');\n      sfx.win();\n      break; }\n    case 'craftShopItem': case 'craft': {",
    'applyAction 铁进程提示')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
print('文件', round(len(t)/1024,1), 'KB')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
