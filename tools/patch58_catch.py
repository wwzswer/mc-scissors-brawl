# -*- coding: utf-8 -*-
"""补丁 58：给 rpsPhase 的收尾段与 hideRpsSlots 加异常捕获，暴露真实错误"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

# hideRpsSlots 容错
old_hide = """function hideRpsSlots(){
  document.getElementById('rpsArea').classList.add('hidden');
  document.getElementById('rpsBtns').classList.remove('hidden');
  ['slotA','slotB'].forEach(id=>{ const e=document.getElementById(e); e.textContent='❔'; e.className='slot'; });
}"""
old_hide2 = """function hideRpsSlots(){
  document.getElementById('rpsArea').classList.add('hidden');
  document.getElementById('rpsBtns').classList.remove('hidden');
  ['slotA','slotB'].forEach(id=>{ const e=document.getElementById(id); e.textContent='❔'; e.className='slot'; });
}"""
new_hide = """function hideRpsSlots(){
  try{
    const area = document.getElementById('rpsArea');
    const btns = document.getElementById('rpsBtns');
    if(area) area.classList.add('hidden');
    if(btns) btns.classList.remove('hidden');
    ['slotA','slotB'].forEach(id=>{ const e=document.getElementById(id); if(e){ e.textContent='❔'; e.className='slot'; } });
  }catch(e){ rlog('hideRpsSlots 异常: '+e.message); }
}"""
if old_hide2 in t:
    t = t.replace(old_hide2, new_hide, 1); notes.append('  ok hideRpsSlots 容错')
elif old_hide in t:
    t = t.replace(old_hide, new_hide, 1); notes.append('  ok hideRpsSlots 容错')
else:
    notes.append('  ! hideRpsSlots 锚点未匹配')

# rpsPhase 收尾段加 try/catch，把异常记进 rlog 并保证 setPhase 一定执行
old_tail = """    hideRpsSlots();
    rlog('hideRpsSlots 完成');
    const st = document.getElementById('rpsStatus');
    if(st) st.textContent = '选择你的出拳';
  }
  setPhase('行动阶段');
  rlog('rpsPhase 返回 order=' + order.length);
  return order;
}"""
new_tail = """    try{
      hideRpsSlots();
      rlog('hideRpsSlots 完成');
      const st = document.getElementById('rpsStatus');
      if(st) st.textContent = '选择你的出拳';
    }catch(e){ rlog('收尾段异常: ' + (e && e.message)); }
  }
  try{ setPhase('行动阶段'); }catch(e){ rlog('setPhase 异常: ' + (e && e.message)); }
  rlog('rpsPhase 返回 order=' + order.length);
  return order;
}"""
if old_tail in t:
    t = t.replace(old_tail, new_tail, 1); notes.append('  ok rpsPhase 收尾容错')
else:
    notes.append('  ! rpsPhase 收尾锚点未匹配')

# 给 gameLoop 里的 rpsPhase 调用加错误捕获
old_call = """      rlog('gameLoop: 调用 rpsPhase');
      const order = await rpsPhase();
      rlog('gameLoop: rpsPhase 已返回');"""
if old_call not in t:
    # 说明上一步 gameLoop 埋点没成功，这里用原始形式
    old_call2 = """      const order = await rpsPhase();"""
    new_call2 = """      rlog('gameLoop: 调用 rpsPhase');
      let order;
      try{ order = await rpsPhase(); rlog('gameLoop: rpsPhase 已返回'); }
      catch(e){ rlog('rpsPhase 抛异常: ' + (e && e.message)); order = alivePlayers(); }"""
    if old_call2 in t:
        t = t.replace(old_call2, new_call2, 1); notes.append('  ok gameLoop 调用容错')
    else:
        notes.append('  ! gameLoop 调用锚点未匹配')
else:
    notes.append('  - gameLoop 埋点已存在')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
