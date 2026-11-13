# -*- coding: utf-8 -*-
"""第 1 步改造：数据层 + 引擎层
   - 进程升级改为「进度点」制（每回合结束存储进度）
   - 猜拳获胜 AP 可设 1 或 2
   - 距离上限 7
   - 2v2 模式（含 AI 队友）
可重复执行（幂等）。
"""
import pathlib, re, sys

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
html = IDX.read_text(encoding='utf-8')
orig = html
notes = []

def sub(old, new, cnt=1, label=''):
    global html
    if old not in html:
        notes.append(f'  ! 未找到: {label or old[:60]}')
        return False
    n = html.count(old)
    if n != cnt:
        notes.append(f'  ~ 出现 {n} 次(期望 {cnt}): {label or old[:60]}')
    html = html.replace(old, new)
    notes.append(f'  ok {label or old[:50]}')
    return True

# ---------- 1. 常量：进度点 / 距离上限 / AP 设置 ----------
sub(
"const UPGRADE = [ null, {cost:2}, {cost:2}, {cost:3}, {cost:3} ];  // 空手→木2 / 木→石2 / 石→铁3 / 铁→钻石3",
"""const UPGRADE = [ null, {cost:2}, {cost:2}, {cost:3}, {cost:3} ];  // 升到该进程需要的进度点：空手→木2 / 木→石2 / 石→铁3 / 铁→钻石3
const MAX_DIST = 7;            // 玩家间最大距离
let apPerWin = 2;              // 每次猜拳获胜获得的 AP（判定除外），可在设置里改成 1
let gameMode = '1v1';          // '1v1' | '2v2'""",
1, '常量 UPGRADE/MAX_DIST/apPerWin')

# ---------- 2. 距离：加上限 ----------
sub(
"""function setDistance(a,b,v){
  v=Math.max(0, Math.round(v));
  G.dist[a.id][b.id]=v; G.dist[b.id][a.id]=v;
}""",
"""function setDistance(a,b,v){
  v = Math.max(0, Math.min(MAX_DIST, Math.round(v)));
  G.dist[a.id][b.id]=v; G.dist[b.id][a.id]=v;
}""",
1, 'setDistance 加上限')

# ---------- 3. 猜拳获胜 AP 用 apPerWin ----------
sub("""  if(win) p.ap+=2; else if(!tie) target.ap+=2;
  log(`✊ ${lname(p)} vs ${lname(target)}：${RPS_NAME[my]} vs ${RPS_NAME[opp]} → ${tie?'平局（无 AP）':(win?'<b>你胜出，+2 AP</b>':`${lname(target)} 胜出，+2 AP`)}`,'l-rps');""",
"""  if(win) p.ap+=apPerWin; else if(!tie) target.ap+=apPerWin;
  log(`✊ ${lname(p)} vs ${lname(target)}：${RPS_NAME[my]} vs ${RPS_NAME[opp]} → ${tie?'平局（无 AP）':(win?`<b>你胜出，+${apPerWin} AP</b>`:`${lname(target)} 胜出，+${apPerWin} AP`)}`,'l-rps');""",
1, 'humanRps 用 apPerWin')

sub("""  if(win) p.ap+=2; else if(!tie) target.ap+=2;
  log(`✊ ${lname(p)} vs ${lname(target)}：${RPS_NAME[my]} vs ${RPS_NAME[opp]} → ${tie?'平局（无 AP）':(win?`${lname(p)} 胜，+2 AP`:`${lname(target)} 胜，+2 AP`)}`,'l-rps');""",
"""  if(win) p.ap+=apPerWin; else if(!tie) target.ap+=apPerWin;
  log(`✊ ${lname(p)} vs ${lname(target)}：${RPS_NAME[my]} vs ${RPS_NAME[opp]} → ${tie?'平局（无 AP）':(win?`${lname(p)} 胜，+${apPerWin} AP`:`${lname(target)} 胜，+${apPerWin} AP`)}`,'l-rps');""",
1, 'aiRps 用 apPerWin')

# ---------- 4. 玩家对象：进度点 / 名称可改 ----------
sub("""    prog:PROG.HAND, items:{}, weapon:null, armor:null, armorCharges:0, ench:{},
    inWater:false, effects:[], buildings:{}, mem:{}, flags:{},
    lastRps:null, rpsTally:{rock:0,scissors:0,paper:0}, kills:0, actionsUsed:0, slotsLeft:1, turnSpent:0 };""",
"""    prog:PROG.HAND, progPts:0, items:{}, weapon:null, armor:null, armorCharges:0, ench:{},
    inWater:false, effects:[], buildings:{}, mem:{}, flags:{},
    lastRps:null, rpsTally:{rock:0,scissors:0,paper:0}, kills:0, actionsUsed:0, slotsLeft:1, turnSpent:0 };""",
1, '玩家对象加 progPts')

# ---------- 5. 进度点核心函数（插在 setDistance 之前） ----------
sub("""/* --- 距离 --- */""",
"""/* --- 进程进度点：每次投入 1 步点亮 1 个小点，满点自动升级，进度保存到 localStorage --- */
function progNeed(p){ const u = UPGRADE[p.prog+1]; return u ? u.cost : 0; }
function progProgress(p){ return p.progPts || 0; }
function progMaxed(p){ return !UPGRADE[p.prog+1]; }
function progSave(p){
  try{
    const all = JSON.parse(localStorage.getItem('mcProg') || '{}');
    all[p.name] = {prog:p.prog, pts:p.progPts||0};
    localStorage.setItem('mcProg', JSON.stringify(all));
  }catch(e){}
}
function progLoad(name){
  try{
    const all = JSON.parse(localStorage.getItem('mcProg') || '{}');
    const v = all[name];
    if(v && typeof v.prog==='number') return {prog:Math.max(0,Math.min(4,v.prog)), pts:Math.max(0,v.pts|0)};
  }catch(e){}
  return null;
}
/* 投入 1 步进度；返回是否发生了升级 */
function addProgPoint(p){
  if(progMaxed(p)) return false;
  p.progPts = (p.progPts||0) + 1;
  let leveled = false;
  while(!progMaxed(p) && p.progPts >= progNeed(p)){
    p.progPts -= progNeed(p);
    p.prog += 1;
    leveled = true;
    log(`⬆️ ${lname(p)} 的进程推进到 <b>${PROG_NAME[p.prog]}</b>！`,'l-good');
    if(p.prog===PROG.STONE) log('（石进程：钓鱼竿是三叉戟的前置；末影珍珠获得后不会消耗）','l-sys');
    if(p.prog===PROG.IRON) log('（铁进程：铁砧可修复护甲；沙漠金字塔可获取 TNT 与附魔金苹果）','l-sys');
  }
  progSave(p);                                   /* 每投入即存储，绝不丢进度 */
  renderAll();
  return leveled;
}
function progPointsHtml(p){
  if(progMaxed(p)) return '<span class="progdots"><i class="dot on"></i><b>已满级</b></span>';
  const need = progNeed(p), got = Math.min(progProgress(p), need);
  let dots = '';
  for(let i=0;i<need;i++) dots += `<i class="dot${i<got?' on':''}"></i>`;
  return `<span class="progdots">${dots}<b>${got}/${need}</b>` +
         `<span class="prognext">→ ${PROG_NAME[p.prog+1]}</span></span>`;
}

/* --- 距离 --- */""",
1, '进度点核心函数')

# ---------- 6. applyAction 的升级分支改为投入进度点 ----------
sub("""    case 'shop_progress': case 'upgrade': {
      const next=p.prog+1;
      if(!UPGRADE[next]){ log(`${lname(p)} 已是最高进程。`,'l-warn'); break; }
      if(p.ap<UPGRADE[next].cost){ log(`${lname(p)} 行动点不足，无法升级（需要 ${UPGRADE[next].cost}，现有 ${p.ap}）。`,'l-warn'); break; }
      itemCost = UPGRADE[next].cost;
      p.prog=next;
      log(`⬆️ ${lname(p)} 升级进程 → <b>${PROG_NAME[next]}</b>（-${itemCost} AP）`,'l-good');
      if(next===PROG.STONE) log('（石进程：钓鱼竿是三叉戟的前置；末影珍珠获得后不会消耗）','l-sys');
      if(next===PROG.IRON) log('（铁进程：铁砧可修复护甲；沙漠金字塔可获取 TNT 与附魔金苹果）','l-sys');
      sfx.win();
      break; }""",
"""    case 'shop_progress': case 'upgrade': {
      if(progMaxed(p)){ log(`${lname(p)} 已是最高进程。`,'l-warn'); break; }
      if(p.ap<1){ log(`${lname(p)} 行动点不足，无法投入进度。`,'l-warn'); break; }
      itemCost = 1;
      const before = p.prog;
      log(`⬆️ ${lname(p)} 投入 1 步进度（${PROG_NAME[before]} → ${PROG_NAME[before+1]}：${Math.min(progProgress(p)+1, progNeed(p))}/${progNeed(p)}）`,'l-sys');
      const leveled = addProgPoint(p);
      if(leveled){ sfx.win(); } else sfx.rps();
      break; }""",
1, 'applyAction 投入进度点')

# ---------- 7. applyShopAction 的 upgrade 同样改为投入进度点 ----------
sub("""  if(a.type==='upgrade'){
    const next=p.prog+1;
    if(!UPGRADE[next] || p.ap<UPGRADE[next].cost) return false;
    p.ap-=UPGRADE[next].cost; p.prog=next;
    log(`⬆️ ${lname(p)} 升级进程 → <b>${PROG_NAME[next]}</b>（-${UPGRADE[next].cost} AP，剩余 ${p.ap}）`,'l-good');
    sfx.win(); renderAll(); return true;
  }""",
"""  if(a.type==='upgrade'){
    if(progMaxed(p) || p.ap<1) return false;
    p.ap -= 1;
    const before = p.prog;
    log(`⬆️ ${lname(p)} 投入 1 步进度（${PROG_NAME[before]} → ${PROG_NAME[before+1]}：${Math.min(progProgress(p)+1, progNeed(p))}/${progNeed(p)}）`,'l-sys');
    const leveled = addProgPoint(p);
    leveled ? sfx.win() : sfx.rps();
    renderAll(); return true;
  }""",
1, 'applyShopAction 投入进度点')

# ---------- 8. 回合结束时存储进度 ----------
sub("""async function endOfRound(opts){
  const o = opts||{};
  log(`── 所有玩家行动结束：结算持续伤害 ──`,'l-sys');""",
"""async function endOfRound(opts){
  const o = opts||{};
  log(`── 所有玩家行动结束：结算持续伤害 ──`,'l-sys');
  for(const q of G.players) if(q.alive) progSave(q);      /* 回合结束：把进程进度存盘 */""",
1, 'endOfRound 存储进度')

# ---------- 9. startGame：模式 / 2v2 / 名称 / 初始距离 1 ----------
sub("""  const players=[];
  players.push(makePlayer('你', true, 0, false, 0));
  const names = AI_NAMES.slice();
  for(let i=0;i<enemyCount;i++){
    const nm = names.splice(rnd(names.length),1)[0];
    players.push(makePlayer(nm, false, 1, true, i+1));
  }
  G = { players, round:1, dist:{}, roundOrder:[], over:false, turnOwner:null };
  players.forEach(a=>{ G.dist[a.id]={}; players.forEach(b=>{ G.dist[a.id][b.id] = a===b?0:1; }); });

  log(`🎮 <b>对战开始！</b>你 vs ${enemyCount} 名 AI（强度：${DIFFS[diffKey].label}）。每人 4 点生命，每次猜拳获胜 +2 AP。`,'l-sys');""",
"""  const players=[];
  const myName = (playerName||'你').trim() || '你';
  players.push(makePlayer(myName, true, 0, false, 0));
  const names = AI_NAMES.slice().filter(n=>n!==myName);
  const is2v2 = (gameMode==='2v2');
  const allyCount = is2v2 ? 1 : 0;
  const foeCount  = is2v2 ? 2 : enemyCount;
  for(let i=0;i<allyCount;i++){
    const nm = names.splice(rnd(names.length),1)[0];
    players.push(makePlayer(nm+'（队友）', false, 0, false, players.length));
  }
  for(let i=0;i<foeCount;i++){
    const nm = names.splice(rnd(names.length),1)[0];
    players.push(makePlayer(nm, false, 1, true, players.length));
  }
  G = { players, round:1, dist:{}, roundOrder:[], over:false, turnOwner:null, progSnap:{} };
  players.forEach(a=>{ G.dist[a.id]={}; players.forEach(b=>{ G.dist[a.id][b.id] = a===b?0:1; }); });
  /* 载入该名称上次保存的进程进度 */
  for(const p of players){
    const saved = progLoad(p.name);
    if(saved){ p.prog=saved.prog; p.progPts=saved.pts; }
  }

  log(`🎮 <b>对战开始！</b>${is2v2?'2V2（你 + AI 队友 vs 2 名敌人）':'你 vs '+foeCount+' 名 AI'}，强度：${DIFFS[diffKey].label}。每人 4 点生命，每次猜拳获胜 +${apPerWin} AP。`,'l-sys');""",
1, 'startGame 模式与名称')

sub("""  log(`进程：空手 → 木(2步) → 石(2步) → 铁(<b>3步</b>) → 钻石(3步)。石进程解锁钓鱼竿（三叉戟的前置）。`,'l-sys');""",
"""  log(`进程（进度点制）：空手 → 木(${UPGRADE[1].cost}点) → 石(${UPGRADE[2].cost}点) → 铁(<b>${UPGRADE[3].cost}点</b>) → 钻石(${UPGRADE[4].cost}点)；每投入 1 步点亮 1 个小点，进度会保存。`,'l-sys');""",
1, 'startGame 日志说明')

# ---------- 10. AI 商店决策：升级改为投入 1 点 ----------
sub("""  /* 升级进程 */
  const up=UPGRADE[p.prog+1];
  if(up && p.ap>=up.cost){
    let s=62+(p.prog+1)*6;
    if(p.hp<=2) s-=16;
    cands.push({s, o:{type:'upgrade',cost:up.cost,isAction:false,label:'升级进程'}});
  }""",
"""  /* 投入 1 步进程进度 */
  if(!progMaxed(p) && p.ap>=1){
    let s=62+(p.prog+1)*6;
    if(p.hp<=2) s-=16;
    if(progProgress(p)+1>=progNeed(p)) s+=26;      /* 差一点就升级时更值得投 */
    cands.push({s, o:{type:'upgrade',cost:1,isAction:false,label:'投入进程进度'}});
  }""",
1, 'aiShopChoice 进度点')

# ---------- 11. 人类选项：升级入口改为「投入进度」 ----------
sub("""    const up = UPGRADE[p.prog+1];
    push({type:'shop_progress', cost: up?up.cost:0, isAction:false, label: up?`⬆️ 升级 → ${PROG_NAME[p.prog+1]}（${up.cost} 步）`:'⬆️ 已满级'});""",
"""    const up = UPGRADE[p.prog+1];
    push({type:'shop_progress', cost:1, isAction:false,
      label: up ? `⬆️ 投入 1 步进度（${PROG_NAME[p.prog]} → ${PROG_NAME[p.prog+1]}：${Math.min(progProgress(p)+1,progNeed(p))}/${progNeed(p)}）`
                : '⬆️ 已满级'});""",
1, 'buildHumanOptions 进度入口')

sub("""    const up=UPGRADE[p.prog+1];
    if(up) push({type:'shop_progress',cost:up.cost,isAction:false,label:'升级进程'});""",
"""    if(!progMaxed(p)) push({type:'shop_progress',cost:1,isAction:false,label:'投入进程进度'});""",
1, 'aiOptions 进度入口')

# ---------- 12. canShow：投入进度只需 1 AP ----------
sub("""  if(opt.type==='shop_progress'){ const up=UPGRADE[p.prog+1]; return !!up && p.ap>=up.cost; }""",
"""  if(opt.type==='shop_progress'){ return !progMaxed(p) && p.ap>=1; }""",
1, 'canShow 进度入口')

# ---------- 13. askHuman 的升级按钮 ----------
sub("""    row3.appendChild(mkShop(up?`⬆️ 升级 → ${PROG_NAME[p.prog+1]}（${up.cost} 步）`:'已满级','progress', !up||p.ap<up.cost));""",
"""    row3.appendChild(mkShop(up?`⬆️ 投入进度 ${Math.min(progProgress(p)+1,progNeed(p))}/${progNeed(p)}`:'已满级','progress', !up||p.ap<1));""",
1, 'askHuman 升级按钮')

# ---------- 14. 商店面板的升级标签（进度式） ----------
sub("""        const d=document.createElement('div'); d.className='item'+(p.ap<cost?' dis':'');
        d.innerHTML=`<div class="it"><span>升级 → ${PROG_NAME[next]}</span><span class="cost">${cost} 步</span></div>
          <div class="desc">解锁更高级的武器 / 护甲 / 建筑。${
            next===PROG.WOOD?'（木进程：木剑、皮革甲、村庄）':
            next===PROG.STONE?'（石进程：石剑、钓鱼竿 → 三叉戟、末影珍珠、林地府邸、女巫小屋）':
            next===PROG.IRON?'（铁进程：铁剑、打火石、盾、铁甲、铁傀儡、铁砧、沙漠金字塔）':
            next===PROG.DIAMOND?'（钻石进程：弩、钻石剑、钻石甲、烟花）':''}</div>`;
        d.onclick=()=>{ if(p.ap<cost) return;
          p.ap-=cost; p.prog=next;
          log(`⬆️ ${lname(p)} 升级进程 → <b>${PROG_NAME[next]}</b>（-${cost} AP，剩余 ${p.ap}）`,'l-good');
          if(next===PROG.STONE) log('（石进程：钓鱼竿是三叉戟的前置；末影珍珠获得后不会消耗）','l-sys');
          if(next===PROG.IRON) log('（铁进程：铁砧可修复护甲；沙漠金字塔可获取 TNT 与附魔金苹果）','l-sys');
          sfx.win(); render(); renderAll();
        };
        grid.appendChild(d);""",
"""        const d=document.createElement('div'); d.className='item'+(p.ap<1?' dis':'');
        const got=Math.min(progProgress(p), cost);
        let dots=''; for(let i=0;i<cost;i++) dots+=`<i class="dot${i<got?' on':''}"></i>`;
        d.innerHTML=`<div class="it"><span>${sprTag(PROG_ICON[next],22)} 投入 1 步进度 → ${PROG_NAME[next]}</span><span class="cost">1 AP</span></div>
          <div class="progrow">${dots}<b>${got}/${cost}</b></div>
          <div class="desc">每投入 1 步点亮 1 个点，集满 ${cost} 点自动升级到 ${PROG_NAME[next]}。进度会在每回合结束时保存。${
            next===PROG.WOOD?'（木进程：木剑、皮革甲、村庄）':
            next===PROG.STONE?'（石进程：石剑、钓鱼竿 → 三叉戟、末影珍珠、林地府邸、女巫小屋）':
            next===PROG.IRON?'（铁进程：铁剑、打火石、盾、铁甲、铁傀儡、铁砧、沙漠金字塔）':
            next===PROG.DIAMOND?'（钻石进程：弩、钻石剑、钻石甲、烟花）':''}</div>`;
        d.onclick=()=>{ if(p.ap<1) return; applyShopAction(p,{type:'upgrade'}); render(); renderAll(); };
        grid.appendChild(d);""",
1, '商店面板升级项')

# ---------- 15. DIFFS 之后加 playerName ----------
sub("""const AI_NAMES = ['史蒂夫','爱丽克丝','僵尸队长','苦力怕','末影人','骷髅弓手'];""",
"""const AI_NAMES = ['史蒂夫','爱丽克丝','僵尸队长','苦力怕','末影人','骷髅弓手'];
let playerName = '你';        /* 玩家名称，可在初始界面修改 */""",
1, 'playerName 变量')

IDX.write_text(html, encoding='utf-8')
print(f'改造完成，文件 {len(html)/1024:.1f} KB（原 {len(orig)/1024:.1f} KB）')
print('\n'.join(notes))
