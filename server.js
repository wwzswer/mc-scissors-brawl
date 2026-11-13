/* =========================================================================
   方块猜拳战场 · 局域网联机服务器
   - 零依赖：只用 Node 内置模块（node:http / node:crypto），Node 18+ 即可
   - 静态托管本目录（index.html / 图标 / manifest / sw.js）
   - 房间系统：9 位大写字母+数字房间码
   - 座位制：6 个座位，每座有队伍(A/B/C/D)，空位可填人机；开局用同一份座位表
   - 实时同步：客户端短轮询 /events 拉增量；房主每 0.8s 上报局面 /snapshot
   - /peek：凭房间码只读看局（QQ 机器人「她」读战报就用它）
   用法： node server.js [端口]       默认端口 8787
   ========================================================================= */
const http = require('node:http');
const fs   = require('node:fs');
const path = require('node:path');
const os   = require('node:os');
const crypto = require('node:crypto');
const { exec } = require('node:child_process');

const ROOT = __dirname;
const PORT = Number(process.argv[2] || process.env.PORT || 8787);
const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';   /* 9 位房间码用的字符集 */
const VERSION = (() => {
  try{ return JSON.parse(fs.readFileSync(path.join(ROOT, 'version.json'), 'utf8')).version || '0.0.0'; }
  catch(e){ return '0.0.0'; }
})();

/* ------------------------------ 工具 ------------------------------ */
const now = () => Date.now();
const SLOT_COUNT = 6;                  /* 一个房间最多 6 个座位 */
const TEAM_LETTERS = ['A','B','C','D'];
const DIFF_LABEL = { easy:'简单', normal:'普通', hard:'困难' };
const AI_NAMES = ['史蒂夫','爱丽克丝','僵尸队长','苦力怕','末影人','骷髅弓手'];

const teamLetter = t => TEAM_LETTERS[Math.max(0, Math.min(3, (t|0)))];
const uid = () => crypto.randomBytes(8).toString('hex');
function makeCode(){
  let code;
  do{
    code = Array.from({length:9}, ()=>ALPHABET[crypto.randomInt(ALPHABET.length)]).join('');
  } while(rooms.has(code));
  return code;
}
const json = (res, obj, code=200) => {
  const body = JSON.stringify(obj);
  res.writeHead(code, {'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store',
    'Access-Control-Allow-Origin':'*'});
  res.end(body);
};
const readBody = req => new Promise(resolve=>{
  let d=''; req.on('data', c=>{ d+=c; if(d.length>2e6) req.destroy(); });
  req.on('end', ()=>{ try{ resolve(d?JSON.parse(d):{}); }catch(e){ resolve({}); } });
});

/* ------------------------------ 房间模型 ------------------------------ */
/* room = {
     code, hostId, mode, apPerWin, diff, started, seed,
     slots: [null | { kind:'human'|'bot', id, name, team:0..3, ready, diff? }],   // 固定 6 格
     log:[{seq,actor,action}], seq, turnId, snapshot, snapshotAt, touched
   } */
const rooms = new Map();
setInterval(()=>{                       // 清理 3 小时无活动的房间
  const t = now();
  for(const [code, r] of rooms) if(t - r.touched > 3*3600*1000) rooms.delete(code);
}, 600000).unref?.();

const occupants = r => r.slots.filter(Boolean);
const humans = r => r.slots.filter(s=>s && s.kind==='human');
const teamCount = r => new Set(occupants(r).map(s=>s.team)).size;
function slotOf(r, id){ return r.slots.findIndex(s=>s && s.kind==='human' && s.id===id); }
function botSlotOf(r, slot){ const s=r.slots[slot]; return (s && s.kind==='bot') ? s : null; }
function teamPop(r, team){ return occupants(r).filter(s=>s.team===team).length; }
/* 新人类进房时默认队伍：空房对手优先，否则补人少的队 */
function defaultTeamFor(r, preferEnemyOf){
  const counts = [0,1,2,3].map(t=>teamPop(r,t));
  if(preferEnemyOf !== undefined && counts[preferEnemyOf] > 0){
    const others = [0,1,2,3].filter(t=>t!==preferEnemyOf).sort((a,b)=>counts[a]-counts[b]);
    if(others.length) return others[0];
  }
  let best = 0;
  for(let t=1;t<4;t++) if(counts[t] < counts[best]) best = t;
  return best;
}
function freeSlot(r){
  const i = r.slots.findIndex(s=>!s);
  return i;
}
function nextBotName(r){
  const used = new Set(occupants(r).map(s=>s.name));
  for(const n of AI_NAMES) if(!used.has(n)) return n;
  for(let i=1;i<99;i++) if(!used.has('人机'+i)) return '人机'+i;
  return '人机';
}
function slotView(r, s, forId){
  if(!s) return null;
  return {
    kind: s.kind, id: s.kind==='human' ? (s.id === forId ? s.id : s.id) : s.id,
    name: s.name, team: s.team|0, ready: !!s.ready,
    isHost: s.kind==='human' && s.id === r.hostId,
    isYou: s.kind==='human' && s.id === forId,
    diff: s.diff || r.diff || 'normal',
  };
}
function roomView(r, forId){
  return {
    code:r.code, mode:r.mode, apPerWin:r.apPerWin, diff:r.diff, started:!!r.started,
    hostId:r.hostId, youId:forId||null, seq:r.seq, seed:r.seed || null,
    slotCount: SLOT_COUNT,
    slots: r.slots.map(s=>slotView(r, s, forId)),
    teams: teamCount(r),
    snapshotAt: r.snapshotAt || 0,
  };
}
/* 只更新房间状态（客户端靠短轮询拉增量） */
function push(r){ r.touched = now(); r.version = (r.version||0) + 1; }

/* ------------------------------ 战报 ------------------------------ */
/* 给 QQ 机器人 / 观战者看的中文战报：谁能读一屏就知道现在什么情况 */
function buildBrief(r){
  const seats = occupants(r);
  const groups = new Map();
  for(const s of seats){ const t=s.team|0; if(!groups.has(t)) groups.set(t, []); groups.get(t).push(s); }
  const lines = [];
  lines.push(`🏟 房间 ${r.code} · ${groups.size} 队 ${seats.length} 人 · ` +
             (r.started ? '对局进行中' : '还没开始') +
             ` · 生命 4 / 猜拳获胜 +${r.apPerWin} AP`);
  lines.push([...groups.keys()].sort((a,b)=>a-b).map(t=>
    `队伍${teamLetter(t)}：` + groups.get(t).map(s=>
      s.name + (s.kind==='bot' ? `(人机·${DIFF_LABEL[s.diff]||'普通'})` : (s.id===r.hostId?'(房主)':''))
    ).join('、')
  ).join('｜'));
  const sn = r.snapshot;
  if(sn && Array.isArray(sn.players)){
    const alive = sn.players.filter(p=>p.alive).length;
    lines.push(`第 ${sn.round} 回合${sn.over ? '（已结束）' : ''} · 存活 ${alive}/${sn.players.length}`);
    lines.push(sn.players.map(p=>{
      const s = seats.find(x=>x.name===p.name);
      const tag = s ? `[${teamLetter(s.team)}]` : '';
      return `${tag}${p.name}：${p.alive?p.hp+'血':'已阵亡'} / ${p.ap}AP / ${p.prog}` +
             (p.armor ? ` / 护甲${p.armor}` : '') + (p.weapon ? ` / ${p.weapon}` : '');
    }).join('；'));
    if(Array.isArray(sn.lastLog) && sn.lastLog.length){
      lines.push('最近：' + sn.lastLog.slice(-5).join(' ⏎ '));
    }
    lines.push(`（局面更新于 ${new Date(sn.ts || now()).toLocaleTimeString('zh-CN', {hour12:false})}）`);
  }else{
    lines.push('还没有局面数据——房主点「开始对局」开打后，每 0.8 秒会上报一次。');
  }
  return lines.join('\n');
}

/* ------------------------------ 静态文件 ------------------------------ */
const MIME = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
  '.css':'text/css; charset=utf-8','.png':'image/png','.jpg':'image/jpeg','.gif':'image/gif',
  '.json':'application/json; charset=utf-8','.ico':'image/x-icon','.md':'text/markdown; charset=utf-8',
  '.webmanifest':'application/manifest+json; charset=utf-8','.svg':'image/svg+xml',
  '.apk':'application/vnd.android.package-archive'};
function serveStatic(req, res, urlPath){
  let rel;
  try{
    rel = decodeURIComponent(urlPath.split('?')[0]);
  }catch(e){
    /* 非法百分号编码（比如 curl 直接把中文塞进 URL）不能把整个服务搞崩 */
    res.writeHead(400, {'Content-Type':'text/plain; charset=utf-8'});
    return res.end('400 bad url');
  }
  if(rel === '/' || rel === '') rel = '/index.html';
  const file = path.normalize(path.join(ROOT, rel));
  if(!file.startsWith(ROOT)){ res.writeHead(403); res.end('forbidden'); return; }
  fs.stat(file, (err, st)=>{
    if(err || !st.isFile()){ res.writeHead(404, {'Content-Type':'text/plain; charset=utf-8'}); res.end('404'); return; }
    res.writeHead(200, {'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Cache-Control':'no-cache'});
    fs.createReadStream(file).pipe(res);
  });
}

/* ------------------------------ 路由 ------------------------------ */
async function handleRequest(req, res){
  const url = req.url || '/';
  if(req.method === 'OPTIONS'){
    res.writeHead(204, {'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Content-Type',
      'Access-Control-Allow-Methods':'GET,POST'});
    return res.end();
  }
  /* ---- API ---- */
  if(url.startsWith('/api/')){
    const p = url.split('?')[0];
    try{
      if(p === '/api/ping') return json(res, {ok:true, rooms:rooms.size, port:PORT, version:VERSION});
      if(p === '/api/version') return json(res, {ok:true, version:VERSION, at:now()});
      if(p === '/api/create' && req.method === 'POST'){
        const b = await readBody(req);
        const code = makeCode();
        const id = uid();
        const slots = new Array(SLOT_COUNT).fill(null);
        slots[0] = {kind:'human', id, name:(b.name||'玩家').slice(0,10), team:0, ready:false};
        const r = {code, hostId:id, mode:b.mode==='2v2'?'2v2':'1v1',
          apPerWin:b.apPerWin===1?1:2, diff:b.diff||'normal', started:false, seed:null,
          slots, seq:0, log:[], turnId:null, snapshot:null, snapshotAt:0,
          state:null, stateSeq:0, touched:now()};
        rooms.set(code, r);
        console.log(`[房间] 创建 ${code}（房主 ${slots[0].name}，模式 ${r.mode}）`);
        return json(res, {ok:true, code, youId:id, room:roomView(r, id)});
      }
      const m = p.match(/^\/api\/room\/([A-Z0-9]{9})\/(join|ready|start|state|events|action|stream|leave|snapshot|peek|team|bot|host|kick)$/);
      if(!m) return json(res, {ok:false, err:'未知接口'}, 404);
      const r = rooms.get(m[1]);
      if(!r) return json(res, {ok:false, err:'房间不存在或已过期'}, 404);
      const sub = m[2];
      const body = req.method === 'POST' ? await readBody(req) : {};

      /* ---- 不需要身份的接口 ---- */
      if(sub === 'peek' && req.method === 'GET'){
        r.touched = now();
        return json(res, {
          ok: true, code: r.code, mode: r.mode, apPerWin: r.apPerWin, started: r.started,
          hostId: r.hostId, slots: roomView(r, null).slots, teams: teamCount(r),
          snapshot: r.snapshot || null, updatedAt: r.snapshotAt || 0,
          brief: buildBrief(r),
        });
      }
      if(sub === 'join' && req.method === 'POST'){
        if(r.started) return json(res, {ok:false, err:'对局已开始'}, 400);
        const idx = freeSlot(r);
        if(idx < 0) return json(res, {ok:false, err:'房间已满（6 个座位）'}, 400);
        const id = uid();
        const hostSlot = r.slots.findIndex(s=>s && s.kind==='human' && s.id===r.hostId);
        const prefer = hostSlot >= 0 ? r.slots[hostSlot].team : undefined;
        r.slots[idx] = {kind:'human', id, name:(body.name||('玩家'+(humans(r).length+1))).slice(0,10),
          team: defaultTeamFor(r, prefer), ready:false};
        r.touched = now(); push(r);
        console.log(`[房间] ${r.code} 加入 ${r.slots[idx].name}（座位 ${idx}，队伍${teamLetter(r.slots[idx].team)}）`);
        return json(res, {ok:true, code:r.code, youId:id, room:roomView(r, id)});
      }
      if(sub === 'stream' && req.method === 'GET'){   /* 兼容旧客户端 */
        const id2 = new URL(url, 'http://x').searchParams.get('id') || '';
        r.touched = now();
        return json(res, {ok:true, seq:r.seq, started:r.started, turnId:r.turnId,
          slots: roomView(r, id2).slots, seats: humans(r).map(s=>({id:s.id, name:s.name, team:s.team}))});
      }

      /* ---- 需要身份 ---- */
      const id = new URL(url, 'http://x').searchParams.get('id') || body.id;
      const mySlotIdx = slotOf(r, id);
      const isHost = r.hostId === id;
      if(sub === 'events' && req.method === 'GET'){
        /* 观战者（不在座位上的）也能拉事件：只读 */
        const since = Number(new URL(url,'http://x').searchParams.get('since') || 0);
        return json(res, {ok:true, seq:r.seq, turnId:r.turnId, started:r.started,
          mode:r.mode, apPerWin:r.apPerWin, diff:r.diff, hostId:r.hostId, seed:r.seed,
          events:r.log.filter(e=>e.seq>since),
          slots: roomView(r, id || null).slots,
          seats: humans(r).map(s=>({id:s.id, name:s.name, team:s.team})),
          snapshot: r.snapshot || null,
          stateSeq: r.stateSeq || 0});
      }
      if(mySlotIdx < 0 && !['events'].includes(sub)) return json(res, {ok:false, err:'你不在该房间中'}, 403);

      /* 联机对局：房主把整份局面推上来，其他端拉下来渲染 */
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
      if(sub === 'snapshot' && req.method === 'POST'){
        r.snapshot = body.snap || null;
        r.snapshotAt = now();
        r.touched = now();
        return json(res, { ok:true });
      }
      if(sub === 'ready' && req.method === 'POST'){
        const seat = r.slots[mySlotIdx];
        seat.ready = body.ready===undefined ? !seat.ready : !!body.ready;
        r.touched = now(); push(r);
        return json(res, {ok:true, room:roomView(r, id)});
      }
      if(sub === 'team' && req.method === 'POST'){
        const idx = Number(body.slot);
        const seat = r.slots[idx];
        if(!seat) return json(res, {ok:false, err:'这个座位是空的'}, 400);
        if(seat.kind==='human' && seat.id !== id && !isHost) return json(res, {ok:false, err:'只能改自己或人机的队伍'}, 403);
        if(isHost === false && seat.kind==='bot') return json(res, {ok:false, err:'人机由房主调整'}, 403);
        const t = Number(body.team);
        if(!(t>=0 && t<=3)) return json(res, {ok:false, err:'队伍只能是 A~D'}, 400);
        seat.team = t|0;
        r.touched = now(); push(r);
        return json(res, {ok:true, room:roomView(r, id)});
      }
      if(sub === 'bot' && req.method === 'POST'){
        if(!isHost) return json(res, {ok:false, err:'只有房主能加/删人机'}, 403);
        if(r.started) return json(res, {ok:false, err:'对局已开始'}, 400);
        const idx = Number(body.slot);
        if(!(idx>=0 && idx<SLOT_COUNT)) return json(res, {ok:false, err:'座位号不合法'}, 400);
        const op = body.op || 'fill';
        if(op === 'clear'){
          const s = r.slots[idx];
          if(!s || s.kind!=='bot') return json(res, {ok:false, err:'这个座位没有人机'}, 400);
          r.slots[idx] = null;
        }else if(op === 'fill'){
          if(r.slots[idx]) return json(res, {ok:false, err:'座位已被占用'}, 400);
          const hostSlot = r.slots.findIndex(s=>s && s.kind==='human' && s.id===r.hostId);
          const prefer = hostSlot >= 0 ? r.slots[hostSlot].team : 0;
          r.slots[idx] = {kind:'bot', id:'bot-'+uid().slice(0,8), name:nextBotName(r),
            team: (Number.isInteger(body.team) ? body.team : defaultTeamFor(r, prefer)),
            ready:true, diff: body.diff || r.diff || 'normal'};
        }else if(op === 'update'){
          const s = botSlotOf(r, idx);
          if(!s) return json(res, {ok:false, err:'这个座位没有人机'}, 400);
          if(Number.isInteger(body.team)) s.team = Math.max(0, Math.min(3, body.team));
          if(DIFF_LABEL[body.diff]) s.diff = body.diff;
          if(typeof body.name === 'string' && body.name.trim()) s.name = body.name.trim().slice(0,10);
        }else{
          return json(res, {ok:false, err:'未知的人机操作'}, 400);
        }
        r.touched = now(); push(r);
        return json(res, {ok:true, room:roomView(r, id)});
      }
      if(sub === 'kick' && req.method === 'POST'){
        if(!isHost) return json(res, {ok:false, err:'只有房主能请人离开'}, 403);
        const idx = Number(body.slot);
        const s = r.slots[idx];
        if(!s) return json(res, {ok:false, err:'座位是空的'}, 400);
        if(s.kind==='human' && s.id===id) return json(res, {ok:false, err:'不能踢自己'}, 400);
        if(r.slots[idx].kind==='human'){
          r.slots[idx] = null;
          if(r.hostId === s.id){
            const nh = humans(r)[0];
            r.hostId = nh ? nh.id : id;
          }
        }else{
          r.slots[idx] = null;
        }
        r.touched = now(); push(r);
        return json(res, {ok:true, room:roomView(r, id)});
      }
      if(sub === 'host' && req.method === 'POST'){
        if(!isHost) return json(res, {ok:false, err:'只有房主能转让'}, 403);
        const idx = Number(body.slot);
        const s = r.slots[idx];
        if(!s || s.kind!=='human') return json(res, {ok:false, err:'只能把房主交给真人座位'}, 400);
        r.hostId = s.id;
        r.touched = now(); push(r);
        return json(res, {ok:true, room:roomView(r, id)});
      }
      if(sub === 'start' && req.method === 'POST'){
        if(!isHost) return json(res, {ok:false, err:'只有房主可以开始'}, 403);
        const seats = occupants(r);
        if(seats.length < 2) return json(res, {ok:false, err:'至少要有 2 个人（可以加人机）'}, 400);
        if(teamCount(r) < 2) return json(res, {ok:false, err:'至少要有 2 个队伍才有对手'}, 400);
        r.started = true;
        r.state = null; r.stateSeq = 0;
        r.seed = Number(body.seed) || ((()=>{ let h=2166136261;
          for(const ch of String(r.code)){ h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
          return (h>>>0)||1; })());
        r.touched = now(); push(r);
        console.log(`[房间] ${r.code} 开始对局（${seats.length} 人 / ${teamCount(r)} 队）`);
        return json(res, {ok:true, room:roomView(r, id), seed:r.seed});
      }
      if(sub === 'state' && req.method === 'GET'){
        return json(res, {ok:true, room:roomView(r, id), seq:r.seq, turnId:r.turnId, logCount:r.log.length});
      }
      if(sub === 'action' && req.method === 'POST'){
        if(!r.started) return json(res, {ok:false, err:'对局未开始'}, 400);
        if(r.turnId && r.turnId!==id) return json(res, {ok:false, err:'还没轮到你'}, 409);
        r.seq += 1;
        const ev = {seq:r.seq, actor:id, action:body.action, at:now()};
        r.log.push(ev);
        if(r.log.length > 4000) r.log = r.log.slice(-3000);
        r.touched = now(); push(r);
        return json(res, {ok:true, seq:r.seq});
      }
      if(sub === 'leave' && req.method === 'POST'){
        r.slots[mySlotIdx] = null;
        if(r.hostId === id){
          const nh = humans(r)[0];
          if(nh) r.hostId = nh.id;
        }
        if(!occupants(r).length) rooms.delete(r.code); else push(r);
        return json(res, {ok:true});
      }
    }catch(e){
      return json(res, {ok:false, err:String(e && e.message || e)}, 500);
    }
    return;
  }
  serveStatic(req, res, url);
}

/* 任何 handler 异常都只回 500，不让进程退出（历史上一个坏 URL 就能把服务打死） */
const server = http.createServer((req, res)=>{
  handleRequest(req, res).catch(err => {
    try{
      console.error('[请求异常]', req.method, req.url, err && err.message);
      if(!res.headersSent) json(res, {ok:false, err:String(err && err.message || err)}, 500);
      else res.end();
    }catch(e){ try{ res.end(); }catch(_){} }
  });
});

/* ------------------------------ 自动打开浏览器 ------------------------------ */
function openBrowser(url){
  if(process.env.NO_OPEN === '1') return;
  const cmd = process.platform === 'win32'
    ? `start "" "${url}"`
    : process.platform === 'darwin' ? `open "${url}"` : `xdg-open "${url}"`;
  try{ exec(cmd, {windowsHide:true}, ()=>{}); }catch(e){}
}

/* ------------------------------ 启动 ------------------------------ */
function lanAddresses(){
  const out = [];
  for(const list of Object.values(os.networkInterfaces())){
    for(const i of list||[]) if(i.family === 'IPv4' && !i.internal) out.push(i.address);
  }
  return out;
}
server.listen(PORT, '0.0.0.0', ()=>{
  const ips = lanAddresses();
  console.log('');
  console.log(`  方块猜拳战场 · 局域网联机服务已启动  (v${VERSION})`);
  console.log('  ────────────────────────────────────────');
  console.log(`  本机：      http://127.0.0.1:${PORT}`);
  for(const ip of ips) console.log(`  局域网：    http://${ip}:${PORT}   <-- 把这个发给朋友`);
  console.log('  ────────────────────────────────────────');
  console.log('  关闭此窗口即停止服务。');
  console.log('');
  setTimeout(()=>{ openBrowser(`http://127.0.0.1:${PORT}`); }, 300);
});
