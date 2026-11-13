import io

# ============================ 服务端：状态存取 ============================
p = 'server.js'
s = io.open(p, encoding='utf-8').read()

def sub(old, new, label):
    global s
    assert old in s, '没找到: ' + label
    s = s.replace(old, new, 1)
    print('  ok', label)

sub("""          slots, seq:0, log:[], turnId:null, snapshot:null, snapshotAt:0, touched:now()};""",
    """          slots, seq:0, log:[], turnId:null, snapshot:null, snapshotAt:0,
          state:null, stateSeq:0, touched:now()};""",
    '房间字段 state/stateSeq')

sub("""      if(sub === 'snapshot' && req.method === 'POST'){""",
    """      /* 联机对局：房主把整份局面推上来，其他端拉下来渲染 */
      if(sub === 'state' && req.method === 'POST'){
        r.state = body.state || null;
        r.stateSeq = Number(body.seq) || (r.stateSeq || 0) + 1;
        r.touched = now();
        return json(res, {ok:true, seq:r.stateSeq});
      }
      if(sub === 'state' && req.method === 'GET'){
        r.touched = now();
        return json(res, {ok:true, seq:r.stateSeq || 0, state:r.state || null});
      }
      if(sub === 'snapshot' && req.method === 'POST'){""",
    'state 接口')

sub("""          slots: roomView(r, id || null).slots,
          seats: humans(r).map(s=>({id:s.id, name:s.name, team:s.team})),
          snapshot: r.snapshot || null});""",
    """          slots: roomView(r, id || null).slots,
          seats: humans(r).map(s=>({id:s.id, name:s.name, team:s.team})),
          snapshot: r.snapshot || null,
          stateSeq: r.stateSeq || 0});""",
    '/events 带 stateSeq')

sub("""        r.started = true;""",
    """        r.started = true;
        r.state = null; r.stateSeq = 0;""",
    '开局清状态')

# 路由白名单里加 state
sub("""join|ready|start|state|events|action|stream|leave|snapshot|peek|team|bot|host|kick""",
    """join|ready|start|state|events|action|stream|leave|snapshot|peek|team|bot|host|kick""",
    '路由已含 state')

io.open(p, 'w', encoding='utf-8', newline='').write(s)

# ============================ 客户端：拉状态 + isLocal ============================
p = 'index.html'
s = io.open(p, encoding='utf-8').read()

sub("""  /* isEnemy 是相对“我”的：房主存的是相对房主的，这里按本机玩家的队伍重算 */
  const me = G.players.find(p=>p.isHuman && p.isLocal) || null;
  if(me){
    for(const p of G.players) p.isEnemy = (p.team !== me.team) && !p.isHuman;
    if(!G.players.some(p=>p.isHuman && p.isLocal)) me.isLocal = true;
  }""",
    """  /* isLocal / isEnemy 都是相对“我”的：房主存的是他自己的视角，这里按座位号重算 */
  const mySeat = (typeof Net !== 'undefined' && Net.youId) ? Net.youId : null;
  for(const p of G.players){
    p.isLocal = !!(p.isHuman && p.seatId && mySeat && p.seatId === mySeat);
  }
  const me = G.players.find(p=>p.isHuman && p.isLocal) || G.players.find(p=>p.isHuman) || null;
  if(me){
    if(!G.players.some(p=>p.isHuman && p.isLocal)) me.isLocal = true;
    for(const p of G.players) p.isEnemy = (p.team !== me.team) && !p.isHuman;
  }""",
    '访客重算 isLocal/isEnemy')

sub("""        const wasStarted = this.started;
        this.started = !!d.started;""",
    """        /* 访客：房主推了新状态就拉下来 */
        if(typeof NetPlay !== 'undefined' && NetPlay.role === 'guest' && d.stateSeq &&
           d.stateSeq > NetPlay.lastStateSeq && !NetPlay.fetching){
          NetPlay.fetching = true;
          NetPlay.lastStateSeq = d.stateSeq;
          fetch(apiBase() + '/api/room/' + this.code + '/state')
            .then(r=>r.json())
            .then(x=>{ if(x && x.ok && x.state) netGuestApplyState(x.state); })
            .catch(()=>{})
            .then(()=>{ NetPlay.fetching = false; });
        }
        const wasStarted = this.started;
        this.started = !!d.started;""",
    'Net.pull 拉状态')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch3 done')
