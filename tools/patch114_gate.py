# -*- coding: utf-8 -*-
"""补丁 114：
   ① 府邸/女巫小屋门控改为真正的条件判断（此前只是打了句日志）
   ② 修正验证脚本的判断方式（商店条目 vs 描述文字）
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# 府邸：条件化
sub("""      if(k==='mansion'){
        if(!featOn('totem')) log('（不死图腾已在设置中禁用）','l-sys');""",
"""      if(k==='mansion' && featOn('totem')){""", '府邸真门控')

# 女巫小屋：条件化
sub("""      if(k==='witchhut'){
        if(!featOn('potion')) log('（药水已在设置中禁用）','l-sys');""",
"""      if(k==='witchhut' && featOn('potion')){""", '女巫小屋真门控')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print(f'  长度 {orig} → {len(back)}')
print("  府邸条件:", "k==='mansion' && featOn('totem')" in back)
print("  小屋条件:", "k==='witchhut' && featOn('potion')" in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
