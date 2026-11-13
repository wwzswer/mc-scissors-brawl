# -*- coding: utf-8 -*-
"""查明 ITEMS 对象的真实范围，找到正确的插入点"""
import pathlib, re

t = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html').read_text(encoding='utf-8')

i = t.find('const ITEMS = {')
print('const ITEMS 位置:', i)
# 从 ITEMS 起做花括号配对，找到对象结尾
depth = 0
started = False
end = None
for k in range(i, len(t)):
    c = t[k]
    if c == '{':
        depth += 1
        started = True
    elif c == '}':
        depth -= 1
        if started and depth == 0:
            end = k
            break
print('ITEMS 对象结束位置:', end)
print()
print('=== ITEMS 对象内容（前 400 字符）===')
print(t[i:i+400])
print()
print('=== ITEMS 对象内容（后 500 字符）===')
print(t[end-500:end+30])
print()
print('=== 各 key 定义行 ===')
seg = t[i:end]
for m in re.finditer(r'^\s*(\w+):\s*\{\s*name:', seg, re.M):
    print('  ', m.group(1))
