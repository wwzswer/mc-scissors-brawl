# -*- coding: utf-8 -*-
"""补丁 3：界面交互逻辑
   - 界面切换（主菜单 / 开始 / 设置 / 规则 / 联机 / 游戏）
   - 设置项绑定与本地保存；名称修改与保存
   - 规则页分类渲染（物品 / 附魔 / 特殊道具 / 机制 / 键位说明）
   - startGame 读取设置；endGame 支持 2v2
可重复执行（先删旧标记块再插）。
"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
html = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global html
    if old not in html:
        notes.append(f'  ! 未找到 {label}')
        return
    html2 = html.replace(old, new, 1)
    assert html2 != html, label
    html = html2
    notes.append(f'  ok {label}')

# ---------- 1) startGame 开头：读取设置 ----------
sub("""async function startGame(){
  document.getElementById('setup').classList.add('hidden');
  document.getElementById('game').classList.remove('hidden');""",
"""async function startGame(){
  loadSettings();
  showScreen('game');""",
'startGame 读取设置')

# ---------- 2) endGame：2v2 判定 ----------
sub("""function checkGameEnd(){
  const me = human();
  const enemies = G.players.filter(p=>p.isEnemy);
  if(!me.alive){ endGame(false); return true; }
  if(enemies.length && enemies.every(e=>!e.alive)){ endGame(true); return true; }
  return false;
}""",
"""function checkGameEnd(){
  const me = human();
  if(!me.alive && !G.players.some(q=>q.alive && q.team===me.team)){ endGame(false); return true; }
  const foes = G.players.filter(p=>p.isEnemy);
  if(foes.length && foes.every(e=>!e.alive)){ endGame(true); return true; }
  /* 队友全灭且自己阵亡也判负 */
  if(!me.alive){ endGame(false); return true; }
  return false;
}""",
'checkGameEnd 支持 2v2')

# ---------- 3) 替换初始化绑定区 ----------
start = html.index('function markActive(sel, attr, val){')
end = html.index('/* 自动化测试入口', start)
new_block = r"""/* =========================================================================
   界面：主菜单 / 设置 / 规则 / 联机 / 游戏
   ========================================================================= */
const SCREENS = ['screen-main','screen-start','screen-setting','screen-rules','screen-net','game'];
let currentScreen = 'screen-main';
const SETUP_CARD = { 'screen-main':1, 'screen-start':1, 'screen-setting':1, 'screen-rules':1, 'screen-net':1 };
function showScreen(id){
  currentScreen = id;
  for(const s of SCREENS){
    const el = document.getElementById(s);
    if(el) el.classList.toggle('hidden', s!==id);
  }
  /* 主菜单类的卡片外层是 #setup 容器，游戏界面单独一个容器 */
  const setupWrap = document.getElementById('setupWrap');
  const gameWrap  = document.getElementById('game');
  if(gameWrap) gameWrap.classList.toggle('hidden', id!=='game');
  if(id==='game' && setupWrap) setupWrap.classList.add('hidden');
  if(id!=='game' && setupWrap) setupWrap.classList.remove('hidden');
  if(id==='screen-start') refreshStartInfo();
}
function markActive(sel, attr, val){
  document.querySelectorAll(sel).forEach(b=>b.classList.toggle('pri', b.getAttribute(attr)===String(val)));
}
/* ---- 设置持久化 ---- */
function saveSettings(){
  try{
    localStorage.setItem('mcSettings', JSON.stringify({
      playerName, gameMode, enemyCount, diffKey, autoMode, apPerWin
    }));
  }catch(e){}
}
function loadSettings(){
  try{
    const v = JSON.parse(localStorage.getItem('mcSettings')||'{}');
    if(typeof v.playerName==='string' && v.playerName.trim()) playerName = v.playerName.trim();
    if(v.gameMode==='1v1'||v.gameMode==='2v2') gameMode = v.gameMode;
    if([1,2,3].includes(v.enemyCount)) enemyCount = v.enemyCount;
    if(v.diffKey && DIFFS[v.diffKey]) diffKey = v.diffKey;
    if(typeof v.autoMode==='boolean') autoMode = v.autoMode;
    if(v.apPerWin===1||v.apPerWin===2) apPerWin = v.apPerWin;
  }catch(e){}
  syncSettingUI();
}
function syncSettingUI(){
  markActive('[data-mode]','data-mode',gameMode);
  markActive('[data-en]','data-en',enemyCount);
  markActive('[data-diff]','data-diff',diffKey);
  markActive('[data-auto]','data-auto',autoMode?1:0);
  markActive('[data-ap]','data-ap',apPerWin);
  const er = document.getElementById('enemyRow');
  if(er) er.style.opacity = (gameMode==='2v2') ? .38 : 1;
  const ni = document.getElementById('nameInput');
  if(ni) ni.value = playerName;
  const ns = document.getElementById('nameSprite');
  if(ns) ns.innerHTML = sprTag('fist', 34) + ' ' + sprTag('coin', 30);
  refreshStartInfo();
}
function refreshStartInfo(){
  const set = (id, txt)=>{ const e=document.getElementById(id); if(e) e.textContent = txt; };
  const modeTxt = gameMode==='2v2' ? '2V2（你 + AI 队友 vs 2 名敌人）' : `1v1（你 vs ${enemyCount} 名 AI）`;
  set('sModeText', modeTxt);
  set('sDiffText', DIFFS[diffKey].label);
  set('sAutoText', autoMode ? '自动出拳' : '自己点');
  set('sApText', `${apPerWin} AP / 次（判定不产生 AP）`);
  const cs = document.getElementById('curSetting');
  if(cs) cs.innerHTML = `<div>名称：<b>${esc(playerName)}</b></div>
    <div>模式：<b>${modeTxt}</b></div>
    <div>强度：<b>${DIFFS[diffKey].label}</b></div>
    <div>猜拳：<b>${autoMode?'自动':'手动'}</b>　获胜 <b>${apPerWin} AP</b></div>
    <div>生命：<b>4</b>　距离上限：<b>${MAX_DIST}</b></div>`;
}
const esc = s => String(s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

/* ---- 规则页 ---- */
const RULE_PAGES = [
  {key:'basic', title:'基础玩法'},
  {key:'items', title:'武器与工具'},
  {key:'armor', title:'防具与装备'},
  {key:'ench',  title:'附魔'},
  {key:'special', title:'特殊道具与建筑'},
  {key:'mech',  title:'环境与判定'},
];
let rulePage = 'basic';
function itemRow(k){
  const it = ITEMS[k];
  const ic = itemIcon(k);
  return `<div class="rulecard">
    <h4>${ic?sprTag(ic,26):''}${esc(it.name)}<span class="pill">${it.cost} 步</span>${it.armor?`<span class="pill">护甲 ${it.armor}</span>`:''}</h4>
    <div class="kv">${it.desc}</div></div>`;
}
function renderRules(){
  const tabs = document.getElementById('ruleTabs');
  const body = document.getElementById('ruleBody');
  if(!tabs || !body) return;
  tabs.innerHTML = RULE_PAGES.map(p=>`<div class="tab${p.key===rulePage?' on':''}" data-rule="${p.key}">${p.title}</div>`).join('');
  tabs.querySelectorAll('[data-rule]').forEach(t=>t.onclick=()=>{ rulePage=t.getAttribute('data-rule'); renderRules(); });
  let h = '';
  if(rulePage==='basic'){
    h = `<div class="rulecard"><h4>${sprTag('rock',26)}${sprTag('scissors',26)}${sprTag('paper',26)} 一回合的流程</h4>
      <div class="kv">
      ① <b>猜拳阶段</b>：你与每个对手各猜一次拳，胜者 <b>+${apPerWin} AP</b>（可在设置里改成 1 AP），平局双方无收益。<br>
      ② <b>行动阶段</b>：每回合每人有 <b>1 次免费行动</b>；之后每 <b>1 AP</b> 可以再买一次行动。制作物品与投入进程进度都只花 AP、不占行动次数。<br>
      ③ <b>回合结束</b>：所有玩家行动结束后统一结算持续伤害（火焰 / 流血），并把进程进度存盘。<br>
      ④ 生命 4 点；敌人全灭即获胜，你或队友全灭即失败。</div></div>
      <div class="rulecard"><h4>${sprTag('prog_wood',26)} 进程与进度点</h4>
      <div class="kv">
      进程树：空手 → 木(${UPGRADE[1].cost}点) → 石(${UPGRADE[2].cost}点) → 铁(${UPGRADE[3].cost}点) → 钻石(${UPGRADE[4].cost}点)。<br>
      你<b>每投入 1 步进度就点亮 1 个小点</b>，集满该级所需的点自动升级；<b>进度在每回合结束时保存</b>（存在本机，换回同名玩家可继续）。<br>
      例：空手 → 木需要 2 点，投入 1 次只点亮 1 个点，再投入 1 次才会升级。多余的点会结转到下一级。</div></div>
      <div class="rulecard"><h4>${sprTag('arrow',26)} 距离与走位</h4>
      <div class="kv">
      玩家两两之间的距离互相独立，<b>初始均为 1 格，上限 ${MAX_DIST} 格</b>。<br>
      · <b>走位 1 格 = 1 步</b>：近战武器必须 <b>0 格</b>才能攻击，所以空手/剑类要先靠近。<br>
      · 末影珍珠：获得后永不消耗，每次使与某人的距离 ±2 格（免费）。<br>
      · 钓鱼竿：2 步，使某人与你的距离 ±1 格（6 格内）。<br>
      · 盾被击碎时，攻击者与你距离 +1。<br>
      注意：A 与 B 距离 0、A 与 C 距离 0 时，B 与 C 的距离可以是 0~${MAX_DIST} 的任意值——三者互不影响。</div></div>`;
  } else if(rulePage==='items'){
    const keys = ['fist','flesh','bread','wood_sword','stone_sword','fishing_rod','ender_pearl','trident','iron_sword','flint','crossbow','diamond_sword','firework','tnt'];
    h = '<div class="rulegrid">' + keys.filter(k=>ITEMS[k]).map(itemRow).join('') + '</div>';
  } else if(rulePage==='armor'){
    const keys = ['leather','shield','iron_armor','golem','diamond_armor','anvil'];
    h = '<div class="rulegrid">' + keys.filter(k=>ITEMS[k]).map(itemRow).join('') + '</div>'
      + `<div class="rulecard" style="margin-top:10px"><h4>${sprTag('anvil',26)} 护甲修复</h4>
      <div class="kv">护甲按“次数”抵消物理伤害：皮革甲 1 次、铁甲/铁傀儡 2 次、钻石甲 3 次。<br>
      耐久用尽后护甲留在身上但失效，<b>需要铁砧才能修复</b>（每次 2 步，恢复满耐久；破损时附魔会失效，修复后需重新附魔）。</div></div>`;
  } else if(rulePage==='ench'){
    h = '<div class="rulegrid">' + ENCH_ORDER.map(k=>{
      const e = ENCH[k];
      const can = e.apply.map(a=>({weapon:'武器',armor:'护甲',trident:'三叉戟'}[a]||a)).join(' / ');
      return `<div class="rulecard"><h4>${sprTag('star',24)}${esc(e.name)}<span class="pill">${can}</span></h4>
        <div class="kv">${esc(e.desc)}</div></div>`;
    }).join('') + '</div>'
    + `<div class="rulecard" style="margin-top:10px"><h4>${sprTag('village',26)} 怎么获得附魔</h4>
      <div class="kv">空手/木进程建造【村庄】（免费，全局 1 座）获得 1 本附魔书；再建造【铁砧】，即可花 1 步把附魔书附到当前武器或护甲上。</div></div>`;
  } else if(rulePage==='special'){
    const keys = ['village','mansion','witchhut','pyramid'];
    h = '<div class="rulegrid">' + keys.filter(k=>ITEMS[k]).map(itemRow).join('')
      + Object.keys(SPECIALS).map(k=>{
          const ic = {tnt:'tnt', god_apple:'god_apple', totem:'totem', potion_heal:'potion_heal', potion_str:'potion_str', potion_swift:'potion_swift'}[k];
          return `<div class="rulecard"><h4>${ic?sprTag(ic,26):''}${esc(SPECIALS[k].name)}</h4><div class="kv">${esc(SPECIALS[k].desc)}</div></div>`;
        }).join('') + '</div>';
  } else {
    h = `<div class="rulegrid">
      <div class="rulecard"><h4>${sprTag('paper',26)} 战斗判定</h4><div class="kv">
      攻击时双方再猜一次拳，<b>攻方胜出才造成伤害</b>，失败则攻击失效。判定不产生 AP。<br>
      多人对战中若判定双方同时胜出，被攻击方可以 <b>消耗 1 AP 直接闪避</b>（没有 AP 就只能挨打）。</div></div>
      <div class="rulecard"><h4>${sprTag('heart',26)} 伤害类型</h4><div class="kv">
      <b>物理 / 火焰 / 法术 / 穿甲</b> 四种。护甲只抵消物理伤害；法术、火焰、穿甲无视护甲。附魔【防穿】可让穿甲伤害失效，【防火】【防爆】【防毒】分别免疫对应伤害。</div></div>
      <div class="rulecard"><h4>${sprTag('flint',26)} 持续伤害</h4><div class="kv">
      火焰与流血在<b>命中时立即结算一次</b>，其余回合在<b>所有玩家行动结束后</b>统一结算。<br>
      例：A 用打火石点燃 B，B 立即扣 0.5；第二回合所有玩家行动结束后才结算第二次 0.5。若 B 在这之前花 1 步跳入水中，则不会受到第二次伤害。</div></div>
      <div class="rulecard"><h4>${sprTag('water',26)} 水</h4><div class="kv">
      花 1 步主动入水，立即清除身上所有火焰/流血，且与其它玩家的距离和所在建筑无关。<br>
      0 格时可以互相把对方拖入/拖出水；持钓鱼竿可在 6 格内把别人钓入/钓出水。</div></div>
      <div class="rulecard"><h4>${sprTag('tnt',26)} TNT 与铁傀儡被动</h4><div class="kv">
      TNT：① 黏在目标头上（1 步，需 0 格）② 引爆（1 步）。中心 2.5（有甲 1.5），其余 1.5（有甲 1）；<b>有友伤，也会炸到自己</b>。<br>
      铁傀儡：护甲 2 次之外，全场玩家都行动过一次后再次轮到你时，可对 2 格内任意玩家发动一次 1.5 物理攻击（需判定）。</div></div>
      <div class="rulecard"><h4>${sprTag('coin',26)} 联机怎么玩</h4><div class="kv">
      主机运行 <code>start-server.cmd</code>，其他人用浏览器打开提示的局域网地址；房主创建房间得到 <b>9 位房间码</b>，其他人输入房间码加入，都准备好后开始。</div></div>
      </div>`;
  }
  body.innerHTML = h;
}

/* ---- 事件绑定 ---- */
const on = (id, fn)=>{ const e=document.getElementById(id); if(e) e.onclick=fn; };
on('mStart', ()=>{ sfx.click(); showScreen('screen-start'); });
on('mSetting', ()=>{ sfx.click(); showScreen('screen-setting'); });
on('mRules', ()=>{ sfx.click(); renderRules(); showScreen('screen-rules'); });
on('mNet', ()=>{ sfx.click(); showScreen('screen-net'); netRefresh(); });
on('sBack', ()=>{ sfx.click(); showScreen('screen-main'); });
on('sToSetting', ()=>{ sfx.click(); showScreen('screen-setting'); });
on('setBack', ()=>{ sfx.click(); saveSettings(); showScreen('screen-main'); });
on('rulesBack', ()=>{ sfx.click(); showScreen('screen-main'); });
on('netBack', ()=>{ sfx.click(); showScreen('screen-main'); });
on('nameSave', ()=>{
  const v = (document.getElementById('nameInput').value||'').trim().slice(0,10) || '你';
  playerName = v; saveSettings();
  const tip=document.getElementById('nameTip'); if(tip){ tip.textContent='已保存'; setTimeout(()=>tip.textContent='',1500); }
  refreshStartInfo(); sfx.win();
});
on('startBtn', ()=>{ try{ sfx.win(); }catch(e){} saveSettings(); startGame(); });

document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{ gameMode=b.dataset.mode; syncSettingUI(); saveSettings(); sfx.click(); });
document.querySelectorAll('[data-en]').forEach(b=>b.onclick=()=>{ enemyCount=+b.dataset.en; syncSettingUI(); saveSettings(); sfx.click(); });
document.querySelectorAll('[data-diff]').forEach(b=>b.onclick=()=>{ diffKey=b.dataset.diff; syncSettingUI(); saveSettings(); sfx.click(); });
document.querySelectorAll('[data-auto]').forEach(b=>b.onclick=()=>{ autoMode=b.dataset.auto==='1'; syncSettingUI(); saveSettings(); sfx.click(); });
document.querySelectorAll('[data-ap]').forEach(b=>b.onclick=()=>{ apPerWin=+b.dataset.ap; syncSettingUI(); saveSettings(); sfx.click(); });
document.querySelectorAll('#rpsBtns .btn').forEach(b=>{
  b.onclick=()=>{ if(rpsResolver){ const r=rpsResolver; rpsResolver=null; rpsPick=b.dataset.mv; sfx.rps(); r(b.dataset.mv); } };
});
const autoToggle=document.getElementById('autoToggle');
if(autoToggle) autoToggle.onclick=()=>{ autoMode=!autoMode; autoToggle.textContent=autoMode?'手动模式':'自动模式'; saveSettings(); sfx.click(); };

/* 顶部信息条刷新（模式 / 本回合 AP / 猜拳进度） */
function refreshTopBar(){
  const mp=document.getElementById('modePill');
  if(mp && G) mp.textContent = gameMode==='2v2' ? '2V2 模式' : '1v1 模式';
  const ap=document.getElementById('apPill');
  if(ap) ap.textContent = `猜拳获胜 +${apPerWin} AP`;
}

/* ---- 联机（阶段一：本机存根，server.js 提供房间服务后接管） ---- */
let netRoom = null;
function netRefresh(){
  const st = document.getElementById('netStatus');
  if(!st) return;
  if(!window.WebSocket || location.protocol==='file:'){
    st.innerHTML = '当前是用 <code>file://</code> 直接打开页面，浏览器不允许联机。<br>请用主机上的 <code>start-server.cmd</code> 启动后，通过 <code>http://局域网IP:8787</code> 打开本页。';
    return;
  }
  st.textContent = netRoom ? `已加入房间 ${netRoom}` : '未连接。可创建房间或输入房间码加入。';
}
on('netCreate', ()=>{ netCreateRoom(); });
on('netJoin', ()=>{ netJoinRoom(); });

loadSettings();
showScreen('screen-main');

"""
html = html[:start] + new_block + html[end:]
IDX.write_text(html, encoding='utf-8')
print('\n'.join(notes))
print(f'交互逻辑写入完成，文件 {len(html)/1024:.1f} KB')
