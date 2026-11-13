// 方块猜拳战场 —— 游戏 MCP server（stdio）。由 DSH 的 MCP 客户端 spawn。
//
// 两种玩法：
//   1) 双人对战（默认）：主人 vs 她。游戏内有两名「人类」玩家，出拳/行动都由外部驱动，
//      她负责把主人的操作转成工具调用，自己也当玩家。
//   2) 单人（vsHer=false）：她一个人打游戏内置 AI。
//
// 安全：只操作这一局游戏，不读写任意文件、不执行命令、不联网。
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function resolveGamePath() {
  const candidates = [
    process.env.MC_GAME_PATH,
    path.resolve(__dirname, '../../mc-scissors-brawl/index.html'),
    path.resolve(__dirname, '../mc-scissors-brawl/index.html'),
    path.resolve(__dirname, '../index.html'),      /* 被拷进游戏仓库里时（mcp/ 目录） */
    'D:/Documents/deepseek-harness/default-workspace/mc-scissors-brawl/index.html',
  ].filter(Boolean);
  for (const p of candidates) {
    try { if (fs.statSync(p).isFile()) return p; } catch {}
  }
  return null;
}

/* ---------------- DOM 桩 ---------------- */
function makeEl(tag) {
  const el = {
    tagName: (tag || 'div').toUpperCase(), children: [], style: {}, dataset: {}, _attrs: {},
    _text: '', _html: '', disabled: false, className: '', parentNode: null, id: '',
    classList: { _s: new Set(), add() {}, remove() {}, toggle() {}, contains() { return false; } },
    appendChild(c) { this.children.push(c); c.parentNode = this; return c; },
    remove() {}, scrollTop: 0, scrollHeight: 0,
    addEventListener() {}, removeEventListener() {}, focus() {}, blur() {},
    getBoundingClientRect() { return { left: 0, top: 0, width: 100, height: 80 }; },
    getAttribute() { return null; }, setAttribute() {},
    querySelectorAll() { return []; }, querySelector() { return null; }, onclick: null,
  };
  Object.defineProperty(el, 'innerHTML', { get() { return el._html; }, set(v) { el._html = String(v); el.children.length = 0; } });
  Object.defineProperty(el, 'textContent', { get() { return el._text; }, set(v) { el._text = String(v); el.children.length = 0; } });
  return el;
}

/* ---------------- 运行态 ---------------- */
const state = {
  gamePath: null, MC: null, sandbox: null, dom: null,
  pending: null,        // { kind:'rps'|'action', who:'you'|'her'|'ai', resolve, p, opts }
  youId: 0,
  herId: null,          // 双人模式下第二个「人类」玩家的 id；单人模式为 null
  duel: true,
  started: false,
  lastError: '',
  /* 网页联机房间：她以真人座位加入后，在这里记座位与增量游标 */
  room: { code: null, seatId: null, base: 'http://127.0.0.1:8787', since: 0, ask: null, started: false },
  since: 0,
};

function readAllLogs() {
  const el = state.dom && state.dom.log;
  if (!el || !Array.isArray(el.children)) return [];
  return el.children.map((d) => {
    const parts = (d.children || []).map((c) => (c._text ? c._text : String(c._html || '').replace(/<[^>]+>/g, ' ')));
    return parts.join(' ').replace(/\s+/g, ' ').trim();
  }).filter(Boolean);
}

function whoOf(p) {
  if (!p) return 'ai';
  if (p.id === state.youId) return 'you';
  if (state.herId !== null && p.id === state.herId) return 'her';
  return 'ai';
}

function loadGame() {
  const p = resolveGamePath();
  if (!p) throw new Error('找不到游戏文件 index.html（可设置环境变量 MC_GAME_PATH 指定）');
  state.gamePath = p;
  const html = fs.readFileSync(p, 'utf8');
  const m = html.match(/<script>([\s\S]*)<\/script>/);
  if (!m) throw new Error('游戏文件里找不到 <script> 段');

  const reg = {};
  const document = {
    createElement: makeEl,
    getElementById(id) { if (!reg[id]) { reg[id] = makeEl('div'); reg[id].id = id; } return reg[id]; },
    querySelectorAll() { return []; }, querySelector() { return null; },
    querySelectorAll() { return []; },
    addEventListener() {}, removeEventListener() {}, dispatchEvent() { return true; },
    body: makeEl('body'), documentElement: makeEl('html'), head: makeEl('head'),
    readyState: 'complete', hidden: false,
  };
  const store = {};
  const localStorage = {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
    clear: () => { for (const k in store) delete store[k]; },
  };
  const noop = () => {};
  /* 游戏里会碰到的浏览器全局，全部给个"存在但什么都不做"的版本。
     注意：以前 window 是空对象 {}，游戏一加载到 window.addEventListener 就抛错，
     表现为 QQ 里「开局失败：window.addEventListener is not a function」。 */
  const win = {
    addEventListener: noop, removeEventListener: noop, dispatchEvent: () => true,
    matchMedia: (q) => ({ matches: false, media: q, addEventListener: noop, removeEventListener: noop, addListener: noop, removeListener: noop }),
    getComputedStyle: () => ({ getPropertyValue: () => '', fontSize: '16px' }),
    innerWidth: 1280, innerHeight: 800, outerWidth: 1280, outerHeight: 800,
    devicePixelRatio: 1, scrollY: 0, scrollTo: noop,
    confirm: () => true, alert: noop, prompt: () => null,
    requestAnimationFrame: (fn) => setTimeout(() => fn(Date.now()), 16),
    cancelAnimationFrame: (id) => clearTimeout(id),
    navigator: { userAgent: 'mcp-mc-brawl/node', language: 'zh-CN', standalone: false, clipboard: { writeText: async () => {} } },
    location: { protocol: 'http:', hostname: '127.0.0.1', host: '127.0.0.1:8787', port: '8787',
                origin: 'http://127.0.0.1:8787', pathname: '/index.html', search: '', hash: '',
                href: 'http://127.0.0.1:8787/index.html', reload: noop, replace: noop, assign: noop },
    screen: { width: 1280, height: 800, availWidth: 1280, availHeight: 800 },
    performance: { now: () => Date.now() },
    localStorage, document,
    URLSearchParams, URL,
  };
  win.window = win;
  win.globalThis = win;
  win.self = win;
  const sandbox = {
    document, window: win, localStorage, URLSearchParams, URL,
    navigator: win.navigator, location: win.location, screen: win.screen, performance: win.performance,
    alert: noop, confirm: win.confirm, prompt: win.prompt,
    getComputedStyle: win.getComputedStyle,
    requestAnimationFrame: win.requestAnimationFrame, cancelAnimationFrame: win.cancelAnimationFrame,
    devicePixelRatio: 1, innerWidth: 1280, innerHeight: 800,
    /* 沙箱不联网：fetch 直接拒绝，游戏里的 .catch 会兜住 */
    fetch: () => Promise.reject(new Error('sandbox: no network')),
    setTimeout, clearTimeout, setInterval, clearInterval,
    console: { log() {}, warn() {}, error() {}, info() {}, debug() {} },
    Math, JSON, Date, Object, Array, String, Number, Boolean, Infinity, NaN,
    isNaN, parseInt, parseFloat, Promise, Set, Map, Error, RegExp, Symbol, TypeError, RangeError,
  };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(m[1], sandbox, { filename: 'mc-brawl-game.js' });

  const MC = sandbox.window.MCGame;
  if (!MC) throw new Error('游戏没导出 MCGame');
  state.MC = MC; state.sandbox = sandbox; state.dom = reg;

  const API = MC.__api;
  API.setRpsExternal((player) => new Promise((resolve) => {
    state.pending = { kind: 'rps', who: whoOf(player), resolve, p: player };
  }));
  API.setAutoPlayer((player, opts) => new Promise((resolve) => {
    state.pending = { kind: 'action', who: whoOf(player), resolve, p: player, opts };
  }));
  try { API.setFastTiming(); } catch {}
  try { if (typeof API.setInstantRps === 'function') API.setInstantRps(); } catch {}
  return MC;
}

async function pump(maxMs = 4000) {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    if (state.pending) return;
    const G = state.MC ? state.MC.state() : null;
    if (G && G.over) return;
    await new Promise((r) => setTimeout(r, 10));
  }
}

/* ---------------- 文本 ---------------- */
function progName(MC, prog) {
  const names = MC.PROG_NAME || ['空手', '木进程', '石进程', '铁进程', '钻石进程'];
  return names[prog] ?? `进程${prog}`;
}
function itemName(MC, key) {
  const it = MC.ITEMS && MC.ITEMS[key];
  return it ? it.name : (key || '空手');
}
function playerLine(MC, API, me, p) {
  const bits = [`${p.hp} 血`];
  if (p.armor && p.armorCharges > 0) bits.push(`${itemName(MC, p.armor)}(${p.armorCharges})`);
  bits.push(`${p.ap} AP`);
  bits.push(progName(MC, p.prog));
  bits.push(`武器 ${itemName(MC, p.weapon || 'fist')}`);
  if (me && p !== me) bits.push(`相距 ${API.distanceBetween(me, p)} 格`);
  return bits.join('，');
}

function pendingLabel() {
  const pd = state.pending;
  if (!pd) return '（等待中）';
  if (pd.kind === 'rps') {
    return pd.who === 'you' ? '猜拳阶段：等主人出拳'
      : pd.who === 'her' ? '猜拳阶段：等她出拳'
      : '猜拳阶段：等 AI 出拳';
  }
  return pd.who === 'you' ? '行动阶段：等主人选择行动'
    : pd.who === 'her' ? '行动阶段：等她选择行动'
    : '行动阶段：等 AI 行动';
}

function stateText() {
  const MC = state.MC;
  if (!MC) return '还没有开局，先调用 mc_new_game。';
  const G = MC.state();
  if (!G) return '还没有开局，先调用 mc_new_game。';
  const API = MC.__api;
  const you = G.players.find((p) => p.id === state.youId) || G.players[0];
  const others = G.players.filter((p) => p !== you);

  if (G.over) {
    return `对局结束：${you.alive ? '主人赢了' : '她赢了'}。共 ${G.round} 回合。\n` +
      `主人：${you.alive ? '存活' : '倒下'}｜对手：${others.map((o) => `${o.name} ${o.alive ? '存活' : '倒下'}`).join('、')}`;
  }

  const lines = [];
  lines.push(`回合 ${G.round}｜${pendingLabel()}`);
  lines.push(`主人：${playerLine(MC, API, you, you)}`);
  for (const o of others) {
    const tag = state.herId !== null && o.id === state.herId ? '（她）' : '';
    lines.push(`${o.name}${tag}：${playerLine(MC, API, you, o)}`);
  }
  for (const who of [you, ...others]) {
    if (who.effects && who.effects.length) {
      lines.push(`${who.name} 状态：${who.effects.map((e) => `${e.label}${e.rounds ? `(${e.rounds}回合)` : ''}`).join('、')}`);
    }
  }
  return lines.join('\n');
}

function optionsText(forWho) {
  const pd = state.pending;
  if (!pd || pd.kind !== 'action') return '';
  if (forWho && pd.who !== forWho) return '';
  const API = state.MC.__api;
  const opts = API.buildHumanOptions(pd.p);
  if (!opts.length) return '（没有可用行动，可以直接 mc_act 传 "pass" 结束）';
  const head = pd.who === 'you' ? '主人可选行动：' : pd.who === 'her' ? '她的可选行动：' : '可选行动：';
  return head + '\n' + opts.map((o, i) => `${i + 1}. ${o.label}`).join('\n');
}

function recentLogs(n = 25) {
  const all = readAllLogs();
  return all.slice(-n).join('\n') || '（暂无日志）';
}

/* 把当前所有待处理的猜拳都推完（平局自动用同一手重出） */
async function drainRps(moveFor) {
  let guard = 0;
  while (state.pending && state.pending.kind === 'rps' && guard++ < 24) {
    const { who, resolve } = state.pending;
    state.pending = null;
    const mv = moveFor(who);
    resolve(mv || 'rock');
    await pump();
  }
}

/* ---------------- MCP ---------------- */
const server = new McpServer({ name: 'mc-brawl', version: '1.1.0' });

server.tool(
  'mc_new_game',
  '开一局「方块猜拳战场」。默认是「主人 vs 她」的双人对战；也可以 vsHer=false 让她单人打 AI。重复调用会重开。',
  {
    vsHer: z.boolean().optional().describe('true（默认）= 主人和她对打；false = 她单人打 AI'),
    mode: z.enum(['1v1', '2v2']).optional().describe('对局模式，默认 1v1'),
    diff: z.enum(['easy', 'normal', 'hard']).optional().describe('AI 难度（仅 vsHer=false 时生效），默认 normal'),
    apPerWin: z.number().int().min(1).max(2).optional().describe('猜拳获胜得几点 AP，默认 2'),
    yourName: z.string().max(12).optional().describe('主人的显示名，默认「主人」'),
    herName: z.string().max(12).optional().describe('她的显示名，默认「她」'),
  },
  async ({ vsHer, mode, diff, apPerWin, yourName, herName }) => {
    try {
      const MC = loadGame();
      state.pending = null;
      state.started = true;
      state.lastError = '';
      const duel = vsHer !== false;
      state.duel = duel;

      MC.start({
        mode: mode || '1v1',
        enemyCount: 1,
        diff: diff || 'normal',
        apPerWin: apPerWin || 2,
        name: yourName || '主人',
        auto: false,
        silent: false,
        seed: (Date.now() & 0x7fffffff) || 1,
      });

      const G = MC.state();
      state.youId = G.players[0].id;
      if (duel) {
        /* 把第 2 名玩家（原本是 AI 敌人）改成第二个「人类」——由她来操控 */
        const foe = G.players[1];
        foe.isHuman = true;
        foe.team = 1;
        if (herName) foe.name = herName;
        state.herId = foe.id;
      } else {
        state.herId = null;
      }

      await pump();
      const intro = duel
        ? `开局完成：主人 vs 她（${mode || '1v1'}）。\n规则：每回合先猜拳拼 AP，赢的人拿 ${apPerWin || 2} AP，然后各自用 AP 行动。`
        : `开局完成（单人，难度 ${diff || 'normal'}）。`;
      return {
        content: [{
          type: 'text',
          text: `${intro}\n\n${stateText()}\n\n${duel ? '下一步：等主人出拳，用 mc_duel_turn(userMove=主人的拳, herMove=你的拳)。' : '出拳用 mc_rps(rock/scissors/paper)，行动用 mc_act。'}`,
        }],
      };
    } catch (err) {
      state.lastError = String(err && err.message ? err.message : err);
      return { content: [{ type: 'text', text: `开局失败：${state.lastError}` }], isError: true };
    }
  },
);

server.tool(
  'mc_duel_turn',
  '双人对战的一轮猜拳：把主人的出拳和你的出拳一起提交。平局会自动用同样的手重出直到分出胜负。返回结算与后续局面。',
  {
    userMove: z.enum(['rock', 'scissors', 'paper']).describe('主人这轮出的：rock 石头 / scissors 剪刀 / paper 布'),
    herMove: z.enum(['rock', 'scissors', 'paper']).describe('你（她）这轮出的：rock 石头 / scissors 剪刀 / paper 布'),
  },
  async ({ userMove, herMove }) => {
    if (!state.MC) return { content: [{ type: 'text', text: '还没有开局，先 mc_new_game。' }], isError: true };
    if (!state.pending || state.pending.kind !== 'rps') {
      return { content: [{ type: 'text', text: `现在不是猜拳阶段。\n\n${stateText()}` }], isError: true };
    }
    const before = readAllLogs().length;
    await drainRps((who) => (who === 'you' ? userMove : herMove));
    const fresh = readAllLogs().slice(before).filter((l) => /猜拳|判定|AP|回合/.test(l));
    const head = fresh.length ? fresh.join('\n') + '\n\n' : '';
    const opts = optionsText();
    return { content: [{ type: 'text', text: head + stateText() + (opts ? `\n\n${opts}` : '') }] };
  },
);

server.tool(
  'mc_state',
  '查看当前对局局面：血量/AP/进度/装备/距离，以及现在轮到谁。',
  {},
  async () => {
    const opts = optionsText();
    return { content: [{ type: 'text', text: stateText() + (opts ? `\n\n${opts}` : '') }] };
  },
);

server.tool(
  'mc_act',
  '执行一个行动。who 指定是谁的行动；choice 是 mc_state 列出的序号，或 "pass" 结束该玩家的行动。',
  {
    who: z.enum(['you', 'her']).optional().describe('you = 主人的行动（默认），her = 她自己的行动'),
    choice: z.union([z.number(), z.string()]).describe('行动序号（1、2…），或 "pass" 结束'),
  },
  async ({ who, choice }) => {
    /* who 不给就自动判断当前轮到谁（她常常会忘记传这个参数） */
    if(!who){
      const pd0 = state.pending;
      who = (pd0 && pd0.who === 'her') ? 'her' : 'you';
    }
    if (!state.MC) return { content: [{ type: 'text', text: '还没有开局，先 mc_new_game。' }], isError: true };
    const pd = state.pending;
    if (!pd || pd.kind !== 'action') {
      return { content: [{ type: 'text', text: `现在不是行动阶段。\n\n${stateText()}` }], isError: true };
    }
    if (pd.who !== who) {
      const nm = pd.who === 'you' ? '主人' : pd.who === 'her' ? '她' : 'AI';
      return { content: [{ type: 'text', text: `现在等的是「${nm}」的行动，不是这个。\n\n${stateText()}` }], isError: true };
    }
    const API = state.MC.__api;
    const opts = API.buildHumanOptions(pd.p);
    const resolve = pd.resolve;
    state.pending = null;

    /* 归一化：允许 "pass"/"PASS"/"跳过"、也允许字符串序号 "3" */
    const raw = String(choice).trim();
    const isPass = /^(pass|跳过|结束)$/i.test(raw);
    if (!isPass) {
      const n = Number(raw);
      if (!Number.isFinite(n) || n < 1 || n > opts.length) {
        state.pending = pd;                      /* 还原，让她能重试 */
        const list = opts.map((o, i) => `${i + 1}. ${o.label}`).join(String.fromCharCode(10));
        return { content: [{ type: 'text', text: `没有第 ${raw} 个行动（共 ${opts.length} 个）：
${list}` }], isError: true };
      }
    }
    const choiceIdx = isPass ? null : Number(raw);

    if (isPass) {
      resolve(null);
      await pump();
      const opts2 = optionsText();
      return { content: [{ type: 'text', text: `已结束行动。\n\n${stateText()}${opts2 ? `\n\n${opts2}` : ''}` }] };
    }
    const idx = Number(choice) - 1;
    if (idx < 0 || idx >= opts.length) {
      resolve(null);
      await pump();
      return {
        content: [{ type: 'text', text: `序号超出范围（当前 ${opts.length} 个行动），已自动结束该玩家行动。\n\n${stateText()}` }],
        isError: true,
      };
    }
    const before = readAllLogs().length;
    resolve(opts[idx]);
    await pump();
    const fresh = readAllLogs().slice(before);
    const head = fresh.length ? fresh.join('\n') + '\n\n' : '';
    const opts2 = optionsText();
    return {
      content: [{
        type: 'text',
        text: `已执行「${opts[idx].label}」。\n\n${head}${stateText()}${opts2 ? `\n\n${opts2}` : ''}`,
      }],
    };
  },
);

server.tool(
  'mc_rps',
  '单人模式出拳（双人对战请用 mc_duel_turn）。',
  { move: z.enum(['rock', 'scissors', 'paper']).describe('rock 石头 / scissors 剪刀 / paper 布') },
  async ({ move }) => {
    if (!state.MC) return { content: [{ type: 'text', text: '还没有开局，先 mc_new_game。' }], isError: true };
    if (!state.pending || state.pending.kind !== 'rps') {
      return { content: [{ type: 'text', text: `现在不是猜拳阶段。\n\n${stateText()}` }], isError: true };
    }
    const before = readAllLogs().length;
    await drainRps(() => move);
    const fresh = readAllLogs().slice(before).filter((l) => /猜拳|判定|AP|回合/.test(l));
    const opts = optionsText();
    return {
      content: [{
        type: 'text',
        text: (fresh.length ? fresh.join('\n') + '\n\n' : '') + stateText() + (opts ? `\n\n${opts}` : ''),
      }],
    };
  },
);

server.tool(
  'mc_quick_turn',
  '单人模式的快速回合：出拳 + 自动替你行动（内置 AI 选最优），直到回合结束。双人对战请用 mc_duel_turn。',
  { move: z.enum(['rock', 'scissors', 'paper']).describe('这一回合出什么') },
  async ({ move }) => {
    if (!state.MC) return { content: [{ type: 'text', text: '还没有开局，先 mc_new_game。' }], isError: true };
    const MC = state.MC, API = MC.__api;
    const before = readAllLogs().length;

    await drainRps(() => move);

    let steps = 0;
    while (state.pending && state.pending.kind === 'action' && steps++ < 15) {
      const p = state.pending.p;
      const all = API.buildHumanOptions(p);
      const payable = all.filter((o) => { try { return API.canPay(p, o); } catch { return true; } });
      const actionable = payable.filter((o) => !['pass', 'switch_weapon', 'armor_priority'].includes(o.type));
      let pick = null;
      if (actionable.length) { try { pick = API.aiPick(p, actionable, []); } catch {} }
      const r0 = state.pending.resolve; state.pending = null;
      if (!pick) { r0(null); await pump(); break; }
      r0(pick);
      await pump();
    }
    let guard = 0;
    while (state.pending && state.pending.kind === 'action' && guard++ < 6) {
      const r2 = state.pending.resolve; state.pending = null; r2(null);
      await pump();
    }

    const fresh = readAllLogs().slice(before);
    return { content: [{ type: 'text', text: (fresh.length ? fresh.join('\n') + '\n\n' : '') + stateText() }] };
  },
);


/* ---------------- 联机房间（网页端那一局）的文本渲染 ---------------- */
function renderRoomSnapshot(code, d, detail) {
  const full = detail === 'full';
  const TEAM = ['A', 'B', 'C', 'D'];
  const DIFF = { easy: '简单', normal: '普通', hard: '困难' };
  /* 服务器从 1.7.0 起返回 slots（固定 6 格，空位是 null），老版本才是 seats */
  const slots = Array.isArray(d.slots) ? d.slots
    : (Array.isArray(d.seats) ? d.seats.map((x) => ({ kind: 'human', ...x })) : []);
  const seated = slots.filter(Boolean);
  const seatText = seated.map((x) => {
    const team = '队伍' + (TEAM[x.team | 0] || '?');
    const kind = x.kind === 'bot' ? `（人机·${DIFF[x.diff] || '普通'}）` : (x.isHost ? '（房主）' : '');
    const me = x.isYou ? '（就是你）' : '';
    return `${team} ${x.name}${kind}${me}${x.ready ? ' ✓' : ''}`;
  }).join('｜');

  const head = `房间 ${code}｜${d.mode || '1v1'}｜座位 ${seated.length}/${slots.length || 6}` +
    (typeof d.teams === 'number' ? `｜${d.teams} 个队伍` : '') +
    `｜${d.started ? '对局进行中' : '等待开始（房主还没点开始）'}`;

  const snap = d.snapshot;
  if (!snap) {
    return [
      head,
      `座位：${seatText || '（所有座位都是空的）'}`,
      '',
      '还没有局面数据：网页端要「开始对局」之后，每 0.8 秒才会上报局面。',
      '（如果房主已经开始了还是没有，让房主刷新一下网页试试）',
    ].join('\n');
  }

  const lines = [head];
  lines.push(`座位：${seatText || '—'}`);
  lines.push(`第 ${snap.round} 回合${snap.over ? '（已结束）' : ''}`);
  for (const p of snap.players || []) {
    const seat = seated.find((x) => x.name === p.name);
    const tag = seat ? `[${TEAM[seat.team | 0] || '?'}]` : '';
    const bits = [`${p.hp} 血`, `${p.ap} AP`];
    if (p.prog) bits.push(p.prog);
    if (p.weapon) bits.push(`武器 ${p.weapon}`);
    if (p.armor) bits.push(p.armor);
    if (p.dist !== null && p.dist !== undefined) bits.push(`相距 ${p.dist} 格`);
    if (!p.alive) bits.push('已倒下');
    lines.push(`  ${tag}${p.name}：${bits.join('，')}`);
  }
  if (snap.lastLog && snap.lastLog.length) {
    const logs = full ? snap.lastLog : snap.lastLog.slice(-1);
    lines.push(full ? '最近动态：' : '刚刚：');
    for (const l of logs) lines.push('  ' + l);
    if (!full && snap.lastLog.length > 1) {
      lines.push(`  （还有 ${snap.lastLog.length - 1} 条更早的，复盘传 detail:"full"）`);
    }
  }
  if (full) {
    const age = d.updatedAt ? Math.round((Date.now() - d.updatedAt) / 1000) : null;
    if (age !== null && age >= 0) lines.push(age <= 3 ? '（数据是实时的）' : `（数据更新于 ${age} 秒前）`);
  }
  return lines.join('\n');
}


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
  if (ask.ask === 'rps') return head + '（用 mc_room_answer move=rock/scissors/paper 回答）' +
    '  💡 顺手把这一回合的行动也排好：plan="1,3,pass" —— 一回合只问一次，快很多。';
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
  '回答 mc_room_wait 的问题。move=出拳；choice=行动序号/id/pass；plan=顺便把整回合行动排好（逗号分隔，最快）。',
  {
    move: z.enum(['rock', 'scissors', 'paper']).optional().describe('出拳：rock/scissors/paper'),
    choice: z.string().optional().describe('行动序号（1、2…）或选项 id，或 "pass"'),
    plan: z.string().optional().describe('整回合计划，逗号分隔，如 "1,3,pass"；和 move 一起传只要一问一答'),
  },
  async ({ move, choice, plan }) => {
    const r = state.room;
    if (!r.code || !r.seatId) return { content: [{ type: 'text', text: '还没进房间，先 mc_room_join。' }], isError: true };
    const ask = r.ask;
    if (!ask) return { content: [{ type: 'text', text: '现在没有要回答的问题（先 mc_room_wait）。' }], isError: true };

    const planList = (typeof plan === 'string' && plan.trim())
      ? plan.split(/[,\uFF0C;\uFF1B\n、]/).map(x => x.trim()).filter(Boolean)
      : [];
    const action = { kind: 'ans', promptId: ask.promptId };
    if (planList.length) action.plan = planList;
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
      return { content: [{ type: 'text', text: `已提交（${what}）。接着 mc_room_wait 等下一条，或者用 mc_room 按房间码看局面。` }] };
    } catch (e) {
      return { content: [{ type: 'text', text: `提交时出错：${e && e.message ? e.message : e}` }], isError: true };
    }
  },
);

server.tool(
  'mc_log',
  '读取最近的战斗日志（纯文本），用于复盘或给群友讲刚才发生了什么。',
  { lines: z.number().int().min(1).max(80).optional().describe('要读最近多少行，默认 25') },
  async ({ lines }) => {
    return { content: [{ type: 'text', text: recentLogs(lines || 25) }] };
  },
);


server.tool(
  'mc_room',
  '凭 9 位联机码读取【网页端正在进行的那一局】的实时局面（只读）。默认返回精简版（回合+双方数据+刚发生的一条），不会占太多上下文；要复盘再传 detail:"full"。',
  {
    code: z.string().regex(/^[A-Z0-9]{9}$/).describe('9 位房间码（大写字母 + 数字）'),
    serverUrl: z.string().optional().describe('联机服务器地址，默认取环境变量 MC_SERVER 或 http://127.0.0.1:8787'),
    detail: z.enum(['brief', 'full']).optional().describe('brief（默认）精简；full 带完整战斗日志，仅复盘时用'),
  },
  async ({ code, serverUrl, detail }) => {
    const base = (serverUrl || process.env.MC_SERVER || 'http://127.0.0.1:8787').replace(/\/+$/, '');
    let d = null;
    try {
      const r = await fetch(`${base}/api/room/${code}/peek`, { cache: 'no-store' });
      d = await r.json();
    } catch (e) {
      return {
        content: [{
          type: 'text',
          text: `连不上联机服务器（${base}）：${e && e.message ? e.message : e}\n\n请确认那台主机已经运行 start-server.cmd，且地址/端口正确。`,
        }],
        isError: true,
      };
    }
    if (!d || !d.ok) {
      return {
        content: [{ type: 'text', text: `读不到房间 ${code}：${(d && d.err) || '房间不存在或已过期（3 小时无活动会回收）'}` }],
        isError: true,
      };
    }
    /* 房主在联机对局里每 250ms 会把整份局面推到 /state，比 snapshot 更全 */
    let live = null;
    try {
      const sr = await fetch(`${base}/api/room/${code}/state`, { cache: 'no-store' });
      const sd = await sr.json();
      if (sd && sd.ok && sd.state) live = sd.state;
    } catch {}
    const text = renderRoomSnapshot(code, d, detail);
    const withBoard = live ? text + String.fromCharCode(10) + String.fromCharCode(10) + '当前局面：' + String.fromCharCode(10) + boardText(live) : text;
    return { content: [{ type: 'text', text: withBoard }] };
  },
);

/* ---------------- 自检：node src/mcp-mc-brawl.js --selftest ----------------
   不开 MCP，直接跑「加载游戏 → 开局 → 走几轮猜拳/行动」，验证沙箱没问题。 */
async function runSelfTest() {
  const log = (m) => console.log(m);
  try {
    log('[1] 加载游戏…');
    const MC = loadGame();
    log('    OK，MCGame 已导出；玩家模板可用: ' + typeof MC.state);
    log('[2] 开局（单人 vs AI，快节奏）…');
    MC.start({ mode: '1v1', enemyCount: 1, diff: 'easy', apPerWin: 2, name: '自检', auto: true, silent: false, seed: 20260101 });
    const G = MC.state();
    if (!G) throw new Error('开局后没有对局状态');
    log('    OK，玩家数 ' + G.players.length + '，回合 ' + G.round);
    log('[3] 推若干轮（自动出拳 + 自动行动）…');
    for (let i = 0; i < 200; i++) {
      const st = MC.state();
      if (st && st.over) break;
      if (state.pending && state.pending.kind === 'rps') {
        const r = state.pending.resolve; state.pending = null; r(['rock', 'scissors', 'paper'][i % 3]);
      } else if (state.pending && state.pending.kind === 'action') {
        const pd = state.pending;
        const opts = MC.__api.buildHumanOptions(pd.p) || [];
        const pick = opts.find((o) => o.type === 'attack') || { type: 'pass' };
        state.pending = null; pd.resolve(pick);
      }
      await new Promise((r) => setTimeout(r, 12));
    }
    const st = MC.state();
    log('    OK，推进到回合 ' + (st && st.round) + '，结束=' + !!(st && st.over));
    log('    ' + String(stateText()).split('\n').slice(0, 3).join(' / '));
    log('[4] 结算面板能不能画（不炸）…');
    try { MC.__api && MC.__api.renderAll && MC.__api.renderAll(); } catch (e) { log('    renderAll 抛错: ' + e.message); }
    log('SELFTEST OK');
    process.exit(0);
  } catch (e) {
    console.log('SELFTEST FAIL: ' + (e && e.stack ? e.stack : e));
    process.exit(1);
  }
}
if (process.argv.includes('--selftest')) {
  await runSelfTest();
} else {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
