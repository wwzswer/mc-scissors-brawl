# -*- coding: utf-8 -*-
"""补丁 4b：把联机客户端插入到 MCGame 导出之前"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
html = IDX.read_text(encoding='utf-8')

if 'const Net = {' in html:
    print('已存在联机客户端，跳过'); raise SystemExit

anchor = '/* 自动化测试入口（浏览器控制台或 Node 冒烟测试均可调用） */'
assert anchor in html

block = r"""/* =========================================================================
   局域网联机客户端
   协议：POST /api/create|join|ready|start|action ｜ GET /api/room/<code>/stream(SSE)|events
   ========================================================================= */
const Net = {
  active:false, code:null, youId:null, room:null, seq:0, es:null,
  seats:[], turnId:null, started:false, onLog:[], pending:null,
  api(p, body){
    return fetch(p, {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body||{})}).then(r=>r.json());
  },
  get(p){ return fetch(p).then(r=>r.json()); },
  status(htmlStr){
    const st = document.getElementById('netStatus');
    if(st) st.innerHTML = htmlStr;
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
    return this.api('/api/room/'+this.code+'/join', {name}).then(d=>{
      if(!d.ok) throw new Error(d.err||'加入失败');
      this.active = true; this.youId = d.youId; this.room = d.room;
      this.seats = d.room.seats; this.seq = 0;
      this.connect(); this.render(); return d;
    });
  },
  connect(){
    if(this.es){ try{ this.es.close(); }catch(e){} }
    try{
      this.es = new EventSource('/api/room/'+this.code+'/stream?id='+this.youId);
    }catch(e){ return; }
    this.es.onmessage = ev=>{
      let d; try{ d = JSON.parse(ev.data); }catch(e){ return; }
      this.started = !!d.started; this.turnId = d.turnId || null;
      if(d.seats) this.seats = d.seats;
      this.render(); this.pull();
    };
    this.es.onerror = ()=>{ this.status('房间 '+this.code+'：连接中断，正在自动重连…'); };
  },
  pull(){
    if(!this.active) return Promise.resolve();
    return this.get('/api/room/'+this.code+'/events?id='+this.youId+'&since='+this.seq)
      .then(d=>{
        if(!d || !d.ok) return;
        if(d.seats) this.seats = d.seats;
        this.turnId = d.turnId || null;
        for(const ev of (d.events||[])){
          this.seq = Math.max(this.seq, ev.seq);
          if(ev.actor === this.youId) continue;         /* 自己发的已本地执行 */
          for(const h of this.onLog){ try{ h(ev); }catch(e){} }
        }
        this.render();
      }).catch(()=>{});
  },
  send(action){
    if(!this.active) return Promise.resolve({ok:true, local:true});
    return this.api('/api/room/'+this.code+'/action', {id:this.youId, action})
      .then(d=>{ if(d && d.ok) this.seq = Math.max(this.seq, d.seq||0); return d; })
      .catch(()=>({ok:false}));
  },
  ready(v){
    return this.api('/api/room/'+this.code+'/ready', {id:this.youId, ready:v}).then(d=>{
      if(d.ok){ this.room = d.room; this.seats = d.room.seats; this.render(); } return d;
    }).catch(()=>{});
  },
  start(){
    return this.api('/api/room/'+this.code+'/start', {id:this.youId}).catch(()=>{});
  },
  render(){
    if(!this.active) return;
    const isHost = this.room && this.room.hostId === this.youId;
    const me = this.seats.find(s=>s.id===this.youId) || {};
    const seats = (this.seats||[]).map(s=>
      '<div>'+(s.isHost?'👑 ':'')+'<b>'+s.name+'</b>'+(s.id===this.youId?'（你）':'')+' '+
      (s.ready?'<span style="color:var(--acc)">已准备</span>':'<span style="color:var(--dim)">未准备</span>')+'</div>').join('');
    this.status(
      '<div class="card" style="margin:8px 0 0;background:#141a26">'+
      '<div style="font-size:13px;margin-bottom:6px">房间码：<b style="color:var(--acc2);font-size:19px;letter-spacing:3px">'+this.code+'</b>'+
      '<span style="color:var(--dim);font-size:12px">（把这个告诉朋友）</span></div>'+
      seats +
      '<div class="row" style="margin-top:10px">'+
      '<button class="btn small" id="netReadyBtn">'+(me.ready?'取消准备':'准备')+'</button>'+
      (isHost?'<button class="btn small pri" id="netStartBtn">开始对局</button>':'')+
      '</div></div>');
    const rb = document.getElementById('netReadyBtn');
    if(rb) rb.onclick = ()=>{ const m = this.seats.find(s=>s.id===this.youId)||{}; this.ready(!m.ready); };
    const sb = document.getElementById('netStartBtn');
    if(sb) sb.onclick = ()=>{ this.start(); };
  },
};
function netNeedServer(){
  if(location.protocol === 'file:'){
    Net.status('当前是用 <code>file://</code> 直接打开页面，浏览器不允许联机。<br>'+
      '请在主机上运行 <code>start-server.cmd</code>，然后所有人用 <code>http://主机IP:8787</code> 打开本页。');
    return true;
  }
  return false;
}
function netCreateRoom(){
  if(netNeedServer()) return;
  Net.status('正在创建房间…');
  Net.create(playerName, {mode:gameMode, apPerWin, diff:diffKey})
     .then(()=>{ try{ sfx.win(); }catch(e){} })
     .catch(e=>Net.status('创建失败：'+e.message));
}
function netJoinRoom(){
  if(netNeedServer()) return;
  const el = document.getElementById('roomCode');
  const code = ((el && el.value)||'').trim().toUpperCase();
  if(!/^[A-Z0-9]{9}$/.test(code)){ Net.status('房间码必须是 9 位大写字母或数字。'); return; }
  Net.status('正在加入…');
  Net.join(code, playerName)
     .then(()=>{ try{ sfx.win(); }catch(e){} })
     .catch(e=>Net.status('加入失败：'+e.message));
}
function netRefresh(){
  if(netNeedServer()) return;
  if(Net.active && Net.code){ Net.render(); return; }
  fetch('/api/ping').then(r=>r.json()).then(d=>{
    Net.status('联机服务已连接（端口 '+d.port+'）。可创建房间，或输入朋友给的 9 位房间码加入。');
  }).catch(()=>{
    Net.status('没有连上联机服务。请先运行 <code>start-server.cmd</code>。');
  });
}

"""
html = html.replace(anchor, block + anchor, 1)
IDX.write_text(html, encoding='utf-8')
print(f'联机客户端已插入，文件 {len(html)/1024:.1f} KB')
