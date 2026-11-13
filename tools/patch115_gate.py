# -*- coding: utf-8 -*-
"""补丁 115：逐行把府邸/女巫小屋门控改为真条件"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
lines = IDX.read_text(encoding='utf-8').split('\n')
changed = []

for i, l in enumerate(lines):
    s = l.strip()
    if s == "if(k==='mansion'){" and 'featOn' not in l:
        lines[i] = l.replace("if(k==='mansion'){", "if(k==='mansion' && featOn('totem')){", 1)
        changed.append('L%d 府邸' % (i + 1))
    elif s == "if(k==='witchhut'){" and 'featOn' not in l:
        lines[i] = l.replace("if(k==='witchhut'){", "if(k==='witchhut' && featOn('potion')){", 1)
        changed.append('L%d 女巫小屋' % (i + 1))

IDX.write_text('\n'.join(lines), encoding='utf-8')
print('逐行修改：')
for c in changed:
    print('  ok', c)
if not changed:
    print('  ! 无修改')

back = IDX.read_text(encoding='utf-8')
print('  府邸条件:', "k==='mansion' && featOn('totem')" in back)
print('  小屋条件:', "k==='witchhut' && featOn('potion')" in back)
# 检查是否还残留“只打日志”的旧行
for i, l in enumerate(back.split('\n'), 1):
    if '已在设置中禁用' in l:
        print('  残留旧行 L%d: %s' % (i, l.strip()[:100]))

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
