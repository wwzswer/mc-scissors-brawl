# -*- coding: utf-8 -*-
"""补丁 46：真正插入 armorHasAny 定义"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

if 'const armorHasAny' in t:
    print('已存在定义，跳过')
else:
    old = "const armorMax = p => p.armor ? (ITEMS[p.armor].armor||0) : 0;"
    new = ("const armorMax = p => p.armor ? (ITEMS[p.armor].armor||0) : 0;\n"
           "/* 是否持有护甲类物品（不论耐久是否耗尽）—— TNT 的伤害档位用它判定 */\n"
           "const armorHasAny = p => !!(p && p.armor && ITEMS[p.armor] && ITEMS[p.armor].armor);")
    assert old in t, 'armorMax 锚点缺失'
    t = t.replace(old, new, 1)
    IDX.write_text(t, encoding='utf-8')
    print('已插入 armorHasAny 定义')

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
