import io

p = 'index.html'
s = io.open(p, encoding='utf-8').read()
orig_len = len(s)

def sub(old, new, label, count=1):
    global s
    assert old in s, '没找到锚点: ' + label
    s = s.replace(old, new, count)
    print('  ok', label)

# ---------------------------------------------------------------- 1) 玩家：seatId / isLocal
sub("""function makePlayer(name, isHuman, team, isEnemy, id){
  return { id, name, isHuman, team, isEnemy, alive:true, hp:4, maxHp:4, ap:0,""",
    """function makePlayer(name, isHuman, team, isEnemy, id){
  return { id, name, isHuman, team, isEnemy, alive:true, hp:4, maxHp:4, ap:0,
    seatId:null, isLocal:false,          /* 联机：座位号 / 是不是本机这位玩家 */""",
    'makePlayer 加 seatId/isLocal')

# ---------------------------------------------------------------- 2) human() → localHuman()
sub("""const human = () => G.players.find(p=>p.isHuman);""",
    """const human = () => G.players.find(p=>p.isHuman);
/* 联机时“我”= 本机座位上的玩家（多真人局里 human() 可能返回对手） */
const localHuman = () => (G && (G.players.find(p=>p.isHuman && p.isLocal) || G.players.find(p=>p.isHuman))) || null;""",
    'localHuman()')

# checkGameEnd 用本机玩家判定胜负
sub("""function checkGameEnd(){
  const me = human();""",
    """function checkGameEnd(){
  const me = localHuman();""",
    'checkGameEnd 用 localHuman')

# ---------------------------------------------------------------- 3) 名单：带 seatId
sub("""    diff: DIFFS[x.diff] ? x.diff : 'normal',
    remote: !!x.remote,          /* 联机房间里的其他真人：本机由 AI 代打 */
    isBot: !!x.isBot,
  }));""",
    """    diff: DIFFS[x.diff] ? x.diff : 'normal',
    remote: !!x.remote,          /* 联机房间里的其他真人 */
    isBot: !!x.isBot,
    seatId: x.seatId || null,    /* 联机座位 id（谁是谁都靠它） */
  }));""",
    'normalizeRoster 保留 seatId')

sub("""      roster: (roster||[]).map(x=>({name:x.name, human:!!x.human, team:x.team|0, diff:x.diff||'normal', remote:!!x.remote, isBot:!!x.isBot}))""",
    """      roster: (roster||[]).map(x=>({name:x.name, human:!!x.human, team:x.team|0, diff:x.diff||'normal', remote:!!x.remote, isBot:!!x.isBot, seatId:x.seatId||null}))""",
    'saveSettings 存 seatId')

# ---------------------------------------------------------------- 4) startGame：seatId / isLocal
sub("""  for(const r of rost.list){
    const team = r.team|0;
    const nm = r.human ? r.name : (r.remote ? r.name + '（远端·AI 代打）' : r.name);
    const p = makePlayer(nm, !!r.human, team, (!r.human) && team!==myTeam, players.length);
    p.diff = r.diff || diffKey;                       /* 每人独立 AI 强度 */
    p.remoteHuman = !!r.remote;                       /* 联机房间里另一个真人（本机 AI 代打） */
    p.isBot = !!r.isBot;
    players.push(p);
  }""",
    """  /* 联机：谁是本机玩家由座位号决定；其他真人也是 human（他们的输入从网络来） */
  const mySeat = (typeof Net !== 'undefined' && Net && Net.youId) ? Net.youId : null;
  const netOn = !!(mySeat && Net && Net.active);
  for(const r of rost.list){
    const team = r.team|0;
    const isMe = !!r.human && (!netOn || !r.seatId || r.seatId === mySeat);
    const p = makePlayer(r.name, !!r.human, team, (!r.human) && team!==myTeam, players.length);
    p.diff = r.diff || diffKey;                       /* 每人独立 AI 强度 */
    p.seatId = r.seatId || null;
    p.isLocal = isMe && !!r.human;
    p.isBot = !!r.isBot;
    players.push(p);
  }""",
    'startGame 设置 seatId/isLocal')

# ---------------------------------------------------------------- 5) rpsPhase：多真人锁步
sub("""async function rpsPhase(){
  rlog('rpsPhase 进入');
  const order=[];
  const me=human();
  if(me.alive) order.push(me);
  for(const p of G.players) if(!p.isHuman && p.alive) order.push(p);
  for(const p of G.players) if(p.alive){ p.actionsUsed=0; }""",
    """async function rpsPhase(){
  rlog('rpsPhase 进入');
  const order=[];
  /* 顺序必须两端一致：先按座位顺序排所有真人，再按固定顺序排 AI */
  for(const p of G.players) if(p.isHuman && p.alive) order.push(p);
  for(const p of G.players) if(!p.isHuman && p.alive) order.push(p);
  for(const p of G.players) if(p.alive){ p.actionsUsed=0; }""",
    'rpsPhase 顺序')

sub("""      const moves = {};
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
      }""",
    """      const moves = {};
      if(netIsOn()){
        /* 联机：本机真人在本地出拳并广播；远端真人的拳等网络送过来；AI 两端各自算（同 seed 同结果） */
        for(const q of live){
          if(!q.alive) continue;
          if(q.isHuman && q.isLocal){
            const mv = await humanRps(q);
            moves[q.id] = mv;
            netSendRps(mv);
          }else if(q.isHuman){
            const mv = await netAskRps(q);
            moves[q.id] = mv || 'rock';
          }else{
            moves[q.id] = await aiRps(q);
          }
        }
      } else {
        for(const q of live){
          if(!q.alive) continue;
          moves[q.id] = q.isHuman ? await humanRps(q) : await aiRps(q);
        }
      }""",
    'rpsPhase 联机分支')

# humanRps 去掉旧的 1v1 联机分支（改由 rpsPhase 负责收发）
sub("""async function humanRps(p){
  rlog('humanRps 进入 autoMode=' + autoMode + ' net=' + netIsOn());
  let my;
  if(netIsOn()){
    document.getElementById('rpsArea').classList.remove('hidden');
    const st0 = document.getElementById('rpsStatus');
    if(st0) st0.textContent = (autoMode ? '自动出拳中…' : '本回合猜拳——选择你的出拳');
    my = autoMode ? pick(['rock','scissors','paper']) : await rpsPrompt(null);
    netSendRps(my);
    const peer = netPeerId();
    const got = peer ? await netWaitRps(peer) : null;
    setLastPeer(got || pick(['rock','scissors','paper']));
    return my;
  }
  if(autoMode){""",
    """async function humanRps(p){
  rlog('humanRps 进入 autoMode=' + autoMode + ' net=' + netIsOn());
  let my;
  if(autoMode){""",
    'humanRps 去掉旧联机分支')

# 自动出拳在联机里不能用引擎 rng（会让两端随机序列错位）
sub("""  if(autoMode){
    my = pick(['rock','scissors','paper']);
    document.getElementById('rpsArea').classList.remove('hidden');""",
    """  if(autoMode){
    /* 联机时这里只是“本机随便出一个”，结果会广播出去，所以绝不能动引擎 rng */
    my = netIsOn() ? ['rock','scissors','paper'][Math.floor(Math.random()*3)] : pick(['rock','scissors','paper']);
    document.getElementById('rpsArea').classList.remove('hidden');""",
    'autoMode 出拳不吃 rng')

# 平局“随机判定”的 rnd 也换成不吃 rng（两端自己算会错位，改成按回合数确定性挑人）
sub("""          const win = live[rnd(live.length)];""",
    """          const win = live[(round + live.length) % live.length];   /* 不用 rng：两端必须选出同一人 */""",
    '平局兜底不吃 rng')

# ---------------------------------------------------------------- 6) takeTurn：远端真人走握手
sub("""    const opts = (isHuman ? buildHumanOptions(p) : aiOptions(p, avoid)).filter(o=>isHuman?canShow(p,o):canPay(p,o));
    const usable = opts.filter(o=>o.type!=='pass' && !avoid.includes(actionKey(o)));
    if(isHuman){
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
      }""",
    """    /* 远端真人的回合：等对方的指令（拆成一次性选项表，网络里只传 id） */
    if(isHuman && netIsOn() && !p.isLocal){
      const done = await netRemoteTurn(p);
      if(done) break;
      continue;
    }
    const opts = (isHuman ? buildHumanOptions(p) : aiOptions(p, avoid)).filter(o=>isHuman?canShow(p,o):canPay(p,o));
    const usable = opts.filter(o=>o.type!=='pass' && !avoid.includes(actionKey(o)));
    if(isHuman){""",
    'takeTurn 远端真人分支')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('部分 1 完成：%d -> %d bytes' % (orig_len, len(s)))
