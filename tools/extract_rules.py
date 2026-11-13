# -*- coding: utf-8 -*-
"""从 index.html 提取当前真实规则数值，作为文档校对基准"""
import pathlib, re, json

t = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html').read_text(encoding='utf-8')
js = t.split('<script>')[1].split('</script>')[0]

print('=== 关键常量 ===')
for name in ['PROG', 'PROG_NAME', 'UPGRADE', 'MAX_DIST', 'ATK_COST', 'CONSUME_COST',
             'ROD_COST', 'MOVE_COST', 'BUILD_COST']:
    m = re.search(r'const ' + name + r'\s*=\s*([^;]+);', js)
    print(f'  {name:<12} = {m.group(1).strip()[:90] if m else "?"}')
m = re.search(r'let apPerWin\s*=\s*(\d+)', js)
print(f'  apPerWin     = {m.group(1) if m else "?"}')
m = re.search(r'let gameMode\s*=\s*[\'"]([\w]+)', js)
print(f'  gameMode 默认 = {m.group(1) if m else "?"}')

print()
print('=== ITEMS 全表 ===')
for m in re.finditer(r"(\w+):\s*\{\s*name:'([^']+)'([^}]*)\}", js):
    key, name, body = m.group(1), m.group(2), m.group(3)
    if key.isupper():
        continue
    c = re.search(r'cost:(\d+)', body)
    prog = re.search(r'prog:PROG\.(\w+)', body)
    build = 'BUILD' if 'build:true' in body else ''
    rep = 'repeat' if 'repeat:true' in body else ''
    mx = re.search(r'max:(\d+)', body)
    arm = re.search(r'armor:(\d+)', body)
    need = re.search(r"need:'(\w+)'", body)
    info = []
    if c: info.append('cost=' + c.group(1))
    if prog: info.append('prog=' + prog.group(1))
    if arm: info.append('armor=' + arm.group(1))
    if build: info.append(build)
    if rep: info.append(rep)
    if mx: info.append('max=' + mx.group(1))
    if need: info.append('need=' + need.group(1))
    print(f'  {key:<16} {name:<8} {" ".join(info)}')

print()
print('=== ENCH 附魔全表 ===')
for m in re.finditer(r"(\w+):\s*\{\s*name:'([^']+)'([^}]*)\}", js):
    key, name, body = m.group(1), m.group(2), m.group(3)
    if 'apply:' not in body:
        continue
    ap = re.search(r"apply:\[([^\]]*)\]", body)
    desc = re.search(r"desc:'([^']*)'", body)
    print(f'  {key:<14} {name:<8} apply=[{ap.group(1) if ap else "?"}]')
    if desc: print(f'      desc: {desc.group(1)[:100]}')

print()
print('=== SPECIALS ===')
i = js.find('const SPECIALS')
if i >= 0:
    seg = js[i:i+1400]
    for m in re.finditer(r"(\w+):\s*\{\s*name:'([^']+)'[^}]*desc:'([^']*)'", seg):
        print(f'  {m.group(1):<14} {m.group(2)}: {m.group(3)[:95]}')

print()
print('=== 各武器伤害（attackProfile 表）===')
i = js.find('const base = {')
if i >= 0:
    print(' ', js[i:js.find('}[key]', i)+5].replace('\n', ' ')[:400])
