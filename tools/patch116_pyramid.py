# -*- coding: utf-8 -*-
"""补丁 116：金字塔的两个选项分别按开关门控"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
lines = IDX.read_text(encoding='utf-8').split('\n')
changed = []

for i, l in enumerate(lines):
    if "oneShot(p, 1, 'TNT ×4（全局唯一）'" in l and 'featOn' not in l:
        lines[i] = l.replace("grid.appendChild(oneShot(", "if(featOn('tnt')) grid.appendChild(oneShot(", 1)
        changed.append('L%d TNT 选项' % (i + 1))
    elif "oneShot(p, 1, '附魔金苹果（全局唯一）'" in l and 'featOn' not in l:
        lines[i] = l.replace("grid.appendChild(oneShot(", "if(featOn('god_apple')) grid.appendChild(oneShot(", 1)
        changed.append('L%d 金苹果选项' % (i + 1))

IDX.write_text('\n'.join(lines), encoding='utf-8')
print('逐行修改：')
for c in changed:
    print('  ok', c)
if not changed:
    print('  ! 无修改')

back = IDX.read_text(encoding='utf-8')
print("  TNT 选项门控:", "if(featOn('tnt')) grid.appendChild(oneShot(" in back)
print("  金苹果门控:", "if(featOn('god_apple')) grid.appendChild(oneShot(" in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
