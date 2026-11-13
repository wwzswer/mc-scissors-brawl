import io, re, sys

p = 'index.html'
s = io.open(p, encoding='utf-8').read()

NET_JS = r'''const Net = {
  active:false, code:null, youId:null, room:null, slots:[], seats:[], seq:0,
  started:false, hostId:null, seed:null, snapshot:null, spectating:false, launched:false,
  timer:null, onLog:[], pending:null, _lastSlots:'',
  isHost(){ return !!this.hostId && this.hostId === this.youId; },
  mySlot(){ return (this.slots||[]).find(s=>s && s.isYou) || null; },
  api(p, body){
    return fetch(apiBase()+p, {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body||{})}).then(r=>r.json());
  },
  get(p){ return fetch(apiBase()+p).then(r=>r.json()); },
  status(htmlStr){
    const st = document.getElementById('netStatus');
    if(st) st.innerHTML = htmlStr;
  },
  /* 把服务器返回的房间塞进本地状态 */
  applyRoom(d){
    if(!d) return;
    if(d.room) this.room = d.room;
    const room = this.room || {};
    if(Array.isArray(d.slots)) this.slots = d.slots;
    else if(room.slots) this.slots = room.slots;
    if(room.hostId) this.hostId = room.hostId;
    if(room.seed) this.seed = room.seed;
    if(typeof room.started === 'boolean') this.started = room.started;
    this.seats = (this.slots||[]).filter(s=>s && s.kind==='human').map(s=>({id:s.id, name:s.name, team:s.team, ready:s.ready}));
  },
  create(name, opts){
    return this.api('/api/create', Object.assign({name}, opts||{})).then(d=>{
      if(!d.ok) throw new Error(d.err||'创建失败');
      this.active = true; this.code = d.code; this.youId = d.youId;
      this.room = d.room; this.seq = 0; this.launched = false;
      this.applyRoom(d);
      this.connect(); this.renderAll(); return d;
    });
  },
  join(code, name){
    this.code = String(code||'').toUpperCase();
    return this.api('/api/room/'+this.code+'/join', {name}).then(d=>{
      if(!d.ok) throw new Error(d.err||'加入失败');
      this.active = true; this.youId = d.youId;
      this.room = d.room; this.seq = 0; this.launched = false;
      this.applyRoom(d);
      this.connect(); this.renderAll(); return d;
    });
  },
  connect(){
    this.onLog = [ ev => { try{ netHandleEvent(ev); }catch(e){} } ];
    if(this.timer) clearInterval(this.timer);
    const tick = ()=>{ if(this.active) this.pull(); };
    this.timer = setInterval(tick, 600);
    tick();
  },
  stop(){ if(this.timer){ clearInterval(this.timer); this.timer = null; } },
  pull(){
    if(!this.active) return Promise.resolve();
    return this.get('/api/room/'+this.code+'/events?id='+this.youId+'&since='+this.seq)
      .then(d=>{
        if(!d || !d.ok) return;
        if(d.slots) this.slots = d.slots;
        if(d.hostId) this.hostId = d.hostId;
        if(d.seed) this.seed = d.seed;
        if(d.snapshot) this.snapshot = d.snapshot;
        this.seats = (d.seats && d.seats.length) ? d.seats
          : (this.slots||[]).filter(s=>s && s.kind==='human').map(s=>({id:s.id, name:s.name, team:s.team, ready:s.ready}));
        const wasStarted = this.started;
        this.started = !!d.started;
        for(const ev of (d.events||[])){
          this.seq = Math.max(this.seq, ev.seq);
          if(ev.actor === this.youId) continue;
          for(const h of this.onLog){ try{ h(ev); }catch(e){} }
        }
        /* 房主开打了 / 有人刚开打：决定这端是「执棋」还是「观战」 */
        if(this.started && !this.launched && !this.spectating) netOnRoomStarted();
        if(this.spectating) renderSpectate();
        this.renderAll();
        return d;
      }).catch(()=>{});
  },
  send(action){
    if(!this.active) return Promise.resolve({ok:true, local:true});
    return this.api('/api/room/'+this.code+'/action', {id:this.youId, action})
      .then(d=>{ if(d && d.ok) this.seq = Math.max(this.seq, d.seq||0); return d; })
      .catch(()=>({ok:false}));
  },
  ready(v){
    return this.api('/api/room/'+this.code+'/ready', {id:this.youId, ready:v})
      .then(d=>{ if(d.ok) this.applyRoom(d); this.renderAll(); return d; }).catch(()=>{});
  },
  setTeam(slot, team){
    return this.api('/api/room/'+this.code+'/team', {id:this.youId, slot, team})
      .then(d=>{ if(d.ok) this.applyRoom(d); else this.status('<span style="color:var(--red)">'+esc(d.err||'改队伍失败')+'</span>');
        this.renderAll(); return d; }).catch(()=>({ok:false}));
  },
  fillBot(slot){
    return this.api('/api/room/'+this.code+'/bot', {id:this.youId, slot, op:'fill'})
      .then(d=>{ if(d.ok) this.applyRoom(d); else this.status('<span style="color:var(--red)">'+esc(d.err||'加人机失败')+'</span>');
        this.renderAll(); return d; }).catch(()=>({ok:false}));
  },
  updateBot(slot, patch){
    return this.api('/api/room/'+this.code+'/bot', Object.assign({id:this.youId, slot, op:'update'}, patch||{}))
      .then(d=>{ if(d.ok) this.applyRoom(d); this.renderAll(); return d; }).catch(()=>({ok:false}));
  },
  clearBot(slot){
    return this.api('/api/room/'+this.code+'/bot', {id:this.youId, slot, op:'clear'})
      .then(d=>{ if(d.ok) this.applyRoom(d); this.renderAll(); return d; }).catch(()=>({ok:false}));
  },
  transferHost(slot){
    return this.api('/api/room/'+this.code+'/host', {id:this.youId, slot})
      .then(d=>{ if(d.ok) this.applyRoom(d); else this.status('<span style="color:var(--red)">'+esc(d.err||'转让失败')+'</span>');
        this.renderAll(); return d; }).catch(()=>({ok:false}));
  },
  leave(){
    const code = this.code, me = this.youId;
    this.stop();
    this.active = false; this.started = false; this.spectating = false; this.launched = false;
    this.slots = []; this.seats = []; this.code = null; this.snapshot = null;
    try{ sfx.click(); }catch(e){}
    if(code) this.api('/api/room/'+code+'/leave', {id:me}).catch(()=>{});
    const sp = document.getElementById('netSpectate'); if(sp){ sp.classList.add('hidden'); sp.innerHTML=''; }
    const lb = document.getElementById('netLobby'); if(lb) lb.classList.add('hidden');
    this.status('已离开房间。');
  },
  start(){
    return this.api('/api/room/'+this.code+'/start', {id:this.youId})
      .then(d=>{ if(!d.ok) this.status('<span style="color:var(--red)">'+esc(d.err||'开始失败')+'</span>');
        else this.applyRoom(d); this.renderAll(); return d; }).catch(()=>({ok:false}));
  },
  copyBrief(){
    const code = this.code;
    if(!code) return;
    return this.get('/api/room/'+code+'/peek').then(d=>{
      const txt = (d && d.brief) || '（还没拿到战报）';
      copyText(txt);
      this.status('<span style="color:var(--acc)">战报已复制，可以直接贴到 QQ 里。</span>');
      const box = document.getElementById('netSpectate');
      if(box && !box.classList.contains('hidden')){ box.innerHTML = spectateHTML(d); }
      return txt;
    }).catch(()=>{});
  },
  render(){ renderLobby(); },
  renderAll(){ try{ this.render(); }catch(e){} try{ window.renderAll(); }catch(e){} },
};
/* 座位表 / 房间面板渲染 */
function copyText(t){
  try{
    if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(t); return true; }
  }catch(e){}
  try{
    const ta = document.createElement('textarea');
    ta.value = t; ta.style.position='fixed'; ta.style.opacity='0';
    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); return true;
  }catch(e){ return false; }
}
function seatCardHTML(s, idx){
  const me = !!(s && s.isYou);
  const host = !!(s && s.isHost);
  const isBot = !!(s && s.kind==='bot');
  const c = s ? (TEAM_COLORS[s.team|0] || TEAM_COLORS[0]) : null;
  const canEdit = Net.isHost();
  const head = s
    ? `<span class="tchip" style="background:${c.bg};color:${c.fg}">队伍${teamLetter(s.team)}</span>`
    : `<span class="tchip" style="background:#222a3a;color:var(--dim)">空位 ${idx+1}</span>`;
  const who = s
    ? `<div style="font-weight:800;margin:6px 0 2px">${esc(s.name)}${me?'（你）':''}${host?' 👑':''}</div>
       <div class="legend" style="font-size:11.5px">${isBot?'🤖 人机':'🧑 真人'}${isBot?(' · '+(DIFFS[s.diff]||DIFFS.normal).label):''}${s.ready?' · <span style="color:var(--acc)">已准备</span>':''}</div>`
    : `<div class="legend" style="margin:6px 0 2px;font-size:11.5px">还没人坐</div>`;
  let ctrl = '';
  /* 队伍下拉：自己的 / 人机（房主）/ 其他真人（房主） */
  const canTeam = s && (me || canEdit);
  if(canTeam){
    const opts = [0,1,2,3].map(t=>`<option value="${t}"${((s.team|0)===t)?' selected':''}>队伍${teamLetter(t)}</option>`).join('');
    ctrl += `<select class="rsmall" data-act="team" data-slot="${idx}" title="换队伍：同队=队友，异队=敌人">${opts}</select>`;
  }
  if(isBot && canEdit){
    const dopts = Object.keys(DIFFS).map(k=>`<option value="${k}"${((s.diff||'normal')===k)?' selected':''}>${DIFFS[k].label}</option>`).join('');
    ctrl += ` <select class="rsmall" data-act="diff" data-slot="${idx}" title="人机强度">${dopts}</select>`;
    ctrl += ` <button class="btn small" data-act="clear" data-slot="${idx}" title="移除人机">✕</button>`;
  }
  if(!s && canEdit){
    ctrl += `<button class="btn small pri" data-act="fill" data-slot="${idx}">＋ 人机</button>`;
  }
  if(s && !me && canEdit){
    ctrl += ` <button class="btn small" data-act="kick" data-slot="${idx}" title="移出房间">踢</button>`;
    if(s.kind==='human' && !host) ctrl += ` <button class="btn small" data-act="host" data-slot="${idx}" title="把房主转给 TA">给房主</button>`;
  }
  return `<div class="seatcard" style="border:1px solid ${me?'var(--acc)':'var(--line)'};border-radius:10px;padding:8px;background:#141a26">
    <div>${head}</div>${who}<div class="row" style="gap:6px;margin-top:6px">${ctrl || '<span class="legend" style="font-size:11px">—</span>'}</div>
  </div>`;
}
function renderLobby(){
  const box = document.getElementById('netLobby');
  const seatsBox = document.getElementById('netSeats');
  if(!box || !seatsBox) return;
  if(!Net.active){ box.classList.add('hidden'); return; }
  box.classList.remove('hidden');
  const codeEl = document.getElementById('netCode');
  if(codeEl) codeEl.textContent = Net.code || '';
  const slots = Net.slots && Net.slots.length ? Net.slots : new Array(6).fill(null);
  const key = JSON.stringify(slots) + (Net.isHost()?'H':'') + (Net.youId||'');
  if(key !== Net._lastSlots){ Net._lastSlots = key; seatsBox.innerHTML = slots.map(seatCardHTML).join(''); }
  const people = slots.filter(Boolean).length;
  const teams = new Set(slots.filter(Boolean).map(s=>s.team|0)).size;
  const info = document.getElementById('netSeatInfo');
  if(info) info.innerHTML = `座位 ${people}/6 · <b>${teams}</b> 个队伍 · ${Net.isHost()?'你是房主':'房主在管'}`;
  const rb = document.getElementById('netReadyBtn');
  if(rb){
    const me = Net.mySlot();
    rb.textContent = (me && me.ready) ? '取消准备' : '准备';
    rb.onclick = ()=>{ const m = Net.mySlot(); Net.ready(!(m && m.ready)); };
  }
  const sb = document.getElementById('netStartBtn');
  if(sb){
    sb.style.display = Net.isHost() ? '' : 'none';
    sb.disabled = !(people >= 2 && teams >= 2);
    sb.onclick = ()=>{ Net.start(); };
  }
  const hb = document.getElementById('netHostBtn');
  if(hb) hb.style.display = 'none';
  const lv = document.getElementById('netLeaveBtn');
  if(lv) lv.onclick = ()=>{ Net.leave(); };
}
/* 房主开局 / 非房主观战 */
function netRosterFromRoom(){
  const out = [];
  for(const s of (Net.slots||[])){
    if(!s) continue;
    const isMe = !!s.isYou;
    out.push({
      name: s.name,
      human: !!isMe,
      team: s.team|0,
      diff: (s.kind==='bot' ? (s.diff || 'normal') : ((Net.room && Net.room.diff) || 'normal')),
      remote: (s.kind==='human' && !isMe),
      isBot: (s.kind==='bot'),
    });
  }
  return out;
}
function netOnRoomStarted(){
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
}
function spectateHTML(peek){
  const sn = (peek && peek.snapshot) || Net.snapshot || null;
  const slots = (peek && peek.slots) || Net.slots || [];
  const head = `<div style="font-weight:800;margin-bottom:6px">📺 观战：房间 ${esc((peek && peek.code) || Net.code || '')}（房主在执棋）</div>`;
  if(!sn || !sn.players){
    return `<div class="card" style="margin:0;background:#141a26">${head}
      <div class="legend">还没开始 / 还没有局面数据。房主开局后这里会实时刷出来，每 0.8 秒一次。</div></div>`;
  }
  const rows = sn.players.map(p=>{
    const s = slots.find(x=>x && x.name===p.name);
    const c = s ? (TEAM_COLORS[s.team|0]||TEAM_COLORS[0]) : null;
    const tag = s ? `<span class="tchip" style="background:${c.bg};color:${c.fg}">${teamLetter(s.team)}</span>` : '';
    return `<div style="display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center;
      padding:5px 0;border-bottom:1px dashed #1b2231;${p.alive?'':'opacity:.45'}">
      ${tag}<div>${esc(p.name)} <span class="legend" style="font-size:11px">${esc(p.prog||'')}${p.weapon?' / '+esc(p.weapon):''}${p.armor?' / 护甲'+esc(p.armor):''}</span></div>
      <div style="text-align:right;font-weight:700">${p.alive?('<span style="color:var(--red)">'+p.hp+'</span> 血'):'阵亡'} · <span style="color:var(--acc2)">'+p.ap+' AP</span></div>
    </div>`;
  }).join('');
  const logs = (sn.lastLog||[]).slice(-5).map(t=>`<div style="font-size:12px;color:var(--dim)">· ${esc(t)}</div>`).join('');
  return `<div class="card" style="margin:0;background:#141a26">${head}
    <div class="legend" style="margin-bottom:6px">第 <b>${sn.round}</b> 回合 · ${sn.over?'<b style="color:var(--acc2)">已结束</b>':'进行中'} · 模式 ${esc(sn.mode||'')}</div>
    ${rows}
    <div style="margin-top:8px">${logs}</div>
    <div class="legend" style="margin-top:8px">想自己执棋？让房主把「给房主」转给你，或你自己创建一个房间。</div></div>`;
}
function renderSpectate(){
  const el = document.getElementById('netSpectate');
  if(!el || !Net.spectating) return;
  el.classList.remove('hidden');
  el.innerHTML = spectateHTML(null);
}
'''

NET_SCREEN_JS = r'''function netNeedServer(){
  if(location.protocol === 'file:'){
    Net.status(
      '<div style="border:1px solid #e05555;background:#2a1414;border-radius:8px;padding:10px 12px;line-height:1.9">'+
      '<b style="color:#ff7b7b;font-size:14px">⚠ 现在不能联机：你是在用 file:// 直接打开本页</b><br>'+
      '浏览器安全策略禁止 file:// 页面访问联机服务。<b>联机必须通过服务器地址打开</b>：<br>'+
      '① 双击 <code>start-server.cmd</code>（会弹一个黑窗口，别关它）<br>'+
      '② 浏览器会自动打开 <code>http://127.0.0.1:8787</code> —— 请在那个页面里玩联机<br>'+
      '③ 朋友在同一局域网，用黑窗口里显示的 <code>http://192.168.x.x:8787</code> 打开'+
      '</div>');
    return true;
  }
  return false;
}
function netFailHint(kind, err){
  const msg = String((err && err.message) || err || '');
  const offline = /Failed to fetch|NetworkError|Load failed|fetch/i.test(msg);
  if(offline){
    return '<div style="border:1px solid #e05555;background:#2a1414;border-radius:8px;padding:10px 12px;line-height:1.9">'+
      '<b style="color:#ff7b7b">连不上联机服务（'+kind+'失败）</b><br>'+
      '① 确认跑 <code>start-server.cmd</code> 的黑窗口还开着（关掉 = 服务停）<br>'+
      '② 没有就重新双击 <code>start-server.cmd</code>，等浏览器自动打开<br>'+
      (apiBase() ? '③ 当前联机服务器地址是 <code>'+esc(apiBase())+'</code>，确认它对不对<br>' : '③ 服务重启后按 F5 刷新本页再试')+
      '</div>';
  }
  return kind + '失败：' + msg;
}
function netGuessServerURL(){
  try{
    const base = apiBase();
    if(base) return base;
    if(location.protocol==='http:' || location.protocol==='https:'){
      return location.origin;
    }
  }catch(e){}
  return 'http://127.0.0.1:8787';
}
function netCreateRoom(){
  if(netNeedServer()) return;
  if(Net.active) return;
  Net.status('正在创建房间…');
  Net.create(playerName, {mode:gameMode, apPerWin, diff:diffKey})
     .then(()=>{ try{ sfx.win(); }catch(e){} Net.status('房间已创建。把房间码发给朋友（QQ 里发也行），空位可以加人机。'); netShowScreen(); })
     .catch(e=>Net.status(netFailHint('创建房间', e)));
}
function netJoinRoom(){
  if(netNeedServer()) return;
  if(Net.active) return;
  const el = document.getElementById('roomCode');
  const code = ((el && el.value)||'').trim().toUpperCase();
  if(!/^[A-Z0-9]{9}$/.test(code)){ Net.status('房间码必须是 9 位大写字母或数字。'); return; }
  Net.status('正在加入…');
  Net.join(code, playerName)
     .then(()=>{ try{ sfx.win(); }catch(e){} Net.status('已加入。点座位换队伍、空位加人机，等房主开局。'); netShowScreen(); })
     .catch(e=>Net.status(netFailHint('加入房间', e)));
}
function netShowScreen(){
  showScreen('screen-net');
  Net.renderAll();
}
function netAddrDialog(){
  const cur = apiBase();
  const v = prompt('联机服务器地址（留空 = 用当前网页地址）\n例：http://192.168.1.10:8787\n（手机 APK 里必须填电脑的局域网地址）', cur);
  if(v === null) return;
  try{
    const clean = String(v).trim().replace(/\/+$/,'');
    if(clean) localStorage.setItem('mcApiBase', clean); else localStorage.removeItem('mcApiBase');
  }catch(e){}
  Net.status(apiBase() ? ('联机服务器：<code>'+esc(apiBase())+'</code>') : '联机服务器：跟随当前网页地址');
  try{ sfx.click(); }catch(e){}
}
function netRefresh(){
  if(netNeedServer()) return;
  if(Net.active){ Net.renderAll(); return; }
  fetch(apiBase()+'/api/ping').then(r=>r.json()).then(d=>{
    Net.status('联机服务已连接（端口 '+d.port+(d.version?(' · v'+d.version):'')+'）。可创建房间，或输入朋友给的 9 位房间码加入。');
  }).catch(()=>{
    Net.status(
      '<div style="border:1px solid #e05555;background:#2a1414;border-radius:8px;padding:10px 12px;line-height:1.9">'+
      '<b style="color:#ff7b7b">没有连上联机服务</b><br>'+
      '请先双击 <code>start-server.cmd</code>（黑窗口别关），它会自动打开浏览器；<br>'+
      '手机/别处打开的话，点上面的「服务器地址」填电脑的局域网地址。'+
      '</div>');
  });
}
'''

def splice(src, start_marker, end_marker, new_text, label):
    i = src.index(start_marker)
    j = src.index(end_marker, i)
    out = src[:i] + new_text + src[j:]
    print('replaced %-22s %6d -> %6d bytes' % (label, j-i, len(new_text)))
    return out

s = splice(s, 'const Net = {', '/* 房间码 -> 确定性种子', NET_JS, 'Net object')
s = splice(s, 'function netNeedServer(){', '/* 统一的“执行一个动作”入口', NET_SCREEN_JS, 'net screen funcs')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
