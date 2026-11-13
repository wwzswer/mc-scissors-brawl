# -*- coding: utf-8 -*-
"""补丁 5：界面收尾
   - showScreen 适配新的 DOM 结构（去掉已不存在的 #setup 容器）
   - 补 .desc 等样式
   - 玩家面板加贴图（进程图标 / 装备图标 / 背包图标 / 进度小点 / 队伍标签 / 距离芯片）
   - 顶部信息条刷新接入 renderAll
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
html = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global html
    if old not in html:
        notes.append(f'  ! 未找到 {label}'); return
    html = html.replace(old, new, 1); notes.append(f'  ok {label}')

# ---------- 1) showScreen 修正 ----------
sub("""  /* 主菜单类的卡片外层是 #setup 容器，游戏界面单独一个容器 */
  const setupWrap = document.getElementById('setupWrap');
  const gameWrap  = document.getElementById('game');
  if(gameWrap) gameWrap.classList.toggle('hidden', id!=='game');
  if(id==='game' && setupWrap) setupWrap.classList.add('hidden');
  if(id!=='game' && setupWrap) setupWrap.classList.remove('hidden');
  if(id==='screen-start') refreshStartInfo();""",
"""  const gameWrap = document.getElementById('game');
  if(gameWrap) gameWrap.classList.toggle('hidden', id!=='game');
  if(id==='screen-start') refreshStartInfo();
  if(id==='screen-rules') renderRules();
  if(id==='screen-net') netRefresh();""",
'showScreen 结构')

# ---------- 2) 补样式 ----------
extra = """
.desc{font-size:12px;color:var(--dim);line-height:1.6}
.distchip .dir{color:var(--acc);font-size:11px;margin-left:4px}
.pcard .spr{margin-right:2px}
.progline{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:7px}
"""
if '.progline{' not in html:
    html = html.replace('.hidden{display:none !important}', '.hidden{display:none !important}' + extra, 1)
    notes.append('  ok 追加样式')

# ---------- 3) 玩家面板：贴图 + 进度小点 + 队伍 + 距离芯片 ----------
old_card = """    const inv = Object.keys(p.items).map(k=>`${ITEMS[k]?ITEMS[k].name:(SPECIALS[k]?SPECIALS[k].name:k)}×${p.items[k]}`).join('、')||'—';
    const bld = Object.keys(p.buildings).map(k=>ITEMS[k]?ITEMS[k].name:k).join('、')||'—';"""
new_card = """    const inv = Object.keys(p.items).map(k=>{
      const nm = ITEMS[k]?ITEMS[k].name:(SPECIALS[k]?SPECIALS[k].name:k);
      const ic = itemIcon(k);
      return (ic?sprTag(ic,20):'')+nm+'×'+p.items[k];
    }).join('　')||'—';
    const bld = Object.keys(p.buildings).map(k=>{
      const ic = itemIcon(k);
      return (ic?sprTag(ic,20):'')+(ITEMS[k]?ITEMS[k].name:k);
    }).join('　')||'—';"""
sub(old_card, new_card, '背包/建筑贴图')

old_stat = """      <div class="stat">
        <span class="k">生命 / 护甲</span><span class="v">${hpStr(p)}</span>
        <span class="k">行动点</span><span class="v">${p.ap}</span>
        <span class="k">进程</span><span class="v">${PROG_NAME[p.prog]}</span>
        <span class="k">装备</span><span class="v">${gearLabel(p)}</span>
        <span class="k">背包</span><span class="v">${inv}</span>
        <span class="k">建筑</span><span class="v">${bld}</span>
        <span class="k">距离</span><span class="v">${others}</span>
      </div>"""
new_stat = """      <div class="stat">
        <span class="k">生命 / 护甲</span><span class="v">${hpStr(p)}</span>
        <span class="k">行动点</span><span class="v">${sprTag('coin',18)} ${p.ap}</span>
        <span class="k">进程</span><span class="v">${sprTag(PROG_ICON[p.prog],22)} ${PROG_NAME[p.prog]}</span>
        <span class="k">装备</span><span class="v">${gearIcons(p)}</span>
        <span class="k">背包</span><span class="v">${inv}</span>
        <span class="k">建筑</span><span class="v">${bld}</span>
      </div>
      <div class="progline">${progPointsHtml(p)}</div>
      <div class="distrow">${distChips(p)}</div>"""
sub(old_stat, new_stat, '面板统计行')

sub("""    const others = G.players.filter(q=>q!==p&&q.alive).map(q=>`${q.name} ${distanceBetween(p,q)}格`).join(' · ')||'—';""",
"""    const others = G.players.filter(q=>q!==p&&q.alive).map(q=>`${q.name} ${distanceBetween(p,q)}格`).join(' · ')||'—';""",
'（保留）')

# 队伍标签
sub("""        <span class="tag ${p.isHuman?'you':'ai'}">${p.isHuman?'玩家':'AI · '+DIFFS[diffKey].label}</span>""",
"""        <span class="tag ${p.isHuman?'you':'ai'}">${p.isHuman?'玩家':(p.isEnemy?'AI 敌人':'AI 队友')}</span>
        ${p.isHuman?'<span class="teamtag">你的队伍</span>':(p.isEnemy?'<span class="teamtag foe">敌方</span>':'<span class="teamtag">你的队伍</span>')}""",
'队伍标签')

# 辅助函数：装备图标 / 距离芯片
sub("""function renderPlayers(){""",
"""function gearIcons(p){
  const out = [];
  if(p.weapon && ITEMS[p.weapon]) out.push(sprTag(itemIcon(p.weapon)||'fist', 22) + ' ' + ITEMS[p.weapon].name);
  else out.push(sprTag('fist', 22) + ' 空手');
  if(p.armor){
    const nm = ITEMS[p.armor].name + (armorActive(p) ? `(${p.armorCharges})` : '(已破损)');
    out.push(sprTag(itemIcon(p.armor), 22) + ' ' + nm);
  } else out.push('无护甲');
  return out.join('　');
}
function distChips(p){
  const list = G.players.filter(q=>q!==p && q.alive);
  if(!list.length) return '';
  return list.map(q=>`<span class="distchip">${q.team===p.team?'🤝':'⚔'} ${esc(q.name)} <b>${distanceBetween(p,q)}</b> 格</span>`).join('');
}
function renderPlayers(){""",
'装备图标/距离芯片函数')

# ---------- 4) renderAll 刷新顶部信息 ----------
sub("""function renderAll(){
  if(!G) return;
  renderPlayers();""",
"""function renderAll(){
  if(!G) return;
  renderPlayers();
  refreshTopBar();""",
'renderAll 刷新顶栏')

# ---------- 5) endOfRound 后自动存档进度（已加），另外回合开始时也存一次 ----------
sub("""    log(`──────── <b>第 ${G.round} 回合</b> ────────`,'l-sys');""",
"""    for(const q of G.players) if(q.alive) progSave(q);
    log(`──────── <b>第 ${G.round} 回合</b> ────────`,'l-sys');""",
'回合开始存档')

IDX.write_text(html, encoding='utf-8')
print('\n'.join(notes))
print(f'补丁 5 完成，文件 {len(html)/1024:.1f} KB')
