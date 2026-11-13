# -*- coding: utf-8 -*-
"""补丁 14：每回合一次猜拳决定 AP
   所有存活玩家同时出拳；平局（所有人同招）则重出；
   直到出现唯一胜者，该玩家获得 AP，本回合猜拳结束。
   联机模式：本地玩家出拳经网络与对手互换后比较。
"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

# ---- 定位并替换 humanRps / aiRps / rpsPhase ----
i1 = t.index('async function humanRps(')
i2 = t.index('function rpsPrompt(')
i3 = t.index('/* --- 行动阶段 --- */')
old_rps = t[i1:i2]
old_phase_start = t.index('async function rpsPhase(')
old_phase_end = t.index('async function humanRps(')

new_human_ai = r"""/* 一次猜拳：人类玩家（联机时与对手互换出拳） */
async function humanRps(p){
  let my;
  if(netIsOn()){
    document.getElementById('rpsArea').classList.remove('hidden');
    document.getElementById('rpsStatus').textContent = (autoMode ? '自动出拳中…' : '本回合猜拳——选择你的出拳');
    my = autoMode ? pick(['rock','scissors','paper']) : await rpsPrompt(null);
    netSendRps(my);
    const peer = netPeerId();
    const got = peer ? await netWaitRps(peer) : null;
    setLastPeer(got || pick(['rock','scissors','paper']));
    return my;
  }
  if(autoMode){
    my = pick(['rock','scissors','paper']);
    document.getElementById('rpsArea').classList.remove('hidden');
    document.getElementById('rpsStatus').textContent = '自动出拳中…';
  } else {
    document.getElementById('rpsArea').classList.remove('hidden');
    document.getElementById('rpsStatus').textContent = '本回合猜拳——选择你的出拳';
    my = await rpsPrompt(null);
  }
  return my;
}
/* 一次猜拳：AI */
async function aiRps(p){
  const foes = aliveEnemiesOf(p);
  return aiRpsMove(p, foes.length ? pick(foes) : p);
}
/* 本回合所有玩家的出拳（key = 玩家 id） */
let roundMoves = {};
let lastPeerMove = null;
function setLastPeer(mv){ lastPeerMove = mv; }

/* 判定胜负：唯一且克制其余所有招式者为胜者；全部相同为平局 */
function judgeRound(moves){
  const list = Object.entries(moves);
  if(list.length < 2) return {winner: list.length ? +list[0][0] : null, tie: list.length < 2};
  const uniq = new Set(list.map(([,m])=>m));
  if(uniq.size === 1) return {winner:null, tie:true};                    /* 所有人同招 → 平局 */
  for(const [id, mv] of list){
    if(list.every(([oid, omv]) => oid===id || BEATS[mv]===omv)){
      /* 该玩家的招式克制其余所有人 */
      return {winner:+id, tie:false};
    }
  }
  /* 没有唯一胜者（三方互克等）→ 也算平局，重出 */
  return {winner:null, tie:true};
}

/* --- 猜拳阶段：每回合只进行一次，平手则重出，直到有人胜出 --- */
async function rpsPhase(){
  const order=[];
  const me=human();
  if(me.alive) order.push(me);
  for(const p of G.players) if(!p.isHuman && p.alive) order.push(p);
  for(const p of G.players) if(p.alive){ p.actionsUsed=0; }

  const live = alivePlayers();
  if(live.length >= 2){
    let round = 0, winner = null;
    while(round++ < 60){
      const moves = {};
      if(netIsOn()){
        /* 联机：本地出拳 + 对手出拳（网络） */
        const my = await humanRps(me);
        moves[me.id] = my;
        const peerMove = lastPeerMove || pick(['rock','scissors','paper']);
        lastPeerMove = null;
        const peer = live.find(q=>!q.isHuman);
        if(peer) moves[peer.id] = peerMove;
        for(const q of live) if(!q.isHuman && !(q.id in moves)) moves[q.id] = await aiRps(q);
      } else {
        for(const q of live){
          moves[q.id] = q.isHuman ? await humanRps(q) : await aiRps(q);
        }
      }
      showSlotsMulti(moves, null);
      const res = judgeRound(moves);
      const detail = live.map(q=>lname(q)+' '+RPS_NAME[moves[q.id]]).join('　');
      if(res.tie){
        log(`✊ <b>猜拳</b>（第 ${round} 轮）：${detail} → <b>平局</b>，重新出拳。`,'l-rps');
        sfx.rps();
        if(autoMode) await sleep(w('rpsAi')||120); else await waitClick('平局！继续出拳 ▶');
        continue;
      }
      winner = P(res.winner);
      log(`✊ <b>猜拳</b>（第 ${round} 轮）：${detail} → <b>${lname(winner)} 胜出，+${apPerWin} AP</b>。`,'l-rps');
      showSlotsMulti(moves, winner.id);
      sfx.win();
      break;
    }
    if(winner){
      winner.ap += apPerWin;
      renderAll();
      if(autoMode) await sleep(w('rpsHuman')||200); else await waitClick('继续 ▶ 进入行动阶段');
    } else {
      log('（猜拳轮次过多，本回合无人获得 AP）','l-warn');
    }
    hideRpsSlots();
    document.getElementById('rpsStatus').textContent='选择你的出拳';
  }
  updatePhase('行动阶段');
  return order;
}

/* 多人心战展示：把每个人的出拳显示在中央区域 */
function showSlotsMulti(moves, winnerId){
  const area = document.getElementById('rpsArea');
  if(!area) return;
  area.classList.remove('hidden');
  const btns = document.getElementById('rpsBtns');
  if(btns) btns.classList.add('hidden');
  const GLY = {rock:'✊', scissors:'✌️', paper:'✋'};
  const box = area.querySelector('.reveal');
  if(!box) return;
  box.innerHTML = alivePlayers().map(q=>{
    const mv = moves[q.id];
    const cls = (winnerId!==null && winnerId!==undefined) ? (q.id===winnerId ? ' win' : ' lose') : '';
    return `<div style="display:flex;flex-direction:column;align-items:center;gap:4px">
      <div class="slot${cls}">${mv?GLY[mv]:'❔'}</div>
      <div style="font-size:11.5px;color:var(--dim)">${esc(q.name)}</div></div>`;
  }).join('');
}

"""
t = t[:old_phase_start] + new_human_ai + t[old_phase_end:i1] + t[i2:]

IDX.write_text(t, encoding='utf-8')
print('已重写猜拳阶段；文件', round(len(t)/1024,1), 'KB')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
