import io

p = 'index.html'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label):
    global s
    assert old in s, '锚点不存在: ' + label
    s = s.replace(old, new, 1)
    print('  ok', label)

# ================= 0) 玩家统计字段 =================
sub("""    lastRps:null, rpsTally:{rock:0,scissors:0,paper:0}, kills:0, actionsUsed:0, slotsLeft:1, turnSpent:0 };""",
    """    lastRps:null, rpsTally:{rock:0,scissors:0,paper:0}, kills:0, actionsUsed:0, slotsLeft:1, turnSpent:0,
    /* 结算统计 */
    st:{ap:0, dmgMax:0, heal:0, kills:0}, progAtRound:0 };""",
    '玩家统计字段')

# ================= 1) AP 统计 =================
sub("""      for(const w of winners) w.ap += apPerWin;""",
    """      for(const w of winners){ w.ap += apPerWin; if(w.st) w.st.ap += apPerWin; }""",
    'AP 统计')

# ================= 2) 伤害 / 击杀统计（靠"当前攻击者"上下文） =================
sub("""function tryDamage(target, dmg, opts={}){""",
    """let CUR_ATTACKER = null;        /* performAttack 期间指向攻击者，用于统计最高伤害/击杀 */
function tryDamage(target, dmg, opts={}){""",
    'CUR_ATTACKER')

sub("""  log(`${lname(target)} 受到 <b>${total}</b> 点伤害${label?`（${label}：${detail}）`:''} → 生命 ${hpStr(target)}`, 'l-dmg');""",
    """  if(CUR_ATTACKER && CUR_ATTACKER.st && CUR_ATTACKER !== target){
    CUR_ATTACKER.st.dmgMax = Math.max(CUR_ATTACKER.st.dmgMax || 0, total);
  }
  log(`${lname(target)} 受到 <b>${total}</b> 点伤害${label?`（${label}：${detail}）`:''} → 生命 ${hpStr(target)}`, 'l-dmg');""",
    '最高伤害统计')

sub("""  p.alive=false; p.hp=0; p.inWater=false;
  log(`☠️ ${lname(p)} 被击败，退出战斗。`,'l-warn');""",
    """  p.alive=false; p.hp=0; p.inWater=false;
  if(CUR_ATTACKER && CUR_ATTACKER.st && CUR_ATTACKER !== p) CUR_ATTACKER.st.kills = (CUR_ATTACKER.st.kills||0) + 1;
  log(`☠️ ${lname(p)} 被击败，退出战斗。`,'l-warn');""",
    '击杀统计')

sub("""function healPlayer(p, amount, src){
  p.hp = rm(Math.min(p.maxHp, p.hp+amount));""",
    """function healPlayer(p, amount, src){
  const before = p.hp;
  p.hp = rm(Math.min(p.maxHp, p.hp+amount));
  if(p.st) p.st.heal = rm((p.st.heal||0) + Math.max(0, rm(p.hp - before)));""",
    '回血统计')

# performAttack 里设置/清理 CUR_ATTACKER
sub("""function performAttack(attacker, target, key, opts={}){
  return (async ()=>{
    const ranged = !!opts.ranged;""",
    """function performAttack(attacker, target, key, opts={}){
  const __prevAttacker = CUR_ATTACKER;
  CUR_ATTACKER = attacker;
  const __done = ()=>{ CUR_ATTACKER = __prevAttacker; };
  return (async ()=>{
    const ranged = !!opts.ranged;""",
    'performAttack 进入设置攻击者')

# performAttack 有多个 return，统一在 finally 里清理更稳：包一层
sub("""    const prof = attackProfile(attacker, key);
    const hits = [[target,1]];""",
    """    const prof = attackProfile(attacker, key);
    const hits = [[target,1]];""",
    '（占位）')

# ================= 3) 进程达到的回合 =================
sub("""    p.prog += 1;
    leveled = true;""",
    """    p.prog += 1;
    if(typeof p.progAtRound === 'undefined' || !p.progAtRound) p.progAtRound = (G && G.round) || 0;
    leveled = true;""",
    '进程回合统计')

# ================= 4) 开局记开始时间 =================
sub("""  G = { players, round:1, dist:{}, roundOrder:[], over:false, turnOwner:null, progSnap:{}, runId:myRun };""",
    """  G = { players, round:1, dist:{}, roundOrder:[], over:false, turnOwner:null, progSnap:{},
        runId:myRun, startedAt: Date.now() };""",
    '开局时间')

# ================= 5) 结算面板 =================
sub("""function endGame(win){
  if(G.over) return;
  G.over=true;
  const ov=document.getElementById('overlay'), box=document.getElementById('overlayBox');
  box.innerHTML = `<h3 style="font-size:22px;margin:0 0 8px">${win?'🏆 你赢了！':'💀 你被击败了'}</h3>
    <p style="font-size:13.5px;color:var(--dim);line-height:1.8">
      共进行 ${G.round} 个回合。${win?'恭喜成为方块世界的最后赢家。':'再来一局吧——试试先做护甲，或抢下铁砧用于修复。'}</p>
    <p style="font-size:12.5px;color:var(--dim);line-height:1.9;text-align:left">
      ${G.players.map(p=>`${p.name}：${p.alive?rm(p.hp)+' 血':'已阵亡'} · ${PROG_NAME[p.prog]} · ${gearLabel(p)}`).join('<br>')}</p>
    <div class="row" style="justify-content:center;margin-top:14px">
      <button class="btn pri" id="againBtn">再来一局</button></div>`;
  ov.classList.remove('hidden');
  document.getElementById('againBtn').onclick=()=>{ ov.classList.add('hidden'); location.reload(); };
  log(win?'🏆 <b>战斗结束：你获胜！</b>':'💀 <b>战斗结束：你被击败。</b>','l-warn');
}""",
    """function fmtDuration(ms){
  const t = Math.max(0, Math.round((ms||0)/1000));
  const m = Math.floor(t/60), s2 = t%60;
  return m + ' 分 ' + String(s2).padStart(2,'0') + ' 秒';
}
/* 结算榜：返回 [{label, who, value}] */
function settlementRows(){
  const P2 = (G && G.players) || [];
  const pickBest = (valFn, cmp)=>{
    let best = null, bestV = null;
    for(const p of P2){
      const v = valFn(p) || 0;
      if(bestV === null || cmp(v, bestV) > 0){ best = p; bestV = v; }
    }
    return {p:best, v:bestV};
  };
  const rows = [];
  const ap = pickBest(p=>p.st && p.st.ap, (a,b)=>a-b);
  if(ap.p) rows.push({label:'最多行动点', who:ap.p.name, value:ap.v + ' AP'});
  const dm = pickBest(p=>p.st && p.st.dmgMax, (a,b)=>a-b);
  if(dm.p) rows.push({label:'最高单次伤害', who:dm.p.name, value:dm.v + ' 点'});
  const kl = pickBest(p=>p.st && p.st.kills, (a,b)=>a-b);
  if(kl.p) rows.push({label:'最多击杀', who:kl.p.name, value:kl.v + ' 人'});
  const hl = pickBest(p=>p.st && p.st.heal, (a,b)=>a-b);
  if(hl.p) rows.push({label:'最多回血', who:hl.p.name, value:rm(hl.v) + ' 点'});
  /* 进程最高；并列时取最早达到的（progAtRound 小的） */
  let bestProg = null;
  for(const p of P2){
    if(!bestProg) { bestProg = p; continue; }
    const a = p.prog, b = bestProg.prog;
    if(a > b){ bestProg = p; continue; }
    if(a === b){
      const ra = p.progAtRound || 9999, rb = bestProg.progAtRound || 9999;
      if(ra < rb) bestProg = p;
    }
  }
  if(bestProg){
    rows.push({label:'进程最高', who:bestProg.name,
      value: PROG_NAME[bestProg.prog] + (bestProg.progAtRound ? `（第 ${bestProg.progAtRound} 回合）` : '')});
  }
  return rows;
}
function settlementHTML(win){
  const rows = settlementRows();
  const dur = fmtDuration((G.startedAt ? Date.now() - G.startedAt : 0));
  const teams = new Set((G.players||[]).map(p=>p.team)).size;
  const info = [
    ['对局时间', dur],
    ['回合数', G.round + ' 回合'],
    ['参战', (G.players||[]).length + ' 人 · ' + teams + ' 个队伍'],
  ];
  const me = (G.players||[]).find(q=>q.isHuman && q.isLocal) || (G.players||[]).find(q=>q.isHuman);
  return `
  <button class="sp-close" id="spClose" aria-label="关闭">✕</button>
  <h3 style="font-size:20px;margin:0 0 2px">${win?'🏆 你赢了！':'💀 你被击败了'}</h3>
  <div class="legend" style="margin-bottom:10px">${me ? esc(me.name) + ' · ' : ''}${PROG_NAME[me?me.prog:0] || ''}${me && me.alive ? ' · 存活' : (me?' · 已阵亡':'')}</div>
  <div class="sec" style="margin-top:0">对局信息</div>
  ${info.map(([k,v])=>`<div class="sp-row"><span class="k">${k}</span><span class="v">${esc(v)}</span></div>`).join('')}
  <div class="sec" style="margin-top:10px">本局记录</div>
  ${rows.map(r=>`<div class="sp-row"><span class="k"><span class="sp-badge">${r.label}</span></span><span class="v">${esc(r.who)} · ${esc(r.value)}</span></div>`).join('')}
  <details style="margin-top:10px"><summary class="legend" style="cursor:pointer">查看每人总结</summary>
    <div class="legend" style="line-height:1.9;margin-top:6px">
      ${(G.players||[]).map(p=>`${esc(p.name)}：${p.alive?rm(p.hp)+' 血':'已阵亡'} · ${PROG_NAME[p.prog]} · ${gearLabel(p)}`).join('<br>')}
    </div></details>
  <div class="row" style="justify-content:center;margin-top:14px;gap:8px">
    <button class="btn pri" id="againBtn">再来一局</button>
    <button class="btn small" id="spClose2">关闭</button>
  </div>`;
}
function endGame(win){
  if(G.over) return;
  G.over=true;
  clearTempGame();                      /* 结算即作废临时存档 */
  const ov=document.getElementById('overlay'), box=document.getElementById('overlayBox');
  box.innerHTML = settlementHTML(win);
  box.classList.add('settlebox');
  ov.classList.add('settle');
  ov.classList.remove('hidden');
  const close = ()=>{ ov.classList.add('hidden'); ov.classList.remove('settle'); box.classList.remove('settlebox'); };
  const b1 = document.getElementById('spClose'); if(b1) b1.onclick = close;
  const b2 = document.getElementById('spClose2'); if(b2) b2.onclick = close;
  const ab = document.getElementById('againBtn');
  if(ab) ab.onclick = ()=>{ ov.classList.add('hidden'); location.reload(); };
  log(win?'🏆 <b>战斗结束：你获胜！</b>':'💀 <b>战斗结束：你被击败。</b>','l-warn');
}""",
    '结算面板')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch2 完成: %d -> %d bytes' % (n0, len(s)))
