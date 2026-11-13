# -*- coding: utf-8 -*-
"""补丁 94：修 judgeSlots 空元素异常 + performAttack 调用保护"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

# 1) judgeSlots / showSlotsMulti / hideRpsSlots：所有 DOM 访问都判空
import re
def show_fn(name):
    m = re.search(r'(?:^|\n)function ' + name + r'\(.*?\n\}', t, re.S)
    return m.group(0) if m else None

for fn in ['judgeSlots', 'showSlotsMulti', 'hideRpsSlots']:
    body = show_fn(fn)
    if body:
        notes.append(f'  · {fn} 现状: ' + body.replace(chr(10), ' ')[:150])
    else:
        notes.append(f'  ! 未找到 {fn}')

# judgeSlots 重写为安全版本
old_js = show_fn('judgeSlots')
if old_js:
    new_js = """function judgeSlots(ra, rb, hit){
  try{
    const a = document.getElementById('slotA');
    const b = document.getElementById('slotB');
    if(a){ a.textContent = RPS_GLYPH[ra] || '❔'; a.className = 'slot' + (hit===true ? ' win' : (hit===false ? ' lose' : '')); }
    if(b){ b.textContent = RPS_GLYPH[rb] || '❔'; b.className = 'slot' + (hit===true ? ' lose' : (hit===false ? ' win' : '')); }
  }catch(e){ /* 界面元素缺失也不能影响判定流程 */ }
}"""
    if old_js in t:
        t = t.replace(old_js, new_js, 1); notes.append('  ok judgeSlots 空安全重写')
    else:
        notes.append('  ! judgeSlots 替换失败')

old_hide = show_fn('hideRpsSlots')
if old_hide:
    new_hide = """function hideRpsSlots(){
  try{
    const area = document.getElementById('rpsArea');
    const btns = document.getElementById('rpsBtns');
    if(area) area.classList.add('hidden');
    if(btns) btns.classList.remove('hidden');
    ['slotA','slotB'].forEach(id=>{ const e=document.getElementById(id); if(e){ e.textContent='❔'; e.className='slot'; } });
  }catch(e){ rlog('hideRpsSlots 异常: ' + e.message); }
}"""
    if old_hide in t:
        t = t.replace(old_hide, new_hide, 1); notes.append('  ok hideRpsSlots 空安全重写')
    else:
        notes.append('  ! hideRpsSlots 替换失败')

# 2) performAttack 中对 doJudgment 的调用保护（找实际写法）
m = re.search(r'const hit\s*=\s*await doJudgment\([^)]*\);', t)
if m:
    indent = '    '
    new_call = ("let hit = false;\n" + indent +
        "try{ hit = await doJudgment(" + m.group(0).split('doJudgment(')[1])
    t = t.replace(m.group(0), new_call, 1)
    notes.append('  ok performAttack 调用保护')
else:
    notes.append('  ! 未找到 doJudgment 调用')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
