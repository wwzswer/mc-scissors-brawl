# -*- coding: utf-8 -*-
"""检查各护甲的 armor 值"""
import pathlib, re

t = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html').read_text(encoding='utf-8')
js = t.split('<script>')[1].split('</script>')[0]
print('=== 各护甲的 armor 值 ===')
for k in ['leather', 'iron_armor', 'diamond_armor', 'golem']:
    m = re.search(k + r":\s*\{([^}]*)\}", js, re.S)
    if m:
        am = re.search(r'armor:(\d+)', m.group(1))
        prog = re.search(r'prog:PROG\.(\w+)', m.group(1))
        cost = re.search(r'cost:(\d+)', m.group(1))
        print(f'  {k:<14} armor={am.group(1) if am else "?"}  prog={prog.group(1) if prog else "?"}  cost={cost.group(1) if cost else "?"}')
    else:
        print(f'  {k:<14} 未找到定义')
print()
print('=== armorMax 函数 ===')
i = js.find('const armorMax =')
print(' ', js[i:i+120])
print()
print('=== armorMaxOf 函数 ===')
i = js.find('function armorMaxOf')
print(' ', js[i:i+140])
