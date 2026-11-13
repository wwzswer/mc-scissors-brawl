# -*- coding: utf-8 -*-
"""定位 rm / rnd 定义并补上缺失的 rnd/rn2"""
import pathlib

P = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = P.read_text(encoding='utf-8')
js = t.split('<script>')[1].split('</script>')[0]

print('=== rm 定义（逐行包含 rm= ）===')
for i, l in enumerate(js.split('\n'), 1):
    if 'rm=' in l.replace(' ', '') and 'const' in l:
        print(f'  L{i}: {l.strip()[:120]}')

print()
print('=== rnd 用法（逐行）===')
for i, l in enumerate(js.split('\n'), 1):
    if 'rnd(' in l:
        print(f'  L{i}: {l.strip()[:120]}')

print()
print('=== 是否已有 rnd 定义 ===')
print('  "function rnd(" 存在:', 'function rnd(' in js)
print('  "rnd =" 存在:', 'rnd =' in js.replace('rnd(', 'X('))
print('  "rn2" 存在:', 'rn2' in js)
