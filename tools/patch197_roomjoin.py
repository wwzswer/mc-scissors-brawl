import io

p = 'D:/Documents/deepseek-harness/default-workspace/qq-bridge/src/mcp-mc-brawl.js'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label):
    global s
    assert old in s, '锚点不存在: ' + label
    s = s.replace(old, new, 1)
    print('  ok', label)

# ---------------- 1) 房间客户端状态 ----------------
sub("""  started: false,
  lastError: '',
};""",
    """  started: false,
  lastError: '',
  /* 网页联机房间：她以真人座位加入后，在这里记座位与增量游标 */
  room: { code: null, seatId: null, base: 'http://127.0.0.1:8787', since: 0, ask: null, started: false },
  since: 0,
};""",
    '房间状态字段')

# ---------------- 2) 房间相关工具 ----------------
ROOM_TOOLS = r'''
/* =========================================================================
   网页联机房间：她坐进一个真座位，和主人在网页里对打
   -------------------------------------------------------------------------
   协议（和网页访客端完全一样，只是把"点按钮"换成工具调用）：
     POST /api/room/<码>/join           占一个座位（isYou）
     GET  /api/room/<码>/events?id=&since=   拉事件，房主会发 {kind:'ask', promptId, ask, list}
     POST /api/room/<码>/action         回 {kind:'ans', promptId, move|id|pass}
   房主（网页端）负责所有结算，她只需要回答"出什么/做哪一项/闪不闪"。
   ========================================================================= */
function roomBase(url) {
  return String(url || state.room.base || process.env.MC_SERVER || 'http://127.0.0.1:8787').replace(/\/+$/, '');
}
async function roomApi(path, body) {
  const url = roomBase() + path;
  const opts = body
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), cache: 'no-store' }
    : { cache: 'no-store' };
  const r = await fetch(url, opts);
  return r.json();
}
function fmtRoomAsk(ask) {
  const list = Array.isArray(ask.list) ? ask.list : [];
  const head = ask.ask === 'rps' ? '✊ 房主那边的引擎问：这一轮你出什么？'
    : ask.ask === 'dodge' ? '🛡 判定平局，房主问：你要不要花 1 AP 闪避？'
    : '🎯 轮到你行动了，可选：';
  if (ask.ask === 'rps') return head + '\n（可用 mc_room_answer move=rock/scissors/paper 回答）';
  const lines = list.map((x, i) => `${i + 1}. ${x.label}`);
  return head + '\n' + lines.join('\n') +
    '\n\n（用 mc_room_answer choice=序号 回答，choice="pass" 表示结束行动）';
}
function boardText(st) {
  if (!st || !Array.isArray(st.players)) return '（还没有局面数据）';
  const lines = [`第 ${st.round} 回合${st.over ? '（已结束）' : ''}`];
  for (const p of st.players) {
    const bits = [p.alive ? `${p.hp} 血` : '已阵亡', `${p.ap} AP`];
    if (p.prog) bits.push(p.prog);
    if (p.weapon) bits.push(`武器 ${p.weapon}`);
    if (p.armor) bits.push(p.armor);
    lines.push(`  ${p.name}：${bits.join('，')}`);
  }
  if (Array.isArray(st.lastLog) && st.lastLog.length) {
    lines.push('刚刚：' + st.lastLog.slice(-1)[0]);
  }
  return lines.join('\n');
}

server.tool(
  'mc_room_join',
  '加入网页端联机房间，占一个座位当**真对手**（不是观战）。用房主给的 9 位房间码。加入后房主点「开始对局」，你就用 mc_room_wait 等轮到你。',
  {
    code: z.string().regex(/^[A-Z0-9]{9}$/).describe('9 位房间码'),
    name: z.string().max(12).optional().describe('座位上的名字，默认「她」'),
    serverUrl: z.string().optional().describe('联机服务器地址，默认 http://127.0.0.1:8787'),
  },
  async ({ code, name, serverUrl }) => {
    try {
      state.room.base = roomBase(serverUrl);
      const d = await roomApi(`/api/room/${code}/join`, { name: name || '她' });
      if (!d || !d.ok) {
        return { content: [{ type: 'text', text: `进不去房间 ${code}：${(d && d.err) || '未知原因'}` }], isError: true };
      }
      state.room.code = code;
      state.room.seatId = d.youId;
      state.room.since = 0;
      state.room.ask = null;
      state.room.started = !!d.room.started;
      const slots = (d.room.slots || []).filter(Boolean);
      const mine = slots.find((x) => x.isYou);
      const team = mine ? 'ABCD'[mine.team | 0] || '?' : '?';
      return {
        content: [{
          type: 'text',
          text: `已加入房间 ${code}，你坐的是**队伍${team}**的座位（座位共 ${slots.length}/6 有人）。\n` +
            `现在等房主点「开始对局」；开始后叫 mc_room_wait 等你的出拳/行动。`,
        }],
      };
    } catch (e) {
      return { content: [{ type: 'text', text: `连不上联机服务器：${e && e.message ? e.message : e}` }], isError: true };
    }
  },
);

server.tool(
  'mc_room_wait',
  '等房主那边的引擎轮到你（出拳 / 行动 / 闪避）。返回可选项；超时就返回「还没轮到你」。',
  { timeoutMs: z.number().int().min(1000).max(60000).optional().describe('最长等多久，默认 20000ms') },
  async ({ timeoutMs }) => {
    const r = state.room;
    if (!r.code || !r.seatId) return { content: [{ type: 'text', text: '还没进房间，先 mc_room_join。' }], isError: true };
    if (r.ask) return { content: [{ type: 'text', text: fmtRoomAsk(r.ask) }] };
    const deadline = Date.now() + (timeoutMs || 20000);
    while (Date.now() < deadline) {
      try {
        const d = await roomApi(`/api/room/${r.code}/events?id=${r.seatId}&since=${r.since}`);
        if (d && d.ok) {
          r.started = !!d.started;
          for (const ev of d.events || []) {
            r.since = Math.max(r.since, ev.seq || 0);
            if (ev.actor === r.seatId) continue;                    /* 自己发的跳过 */
            const a = ev.action || {};
            if (a.kind === 'ask') { r.ask = a; return { content: [{ type: 'text', text: fmtRoomAsk(a) }] }; }
          }
          if (!r.started) {
            return { content: [{ type: 'text', text: '房主还没点「开始对局」。等一会儿再 mc_room_wait，或者让房主开始。' }] };
          }
        }
      } catch (e) { /* 网络抖动就再试 */ }
      await new Promise((res) => setTimeout(res, 400));
    }
    return { content: [{ type: 'text', text: '还没轮到你（房主那边可能还在结算，或者已经在等你下一步）。稍后再 mc_room_wait。' }] };
  },
);

server.tool(
  'mc_room_answer',
  '回答 mc_room_wait 给出的问题：出拳传 move；行动传 choice（序号或选项 id）；结束行动传 choice="pass"。',
  {
    move: z.enum(['rock', 'scissors', 'paper']).optional().describe('猜拳：rock/scissors/paper'),
    choice: z.union([z.string(), z.number()]).optional().describe('行动序号（1、2…）或选项 id，或 "pass"'),
  },
  async ({ move, choice }) => {
    const r = state.room;
    if (!r.code || !r.seatId) return { content: [{ type: 'text', text: '还没进房间，先 mc_room_join。' }], isError: true };
    const ask = r.ask;
    if (!ask) return { content: [{ type: 'text', text: '现在没有要回答的问题（先 mc_room_wait）。' }], isError: true };

    const action = { kind: 'ans', promptId: ask.promptId };
    if (ask.ask === 'rps') {
      const mv = move || (typeof choice === 'string' && ['rock', 'scissors', 'paper'].includes(choice) ? choice : null);
      if (!mv) return { content: [{ type: 'text', text: '猜拳要传 move=rock/scissors/paper。' }], isError: true };
      action.move = mv;
    } else {
      const raw = String(choice == null ? '' : choice).trim();
      if (!raw) return { content: [{ type: 'text', text: '要传 choice=序号（或 "pass"）。' }], isError: true };
      if (/^(pass|跳过|结束)$/i.test(raw)) {
        action.pass = true;
      } else {
        const list = Array.isArray(ask.list) ? ask.list : [];
        const byId = list.find((x) => x.id === raw);
        const idx = Number(raw);
        const item = byId || (Number.isFinite(idx) && idx >= 1 && idx <= list.length ? list[idx - 1] : null);
        if (!item) {
          const names = list.map((x, i) => `${i + 1}. ${x.label}`).join('\n');
          return { content: [{ type: 'text', text: `没有这个选项：${raw}\n可用：\n${names}` }], isError: true };
        }
        action.id = item.id;
      }
    }

    try {
      const d = await roomApi(`/api/room/${r.code}/action`, { id: r.seatId, action });
      if (!d || !d.ok) return { content: [{ type: 'text', text: `提交失败：${(d && d.err) || '未知'}` }], isError: true };
      r.ask = null;
      const what = action.move ? `出拳 ${action.move}` : action.pass ? '结束行动' : `选了 ${action.id}`;
      return { content: [{ type: 'text', text: `已提交（${what}）。接着 mc_room_wait 等下一条，或者 mc_room_board 看局面。` }] };
    } catch (e) {
      return { content: [{ type: 'text', text: `提交时出错：${e && e.message ? e.message : e}` }], isError: true };
    }
  },
);

server.tool(
  'mc_room_board',
  '看当前网页房间的局面（每人的血量/AP/进程/装备）与最近一条日志。',
  {},
  async () => {
    const r = state.room;
    if (!r.code) return { content: [{ type: 'text', text: '还没进房间，先 mc_room_join（或者用 mc_room 按房间码只读看）。' }], isError: true };
    try {
      const d = await roomApi(`/api/room/${r.code}/state`);
      if (!d || !d.ok) return { content: [{ type: 'text', text: `读不到房间：${(d && d.err) || '未知'}` }], isError: true };
      return { content: [{ type: 'text', text: `房间 ${r.code}\n` + boardText(d) }] };
    } catch (e) {
      return { content: [{ type: 'text', text: `连不上：${e && e.message ? e.message : e}` }], isError: true };
    }
  },
);

'''
sub("server.tool(\n  'mc_log',", ROOM_TOOLS + "server.tool(\n  'mc_log',", '房间四件套工具')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch room-join: %d -> %d bytes' % (n0, len(s)))
