# -*- coding: utf-8 -*-
"""补丁 90：【根治“判定平局卡死”】保护模态选择 UI 不被重绘冲掉
   问题：askDodge / chooseArmorMode 把按钮放在 #actionbar 里，
        而判定每轮都会 renderAll() → buildActionPanel() 重建面板，
        把玩家正在点的“闪避/赌一把”按钮冲掉 → 点不到 → 只能等 30 秒超时。
   修复：引入 uiLock，锁定期间 renderAll 不重建行动面板；所有模态选择 UI 都上锁。
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

# 1) 全局锁
sub("""/* 玩家回合中记住当前选项与“结算回调”，供界面重绘时复用 */
let pendingChoice = null;      /* { opts, settle } */
let pendingChoiceFor = null;   /* 该面板属于哪个玩家 */""",
"""/* 玩家回合中记住当前选项与“结算回调”，供界面重绘时复用 */
let pendingChoice = null;      /* { opts, settle } */
let pendingChoiceFor = null;   /* 该面板属于哪个玩家 */
/* 模态选择 UI 锁：为 true 时不重建行动面板，避免把玩家正在点的按钮冲掉
   （判定平局选闪避、钻石剑选护甲模式等都属于这种情况） */
let uiLock = false;
function lockUI(){ const prev = uiLock; uiLock = true; return prev; }
function unlockUI(prev){ uiLock = !!prev; }""", 'uiLock 定义')

sub("""  /* 【界面同步】只要玩家正在选择行动，就把行动面板整体重绘一遍，
     这样 AP 数字、进程进度、按钮标价、可选项都会立刻反映最新状态 */
  if(pendingChoice && pendingChoiceFor && pendingChoiceFor.alive && !G.over){
    try{ buildActionPanel(pendingChoiceFor, pendingChoice.opts, pendingChoice.settle); }catch(e){}
  }""",
"""  /* 【界面同步】只要玩家正在选择行动，就把行动面板整体重绘一遍，
     这样 AP 数字、进程进度、按钮标价、可选项都会立刻反映最新状态。
     注意：模态选择（闪避/护甲）进行中时锁定，绝不覆盖玩家正在点的按钮。 */
  if(uiLock) return;
  if(pendingChoice && pendingChoiceFor && pendingChoiceFor.alive && !G.over){
    try{ buildActionPanel(pendingChoiceFor, pendingChoice.opts, pendingChoice.settle); }catch(e){}
  }""", 'renderAll 尊重锁')

# 2) askDodge 上锁
sub("""function askDodge(target, attacker){
  return new Promise(res=>{
    let done = false;
    const finish = (v)=>{ if(done) return; done = true; res(v); };""",
"""function askDodge(target, attacker){
  return new Promise(res=>{
    let done = false;
    const prevLock = lockUI();                 /* 锁住面板，防止被重绘冲掉 */
    const finish = (v)=>{ if(done) return; done = true; unlockUI(prevLock); res(v); };""",
'askDodge 上锁')

# 3) chooseArmorMode 上锁
sub("""      let done=false;
      const finish=(v)=>{ if(done) return; done=true; bar.innerHTML=''; res(v); };""",
"""      let done=false;
      const prevLock = lockUI();               /* 锁住面板，防止被重绘冲掉 */
      const finish=(v)=>{ if(done) return; done=true; unlockUI(prevLock); bar.innerHTML=''; res(v); };""",
'chooseArmorMode 上锁')

# 4) 判定流程本身也上锁（hideRpsSlots 之后解锁）
sub("""    rlog('doJudgment 进入: ' + lname(attacker) + ' → ' + lname(target) + ' instant=' + !!o.instant);""",
"""    rlog('doJudgment 进入: ' + lname(attacker) + ' → ' + lname(target) + ' instant=' + !!o.instant);
    const prevJudgeLock = lockUI();            /* 判定期间不重建面板 */""", '判定上锁')

sub("""    const finish = ()=>{
      clearTimeout(guardTimer);
      hideRpsSlots();
      rlog('hideRpsSlots 完成，resolve 判定');
      safeResolve(hit);
    };""",
"""    const finish = ()=>{
      clearTimeout(guardTimer);
      hideRpsSlots();
      unlockUI(prevJudgeLock);                 /* 判定结束，恢复面板重绘 */
      rlog('hideRpsSlots 完成，resolve 判定');
      safeResolve(hit);
    };""", '判定解锁')

# 5) 兜底超时也要解锁
sub("""    const guardTimer = setTimeout(()=>{ rlog('doJudgment 兜底超时收尾'); safeResolve(hit); }, 20000);""",
"""    const guardTimer = setTimeout(()=>{
      rlog('doJudgment 兜底超时收尾');
      unlockUI(prevJudgeLock);
      try{ hideRpsSlots(); }catch(e){}
      safeResolve(hit);
    }, 20000);""", '兜底解锁')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
