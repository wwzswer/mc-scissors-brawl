# -*- coding: utf-8 -*-
"""核对 5 项失败：区分检查脚本误报 vs 真实缺失"""
import pathlib, re

ROOT = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
idx = (ROOT / 'index.html').read_text(encoding='utf-8')
js = idx.split('<script>')[1].split('</script>')[0]
srv = (ROOT / 'server.js').read_text(encoding='utf-8')

print('【1】SPRITE_POS 实际内容')
m = re.search(r'const SPRITE_POS = ', js)
seg = js[m.end():m.end()+180] if m else ''
print('  片段:', seg[:170].replace('\n',' '))
keys = re.findall(r'"([a-z_0-9]+)":\s*\[', js)
print('  图标 key 数（宽松正则）:', len(set(keys)))

print('\n【4】server 接口字符串')
for s in ['/api/create', '/api/room/', "'join'", '"/api/create"', "sub === 'join'"]:
    print(f'  {s!r:26} -> {srv.count(s)} 次')

print('\n【5】猜拳加 AP 的实际写法')
for mm in re.finditer(r'.*ap\s*\+=\s*apPerWin.*', js):
    print('  ', mm.group(0).strip()[:120])

print('\n【8】规则分页定义')
i = js.find('const RULE_PAGES')
print(js[i:i+420] if i>=0 else '  未找到 RULE_PAGES')

print('\n【8】规则页物品条目渲染')
for mm in re.finditer(r'.*itemRow.*', js):
    print('  ', mm.group(0).strip()[:120])
i2 = js.find('function itemRow')
print('  itemRow 定义:', js[i2:i2+200].replace('\n',' ') if i2>=0 else '未找到')
