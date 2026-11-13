# -*- coding: utf-8 -*-
"""精确查找 rnd / pick 的定义"""
import pathlib

P = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = P.read_text(encoding='utf-8')
js = t.split('<script>')[1].split('</script>')[0]

# 直接找 "rnd" 的每一处出现及其上下文
key = 'rnd'
idx = 0
print('=== 所有 rnd 出现处（含上下文 40 字符）===')
while True:
    i = js.find(key, idx)
    if i < 0:
        break
    ctx = js[max(0, i-45):i+45].replace('\n', ' ⏎ ')
    print(f'  @{i}: ...{ctx}...')
    idx = i + 1

print()
print('=== pick 定义 ===')
i = js.find('const pick')
print(' ', js[i:i+120] if i >= 0 else '未找到')
i2 = js.find('function pick')
print(' ', js[i2:i2+120] if i2 >= 0 else '(无 function pick)')
