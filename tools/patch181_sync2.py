import io

p = 'index.html'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label, count=1):
    global s
    assert old in s, '没找到锚点: ' + label
    s = s.replace(old, new, count)
    print('  ok', label)

# ---------------------------------------------------------------- 1) 事件解析扩展
sub("""/* 收到远端事件 */
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
"""/* 收到远端事件 */
function netHandleEvent(ev){
  const a = ev.action || {};
  if(a.kind === 'rps'){ netIn.rps[ev.actor] = a.move; return; }
  if(a.kind === 'act'){
    netIn.act[ev.actor] = netIn.act[ev.actor] || [];
    netIn.act[ev.actor].push(a.action);
    return;
  }
  if(a.kind === 'seed' && typeof a.seed === 'number'){ setSeed(a.seed); return; }
  /* ---- 联机对局同步：提问 / 回答 ---- */
  if(a.kind === 'ask'){
    if(typeof NetPlay !== 'undefined' && NetPlay.role === 'guest'){
      NetPlay.ask = { promptId: a.promptId, ask: a.ask };
      netGuestPrompt(a.ask, a.list || [], a.ask === 'rps' ? '✊ 猜拳：你出什么？'
        : a.ask === 'dodge' ? '🛡 对手判定平局：花 1 AP 闪避吗？' : '🎯 轮到你行动');
    }
    return;
  }
  if(a.kind === 'ans'){
    const w = (typeof NetPlay !== 'undefined') ? NetPlay.waiting : null;
    if(w && w.seatId === ev.actor && (!a.promptId || a.promptId === w.promptId)){
      try{ clearTimeout(w.timer); }catch(e){}
      NetPlay.waiting = null;
      w.resolve(a);
    }
    return;
  }
}""",
    'netHandleEvent 扩展 ask/ans')

# ---------------------------------------------------------------- 2) 主体：同步运行时（插在 netStartMatch 之前）
SYNC = r'''
/* =========================================================================
   联机对局同步（房主权威）
   -------------------------------------------------------------------------
   房主 host：只跑一份引擎，负责所有结算；轮到远端真人时发“提问”等回答。
   访客 guest：不跑引擎，只接收房主推来的局面并渲染；把本地选择发回去。
   这样不存在两端 RNG 失步问题——局面永远只有一份真相。
   ========================================================================= */
const NetPlay = {
  role: null,          /* 'host' | 'guest' */
  seq: 0,              /* 提问/状态自增号 */
  lastStateSeq: 0,     /* 访客已应用的状态版本 */
  lastPush: 0,
  ask: null,           /* 访客当前待回答的提问 */
  waiting: null,       /* 房主当前在等谁回答 */
};
const NET_ASK_TIMEOUT = 180000;
const netIsHostEngine = () => NetPlay.role === 'host';
const netIsGuestView = () => NetPlay.role === 'guest';

/* ---------------- 房主：问远端要一个决定 ---------------- */
function netAskSeat(p, kind, list){
  const seatId = p && p.seatId;
  return new Promise(resolve=>{
    if(!seatId || !Net.active){ resolve(null); return; }
    const promptId = 'q' + (++NetPlay.seq) + '-' + Math.random().toString(36).slice(2, 7);
    NetPlay.waiting = { seatId, promptId, resolve, timer:null };
    Net.send({ kind:'ask', ask:kind, promptId, list:list||[], name:p.name });
    setNetWaitHint(`等待 ${p.name} ${kind==='rps'?'出拳':kind==='dodge'?'决定闪避':'行动'}…`);
    NetPlay.waiting.timer = setTimeout(()=>{
      if(NetPlay.waiting && NetPlay.waiting.promptId === promptId){
        NetPlay.waiting = null;
        setNetWaitHint('');
        resolve(null);
      }
    }, NET_ASK_TIMEOUT);
  });
}
async function netAskRps(p){
  const ans = await netAskSeat(p, 'rps', [
    {id:'rock',     label:'✊ 石头', move:'rock'},
    {id:'scissors', label:'✌️ 剪刀', move:'scissors'},
    {id:'paper',    label:'✋ 布',   move:'paper'},
  ]);
  setNetWaitHint('');
  return (ans && ans.move) || null;
}
/* 把人类可用的行动 + 商店/护甲命令摊平成一张表（网络里只传 id） */
function netShopOptions(p){
  const out = [];
  const next = p.prog + 1;
  if(UPGRADE[next] && p.ap >= 1){
    out.push({ label:`⬆️ 投入 1 步进程进度 → ${PROG_NAME[next]}（1 AP）`,
               shop:{type:'upgrade'}, cost:1, group:'进程' });
  }
  for(const k of Object.keys(ITEMS)){
    const it = ITEMS[k];
    if(k === 'god_apple' && !featOn('god_apple')) continue;
    if(k === 'tnt' && !featOn('tnt')) continue;
    if(it.prog > p.prog) continue;
    if(it.build){ if(!buildAllowed(p, k)) continue; }
    else{
      if(!it.repeat && hasItem(p, k)) continue;
      if(it.need && !hasItem(p, it.need)) continue;
    }
    const cost = it.build ? BUILD_COST : 1;
    if(p.ap < cost) continue;
    out.push({ label:`🛠 ${it.build ? (p.buildings[k] ? '进入 ' : '前往 ') : (itemProgress(p,k)>0?'推进 ':'制作 ')}${it.name}（${cost} AP）`,
               shop:{type:'craft', key:k}, cost, group:'商店' });
  }
  /* 护甲优先顺序（不花 AP，只是换个顺序） */
  const ars = armorsOf(p);
  if(ars.length > 1){
    for(const a of ars){
      out.push({ label:`🛡 优先消耗：${a.name || a.key}`, shop:{type:'armorPriority', key:a.key}, cost:0, group:'装备' });
    }
  }
  return out;
}
function netOptionList(p){
  const out = [];
  for(const o of buildHumanOptions(p).filter(o=>canShow(p, o))){
    if(o.type === 'shop_progress' || o.type === 'shop_craft') continue;   /* 商店改平铺 */
    out.push({ label:o.label, opt:o, cost:o.cost || 0, group:'行动' });
  }
  for(const c of netShopOptions(p)) out.push(c);
  return out.map((x, i)=>Object.assign({id:'o'+i}, x));
}
async function netRemoteTurn(p){
  let guard = 0;
  while(p.alive && !G.over && guard++ < 40){
    if(G.turnSpent >= 8) break;
    const list = netOptionList(p);
    const ans = await netAskSeat(p, 'act', list);
    setNetWaitHint('');
    if(!ans){ log(`⌛ ${lname(p)} 太久没回应，跳过他的行动。`, 'l-warn'); return false; }
    if(ans.pass) return true;
    const item = list.find(x=>x.id === ans.id);
    if(!item) continue;
    try{
      if(item.shop){
        if(item.shop.type === 'armorPriority') setArmorPriority(p, item.shop.key);
        else applyShopAction(p, item.shop);
      }else{
        await runAction(p, item.opt);
      }
    }catch(e){ log('（远端动作执行出错：' + (e && e.message) + '）', 'l-warn'); }
    renderAll();
  }
  return true;
}
/* 等待提示（右下角小条） */
function setNetWaitHint(txt){
  try{
    let el = document.getElementById('netWaitHint');
    if(!el){
      el = document.createElement('div');
      el.id = 'netWaitHint';
      el.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);bottom:14px;z-index:9997;'+
        'background:#1b2130;border:1px solid var(--line);color:var(--text,#e8ecf5);padding:7px 14px;'+
        'border-radius:999px;font-size:12.5px;box-shadow:0 8px 24px rgba(0,0,0,.45);display:none';
      document.body.appendChild(el);
    }
    el.textContent = txt || '';
    el.style.display = txt ? 'block' : 'none';
  }catch(e){}
}

/* ---------------- 房主：把局面推给所有端 ---------------- */
function netSerializeGame(){
  if(!G) return null;
  return {
    seq: ++NetPlay.seq,
    round: G.round,
    over: !!G.over,
    turnOwner: G.turnOwner,
    dist: G.dist,
    phase: (document.getElementById('phasePill') || {}).textContent || '',
    apPerWin,
    mode: gameMode,
    players: G.players.map(p=>Object.assign({}, p)),
    log: (G.logLines || []).slice(-90),
  };
}
function netPushState(){
  if(!netIsHostEngine() || !Net.active || !G) return;
  const now = Date.now();
  if(now - NetPlay.lastPush < 250) return;
  NetPlay.lastPush = now;
  let st;
  try{ st = netSerializeGame(); }catch(e){ return; }
  if(!st) return;
  try{
    fetch(apiBase() + '/api/room/' + Net.code + '/state', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ id: Net.youId, seq: st.seq, state: st })
    }).catch(()=>{});
  }catch(e){}
}

/* ---------------- 访客：把状态画出来 ---------------- */
function netGuestApplyState(st){
  if(!st || !Array.isArray(st.players)) return;
  const runId = (G && G.runId) || 1;
  G = {
    players: st.players.map(p=>Object.assign({}, p)),
    round: st.round || 1,
    dist: st.dist || {},
    roundOrder: [],
    over: !!st.over,
    turnOwner: st.turnOwner,
    progSnap: {},
    runId,
    logLines: st.log || [],
    guest: true,
  };
  /* isEnemy 是相对“我”的：房主存的是相对房主的，这里按本机玩家的队伍重算 */
  const me = G.players.find(p=>p.isHuman && p.isLocal) || null;
  if(me){
    for(const p of G.players) p.isEnemy = (p.team !== me.team) && !p.isHuman;
    if(!G.players.some(p=>p.isHuman && p.isLocal)) me.isLocal = true;
  }
  try{ renderAll(); }catch(e){}
  try{
    if(st.phase){ const el = document.getElementById('phasePill'); if(el) el.textContent = st.phase; }
    const rp = document.getElementById('roundPill'); if(rp) rp.textContent = '回合 ' + (st.round||1);
    const tp = document.getElementById('turnPill');
    if(tp) tp.textContent = (st.turnOwner!=null && G.players[st.turnOwner])
      ? ('当前行动：' + G.players[st.turnOwner].name) : '';
  }catch(e){}
  renderGuestLog(st.log || []);
  if(st.over) netGuestResult();
}
function renderGuestLog(lines){
  const el = document.getElementById('log');
  if(!el) return;
  el.innerHTML = (lines || []).map(x=>{
    if(typeof x === 'string') return '<div>' + x + '</div>';
    return '<div class="' + (x.c || '') + '">' + (x.h || '') + '</div>';
  }).join('');
  el.scrollTop = el.scrollHeight;
}
function netGuestResult(){
  try{
    const me = G && G.players.find(p=>p.isHuman && p.isLocal);
    const foes = (G && G.players.filter(p=>!p.isHuman && p.team !== (me ? me.team : -1))) || [];
    const win = me ? me.alive && foes.every(f=>!f.alive) : false;
    const ov = document.getElementById('overlay');
    const box = document.getElementById('overlayBox');
    if(!ov || !box) return;
    box.innerHTML = `<h3 style="font-size:22px;margin:0 0 8px">${win ? '🏆 你们赢了！' : '💀 这一局输了'}</h3>
      <p style="font-size:13.5px;color:var(--dim);line-height:1.8">共进行 ${G.round} 个回合（房主的引擎结算）。</p>
      <div class="row" style="justify-content:center;margin-top:14px">
        <button class="btn pri" id="againBtn">再来一局</button></div>`;
    ov.classList.remove('hidden');
    const b = document.getElementById('againBtn');
    if(b) b.onclick = ()=>{ location.reload(); };
  }catch(e){}
}

/* ---------------- 访客：提问面板 ---------------- */
function ensureNetAskBox(){
  let box = document.getElementById('netAsk');
  if(!box){
    box = document.createElement('div');
    box.id = 'netAsk';
    box.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);bottom:10px;z-index:9996;'+
      'width:min(720px,calc(100vw - 20px));max-height:52vh;overflow:auto;display:none;'+
      'background:linear-gradient(180deg,#1b2130,#151a22);border:1px solid var(--acc);border-radius:14px;'+
      'padding:12px;box-shadow:0 14px 40px rgba(0,0,0,.6);font-size:13px';
    document.body.appendChild(box);
  }
  return box;
}
function netGuestPrompt(kind, list, title){
  const box = ensureNetAskBox();
  box.style.display = 'block';
  box.innerHTML = `<div style="font-weight:800;margin-bottom:8px;color:var(--acc)">${esc(title || '轮到你')}</div>`;
  const row = document.createElement('div');
  row.className = 'row';
  row.style.gap = '8px';
  const send = (extra)=>{
    const q = NetPlay.ask || {};
    Net.send(Object.assign({kind:'ans', promptId:q.promptId}, extra));
    NetPlay.ask = null;
    box.style.display = 'none';
  };
  for(const item of (list || [])){
    const b = document.createElement('button');
    b.className = 'btn small' + (kind === 'rps' ? ' pri' : '');
    b.textContent = item.label || String(item);
    b.onclick = ()=>{ try{ sfx.click(); }catch(e){} send({ id:item.id, move:item.move }); };
    row.appendChild(b);
  }
  if(kind === 'act'){
    const pass = document.createElement('button');
    pass.className = 'btn small';
    pass.textContent = '⏭ 结束行动';
    pass.onclick = ()=>{ try{ sfx.click(); }catch(e){} send({ pass:true }); };
    row.appendChild(pass);
  }
  box.appendChild(row);
  if(kind === 'act' && (list||[]).length === 0){
    const tip = document.createElement('div');
    tip.className = 'legend';
    tip.style.marginTop = '6px';
    tip.textContent = '没有可用行动（AP 不够 / 距离不够），可以直接结束行动。';
    box.appendChild(tip);
  }
}

'''
sub("/* 房主开打了 / 有人刚开打：决定这端是「执棋」还是「观战」 */",
    SYNC + "/* 房主开打了 / 有人刚开打：决定这端是「执棋」还是「观战」 */",
    '插入同步运行时')

# ---------------------------------------------------------------- 3) 开局：两端都进对局（访客不进引擎循环）
sub("""function netOnRoomStarted(){
  const me = Net.mySlot();
  if(me && Net.isHost()){
    Net.launched = true;
    try{
      roster = normalizeRoster(netRosterFromRoom()).list.map((x,i)=>({...x}));
      /* 保留 remote 标记，方便开局日志区分「远端真人（本机代打）」 */
      const raw = netRosterFromRoom();
      roster = raw.map((x,i)=>({name:x.name, human:x.human, team:x.team, diff:x.diff, remote:x.remote}));
      saveSettings();
    }catch(e){}
    const seed = Net.seed || netSeedFromCode(Net.code);
    netStartMatch(seed);
  }else{
    Net.spectating = true;
    renderSpectate();
  }
}""",
"""function netOnRoomStarted(){
  const me = Net.mySlot();
  if(!me){                                  /* 不在座位上：只能观战 */
    Net.spectating = true;
    renderSpectate();
    return;
  }
  Net.launched = true;
  Net.spectating = false;
  NetPlay.role = Net.isHost() ? 'host' : 'guest';
  try{
    const raw = netRosterFromRoom();
    roster = raw.map(x=>({ name:x.name, human:x.human, team:x.team, diff:x.diff,
                           remote:x.remote, isBot:x.isBot, seatId:x.seatId }));
    ensureRoster();
    saveSettings();
  }catch(e){}
  const seed = Net.seed || netSeedFromCode(Net.code);
  if(NetPlay.role === 'host'){
    netStartMatch(seed);
  }else{
    /* 访客：不跑引擎，等房主推状态过来 */
    setSeed(seed);
    showScreen('game');
    const lg = document.getElementById('log');
    if(lg) lg.innerHTML = '<div class="l-sys">🌐 已连上房主的对局，正在接收局面…</div>';
    const mp = document.getElementById('modePill');
    if(mp) mp.textContent = '联机对局';
    NetPlay.lastStateSeq = 0;
  }
}""",
    'netOnRoomStarted 双端进对局')

# ---------------------------------------------------------------- 4) 名单带上 seatId
sub("""    out.push({
      name: s.name,
      human: !!isMe,
      team: s.team|0,
      diff: (s.kind==='bot' ? (s.diff || 'normal') : ((Net.room && Net.room.diff) || 'normal')),
      remote: (s.kind==='human' && !isMe),
      isBot: (s.kind==='bot'),
    });""",
"""    out.push({
      name: s.name,
      human: (s.kind === 'human'),        /* 联机时所有真人座位都是 human（谁本机由 seatId 判定） */
      team: s.team|0,
      diff: (s.kind==='bot' ? (s.diff || 'normal') : ((Net.room && Net.room.diff) || 'normal')),
      remote: (s.kind==='human' && !isMe),
      isBot: (s.kind==='bot'),
      seatId: s.kind==='human' ? s.id : null,
    });""",
    'netRosterFromRoom 带 seatId')

# ---------------------------------------------------------------- 5) startGame：访客不跑主循环
sub("""  renderAll();
  if(!silentStart) gameLoop();""",
"""  renderAll();
  if(!silentStart && !netIsGuestView()) gameLoop();""",
    'startGame 访客不跑主循环')

# ---------------------------------------------------------------- 6) renderAll 末尾推状态
sub("""  try{ pushSnapshot(); }catch(e){}
}""",
"""  try{ pushSnapshot(); }catch(e){}
  try{ if(typeof netPushState === 'function' && netIsHostEngine()) netPushState(); }catch(e){}
}""",
    'renderAll 推送状态')

# ---------------------------------------------------------------- 7) 快照只由房主上传
sub("""function pushSnapshot(){
  try{
    if(!Net || !Net.active || !Net.code) return;      /* 单机模式直接跳过 */""",
"""function pushSnapshot(){
  try{
    if(!Net || !Net.active || !Net.code) return;      /* 单机模式直接跳过 */
    if(typeof netIsGuestView === 'function' && netIsGuestView()) return;   /* 访客不冒充房主上报 */""",
    'pushSnapshot 只房主上报')

# ---------------------------------------------------------------- 8) askDodge：远端防御者走握手
sub("""function askDodge(target, attacker){
  return new Promise(res=>{""",
"""function askDodge(target, attacker){
  if(netIsOn() && target && target.isHuman && !target.isLocal){
    return netAskSeat(target, 'dodge', [
      {id:'yes', label:'🛡 花 1 AP 闪避'},
      {id:'no',  label:'🎲 不花 AP，继续判定'},
    ]).then(ans => { setNetWaitHint(''); return !!(ans && ans.id === 'yes'); });
  }
  return new Promise(res=>{""",
    'askDodge 远端握手')

# ---------------------------------------------------------------- 9) 日志进 G.logLines（供推送）
sub("""function log(msg, cls){
  const el=document.getElementById('log'); if(!el) return;""",
"""function log(msg, cls){
  /* 顺便记一份到 G.logLines：联机时房主要把这些日志推给访客端 */
  try{
    if(G){
      G.logLines = G.logLines || [];
      G.logLines.push({h: msg, c: cls || ''});
      if(G.logLines.length > 400) G.logLines = G.logLines.slice(-300);
    }
  }catch(e){}
  const el=document.getElementById('log'); if(!el) return;""",
    'log 记录到 G.logLines')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch2: %d -> %d bytes' % (n0, len(s)))
