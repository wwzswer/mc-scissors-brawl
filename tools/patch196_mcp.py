import io

p = 'D:/Documents/deepseek-harness/default-workspace/qq-bridge/src/mcp-mc-brawl.js'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label):
    global s
    assert old in s, '锚点不存在: ' + label
    s = s.replace(old, new, 1)
    print('  ok', label)

# ---------------- 1) 更完整的 window / document 桩 ----------------
old_sandbox = """  const reg = {};
  const document = {
    createElement: makeEl,
    getElementById(id) { if (!reg[id]) { reg[id] = makeEl('div'); reg[id].id = id; } return reg[id]; },
    querySelectorAll() { return []; }, querySelector() { return null; }, body: makeEl('body'),
  };
  const store = {};
  const localStorage = {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
    clear: () => { for (const k in store) delete store[k]; },
  };
  const sandbox = {
    document, window: {}, localStorage,
    setTimeout, clearTimeout, setInterval, clearInterval,
    console: { log() {}, warn() {}, error() {}, info() {}, debug() {} },
    Math, JSON, Date, Object, Array, String, Number, Boolean, Infinity, NaN,
    isNaN, parseInt, parseFloat, Promise, Set, Map, Error, RegExp, Symbol, TypeError, RangeError,
  };
  sandbox.globalThis = sandbox;"""

new_sandbox = """  const reg = {};
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
    setTimeout, clearTimeout, setInterval, clearInterval,
    console: { log() {}, warn() {}, error() {}, info() {}, debug() {} },
    Math, JSON, Date, Object, Array, String, Number, Boolean, Infinity, NaN,
    isNaN, parseInt, parseFloat, Promise, Set, Map, Error, RegExp, Symbol, TypeError, RangeError,
  };
  sandbox.globalThis = sandbox;"""
sub(old_sandbox, new_sandbox, '沙箱补齐 window/document 桩')

# ---------------- 2) 自检模式 ----------------
sub("""const transport = new StdioServerTransport();
await server.connect(transport);""",
    """/* ---------------- 自检：node src/mcp-mc-brawl.js --selftest ----------------
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
    log('    ' + String(stateText()).split('\\n').slice(0, 3).join(' / '));
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
}""",
    '自检模式')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch mcp: %d -> %d bytes' % (n0, len(s)))
