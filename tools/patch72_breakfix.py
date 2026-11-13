# -*- coding: utf-8 -*-
"""补丁 72：tryDamage 传入真正破损的护甲件"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

old = "      breakArmor(target);"
new = "      breakArmor(target, res.broke);          /* 明确指定破损件，避免误清下一件护甲 */"

if old in t:
    n = t.count(old)
    t = t.replace(old, new)
    IDX.write_text(t, encoding='utf-8')
    print(f'已修改 breakArmor 调用 {n} 处')
else:
    print('! 未找到 breakArmor(target) 调用')

# 同时检查其它把 breakArmor 用在“护甲清零”语义的地方（保持原样）
import re
print('\n所有 breakArmor 调用：')
for i, l in enumerate(t.split('\n'), 1):
    if 'breakArmor' in l:
        print(f'  L{i}: {l.strip()[:120]}')

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
