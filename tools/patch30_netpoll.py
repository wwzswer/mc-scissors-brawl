# -*- coding: utf-8 -*-
"""补丁 30：修复联机接口挂起
   原因：服务端在处理 /ready、/action 时向 SSE 长连接 res.write()，
        该写操作会让请求处理挂起（长连接背压），导致响应永不返回。
   方案：改用短轮询（客户端每 600ms 拉增量事件），不再持有 SSE 长连接；
        服务端 push() 只维护房间状态、不写长连接。
"""
import pathlib

ROOT = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')

# ---------------- 服务端 ----------------
S = ROOT / 'server.js'
s = S.read_text(encoding='utf-8')
notes = []

def sub_s(old, new, label):
    global s
    if old not in s:
        notes.append('  ! server 未找到 ' + label); return False
    s = s.replace(old, new, 1); notes.append('  ok server ' + label); return True

sub_s("""function push(r){
  r.touched = now();
  const payload = `data: ${JSON.stringify({seq:r.seq, logCount:r.log.length, turnId:r.turnId,
    started:r.started, seats:roomView(r).seats})}\\n\\n`;
  for(const res of r.clients){
    try{ res.write(payload); }catch(e){ r.clients.delete(res); }
  }
}""",
"""/* 只更新房间状态（不再向长连接写入，避免请求处理被背压挂起）。
   客户端通过短轮询 /events 拉增量。 */
function push(r){
  r.touched = now();
  r.version = (r.version||0) + 1;
}""", 'push 改为无 IO')

sub_s("""      if(sub === 'stream' && req.method === 'GET'){
        const id = new URL(url, 'http://x').searchParams.get('id') || '';
        res.writeHead(200, {'Content-Type':'text/event-stream; charset=utf-8','Cache-Control':'no-cache',
          'Connection':'keep-alive','Access-Control-Allow-Origin':'*'});
        res.write(`retry: 1500\\n\\n`);
        r.clients.add(res);
        r.touched = now();
        res.write(`data: ${JSON.stringify({seq:r.seq, logCount:r.log.length, started:r.started, seats:roomView(r).seats})}\\n\\n`);
        const ka = setInterval(()=>{ try{ res.write(': ka\\n\\n'); }catch(e){} }, 20000);
        req.on('close', ()=>{ clearInterval(ka); r.clients.delete(res); });
        return;
      }""",
"""      if(sub === 'stream' && req.method === 'GET'){
        /* 兼容旧客户端：不退化为长连接，直接回一帧状态后结束 */
        const id2 = new URL(url, 'http://x').searchParams.get('id') || '';
        r.touched = now();
        return json(res, {seq:r.seq, logCount:r.log.length, started:r.started, turnId:r.turnId, seats:roomView(r, id2).seats});
      }""", 'stream 改为一次性快照')

# 事件接口补充 seats/started（轮询用）
sub_s("""      if(sub === 'events' && req.method === 'GET'){
        const since = Number(new URL(url,'http://x').searchParams.get('since') || 0);
        return json(res, {ok:true, seq:r.seq, turnId:r.turnId,
          events:r.log.filter(e=>e.seq>since), seats:roomView(r).seats});
      }""",
"""      if(sub === 'events' && req.method === 'GET'){
        const since = Number(new URL(url,'http://x').searchParams.get('since') || 0);
        return json(res, {ok:true, seq:r.seq, turnId:r.turnId, started:r.started,
          mode:r.mode, apPerWin:r.apPerWin, diff:r.diff,
          events:r.log.filter(e=>e.seq>since), seats:roomView(r, id).seats});
      }""", 'events 返回完整状态')

S.write_text(s, encoding='utf-8')

# ---------------- 客户端 ----------------
C = ROOT / 'index.html'
c = C.read_text(encoding='utf-8')

def sub_c(old, new, label):
    global c
    if old not in c:
        notes.append('  ! client 未找到 ' + label); return False
    c = c.replace(old, new, 1); notes.append('  ok client ' + label); return True

sub_c("""  connect(){
    if(this.es){ try{ this.es.close(); }catch(e){} }
    this.onLog = [ ev => { try{ netHandleEvent(ev); }catch(e){} } ];
    try{
      this.es = new EventSource('/api/room/'+this.code+'/stream?id='+this.youId);
    }catch(e){ return; }
    this.es.onmessage = ev=>{
      let d; try{ d = JSON.parse(ev.data); }catch(e){ return; }
      const wasStarted = this.started;
      this.started = !!d.started; this.turnId = d.turnId || null;
      /* 房主点了“开始对局”：所有端用同一 seed 自动开局 */
      if(this.started && !wasStarted && !this._launched){
        this._launched = true;
        const seed = netSeedFromCode(this.code);
        netStartMatch(seed);
      }
      if(d.seats) this.seats = d.seats;
      this.render(); this.pull();
    };
    this.es.onerror = ()=>{ this.status('房间 '+this.code+'：连接中断，正在自动重连…'); };
  },""",
"""  /* 短轮询：每 600ms 拉一次增量（稳定、不受长连接背压影响） */
  connect(){
    this.onLog = [ ev => { try{ netHandleEvent(ev); }catch(e){} } ];
    if(this.timer) clearInterval(this.timer);
    const tick = ()=>{ if(this.active) this.pull(); };
    this.timer = setInterval(tick, 600);
    tick();
  },
  stop(){ if(this.timer){ clearInterval(this.timer); this.timer = null; } },""", 'connect 改轮询')

sub_c("""  pull(){
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
  },""",
"""  pull(){
    if(!this.active) return Promise.resolve();
    return this.get('/api/room/'+this.code+'/events?id='+this.youId+'&since='+this.seq)
      .then(d=>{
        if(!d || !d.ok) return;
        if(d.seats) this.seats = d.seats;
        this.turnId = d.turnId || null;
        const wasStarted = this.started;
        this.started = !!d.started;
        /* 房主点了“开始对局”：所有端用同一 seed 自动开局 */
        if(this.started && !wasStarted && !this._launched){
          this._launched = true;
          netStartMatch(netSeedFromCode(this.code));
        }
        for(const ev of (d.events||[])){
          this.seq = Math.max(this.seq, ev.seq);
          if(ev.actor === this.youId) continue;         /* 自己发的已本地执行 */
          for(const h of this.onLog){ try{ h(ev); }catch(e){} }
        }
        this.render();
      }).catch(()=>{});
  },""", 'pull 处理开局')

C.write_text(c, encoding='utf-8')

print('\n'.join(notes))
print('server.js', round(len(s)/1024,1), 'KB ｜ index.html', round(len(c)/1024,1), 'KB')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    c.split('<script>')[1].split('</script>')[0], encoding='utf-8')
