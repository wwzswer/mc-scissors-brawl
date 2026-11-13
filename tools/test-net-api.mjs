const B = process.env.BASE || 'http://127.0.0.1:8787';
const post = (p, b) => fetch(B+p, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b||{})}).then(r=>r.json());
const get  = (p) => fetch(B+p).then(r=>r.json());
let fails = 0;
const ok = (c, m, extra) => { if(!c) fails++; console.log((c?'✔ ':'✘ ')+m+(extra!==undefined?'  '+JSON.stringify(extra):'')); };

const c = await post('/api/create', {name:'房主小明', mode:'2v2'});
ok(c.ok && c.code.length===9, '创建房间拿到 9 位码', c.code);
const code = c.code, host = c.youId;
ok(c.room.slots.length===6 && c.room.slots[0].name==='房主小明', '房间有 6 个座位，房主坐 0 号', c.room.slots.map(s=>s&&s.name));

const j = await post(`/api/room/${code}/join`, {name:'朋友小红'});
ok(j.ok && j.room.slots.filter(Boolean).length===2, '第二人加入', j.room.slots.map(s=>s&&(s.name+'/'+s.team)));
const friend = j.youId;
const friendSlotIdx = j.room.slots.findIndex(s=>s&&s.isYou);
ok(j.room.slots[friendSlotIdx].team === 1, '第二人默认进敌对队（队伍 B）', j.room.slots[friendSlotIdx].team);

let r = await post(`/api/room/${code}/team`, {id:friend, slot:friendSlotIdx, team:2});
ok(r.ok && r.room.slots[friendSlotIdx].team===2, '朋友把自己的队伍改成 C');
r = await post(`/api/room/${code}/team`, {id:friend, slot:0, team:0});
ok(!r.ok, '朋友不能改房主的队伍', r.err);
r = await post(`/api/room/${code}/bot`, {id:friend, slot:2, op:'fill'});
ok(!r.ok, '只有房主能加人机', r.err);
r = await post(`/api/room/${code}/bot`, {id:host, slot:2, op:'fill', diff:'hard'});
ok(r.ok && r.room.slots[2] && r.room.slots[2].kind==='bot' && r.room.slots[2].team===1, '房主在空位加人机（默认进人最少且不是自己的队）', r.room.slots[2]);
r = await post(`/api/room/${code}/bot`, {id:host, slot:3, op:'fill', diff:'easy'});
ok(r.ok && r.room.slots[3] && r.room.slots[3].kind==='bot', '再加一个人机');
r = await post(`/api/room/${code}/bot`, {id:host, slot:3, op:'update', diff:'hard', team:2});
ok(r.ok && r.room.slots[3].diff==='hard' && r.room.slots[3].team===2, '改人机强度与队伍');
r = await post(`/api/room/${code}/bot`, {id:host, slot:2, op:'fill'});
ok(!r.ok, '已占座位不能再加人机', r.err);
r = await post(`/api/room/${code}/team`, {id:host, slot:5, team:1});
ok(!r.ok, '空位不能改队伍', r.err);

let p = await get(`/api/room/${code}/peek`);
ok(p.ok && p.brief.includes('房间 '+code) && p.brief.includes('队伍A'), 'peek 能拿到中文战报', p.brief.split('\n')[1]);
ok(p.slots.filter(Boolean).length===4 && p.teams===3, 'peek 有 4 人 3 队', {people:p.slots.filter(Boolean).length, teams:p.teams});

const st = await post(`/api/room/${code}/start`, {id:host});
ok(st.ok && st.room.started, '房主开局成功', {seed: st.seed});
const st2 = await post(`/api/room/${code}/start`, {id:friend});
ok(!st2.ok, '非房主不能开局', st2.err);

const snap = {ts:Date.now(), round:7, over:false, mode:'2v2', apPerWin:2,
  players:[
    {name:'房主小明', hp:4, ap:2, prog:'石进程', weapon:'石剑', armor:'', alive:true},
    {name:'朋友小红', hp:1, ap:0, prog:'空手', weapon:'一拳', armor:'皮革甲(1)', alive:true},
    {name:'史蒂夫', hp:0, ap:0, prog:'空手', weapon:'一拳', armor:'', alive:false},
    {name:'末影人', hp:3, ap:1, prog:'铁进程', weapon:'铁剑', armor:'', alive:true},
  ], lastLog:['第 7 回合','房主小明 用 石剑 命中 朋友小红 -1 血']};
const sn = await post(`/api/room/${code}/snapshot`, {id:host, snap});
ok(sn.ok, '房主上报局面快照');
p = await get(`/api/room/${code}/peek`);
ok(p.brief.includes('第 7 回合') && p.brief.includes('朋友小红') && p.brief.includes('最近'), '战报包含回合/血量/最近日志');
ok(p.snapshot && p.snapshot.players.length===4, 'peek 带完整局面');
console.log('\n--- 战报全文 ---\n' + p.brief + '\n--- end ---\n');

r = await post(`/api/room/${code}/host`, {id:host, slot:friendSlotIdx});
ok(r.ok && r.room.hostId===friend, '房主可以转给朋友');
r = await post(`/api/room/${code}/kick`, {id:friend, slot:2});
ok(r.ok && !r.room.slots[2], '新房主踢掉人机');
r = await post(`/api/room/${code}/leave`, {id:friend});
ok(r.ok, '离开房间');
p = await get(`/api/room/${code}/peek`);
ok(p.slots.filter(Boolean).length===2, '剩 2 人（人机还在）', p.slots.filter(Boolean).map(s=>s.name));

/* 回归：非法百分号编码的 URL 不能把服务打死（历史上这里崩过一次） */
const bad = await fetch(B + '/dist/%E0%A4%A').then(r=>r.status).catch(()=>'net-error');
ok(bad === 400, '非法编码的 URL 返回 400 而不是崩服务', bad);
const alive = await get('/api/ping');
ok(alive.ok === true, '被坏请求打过之后服务仍然存活', alive.version);

const v = await get('/api/version');
ok(v.ok && v.version==='1.7.0', '版本接口可用', v.version);
const vj = await get('/version.json');
ok((vj.version||'').length>0, 'version.json 可取到', vj.version);

console.log('\n' + (fails===0 ? 'API ALL PASS' : 'API FAILURES: '+fails));
process.exit(fails?1:0);
