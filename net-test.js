/* 局域网联机 · 服务端全链路测试（Node，无浏览器）
   验证：房间创建 / 9 位房间码 / 加入 / 座位同步 / 准备 / 开始 / 动作广播 / 增量事件 / 轮次校验
   用法： node net-test.js [端口]                                              */
const http = require('node:http');

const PORT = Number(process.argv[2] || 8787);
const BASE = `http://127.0.0.1:${PORT}`;

let pass = 0, fail = 0;
const fails = [];
function ok(cond, name, extra){
  if(cond){ pass++; console.log(`  ✅ ${name}`); }
  else { fail++; fails.push(name); console.log(`  ❌ ${name}${extra!==undefined?'  → '+JSON.stringify(extra):''}`); }
}
function post(p, body){
  return new Promise((resolve, reject)=>{
    const data = JSON.stringify(body||{});
    const req = http.request(BASE+p, {method:'POST', headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}},
      res=>{ let d=''; res.on('data',c=>d+=c); res.on('end',()=>{ try{ resolve(JSON.parse(d)); }catch(e){ reject(new Error('bad json: '+d.slice(0,120))); } }); });
    req.on('error', reject); req.write(data); req.end();
  });
}
function get(p){
  return new Promise((resolve, reject)=>{
    http.get(BASE+p, res=>{ let d=''; res.on('data',c=>d+=c); res.on('end',()=>{ try{ resolve(JSON.parse(d)); }catch(e){ reject(new Error('bad json: '+d.slice(0,120))); } }); })
      .on('error', reject);
  });
}
const sleep = ms => new Promise(r=>setTimeout(r,ms));

(async ()=>{
  console.log(`\n联机服务端测试（${BASE}）`);

  console.log('\n【1】服务可达性');
  const ping = await get('/api/ping');
  ok(ping.ok === true, '服务在运行', ping);
  ok(typeof ping.port === 'number', '返回端口号', ping.port);

  console.log('\n【2】创建房间与 9 位房间码');
  const a = await post('/api/create', {name:'房主A', mode:'1v1', apPerWin:2, diff:'normal'});
  ok(a.ok === true, '房主创建成功', a.err);
  ok(/^[A-Z0-9]{9}$/.test(a.code), `房间码是 9 位大写字母+数字：${a.code}`, a.code);
  ok(!!a.youId, '返回房主唯一 id');
  const code = a.code;
  ok(a.room.seats.length === 1 && a.room.seats[0].isHost === true, '房主在座位上', a.room.seats);

  console.log('\n【3】第二个客户端加入');
  const b = await post(`/api/room/${code}/join`, {name:'加入者B'});
  ok(b.ok === true, 'B 加入成功', b.err);
  ok(b.youId !== a.youId, 'B 的 id 与房主不同');
  await sleep(120);
  const stA = await get(`/api/room/${code}/state?id=${a.youId}`);
  const stB = await get(`/api/room/${code}/state?id=${b.youId}`);
  ok(stA.room.seats.length === 2, '房主看到 2 个座位', stA.room.seats.length);
  ok(stB.room.seats.length === 2, 'B 看到 2 个座位', stB.room.seats.length);
  const names = stA.room.seats.map(s=>s.name).sort().join(',');
  ok(names === '加入者B,房主A', '两端看到的玩家一致', names);
  ok(stA.room.hostId === a.youId, '房主标识正确');

  console.log('\n【4】非法输入');
  const bad = await post('/api/room/ZZZZZZZZZ/join', {name:'X'});
  ok(bad.ok === false, '不存在的房间码被拒绝', bad.err);
  const noSeat = await get(`/api/room/${code}/state?id=deadbeef`);
  ok(noSeat.ok === false, '非房间成员读状态被拒绝', noSeat.err);

  console.log('\n【5】准备状态同步');
  await post(`/api/room/${code}/ready`, {id:a.youId, ready:true});
  await post(`/api/room/${code}/ready`, {id:b.youId, ready:true});
  await sleep(120);
  const st2 = await get(`/api/room/${code}/state?id=${a.youId}`);
  ok(st2.room.seats.filter(s=>s.ready).length === 2, '两人都已准备', st2.room.seats.map(s=>s.ready));

  console.log('\n【6】只有房主能开始');
  const notHost = await post(`/api/room/${code}/start`, {id:b.youId});
  ok(notHost.ok === false, '非房主开始被拒绝', notHost.err);
  const started = await post(`/api/room/${code}/start`, {id:a.youId});
  ok(started.ok === true, '房主开始成功');
  await sleep(120);
  const st3 = await get(`/api/room/${code}/state?id=${a.youId}`);
  ok(st3.room.started === true, '房间状态变为已开始');

  console.log('\n【7】动作广播与增量事件');
  const s0 = (await get(`/api/room/${code}/events?id=${a.youId}&since=0`)).seq;
  await post(`/api/room/${code}/action`, {id:a.youId, action:{kind:'rps', move:'rock'}});
  await post(`/api/room/${code}/action`, {id:b.youId, action:{kind:'rps', move:'scissors'}});
  await sleep(150);
  const evA = await get(`/api/room/${code}/events?id=${a.youId}&since=0`);
  const evB = await get(`/api/room/${code}/events?id=${b.youId}&since=0`);
  ok(evA.events.length >= 2, 'A 能拉到 2 条事件', evA.events.length);
  ok(evB.events.length >= 2, 'B 能拉到 2 条事件', evB.events.length);
  const moves = evA.events.filter(e=>e.action && e.action.kind==='rps').map(e=>e.action.move).sort();
  ok(moves.join(',') === 'rock,scissors', '出拳内容被正确广播', moves);
  const actorSet = new Set(evA.events.map(e=>e.actor));
  ok(actorSet.size === 2, '两个客户端的动作都记录了', [...actorSet].length);
  /* 增量：带上已应用 seq 后不应重复收到旧事件 */
  const evA2 = await get(`/api/room/${code}/events?id=${a.youId}&since=${evA.seq}`);
  ok(evA2.events.length === 0, '增量拉取不会重复返回旧事件', evA2.events.length);

  console.log('\n【8】行动权校验（服务端 turnId）');
  const st4 = await get(`/api/room/${code}/state?id=${a.youId}`);
  ok('turnId' in st4, '状态里带 turnId 字段');

  console.log('\n【9】离开房间');
  const left = await post(`/api/room/${code}/leave`, {id:b.youId});
  ok(left.ok === true, 'B 离开成功');
  await sleep(120);
  const st5 = await get(`/api/room/${code}/state?id=${a.youId}`);
  ok(st5.room.seats.length === 1, '离开后只剩房主', st5.room.seats.length);

  console.log('\n【10】2V2 房间容量（最多 4 人）');
  const c = await post('/api/create', {name:'房主C', mode:'2v2', apPerWin:1});
  ok(c.ok === true, '创建 2V2 房间');
  const code2 = c.code;
  await post(`/api/room/${code2}/join`, {name:'P2'});
  await post(`/api/room/${code2}/join`, {name:'P3'});
  const p4 = await post(`/api/room/${code2}/join`, {name:'P4'});
  ok(p4.ok === true, '第 4 人加入成功');
  const p5 = await post(`/api/room/${code2}/join`, {name:'P5'});
  ok(p5.ok === false, '第 5 人被拒绝（房间已满）', p5.err);
  const st6 = await get(`/api/room/${code2}/state?id=${c.youId}`);
  ok(st6.room.seats.length === 4, '2V2 房间共 4 个座位', st6.room.seats.length);
  ok(st6.room.mode === '2v2', '模式为 2v2', st6.room.mode);
  ok(st6.room.apPerWin === 1, 'AP 设置被房间继承（1 AP）', st6.room.apPerWin);

  console.log('\n【11】静态资源可访问（联机时靠它加载游戏）');
  const html = await new Promise((resolve,reject)=>{
    http.get(BASE+'/index.html', res=>{ let d=''; res.on('data',c=>d+=c); res.on('end',()=>resolve({code:res.statusCode, len:d.length, hasGame:d.includes('MCGame')})); }).on('error',reject);
  });
  ok(html.code === 200, 'index.html 返回 200', html.code);
  ok(html.len > 100000, 'index.html 体积正常（含贴图）', html.len);
  ok(html.hasGame, '页面里包含游戏脚本');

  console.log('\n──────────────────────────────');
  console.log(`通过 ${pass} 项，失败 ${fail} 项`);
  if(fail) console.log('失败项：\n  - ' + fails.join('\n  - '));
  process.exit(fail ? 1 : 0);
})().catch(e=>{ console.error('测试异常:', e); process.exit(2); });
