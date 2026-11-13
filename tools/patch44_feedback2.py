# -*- coding: utf-8 -*-
"""补丁 44：按用户反馈修正
   ① 猜拳卡死修复：用 rpsDecided 变量（平局 0 / 胜出 1）驱动循环；
      重构等待交互（promptChoice）避免 resolver 互相干扰、按钮消失、超时无出口
   ② 多人猜拳判定规则修正：按“同招式组”比较——被另一组克制则不算胜出
   ③ TNT 改为法术伤害，数值只与“有无护甲类物品”有关
   ④ 铁傀儡被动攻击不消耗 AP
   ⑤ 所有建筑建造消耗 1 AP
   ⑥ 火焰伤害：首次也不立即结算，统一放回合末尾；入水把剩余次数设为 0
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

# ============ ① 统一等待交互（带超时 + 防重复） ============
sub("""function waitClick(label){
  return new Promise(res=>{
    const bar=document.getElementById('actionbar'); bar.innerHTML='';
    const b=document.createElement('button');
    b.className='btn pri'; b.textContent=label||'继续 ▶';
    b.onclick=()=>{ sfx.click(); clickResolver=null; res(); };
    clickResolver=res;
    bar.appendChild(b);
  });
}""",
"""/* 统一的“等玩家点一下”交互：带超时与防重复，避免任何情况下卡死 */
function waitClick(label, opts){
  const o = opts||{};
  return new Promise(res=>{
    let done = false;
    const finish = ()=>{ if(done) return; done = true; clickResolver = null; res(); };
    const bar = o.bar || document.getElementById('actionbar');
    bar.innerHTML = '';
    const b = document.createElement('button');
    b.className = 'btn pri';
    b.textContent = label || '继续 ▶';
    b.onclick = ()=>{ try{ sfx.click(); }catch(e){} finish(); };
    clickResolver = finish;
    bar.appendChild(b);
    /* 兜底：按钮被意外移除 / 玩家长时间不操作时自动放行，绝不死等 */
    const iv = setInterval(()=>{
      if(done){ clearInterval(iv); return; }
      if(!b.isConnected || (o.timeout && Date.now()-t0 > o.timeout)){ clearInterval(iv); finish(); }
    }, 250);
    const t0 = Date.now();
  });
}
/* 等玩家出拳（猜拳阶段用）：按钮出现且确保可见 */
function promptRpsMove(target){
  return new Promise(res=>{
    let done = false;
    const finish = (mv)=>{ if(done) return; done = true; rpsResolver = null; res(mv); };
    const area = document.getElementById('rpsArea');
    const btns = document.getElementById('rpsBtns');
    if(area) area.classList.remove('hidden');
    if(btns) btns.classList.remove('hidden');
    const st = document.getElementById('rpsStatus');
    if(st) st.textContent = target ? `与 ${target.name} 猜拳 — 选择你的出拳` : '本回合猜拳 — 选择你的出拳（平手会重出）';
    rpsResolver = finish;
    /* 兜底：界面异常时给一个随机出拳，保证流程继续 */
    const iv = setInterval(()=>{
      if(done){ clearInterval(iv); return; }
      if(!btns || !btns.isConnected){ clearInterval(iv); finish(pick(['rock','scissors','paper'])); }
    }, 500);
  });
}""", 'waitClick/promptRpsMove 重构')

sub("""function rpsPrompt(target){
  return new Promise(res=>{
    document.getElementById('rpsArea').classList.remove('hidden');
    document.getElementById('rpsBtns').classList.remove('hidden');
    document.getElementById('rpsStatus').textContent =
      target ? `与 ${target.name} 猜拳 — 选择你的出拳` : '本回合猜拳 — 选择你的出拳（平手会重出）';
    rpsResolver=res;
  });
}""",
"""/* 兼容旧调用名 */
function rpsPrompt(target){ return promptRpsMove(target); }""", 'rpsPrompt 兼容')

# ============ ② judgeRound 按“同招式组”判定 ============
sub("""function judgeRound(moves){
  const list = Object.entries(moves);
  if(list.length === 0) return {winner:null, tie:true};
  if(list.length === 1) return {winner:+list[0][0], tie:false};
  const uniq = new Set(list.map(([,m])=>m));
  if(uniq.size === 1) return {winner:null, tie:true};                    /* 所有人同招 → 平局 */
  /* ① 克制其余所有人 */
  for(const [id, mv] of list){
    if(list.every(([oid, omv]) => oid===id || BEATS[mv]===omv)) return {winner:+id, tie:false};
  }
  /* ③ 没有绝对胜者：在“至少赢过一人”的玩家里随机选一个 */
  const scored = list.map(([id,mv])=>({id:+id, win: list.filter(([oid,omv])=>oid!==id && BEATS[mv]===omv).length}));
  const cand = scored.filter(s=>s.win>0);
  if(cand.length === 0) return {winner:null, tie:true};
  const best = Math.max(...cand.map(c=>c.win));
  const top = cand.filter(c=>c.win===best);
  return {winner: top[rnd(top.length)].id, tie:false};
}""",
"""/* 猜拳胜负：按“同招式组”比较
   ① 把出同一招式的玩家分成若干组
   ② 若某组克制其他所有组 → 该组内随机一人胜出
      例：A 剪刀、B 剪刀、C 石头 → 石头组胜出，C 得 AP
   ③ 若存在互克（如 A 剪刀、B 石头、C 布）或全员同招 → 平局，重出
*/
function judgeRound(moves){
  const list = Object.entries(moves);
  if(list.length === 0) return {winner:null, tie:true};
  if(list.length === 1) return {winner:+list[0][0], tie:false};
  const groups = {};                                  /* 招式 -> [玩家id] */
  for(const [id, mv] of list){ (groups[mv] = groups[mv] || []).push(+id); }
  const kinds = Object.keys(groups);
  if(kinds.length === 1) return {winner:null, tie:true};   /* 全员同招 → 平局 */
  const winners = kinds.filter(k => kinds.every(o => o===k || BEATS[k]===o));
  if(winners.length === 0) return {winner:null, tie:true};  /* 互克 → 平局，重出 */
  const pool = groups[winners[0]];
  return {winner: pool[rnd(pool.length)], tie:false};
}""", 'judgeRound 按同招式组')

# ============ ③ rpsPhase 重构（rpsDecided 驱动 + 不会卡死） ============
i = t.index('async function rpsPhase(){')
j = t.index('/* 多人心战展示', i)
new_phase = """async function rpsPhase(){
  const order=[];
  const me=human();
  if(me.alive) order.push(me);
  for(const p of G.players) if(!p.isHuman && p.alive) order.push(p);
  for(const p of G.players) if(p.alive){ p.actionsUsed=0; }

  const live = alivePlayers();
  if(live.length >= 2){
    const myRun = G.runId;
    let rpsDecided = 0;      /* 0 = 平局（回到猜拳）｜1 = 已有人胜出 */
    let round = 0;
    while(!rpsDecided && round++ < 60){
      if(G.runId !== myRun) return order;              /* 新局已开始 */
      const moves = {};
      if(netIsOn()){
        const my = await humanRps(me);
        moves[me.id] = my;
        const peerMove = lastPeerMove || pick(['rock','scissors','paper']);
        lastPeerMove = null;
        const peer = live.find(q=>!q.isHuman);
        if(peer) moves[peer.id] = peerMove;
        for(const q of live) if(!q.isHuman && !(q.id in moves)) moves[q.id] = await aiRps(q);
      } else {
        for(const q of live){
          if(!q.alive) continue;
          moves[q.id] = q.isHuman ? await humanRps(q) : await aiRps(q);
        }
      }
      const res = judgeRound(moves);
      const detail = live.filter(q=>q.id in moves).map(q=>lname(q)+' '+RPS_NAME[moves[q.id]]).join('　');
      if(res.tie){
        rpsDecided = 0;
        log(`✊ <b>猜拳</b>（第 ${round} 轮）：${detail} → <b>平局</b>，重新出拳。`,'l-rps');
        showSlotsMulti(moves, null);
        try{ sfx.rps(); }catch(e){}
        if(round >= 8){
          /* 连续平局过多：随机指定一名玩家获得本回合 AP，保证游戏推进 */
          const win = live[rnd(live.length)];
          rpsDecided = 1;
          win.ap += apPerWin;
          log(`✊ 连续 ${round} 轮平局，随机判定 <b>${lname(win)}</b> 胜出并获得 ${apPerWin} AP。`,'l-warn');
          showSlotsMulti(moves, win.id);
          break;
        }
        if(instantRps){ /* 无头：直接重出 */ }
        else if(autoMode) await sleep(w('rpsAi') || 120);
        else await waitClick('平局！继续出拳 ▶');
        continue;
      }
      rpsDecided = 1;
      const winner = P(res.winner);
      winner.ap += apPerWin;
      log(`✊ <b>猜拳</b>（第 ${round} 轮）：${detail} → <b>${lname(winner)} 胜出，+${apPerWin} AP</b>。`,'l-rps');
      showSlotsMulti(moves, winner.id);
      try{ sfx.win(); }catch(e){}
    }
    if(!rpsDecided) log('（猜拳轮次过多，本回合无人获得 AP）','l-warn');
    renderAll();
    /* 展示结果后进入行动阶段：自动模式稍等，手动模式点一下；两者都有兜底，不会卡死 */
    if(!instantRps){
      if(autoMode) await sleep(w('rpsHuman') || 200);
      else await waitClick('继续 ▶ 进入行动阶段');
    }
    hideRpsSlots();
    const st = document.getElementById('rpsStatus');
    if(st) st.textContent = '选择你的出拳';
  }
  setPhase('行动阶段');
  return order;
}

"""
t = t[:i] + new_phase + t[j:]
notes.append('  ok rpsPhase 重构')

# ============ ④ TNT 改法术伤害，数值只看有无护甲 ============
sub("""    if(key==='tnt'){
      log(`💥 <b>TNT 引爆！</b>`,'l-warn'); sfx.boom();
      const centre = target && target.alive ? target : attacker;
      const mainDmg  = armorActive(centre) ? 1.5 : 2.5;
      const splash   = armorActive(centre) ? 1.0 : 1.5;
      for(const v of alivePlayers()){
        const d = (v===centre) ? mainDmg : splash;
        /* TNT 的爆炸伤害直接按“有甲/无甲”取固定值，不消耗护甲耐久 */
        tryDamage(v,[d,0,0,0],{ isExplosion:true, noArmorConsume:true, label: v===centre?'TNT 中心爆炸':'TNT 溅射' });
      }
      log(`（TNT 范围爆炸：距中心 0 格 ${mainDmg}，其余 ${splash}；有友方伤害，也会伤到自己）`,'l-sys');
      return true;
    }""",
"""    if(key==='tnt'){
      log(`💥 <b>TNT 引爆！</b>`,'l-warn');
      try{ sfx.boom(); }catch(e){}
      const centre = target && target.alive ? target : attacker;
      const armed = armorHasAny(centre);                 /* 只看“是否持有护甲类物品” */
      const mainDmg = armed ? 1.5 : 2.5;                 /* 距中心 0 格 */
      const splash  = armed ? 1.0 : 1.5;                 /* 其余玩家（含自己） */
      for(const v of alivePlayers()){
        const d = (v===centre) ? mainDmg : splash;
        /* TNT 是法术伤害：无视护甲耐久，数值只与有无护甲物品有关 */
        tryDamage(v,[0,0,d,0],{ isExplosion:true, noArmorConsume:true,
          label: v===centre ? 'TNT 中心爆炸（法术）' : 'TNT 溅射（法术）' });
      }
      log(`（TNT 范围爆炸·法术伤害：距中心 0 格 ${mainDmg}，其余 ${splash}；有友方伤害，也会伤到自己）`,'l-sys');
      return true;
    }""", 'TNT 改法术')

# “持有护甲类物品”判定
sub("""function armorActive(p){ return !!p.armor && p.armorCharges>0; }""",
"""function armorActive(p){ return !!p.armor && p.armorCharges>0; }
/* 是否持有护甲类物品（不论耐久是否耗尽）—— TNT 伤害档位用它判定 */
function armorHasAny(p){ return !!(p && p.armor && ITEMS[p.armor] && ITEMS[p.armor].armor); }""",
'armorHasAny')

# ============ ⑤ 铁傀儡被动不消耗 AP ============
sub("""    for(const e of enemies.filter(e=>distanceBetween(p,e)<=2))
      push({type:'golem_punch',targetId:e.id,cost:0,label:`🥊 铁傀儡被动：攻击 ${e.name}（1.5，判定）`});""",
"""    for(const e of enemies.filter(e=>distanceBetween(p,e)<=2))
      push({type:'golem_punch',targetId:e.id,cost:0,isAction:false,label:`🥊 铁傀儡被动：攻击 ${e.name}（免费，不占行动）`});""",
'铁傀儡被动免费（人类选项）')

sub("""    for(const e of enemies.filter(e=>distanceBetween(p,e)<=2))
      push({type:'golem_punch',targetId:e.id,cost:0,label:'铁傀儡攻击 '+e.name});""",
"""    for(const e of enemies.filter(e=>distanceBetween(p,e)<=2))
      push({type:'golem_punch',targetId:e.id,cost:0,isAction:false,label:'铁傀儡攻击（免费）'});""",
'铁傀儡被动免费（AI 选项）')

# applyAction：免费即时动作集合加入 golem_punch
sub("""  const isFree = ['switch_weapon','pearl','pass'].includes(a.type);   /* 免费即时动作：不占行动次数 */""",
"""  const isFree = ['switch_weapon','pearl','pass','golem_punch'].includes(a.type);  /* 免费即时动作：不占行动次数 */""",
'免费动作集合')

# ============ ⑥ 所有建筑建造 = 1 AP ============
sub("""function itemNeed(k){ const it=ITEMS[k]; return it ? (it.cost||0) : 0; }""",
"""/* 建筑：建造只花 1 AP（不走向进度式）；物品：走进度式，每步 1 AP */
const BUILD_COST = 1;
function itemNeed(k){ const it=ITEMS[k]; return it ? (it.cost||0) : 0; }""",
'BUILD_COST 常量')

sub("""    if(it.build && !buildAllowed(p,a.key)) return false;          /* 建筑类仍一次性建造 */
    if(it.build){
      if(p.ap < (it.cost||0)) return false;
      p.ap -= it.cost;
      const done = craft(p, a.key);
      renderAll();
      return done;
    }""",
"""    if(it.build && !buildAllowed(p,a.key)) return false;          /* 建筑类一次性建造 */
    if(it.build){
      if(p.ap < BUILD_COST) return false;
      p.ap -= BUILD_COST;                                          /* 前往任意建筑统一 1 AP */
      const done = craft(p, a.key);
      renderAll();
      return done;
    }""", '建筑 1 AP（AI/统一入口）')

sub("""    case 'craftShopItem': case 'craft': {
      const it = ITEMS[a.key];
      if(!it){ break; }
      if(it.build){
        if(p.ap<it.cost){ log(`${lname(p)} 行动点不足，无法建造 ${it.name}。`,'l-warn'); break; }
        itemCost = it.cost; craft(p, a.key); break;
      }""",
"""    case 'craftShopItem': case 'craft': {
      const it = ITEMS[a.key];
      if(!it){ break; }
      if(it.build){
        if(p.ap<BUILD_COST){ log(`${lname(p)} 行动点不足，无法前往 ${it.name}。`,'l-warn'); break; }
        itemCost = BUILD_COST; craft(p, a.key); break;
      }""", '建筑 1 AP（applyAction）')

sub("""        d.onclick=()=>{ if(p.ap<it.cost) return; applyShopAction(p,{type:'craft',key:k}); render(); renderAll(); };""",
"""        d.onclick=()=>{ if(p.ap<(it.build?BUILD_COST:1)) return; applyShopAction(p,{type:'craft',key:k}); render(); renderAll(); };""",
'建筑 1 AP（商店按钮）')

# ============ ⑦ 火焰：首次不立即结算，统一回合末；入水置 0 ============
sub("""    /* 附加火焰：首次立即结算，其余留到回合结束时结算 */
    if(prof.burnTicks>0 && target.alive){
      addEffect(target,'burn',prof.burnTicks,99,'火焰');
      log(`🔥 ${lname(target)} 被点燃：立即结算 0.5 火焰伤害，剩余 ${prof.burnTicks-1} 次将在本回合所有玩家行动结束后结算。`,'l-warn');
      tryDamage(target,[0,0.5,0,0],{label:'点燃（立即结算）'});
      const burn = target.effects.find(e=>e.type==='burn');
      if(burn){ burn.power = rm(burn.power-1); if(burn.power<=0) target.effects=target.effects.filter(e=>e!==burn); }
    }""",
"""    /* 点燃：本回合不立即扣血，效果次数留到回合结束统一结算（入水可取消） */
    if(prof.burnTicks>0 && target.alive){
      addEffect(target,'burn',prof.burnTicks,99,'火焰');
      log(`🔥 ${lname(target)} 被点燃：将在本回合所有玩家行动结束后结算 ${prof.burnTicks} 次 0.5 火焰伤害（此时入水可取消）。`,'l-warn');
    }""", '火焰不再立即结算')

sub("""    /* 火焰（层数 = 尚未结算的次数；首次伤害已在点燃时立即结算过） */
    const burn = p.effects.find(e=>e.type==='burn');
    if(burn && !p.inWater){
      log(`🔥 ${lname(p)} 的火焰结算（剩余 ${burn.power} 次）。`,'l-warn');
      for(let i=0;i<burn.power && p.alive;i++) await tryDamage(p,[0,0.5,0,0],{label:'火焰持续伤害'});
      burn.power = 0;
    }
    if(burn) p.effects = p.effects.filter(e=>e!==burn);""",
"""    /* 火焰：统一在回合结束结算；层数 = 待结算次数（入水会把它设为 0） */
    const burn = p.effects.find(e=>e.type==='burn');
    if(burn && burn.power > 0 && !p.inWater){
      log(`🔥 ${lname(p)} 的火焰结算（${burn.power} 次）。`,'l-warn');
      for(let i=0;i<burn.power && p.alive;i++) await tryDamage(p,[0,0.5,0,0],{label:'火焰持续伤害'});
    }
    if(burn){ burn.power = 0; p.effects = p.effects.filter(e=>e!==burn); }""", '火焰回合末结算')

# 入水：把火焰次数设为 0
sub("""function removeBurn(p){
  const had = p.effects.some(e=>e.type==='burn'||e.type==='bleed');
  p.effects = p.effects.filter(e=>e.type!=='burn' && e.type!=='bleed');
  if(had) log(`💧 ${lname(p)} 身上的火焰 / 流血被水清除。`,'l-good');
}""",
"""function removeBurn(p){
  const had = p.effects.some(e=>e.type==='burn'||e.type==='bleed');
  for(const e of p.effects) if(e.type==='burn') e.power = 0;      /* 剩余次数置 0：本回合不再结算 */
  p.effects = p.effects.filter(e=>e.type!=='burn' && e.type!=='bleed');
  if(had) log(`💧 ${lname(p)} 身上的火焰 / 流血被水清除（本回合不再受其伤害）。`,'l-good');
}""", '入水置 0')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
