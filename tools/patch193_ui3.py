import io

p = 'index.html'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label):
    global s
    assert old in s, '锚点不存在: ' + label
    s = s.replace(old, new, 1)
    print('  ok', label)

# ---------------- 1) 行动面板/商店：手机上渲染到悬浮球里 ----------------
sub("""function buildActionPanel(p, opts, settle){
  window.__mcOptions = opts;
  pendingChoice = { opts, settle };
  pendingChoiceFor = p;
  const allOpts = opts || [];
  const bar = document.getElementById('actionbar');
  if(!bar) return;""",
    """function isMobileUI(){ return window.innerWidth <= 760; }
/* 行动面板的宿主：手机 → 悬浮球抽屉；桌面 → 行动区卡片 */
function actionHostEl(){
  if(isMobileUI()){
    const body = document.getElementById('fabSheetBody');
    if(body) return body;
  }
  return document.getElementById('actionbar');
}
function buildActionPanel(p, opts, settle){
  window.__mcOptions = opts;
  const isNewChoice = (pendingChoice === null || pendingChoice === undefined) || pendingChoice.settle !== settle;
  pendingChoice = { opts, settle };
  pendingChoiceFor = p;
  const allOpts = opts || [];
  const bar = actionHostEl();
  if(!bar) return;
  if(isMobileUI() && isNewChoice) fabToggle(true);   /* 轮到你了：自动弹开抽屉 */""",
    '行动面板宿主')

# openShop 也走同一宿主
sub("""  let mode = craftFirst ? 'progress' : 'craft';
  const bar=document.getElementById('actionbar');""",
    """  let mode = craftFirst ? 'progress' : 'craft';
  const bar=actionHostEl();""",
    'openShop 宿主')

# ---------------- 2) 悬浮球 / 返回键 / 临时存档 / 退出确认 ----------------
FEATURE = r'''
/* =========================================================================
   手机端交互：悬浮球（行动抽屉）+ 左上角返回键
   ========================================================================= */
function fabToggle(force){
  const sheet = document.getElementById('fabSheet');
  const fab = document.getElementById('fab');
  if(!sheet || !fab) return;
  const open = (force === undefined) ? !sheet.classList.contains('open') : !!force;
  sheet.classList.toggle('open', open);
  fab.textContent = open ? '✕' : '＋';
  if(open) fab.classList.remove('attn');
}
function updateFabAttn(){
  const fab = document.getElementById('fab');
  const sheet = document.getElementById('fabSheet');
  if(!fab || !sheet) return;
  const waiting = !!pendingChoice && !sheet.classList.contains('open');
  fab.classList.toggle('attn', waiting);
}
function updateFabVisibility(){
  const fab = document.getElementById('fab');
  const sheet = document.getElementById('fabSheet');
  const inGame = !!document.getElementById('game') && !document.getElementById('game').classList.contains('hidden');
  const show = inGame && isMobileUI();
  if(fab) fab.classList.toggle('hidden', !show);
  if(!show && sheet) sheet.classList.remove('open');
  updateFabAttn();
}
/* 左上角返回键 */
function updateBackBtn(){
  const b = document.getElementById('backBtn');
  if(!b) return;
  const scr = (typeof currentScreen !== 'undefined') ? currentScreen : 'screen-main';
  b.classList.toggle('hidden', scr === 'screen-main');
}
function quitGame(){
  const net = (typeof Net !== 'undefined' && Net.active);
  const msg = net
    ? '退出联机房间？\n\n多人对局不会保存进度，退出后这一局就散了。'
    : '退出这一局？\n\n单人会留一份临时存档，可以从主菜单「继续上次对局」接着打（结算或开新局才会清掉）。';
  if(!confirm(msg)) return;
  try{ saveTempGame(true); }catch(e){}
  if(net){ try{ Net.leave(); }catch(e){} }
  if(G) G.over = true;              /* 让旧的主循环自行退出 */
  try{ gameLoopStop(); }catch(e){}
  showScreen('screen-main');
  updateBackBtn(); updateFabVisibility(); refreshResumeBtn();
}
function onBackBtn(){
  const scr = (typeof currentScreen !== 'undefined') ? currentScreen : 'screen-main';
  if(scr === 'game'){ quitGame(); return; }
  if(scr !== 'screen-main'){ showScreen('screen-main'); updateBackBtn(); return; }
}
/* =========================================================================
   临时存档（只存单机；多人不存）
   ========================================================================= */
const TEMP_KEY = 'mcTempSave';
function tempSaveAllowed(){
  if(!G || G.over) return false;
  if(typeof Net !== 'undefined' && Net.active) return false;
  if(typeof NetPlay !== 'undefined' && NetPlay.role) return false;
  return true;
}
function saveTempGame(force){
  if(!tempSaveAllowed()) return;
  const now = Date.now();
  if(!force && now - (saveTempGame._last || 0) < 1500) return;
  saveTempGame._last = now;
  try{
    localStorage.setItem(TEMP_KEY, JSON.stringify({
      v: 1, at: now,
      G: {
        players: G.players, round: G.round, dist: G.dist, turnOwner: G.turnOwner,
        startedAt: G.startedAt, logLines: (G.logLines || []).slice(-60),
      }
    }));
    refreshResumeBtn();
  }catch(e){}
}
function clearTempGame(){
  try{ localStorage.removeItem(TEMP_KEY); }catch(e){}
  refreshResumeBtn();
}
function loadTempGame(){
  try{
    const d = JSON.parse(localStorage.getItem(TEMP_KEY) || 'null');
    if(!d || !d.G || !Array.isArray(d.G.players) || !d.G.players.length) return null;
    return d;
  }catch(e){ return null; }
}
function refreshResumeBtn(){
  const b = document.getElementById('mResume');
  if(!b) return;
  const d = loadTempGame();
  if(d){
    b.classList.remove('hidden');
    b.textContent = '⏵ 继续上次对局（第 ' + (d.G.round || 1) + ' 回合 · ' + (d.G.players.length) + ' 人）';
  }else{
    b.classList.add('hidden');
  }
}
function resumeTempGame(){
  const d = loadTempGame();
  if(!d){ appToast('没有可继续的对局'); return; }
  const g = d.G;
  runSeq += 1;
  G = {
    players: g.players, round: g.round || 1, dist: g.dist || {}, roundOrder: [],
    over: false, turnOwner: null, progSnap: {}, runId: runSeq,
    startedAt: g.startedAt || Date.now(), logLines: (g.logLines || []).slice(-60),
  };
  for(const p of G.players){
    p.isLocal = !!p.isHuman;
    if(!p.st) p.st = {ap:0, dmgMax:0, heal:0, kills:0};
  }
  /* 距离表兜底重建 */
  if(!G.dist || !Object.keys(G.dist).length){
    G.dist = {};
    G.players.forEach(a=>{ G.dist[a.id] = {}; G.players.forEach(b=>{ G.dist[a.id][b.id] = a===b?0:1; }); });
  }
  pendingChoice = null; pendingChoiceFor = null;
  showScreen('game');
  try{ renderGuestLog(G.logLines); }catch(e){}
  log('⏵ 已继续上次的对局（临时存档）—— 结算或开新单机局才会清掉它。','l-good');
  renderAll();
  updateBackBtn(); updateFabVisibility();
  gameLoop();
}
/* 旧循环停止用：把 over 置位即可，gameLoop 每轮都会检查 */
function gameLoopStop(){ if(G) G.over = true; }
'''
sub("""/* =========================================================================
   联机对局同步（房主权威）""",
    FEATURE + """
/* =========================================================================
   联机对局同步（房主权威）""",
    '插入悬浮球/返回键/临时存档')

# ---------------- 3) showScreen 同步按钮状态 ----------------
sub("""  if(id==='screen-start') refreshStartInfo();
}""",
    """  if(id==='screen-start') refreshStartInfo();
  try{ updateBackBtn(); updateFabVisibility(); }catch(e){}
}""",
    'showScreen 同步按钮')

# ---------------- 4) renderAll 里自动存临时档 + 悬浮球提示 ----------------
sub("""  try{ if(typeof netPushState === 'function' && netIsHostEngine()) netPushState(); }catch(e){}
}""",
    """  try{ if(typeof netPushState === 'function' && netIsHostEngine()) netPushState(); }catch(e){}
  try{ saveTempGame(); }catch(e){}
  try{ updateFabAttn(); }catch(e){}
}""",
    'renderAll 存临时档')

# ---------------- 5) 联机退出确认 ----------------
sub("""  leave(){
    const code = this.code, me = this.youId;""",
    """  leave(skipConfirm){
    if(!skipConfirm && this.active && !confirm('退出联机房间？\\n\\n多人对局不会保存进度，退出后这一局就散了。')) return;
    const code = this.code, me = this.youId;""",
    'Net.leave 确认')

# ---------------- 6) 开新单机局时清掉临时档 ----------------
sub("""  runSeq += 1;
  const myRun = runSeq;
  showScreen('game');""",
    """  runSeq += 1;
  const myRun = runSeq;
  try{ if(!(typeof Net !== 'undefined' && Net.active)) clearTempGame(); }catch(e){}
  showScreen('game');""",
    '开新局清临时档')

# ---------------- 7) 联机状态里带上开始时间 ----------------
sub("""    apPerWin,
    mode: gameMode,
    players: G.players.map(p=>Object.assign({}, p)),""",
    """    apPerWin,
    mode: gameMode,
    startedAt: G.startedAt || Date.now(),
    players: G.players.map(p=>Object.assign({}, p)),""",
    '状态带 startedAt')

sub("""    runId,
    logLines: st.log || [],
    guest: true,
  };""",
    """    runId,
    startedAt: st.startedAt || Date.now(),
    logLines: st.log || [],
    guest: true,
  };""",
    '访客带 startedAt')

# ---------------- 8) 访客结算也走同一套面板 ----------------
sub("""function netGuestResult(){
  try{
    const me = G && G.players.find(p=>p.isHuman && p.isLocal);
    const foes = (G && G.players.filter(p=>!p.isHuman && p.team !== (me ? me.team : -1))) || [];
    const win = me ? me.alive && foes.every(f=>!f.alive) : false;
    const ov = document.getElementById('overlay');
    const box = document.getElementById('overlayBox');
    if(!ov || !box) return;""",
    """function netGuestResult(){
  try{
    const me = G && G.players.find(p=>p.isHuman && p.isLocal);
    const foes = (G && G.players.filter(p=>!p.isHuman && p.team !== (me ? me.team : -1))) || [];
    const win = me ? me.alive && foes.every(f=>!f.alive) : false;
    const ov = document.getElementById('overlay');
    const box = document.getElementById('overlayBox');
    if(!ov || !box) return;
    if(typeof settlementHTML === 'function'){
      box.innerHTML = settlementHTML(win);
      box.classList.add('settlebox');
      ov.classList.add('settle');
      ov.classList.remove('hidden');
      const c1 = document.getElementById('spClose');
      const c2 = document.getElementById('spClose2');
      const close = ()=>{ ov.classList.add('hidden'); ov.classList.remove('settle'); box.classList.remove('settlebox'); };
      if(c1) c1.onclick = close;
      if(c2) c2.onclick = close;
      const ab = document.getElementById('againBtn');
      if(ab) ab.onclick = ()=>{ location.reload(); };
      return;
    }""",
    '访客结算复用结算面板')

# ---------------- 9) 事件绑定 ----------------
sub("""on('mSetting', ()=>{ sfx.click(); showScreen('screen-setting'); refreshProgInfo(); });""",
    """on('mSetting', ()=>{ sfx.click(); showScreen('screen-setting'); refreshProgInfo(); });
on('mResume', ()=>{ try{ sfx.click(); }catch(e){} resumeTempGame(); });
on('backBtn', ()=>{ try{ sfx.click(); }catch(e){} onBackBtn(); });
on('fab', ()=>{ try{ sfx.click(); }catch(e){} fabToggle(); });
on('fabClose', ()=>{ try{ sfx.click(); }catch(e){} fabToggle(false); });""",
    '按钮事件')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch3 完成: %d -> %d bytes' % (n0, len(s)))
