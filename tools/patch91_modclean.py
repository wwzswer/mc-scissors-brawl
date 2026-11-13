# -*- coding: utf-8 -*-
"""补丁 91：模态选择结束后清理按钮并立即恢复行动面板
   问题：askDodge / chooseArmorMode 结束后只解锁，没清掉自己的按钮，
        会残留并盖住真正的行动面板。
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# askDodge：结束时清空面板再解锁，并触发一次重绘
sub("""    const prevLock = lockUI();                 /* 锁住面板，防止被重绘冲掉 */
    const finish = (v)=>{ if(done) return; done = true; unlockUI(prevLock); res(v); };""",
"""    const prevLock = lockUI();                 /* 锁住面板，防止被重绘冲掉 */
    const finish = (v)=>{
      if(done) return;
      done = true;
      const b = document.getElementById('actionbar');
      if(b) b.innerHTML = '';                  /* 清掉自己的按钮，别盖住行动面板 */
      unlockUI(prevLock);
      try{ renderAll(); }catch(e){}            /* 立刻恢复真正的行动面板 */
      res(v);
    };""", 'askDodge 结束清理')

# chooseArmorMode：结束时清空并恢复
sub("""      let done=false;
      const prevLock = lockUI();               /* 锁住面板，防止被重绘冲掉 */
      const finish=(v)=>{ if(done) return; done=true; unlockUI(prevLock); bar.innerHTML=''; res(v); };""",
"""      let done=false;
      const prevLock = lockUI();               /* 锁住面板，防止被重绘冲掉 */
      const finish=(v)=>{
        if(done) return;
        done=true;
        bar.innerHTML='';
        unlockUI(prevLock);
        try{ renderAll(); }catch(e){}          /* 立刻恢复行动面板 */
        res(v);
      };""", 'chooseArmorMode 结束清理')

# doJudgment 收尾：解锁后重绘一次，确保行动面板回来
sub("""      unlockUI(prevJudgeLock);                 /* 判定结束，恢复面板重绘 */
      rlog('hideRpsSlots 完成，resolve 判定');
      safeResolve(hit);""",
"""      unlockUI(prevJudgeLock);                 /* 判定结束，恢复面板重绘 */
      try{ renderAll(); }catch(e){}            /* 让行动面板立刻回到正确状态 */
      rlog('hideRpsSlots 完成，resolve 判定');
      safeResolve(hit);""", '判定结束重绘')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
