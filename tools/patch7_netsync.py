# -*- coding: utf-8 -*-
"""补丁 7：联机对局同步 + 文案修正
   同步策略：两端用相同 seed 跑同一套引擎（确定性 RNG 已就绪），
   本地动作通过服务器广播，收到对方动作后按顺序本地应用。
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
html = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global html
    if old not in html:
        notes.append(f'  ! 未找到 {label}'); return
    html = html.replace(old, new, 1); notes.append(f'  ok {label}')

# ---------- 1) 网络输入队列 ----------
sub("""/* 可注入的“自动玩家”钩子：无头测试与自动演示用，正常游戏时为 null */
let autoPlayer = null;""",
"""/* 可注入的“自动玩家”钩子：无头测试与自动演示用，正常游戏时为 null */
let autoPlayer = null;
/* ---------------- 联机：远端输入队列 ----------------
   两端跑同一套引擎（同 seed → 确定性 RNG），本地动作经服务器广播，
   收到对方动作后按序本地应用，从而保持两边状态一致。 */
const netIn = { rps:{}, act:{} };
function netIsOn(){ return (typeof Net!=='undefined') && Net.active && Net.started; }
function netIsLocal(p){ return !netIsOn() || p.isHuman; }
function netPeerId(){                       /* 联机时取第一个非本机的座位 */
  if(!netIsOn()) return null;
  const s = Net.seats.find(s=>s.id!==Net.youId);
  return s ? s.id : null;
}
function netSendRps(mv){ if(netIsOn()) Net.send({kind:'rps', move:mv}); }
function netSendAct(a){
  if(!netIsOn()) return;
  const payload = Object.assign({}, a);
  delete payload.__spe;
  Net.send({kind:'act', action:payload});
}
function netWaitRps(fromId, ms){
  return new Promise(res=>{
    const t0 = Date.now();
    const tick = ()=>{
      if(netIn.rps[fromId]){ const v = netIn.rps[fromId]; delete netIn.rps[fromId]; return res(v); }
      if(Date.now()-t0 > (ms||60000)) return res(null);
      setTimeout(tick, 40);
    };
    tick();
  });
}
function netWaitAct(fromId, ms){
  return new Promise(res=>{
    const t0 = Date.now();
    const tick = ()=>{
      if(netIn.act[fromId] && netIn.act[fromId].length) return res(netIn.act[fromId].shift());
      if(Date.now()-t0 > (ms||120000)) return res(null);
      setTimeout(tick, 40);
    };
    tick();
  });
}
/* 收到远端事件 */
function netHandleEvent(ev){
  const a = ev.action || {};
  if(a.kind === 'rps'){ netIn.rps[ev.actor] = a.move; return; }
  if(a.kind === 'act'){
    netIn.act[ev.actor] = netIn.act[ev.actor] || [];
    netIn.act[ev.actor].push(a.action);
    return;
  }
  if(a.kind === 'seed' && typeof a.seed === 'number'){ setSeed(a.seed); return; }
}""",
'网络输入队列')

# ---------- 2) humanRps 支持联机 ----------
sub("""async function humanRps(p, target){
  let my;
  if(autoMode || clickResolver===null){
    my = pick(['rock','scissors','paper']);
    document.getElementById('rpsArea').classList.remove('hidden');
    document.getElementById('rpsStatus').textContent = autoMode? '自动出拳中…' : '与 '+target.name+' 猜拳——选择你的出拳';
    if(!autoMode) my = await rpsPrompt(target);
  }
  const opp = aiRpsMove(target, p);""",
"""async function humanRps(p, target){
  let my;
  if(netIsOn()){
    /* 联机：自己点（或自动），对手的出拳从网络来 */
    document.getElementById('rpsArea').classList.remove('hidden');
    document.getElementById('rpsStatus').textContent = '与 '+(netPeerId()?'对手':'AI')+' 猜拳——选择你的出拳';
    my = autoMode ? pick(['rock','scissors','paper']) : await rpsPrompt(target);
    netSendRps(my);
    const peer = netPeerId();
    const got = peer ? await netWaitRps(peer) : null;
    var oppNet = got || pick(['rock','scissors','paper']);
  } else {
    if(autoMode || clickResolver===null){
      my = pick(['rock','scissors','paper']);
      document.getElementById('rpsArea').classList.remove('hidden');
      document.getElementById('rpsStatus').textContent = autoMode? '自动出拳中…' : '与 '+target.name+' 猜拳——选择你的出拳';
      if(!autoMode) my = await rpsPrompt(target);
    }
  }
  const opp = netIsOn() ? oppNet : aiRpsMove(target, p);""",
'humanRps 联机')

# ---------- 3) takeTurn 支持联机（人类回合等远端动作） ----------
sub("""    if(isHuman){
      /* 人类回合：默认等玩家点按钮；若注入了自动玩家钩子（无头测试 / 自动演示）则交给它 */
      let choice;
      if(autoPlayer){""",
"""    if(isHuman){
      /* 联机模式下人类回合 = 本地玩家 + 远端玩家的动作都会到达，这里先处理远端的 */
      if(netIsOn()){
        const peer = netPeerId();
        const remote = peer ? await netWaitAct(peer, 60000) : null;
        if(remote){
          const actor = P(0);
          log(`📡 收到对手动作：${remote.label || remote.type}`,'l-sys');
          await runAction(actor, remote);
          continue;
        }
      }
      /* 人类回合：默认等玩家点按钮；若注入了自动玩家钩子（无头测试 / 自动演示）则交给它 */
      let choice;
      if(autoPlayer){""",
'takeTurn 联机')

# ---------- 4) 本地人类动作广播 ----------
sub("""      const ok = await runAction(p, choice);
      if(ok===false) avoid.push(actionKey(choice));
      await sleep(w('actionHuman'));
    } else {""",
"""      netSendAct(choice);
      const ok = await runAction(p, choice);
      if(ok===false) avoid.push(actionKey(choice));
      await sleep(w('actionHuman'));
    } else {""",
'人类动作广播')

# ---------- 5) 联机开始后接管事件 ----------
sub("""    const sb = document.getElementById('netStartBtn');
    if(sb) sb.onclick = ()=>{ this.start(); };""",
"""    const sb = document.getElementById('netStartBtn');
    if(sb) sb.onclick = ()=>{ this.start(); };""",
'（保留）')

sub("""  connect(){
    if(this.es){ try{ this.es.close(); }catch(e){} }""",
"""  connect(){
    if(this.es){ try{ this.es.close(); }catch(e){} }
    this.onLog = [ ev => { try{ netHandleEvent(ev); }catch(e){} } ];""",
'联机事件接入')

# 房主开始对局 → 所有端自动开局（用房间码派生的同一个种子）
sub("""    if(sub === 'start' && req.method === 'POST'){""",
"""    if(sub === 'start' && req.method === 'POST'){""",
'（服务端占位）')

# ---------- 6) 文案修正 ----------
sub("""  <div class="sub">猜拳夺 AP → 升进程 / 造装备 / 收补给 → 相互战斗。每次猜拳获胜 <b>+2 AP</b>，每位玩家 <b>4 点生命</b>。</div>""",
"""  <div class="sub">猜拳夺 AP → 升进程 / 造装备 / 收补给 → 相互战斗。每位玩家 <b>4 点生命</b>，猜拳获胜的 AP 可在设置里选 <b>1 或 2</b>（判定不产生 AP）。</div>""",
'顶部说明文案')

sub("""          <div><b>距离</b>：初始 0 格；末影珍珠 ±2、钓鱼竿 ±1、盾 +1</div>""",
"""          <div><b>距离</b>：初始 1 格、上限 ${MAX_DIST} 格、两两独立；走位 1 步 ±1 格、末影珍珠 ±2、钓鱼竿 ±1、盾 +1。近战需 0 格</div>""",
'速查区距离文案')

IDX.write_text(html, encoding='utf-8')
print('\n'.join(notes))
print(f'补丁 7 完成，文件 {len(html)/1024:.1f} KB')
