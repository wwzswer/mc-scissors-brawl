# -*- coding: utf-8 -*-
"""检查各物品的 cost / repeat / max 配置"""
import pathlib, re

t = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html').read_text(encoding='utf-8')
js = t.split('<script>')[1].split('</script>')[0]

keys = ['trident','fishing_rod','village','diamond_armor','iron_armor','golem','flesh','bread','flint',
        'shield','firework','crossbow','diamond_sword','iron_sword','stone_sword','wood_sword','leather',
        'ender_pearl','tnt','anvil','mansion','witchhut','pyramid','fist']

print('=== 物品配置 ===')
for k in keys:
    m = re.search(k + r":\s*\{([^}]*)\}", js, re.S)
    if not m:
        print(f'  {k:<15} 未找到')
        continue
    body = m.group(1)
    c = re.search(r'cost:(\d+)', body)
    rep = re.search(r'repeat:(true|false)', body)
    mx = re.search(r'max:(\d+)', body)
    bl = 'BUILD' if 'build:true' in body else ''
    prog = re.search(r'prog:PROG\.(\w+)', body)
    print(f'  {k:<15} cost={c.group(1) if c else "?":<3} {bl:<6} repeat={rep.group(1) if rep else "-":<5} max={mx.group(1) if mx else "-":<3} prog={prog.group(1) if prog else "-"}')

print()
print('=== buildAllowed 实现（村庄 max:1 的影响）===')
i = js.find('function buildAllowed')
print(js[i:i+420] if i >= 0 else '未找到')

print()
print('=== 火焰/腐肉的伤害类型 ===')
for i2, l in enumerate(js.split('\n'), 1):
    if 'burnTicks' in l or "prof.burn" in l or 'bleed' in l:
        print(f'  L{i2}: {l.strip()[:130]}')
