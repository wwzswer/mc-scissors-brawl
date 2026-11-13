# -*- coding: utf-8 -*-
"""定位：忠诚附魔 / 三叉戟掷出 / 府邸图腾 / 攻击扣AP顺序"""
import pathlib

t = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html').read_text(encoding='utf-8')
js = t.split('<script>')[1].split('</script>')[0]
lines = js.split('\n')

print('=== 1) 忠诚 / 掷出三叉戟 / 拾取 ===')
for i, l in enumerate(lines, 1):
    s = l.strip()
    if ('loyalty' in s) or ('掷出' in s) or ('拾取' in s):
        print(f'  L{i}: {s[:150]}')

print()
print('=== 2) 府邸 → 不死图腾 ===')
i = js.find("case 'craftShopItem': case 'craft':")
seg = js[js.find('function craft('):js.find('function craft(')+1800]
for ln in seg.split('\n'):
    if 'mansion' in ln or 'totem' in ln or 'witchhut' in ln or 'village' in ln:
        print('  ', ln.strip()[:150])

print()
print('=== 3) applyAction 扣 AP 的位置（攻击分支）===')
i2 = js.find('async function applyAction')
seg2 = js[i2:i2+1400]
for ln in seg2.split('\n')[:34]:
    print('  ', ln.rstrip()[:130])
