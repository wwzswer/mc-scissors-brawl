import io

p = 'index.html'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label):
    global s
    assert old in s, '锚点不存在: ' + label
    s = s.replace(old, new, 1)
    print('  ok', label)

# ============ 1) 猜拳阶段结束：保留猜拳 UI，不再隐藏 ============
sub("""    try{
      hideRpsSlots();
      rlog('hideRpsSlots 完成');
      const st = document.getElementById('rpsStatus');
      if(st) st.textContent = '选择你的出拳';
    }catch(e){ rlog('收尾段异常: ' + (e && e.message)); }""",
    """    try{
      /* 刚打完的猜拳结果留在场上，方便回看谁出了什么（不再 hideRpsSlots） */
      const st = document.getElementById('rpsStatus');
      if(st) st.textContent = '👆 本回合猜拳结果（点击下方按钮无副作用，下一回合会重开）';
      const btns = document.getElementById('rpsBtns');
      if(btns) btns.classList.add('hidden');       /* 结果展示阶段把出拳按钮藏起来，避免误点 */
    }catch(e){ rlog('收尾段异常: ' + (e && e.message)); }""",
    '猜拳结束保留 UI')

# 新一轮猜拳开始时把按钮放回来
sub("""async function rpsPhase(){
  rlog('rpsPhase 进入');""",
    """async function rpsPhase(){
  rlog('rpsPhase 进入');
  try{                                            /* 新一轮：把出拳按钮放回来 */
    const btns = document.getElementById('rpsBtns');
    if(btns) btns.classList.remove('hidden');
    const area = document.getElementById('rpsArea');
    if(area) area.classList.remove('hidden');
    const st = document.getElementById('rpsStatus');
    if(st) st.textContent = '选择你的出拳';
  }catch(e){}""",
    '新一轮恢复出拳按钮')

# ============ 2) 结算：0 值也显示 ============
sub("""  if(ap.p && ap.v > 0) rows.push({label:'最多行动点', who:ap.p.name, value:ap.v + ' AP'});""",
    """  if(ap.p) rows.push({label:'最多行动点', who:ap.p.name, value:ap.v + ' AP'});""",
    '行动点显示 0')
sub("""  if(dm.p && dm.v > 0) rows.push({label:'最高单次伤害', who:dm.p.name, value:dm.v + ' 点'});""",
    """  if(dm.p) rows.push({label:'最高单次伤害', who:dm.p.name, value:dm.v + ' 点'});""",
    '伤害显示 0')
sub("""  if(kl.p && kl.v > 0) rows.push({label:'最多击杀', who:kl.p.name, value:kl.v + ' 人'});""",
    """  if(kl.p) rows.push({label:'最多击杀', who:kl.p.name, value:kl.v + ' 人'});""",
    '击杀显示 0')
sub("""  if(hl.p && hl.v > 0) rows.push({label:'最多回血', who:hl.p.name, value:rm(hl.v) + ' 点'});""",
    """  if(hl.p) rows.push({label:'最多回血', who:hl.p.name, value:rm(hl.v) + ' 点'});""",
    '回血显示 0')

# ============ 3) 悬浮球：renderAll/resize 时校正可见性；有待选项必可见 ============
sub("""  try{ saveTempGame(); }catch(e){}
  try{ updateFabAttn(); }catch(e){}
}""",
    """  try{ saveTempGame(); }catch(e){}
  try{ updateFabVisibility(); updateFabAttn(); }catch(e){}
}""",
    'renderAll 校正悬浮球')

sub("""function updateFabVisibility(){
  const fab = document.getElementById('fab');
  const sheet = document.getElementById('fabSheet');
  const inGame = !!document.getElementById('game') && !document.getElementById('game').classList.contains('hidden');
  const show = inGame && isMobileUI();
  if(fab) fab.classList.toggle('hidden', !show);
  if(!show && sheet) sheet.classList.remove('open');
  updateFabAttn();
}""",
    """function updateFabVisibility(){
  const fab = document.getElementById('fab');
  const sheet = document.getElementById('fabSheet');
  if(!fab) return;
  const inGame = !!document.getElementById('game') && !document.getElementById('game').classList.contains('hidden');
  const busy = !!pendingChoice || (typeof G !== 'undefined' && G && !G.over);
  /* 只要在游戏里（或还有待选行动）就必须能点开，宁可多显示也别把玩家卡死 */
  const show = (inGame || busy) && isMobileUI();
  fab.classList.toggle('hidden', !show);
  if(!show && sheet) sheet.classList.remove('open');
  updateFabAttn();
}
window.addEventListener('resize', ()=>{ try{ updateFabVisibility(); }catch(e){} });
window.addEventListener('orientationchange', ()=>{ setTimeout(()=>{ try{ updateFabVisibility(); }catch(e){} }, 200); });""",
    '悬浮球可见性兜底')

# 行动面板出现时，务必把悬浮球显示出来（手机的"轮到你"入口）
sub("""  if(isMobileUI() && isNewChoice) fabToggle(true);   /* 轮到你了：自动弹开抽屉 */""",
    """  if(isMobileUI()){
    const fabEl = document.getElementById('fab');
    if(fabEl) fabEl.classList.remove('hidden');
    if(isNewChoice) fabToggle(true);                 /* 轮到你了：自动弹开抽屉 */
  }""",
    '行动面板显示悬浮球')

# ============ 4) 主动结算 ============
sub("""function settlementHTML(win){""",
    """function settlementHTML(win, manual){
  const TITLE = manual ? '📊 本局已结算' : (win ? '🏆 你赢了！' : '💀 你被击败了');""",
    '结算标题支持主动结算')

sub("""  return `
  <button class="sp-close" id="spClose" aria-label="关闭">✕</button>
  <h3 style="font-size:20px;margin:0 0 2px">${win?'🏆 你赢了！':'💀 你被击败了'}</h3>""",
    """  return `
  <button class="sp-close" id="spClose" aria-label="关闭">✕</button>
  <h3 style="font-size:20px;margin:0 0 2px">${TITLE}</h3>""",
    '结算标题使用变量')

sub("""function endGame(win){
  if(G.over) return;
  G.over=true;
  clearTempGame();                      /* 结算即作废临时存档 */
  const ov=document.getElementById('overlay'), box=document.getElementById('overlayBox');
  box.innerHTML = settlementHTML(win);""",
    """function endGame(win, manual){
  if(G.over) return;
  G.over=true;
  clearTempGame();                      /* 结算即作废临时存档 */
  const ov=document.getElementById('overlay'), box=document.getElementById('overlayBox');
  box.innerHTML = settlementHTML(win, !!manual);""",
    'endGame 支持主动结算')

sub("""  log(win?'🏆 <b>战斗结束：你获胜！</b>':'💀 <b>战斗结束：你被击败。</b>','l-warn');
}""",
    """  log(manual ? '📊 <b>本局已主动结算。</b>'
      : (win?'🏆 <b>战斗结束：你获胜！</b>':'💀 <b>战斗结束：你被击败。</b>'),'l-warn');
}
/* 主动结算：中途结束这一局并按当前局面出结算 */
function manualSettle(){
  if(!G || G.over){ appToast('现在没有进行中的对局'); return; }
  if(!confirm('现在就结算这一局吗？\\n\\n会立刻按当前局面出结算，并清除临时存档。')) return;
  const me = (typeof localHuman === 'function' ? localHuman() : null) || G.players.find(p=>p.isHuman);
  const foes = G.players.filter(p=>!p.isHuman && me && p.team !== me.team);
  const win = !!(me && me.alive && foes.length && foes.every(f=>!f.alive));
  if(typeof NetPlay !== 'undefined' && NetPlay.role === 'guest'){
    appToast('观战端不能结算，让房主结算。');
    return;
  }
  try{ G.over = true; }catch(e){}
  endGame(win, true);
}""",
    '主动结算函数')

# 悬浮球抽屉头部加「结算」按钮
sub("""  <div class="fshead"><b>⚔ 行动 · 制作 · 收集</b><button class="btn small" id="fabClose">✕</button></div>""",
    """  <div class="fshead"><b>⚔ 行动 · 制作 · 收集</b>
    <span style="display:flex;gap:6px"><button class="btn small" id="fabSettle">📊 结算</button><button class="btn small" id="fabClose">✕</button></span></div>""",
    '抽屉加结算按钮')

# 桌面端行动面板里也放一个结算按钮
sub("""  const endBtn = document.createElement('button');
  endBtn.className = 'btn small';
  endBtn.textContent = '⏭ 结束回合';""",
    """  const settleBtn = document.createElement('button');
  settleBtn.className = 'btn small';
  settleBtn.textContent = '📊 结算';
  settleBtn.title = '按当前局面立刻结算本局';
  settleBtn.onclick = ()=>{ try{ sfx.click(); }catch(e){} manualSettle(); };

  const endBtn = document.createElement('button');
  endBtn.className = 'btn small';
  endBtn.textContent = '⏭ 结束回合';""",
    '面板加结算按钮')

sub("""on('fabClose', ()=>{ try{ sfx.click(); }catch(e){} fabToggle(false); });""",
    """on('fabClose', ()=>{ try{ sfx.click(); }catch(e){} fabToggle(false); });
on('fabSettle', ()=>{ try{ sfx.click(); }catch(e){} manualSettle(); });""",
    '结算按钮事件')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch195 完成: %d -> %d bytes' % (n0, len(s)))
