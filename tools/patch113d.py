# -*- coding: utf-8 -*-
"""补丁 113d（修正版）：逐行补齐门控；先写盘再校验"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
lines = IDX.read_text(encoding='utf-8').split('\n')
changed = []

for i, l in enumerate(lines):
    if "type:'potion'" in l and 'featOn' not in l:
        lines[i] = l.replace("if(hasItem(", "if(featOn('potion') && hasItem(", 1)
        changed.append('L%d 药水选项' % (i+1)); continue
    if "if(k==='witchhut'){" in l and 'featOn' not in l:
        ind = l[:len(l) - len(l.lstrip())]
        lines[i] = l + "\n" + ind + "  if(!featOn('potion')) log('（药水已在设置中禁用）','l-sys');"
        changed.append('L%d 女巫小屋门控' % (i+1)); continue
    if "if(k==='mansion'){" in l and 'featOn' not in l:
        ind = l[:len(l) - len(l.lstrip())]
        lines[i] = l + "\n" + ind + "  if(!featOn('totem')) log('（不死图腾已在设置中禁用）','l-sys');"
        changed.append('L%d 府邸门控' % (i+1)); continue
    if 'p.buildings.pyramid && p.ap>=1' in l and 'featOn' not in l:
        lines[i] = l.replace("p.buildings.pyramid && p.ap>=1",
                             "p.buildings.pyramid && p.ap>=1 && (featOn('tnt') || featOn('god_apple'))", 1)
        changed.append('L%d 金字塔选项门控' % (i+1)); continue

IDX.write_text('\n'.join(lines), encoding='utf-8')

print('逐行修改：')
for c in changed:
    print('  ok', c)
if not changed:
    print('  ! 没有任何修改')

back = IDX.read_text(encoding='utf-8')
print('')
print('--- 落盘校验 ---')
for k in ['totem', 'potion', 'tnt', 'god_apple']:
    needle = "featOn('" + k + "')"
    print('  ' + needle + ' ×' + str(back.count(needle)))
print('  金字塔选项门控:', "featOn('tnt') || featOn('god_apple')" in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
