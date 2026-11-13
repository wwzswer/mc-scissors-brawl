# -*- coding: utf-8 -*-
"""补丁 54：在猜拳关键节点埋诊断日志（__rpsLog），精确定位卡点"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# 日志工具
sub("""/* 统一的“等玩家点一下”交互：""",
"""/* 猜拳流程诊断日志（仅内存，不影响玩法） */
function rlog(s){ try{ (globalThis.__rpsLog = globalThis.__rpsLog || []).push(s); }catch(e){} }

/* 统一的“等玩家点一下”交互：""", 'rlog 工具')

# rpsPhase 各节点
sub("""async function rpsPhase(){
  const order=[];""",
"""async function rpsPhase(){
  rlog('rpsPhase 进入');
  const order=[];""", 'rpsPhase 进入')

sub("""    while(!rpsDecided && round++ < 60){
      if(G.runId !== myRun) return order;              /* 新局已开始 */""",
"""    while(!rpsDecided && round++ < 60){
      rlog('while 第 ' + round + ' 轮开始');
      if(G.runId !== myRun) return order;              /* 新局已开始 */""", 'while 轮次')

sub("""      const res = judgeRound(moves);
      const detail = live.filter(q=>q.id in moves).map(q=>lname(q)+' '+RPS_NAME[moves[q.id]]).join('　');""",
"""      const res = judgeRound(moves);
      rlog('判定: tie=' + res.tie + ' winner=' + res.winner + ' moves=' + JSON.stringify(moves));
      const detail = live.filter(q=>q.id in moves).map(q=>lname(q)+' '+RPS_NAME[moves[q.id]]).join('　');""", '判定结果')

sub("""        if(instantRps){ /* 无头：直接重出 */ }
        else if(autoMode) await sleep(w('rpsAi') || 120);
        else await waitClick('平局！继续出拳 ▶');
        continue;""",
"""        if(instantRps){ rlog('平局：instantRps 直接重出'); }
        else if(autoMode){ rlog('平局：autoMode 等待'); await sleep(w('rpsAi') || 120); rlog('平局：autoMode 等待结束'); }
        else { rlog('平局：等待玩家点击“继续出拳”'); await waitClick('平局！继续出拳 ▶'); rlog('平局：玩家已点击，重出'); }
        continue;""", '平局等待')

sub("""    if(!rpsDecided) log('（猜拳轮次过多，本回合无人获得 AP）','l-warn');
    renderAll();""",
"""    rlog('while 结束 rpsDecided=' + rpsDecided + ' round=' + round);
    if(!rpsDecided) log('（猜拳轮次过多，本回合无人获得 AP）','l-warn');
    renderAll();""", 'while 结束')

sub("""    if(!instantRps){
      if(autoMode) await sleep(w('rpsHuman') || 200);
      else await waitClick('继续 ▶ 进入行动阶段');
    }
    hideRpsSlots();""",
"""    if(!instantRps){
      if(autoMode){ rlog('进入行动阶段：autoMode 等待'); await sleep(w('rpsHuman') || 200); rlog('进入行动阶段：等待结束'); }
      else { rlog('进入行动阶段：等待玩家点击'); await waitClick('继续 ▶ 进入行动阶段'); rlog('进入行动阶段：玩家已点击'); }
    } else { rlog('进入行动阶段：instantRps 跳过等待'); }
    hideRpsSlots();
    rlog('hideRpsSlots 完成');""", '进入行动阶段等待')

sub("""  setPhase('行动阶段');
  return order;
}""",
"""  setPhase('行动阶段');
  rlog('rpsPhase 返回 order=' + order.length);
  return order;
}""", 'rpsPhase 返回')

# humanRps 分支
sub("""async function humanRps(p){
  let my;""",
"""async function humanRps(p){
  rlog('humanRps 进入 autoMode=' + autoMode + ' net=' + netIsOn());
  let my;""", 'humanRps 进入')

# gameLoop 调用点
sub("""      const order = await rpsPhase();""",
"""      rlog('gameLoop: 调用 rpsPhase');
      const order = await rpsPhase();
      rlog('gameLoop: rpsPhase 已返回');""", 'gameLoop 调用')

# 导出
old_exp = "    getLastClickAt: ()=>lastClickAt, rpsBtnHit,"
new_exp = "    getLastClickAt: ()=>lastClickAt, rpsBtnHit, getRpsLog: ()=>globalThis.__rpsLog || [],"
if old_exp in t and 'getRpsLog' not in t:
    t = t.replace(old_exp, new_exp, 1); notes.append('  ok 导出 getRpsLog')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
