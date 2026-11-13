# -*- coding: utf-8 -*-
"""补丁 4：确定性随机（种子 RNG）+ 联机客户端
   - 把 8 处 Math.random() 换成种子 RNG 的 R()，让两端在相同种子下完全一致
   - 实现 netCreateRoom / netJoinRoom / NetSession（SSE 收 + POST 发）
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
html = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label, cnt=None):
    global html
    if old not in html:
        notes.append(f'  ! 未找到 {label}'); return
    n = html.count(old)
    if cnt is not None and n != cnt:
        notes.append(f'  ~ {label} 出现 {n} 次（期望 {cnt}）')
    html = html.replace(old, new)
    notes.append(f'  ok {label}')

# ---------- 1) 常量与种子 RNG ----------
sub("""const rnd = n => Math.floor(Math.random()*n);""",
"""/* 确定性随机：同一 seed 下两端序列完全一致（联机同步的前提） */
function mulberry32(a){
  return function(){
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
let rng = mulberry32((Math.random()*2**31)|0);   /* 单机默认随机种子 */
const R = () => rng();
function setSeed(s){ rng = mulberry32((Number(s)|0) || 1); }
const rnd = n => Math.floor(R()*n);""",
'种子 RNG')

sub("""(target.isHuman || Math.random()<0.8)""", """(target.isHuman || R()<0.8)""", '判定闪避随机')
sub("""if((!cfg.readHuman && !opponent.isHuman) || Math.random()>cfg.competence) return pick(moves);""",
    """if((!cfg.readHuman && !opponent.isHuman) || R()>cfg.competence) return pick(moves);""", 'AI 猜拳 competence')
sub("""return Math.random()<0.7 ? counter : pick(moves);""", """return R()<0.7 ? counter : pick(moves);""", 'AI 反制概率')
sub("""return Promise.resolve(Math.random()<0.5?'pierce':'break');""",
    """return Promise.resolve(R()<0.5?'pierce':'break');""", 'AI 钻石剑选择')
sub("""const scored = opts.map(o=>({o, s:score(o) + (Math.random()*14-7)}));""",
    """const scored = opts.map(o=>({o, s:score(o) + (R()*14-7)}));""", 'AI 评分抖动')
sub("""if(Math.random()<cfg.mistake && scored.length>2) return scored[1+rnd(Math.min(2,scored.length-1))].o;""",
    """if(R()<cfg.mistake && scored.length>2) return scored[1+rnd(Math.min(2,scored.length-1))].o;""", 'AI 失误率')
sub("""const chosen = (Math.random()<cfg.mistake && cands.length>1) ? cands[1] : cands[0];""",
    """const chosen = (R()<cfg.mistake && cands.length>1) ? cands[1] : cands[0];""", 'AI 购买失误')

# ---------- 2) 联机客户端 ----------
sub("""/* ---- 联机（阶段一：本机存根，server.js 提供房间服务后接管） ---- */
let netRoom = null;
function netRefresh(){
  const st = document.getElementById('netStatus');
  if(!st) return;
  if(!window.WebSocket || location.protocol==='file:'){
    st.innerHTML = '当前是用 <code>file://</code> 直接打开页面，浏览器不允许联机。<br>请用主机上的 <code>start-server.cmd</code> 启动后，通过 <code>http://局域网IP:8787</code> 打开本页。';
    return;
  }
  st.textContent = netRoom ? `已加入房间 ${netRoom}` : '未连接。可创建房间或输入房间码加入。';
}
on('netCreate', ()=>{ netCreateRoom(); });
on('netJoin', ()=>{ netJoinRoom(); });""",
r"""/* =========================================================================
   局域网联机客户端
   协议：POST /api/create|join|ready|start|action   GET /api/room/<code>/stream(SSE)|events
   ========================================================================= */
const Net = {
  active:false, code:null, youId:null, room:null, seq:0, es:null,
  seats:[], turnId:null, started:false, onLog:[], onTurn:null, pending:null,
  api(p, body){
    return fetch(p, {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body||{})}).then(r=>r.json());
  },
  get(p){ return fetch(p).then(r=>r.json()); },
  status(html){
    const st = document.getElementById('netStatus');
    if(st) st.innerHTML = html;
  },
  setName(name){
    return this.api('/api/room/'+this.code+'/join',{name}).then(d=>{
      if(!d.ok) throw new Error(d.err||'加入失败');
      this.youId = d.youId; this.room = d.room; this.seats = d.room.seats;
      return d;
    });
  },
  create(name, opts){
    return this.api('/api/create', Object.assign({name}, opts||{})).then(d=>{
      if(!d.ok) throw new Error(d.err||'创建失败');
      this.active = true; this.code = d.code; this.youId = d.youId;
      this.room = d.room; this.seats = d.room.seats; this.seq = 0;
      this.connect(); this.render(); return d;
    });
  },
  join(code, name){
    this.code = String(code||'').toUpperCase();
    return this.setName(name).then(d=>{
      this.active = true; this.seq = 0; this.connect(); this.render(); return d;
    });
  },
  connect(){
    if(this.es) try{ this.es.close(); }catch(e){}
    this.es = new EventSource(`/api/room/${this.code}/stream?id=${this.youId}`);
    this.es.onmessage = ev=>{
      let d; try{ d = JSON.parse(ev.data); }catch(e){ return; }
      this.started = !!d.started; this.turnId = d.turnId || null;
      if(d.seats) this.seats = d.seats;
      this.render();
      this.pull();
    };
    this.es.onerror = ()=>{ this.status(`房间 ${this.code}：连接中断，正在重连…`); };
  },
  pull(){
    if(!this.active) return Promise.resolve();
    return this.get(`/api/room/${this.code}/events?id=${this.youId}&since=${this.seq}`)
      .then(d=>{
        if(!d.ok) return;
        if(d.seats) this.seats = d.seats;
        this.turnId = d.turnId || null;
        for(const ev of (d.events||[])){
          this.seq = Math.max(this.seq, ev.seq);
          if(ev.actor === this.youId) continue;        /* 自己发的已本地执行 */
          for(const h of this.onLog) { try{ h(ev); }catch(e){} }
        }
        this.render();
      }).catch(()=>{});
  },
  send(action){
    if(!this.active) return Promise.resolve({ok:true, local:true});
    return this.api(`/api/room/${this.code}/action`, {id:this.youId, action})
      .then(d=>{ if(d.ok) this.seq = Math.max(this.seq, d.seq||0); return d; });
  },
  ready(v){
    return this.api(`/api/room/${this.code}/ready`, {id:this.youId, ready:v}).then(d=>{
      if(d.ok){ this.room = d.room; this.seats = d.room.seats; this.render(); } return d;
    });
  },
  start(){
    return this.api(`/api/room/${this.code}/start`, {id:this.youId}).then(d=>{ return d; });
  },
  render(){
    if(!this.active){ return; }
    const isHost = this.room && this.room.hostId === this.youId;
    const seats = (this.seats||[]).map(s=>
      `<div>${s.isHost?'👑 ':''}<b>${s.name}</b>${s.id===this.youId?'（你）':''} ${s.ready?'<span style="color:var(--acc)">已准备</span>':'<span style="color:var(--dim)">未准备</span>'}</div>`).join('');
    this.status(`
      <div class="card" style="margin:8px 0 0;background:#141a26">
        <div style="font-size:13px;margin-bottom:6px">房间码：<b style="color:var(--acc2);font-size:19px;letter-spacing:3px">${this.code}</b>
          <span style="color:var(--dim);font-size:12px">（把这个告诉朋友）</span></div>
        ${seats}
        <div class="row" style="margin-top:10px">
          <button class="btn small" id="netReadyBtn">${(this.seats.find(s=>s.id===this.youId)||{}).ready?'取消准备':'准备'}</button>
          ${isHost?'<button class="btn small pri" id="netStartBtn">开始对局</button>':''}
        </div>
      </div>`);
    const rb = document.getElementById('netReadyBtn');
    if(rb) rb.onclick = ()=>{ const me = this.seats.find(s=>s.id===this.youId)||{}; this.ready(!me.ready); };
    const sb = document.getElementById('netStartBtn');
    if(sb) sb.onclick = ()=>{ this.start(); };
  },
};
function netCreateRoom(){
  if(location.protocol === 'file:'){ Net.status('请先运行 start-server.cmd，再通过 http://局域网IP:8787 打开本页。'); return; }
  Net.status('正在创建房间…');
  Net.create(playerName, {mode:gameMode, apPerWin, diff:diffKey})
     .then(()=>sfx.win())
     .catch(e=>Net.status('创建失败：'+e.message));
}
function netJoinRoom(){
  if(location.protocol === 'file:'){ Net.status('请先运行 start-server.cmd，再通过 http://局域网IP:8787 打开本页。'); return; }
  const code = (document.getElementById('roomCode').value||'').trim().toUpperCase();
  if(!/^[A-Z0-9]{9}$/.test(code)){ Net.status('房间码必须是 9 位大写字母或数字。'); return; }
  Net.status('正在加入…');
  Net.join(code, playerName)
     .then(()=>sfx.win())
     .catch(e=>Net.status('加入失败：'+e.message));
}
function netRefresh(){
  if(location.protocol === 'file:'){
    Net.status('当前是用 <code>file://</code> 直接打开页面，浏览器不允许联机。<br>请用主机上的 <code>start-server.cmd</code> 启动后，通过 <code>http://局域网IP:8787</code> 打开本页。');
    return;
  }
  if(Net.active && Net.code){ Net.render(); return; }
  fetch('/api/ping').then(r=>r.json()).then(d=>{
    Net.status(`服务已连接（端口 ${d.port}）。可创建房间，或输入朋友给的 9 位房间码加入。`);
  }).catch(()=>{
    Net.status('没有连上联机服务。请先运行 <code>start-server.cmd</code>。');
  });
}
on('netCreate', ()=>{ netCreateRoom(); });
on('netJoin', ()=>{ netJoinRoom(); });""",
'联机客户端')

IDX.write_text(html, encoding='utf-8')
print('\n'.join(notes))
print(f'补丁 4 完成，文件 {len(html)/1024:.1f} KB')
