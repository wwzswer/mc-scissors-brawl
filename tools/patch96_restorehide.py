# -*- coding: utf-8 -*-
"""补丁 96：补回被误删的 hideRpsSlots，并确认 judgeSlots 完好"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

def has_fn(name):
    return len(re.findall(r'(?:^|\n)function ' + name + r'\(', t)) > 0

print('hideRpsSlots 存在:', has_fn('hideRpsSlots'))
print('judgeSlots 存在:', has_fn('judgeSlots'))

if not has_fn('hideRpsSlots'):
    # 插到 showSlotsMulti 之后
    m = re.search(r'(?:^|\n)function showSlotsMulti\(.*?\n\}', t, re.S)
    anchor = m.group(0) if m else None
    fn = """

function hideRpsSlots(){
  try{
    const area = document.getElementById('rpsArea');
    const btns = document.getElementById('rpsBtns');
    if(area) area.classList.add('hidden');
    if(btns) btns.classList.remove('hidden');
    ['slotA','slotB'].forEach(id=>{ const e=document.getElementById(id); if(e){ e.textContent='❔'; e.className='slot'; } });
    const st = document.getElementById('rpsStatus');
    if(st) st.textContent = '选择你的出拳';
  }catch(e){ /* 界面缺失也不能影响流程 */ }
}"""
    if anchor:
        t = t.replace(anchor, anchor + fn, 1)
    else:
        # 兜底：插到 judgeSlots 之前
        m2 = re.search(r'(?:^|\n)function judgeSlots\(', t)
        if m2:
            t = t[:m2.start()] + fn + '\n' + t[m2.start():]
    IDX.write_text(t, encoding='utf-8')
    print('已补回 hideRpsSlots')
else:
    print('无需补回')

print('补回后 hideRpsSlots 数量:', len(re.findall(r'(?:^|\n)function hideRpsSlots\(', t)))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
