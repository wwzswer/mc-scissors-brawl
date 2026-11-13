# -*- coding: utf-8 -*-
"""补丁 22：按用户反馈修正
   ① 低级物品在高级进程仍可获取（修掉最后一处 it.prog!==p.prog）
   ② 所有多步物品改为「进度式」：每投入 1 步点亮 1 个点，集满才拿到；进度保存
   ③ 进程需求改为：空手 → 木进程 1 点（进程名改回 5 级，木进程恢复）
   ④ 新增：可以切换手上的工具进行攻击
"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ================= ① 修掉最后一处进程过滤 =================
sub("""  for(const k of Object.keys(ITEMS)){
      const it=ITEMS[k];
      if(it.prog!==p.prog) continue;
      if(it.build){ if(!buildAllowed(p,k)) continue; }
      else if(!it.repeat && hasItem(p,k)) continue;
      if(it.need && !hasItem(p,it.need)) continue;
      push({type:'craftShopItem',key:k,cost:it.cost,isAction:false,label:'制作 '+it.name});
    }""",
"""  for(const k of Object.keys(ITEMS)){
      const it=ITEMS[k];
      if(it.prog>p.prog) continue;                 /* 已解锁进程的物品永久可做 */
      if(it.build){ if(!buildAllowed(p,k)) continue; }
      else if(!it.repeat && hasItem(p,k)) continue;
      if(it.need && !hasItem(p,it.need)) continue;
      push({type:'craftShopItem',key:k,cost:it.cost,isAction:false,label:'制作 '+it.name});
    }""", 'aiOptions 进程过滤')

# 兼容：如果上面没匹配到，退化为直接替换
if t.count('it.prog!==p.prog') > 0:
    t = t.replace('it.prog!==p.prog', 'it.prog>p.prog')
    notes.append(f'  ok 兜底替换 it.prog!==p.prog -> >')

# 清掉商店里那段旧的三元表达式（重复 key，且文案过期）
t2 = re.sub(r"\$\{\s*\n\s*next===PROG\.STONE\?'（木进程：[^}]*?\}''", "''", t, flags=re.S)
if t2 != t:
    t = t2; notes.append('  ok 清理商店旧进程说明')

# ================= ③ 进程需求：空手 → 木 1 点 =================
sub("const PROG = { HAND:0, STONE:1, IRON:2, DIAMOND:3 };   /* 木进程已并入石进程 */",
    "const PROG = { HAND:0, WOOD:1, STONE:2, IRON:3, DIAMOND:4 };", 'PROG 枚举恢复 5 级')
sub("const PROG_NAME = ['空手','石进程','铁进程','钻石进程'];",
    "const PROG_NAME = ['空手','木进程','石进程','铁进程','钻石进程'];", 'PROG_NAME 恢复')
sub("const UPGRADE = [ null, {cost:1}, {cost:3}, {cost:3} ];  // 升到该进程需要的进度点：空手→石 1 / 石→铁 3 / 铁→钻石 3",
    "const UPGRADE = [ null, {cost:1}, {cost:2}, {cost:3}, {cost:3} ];  // 升到该进程所需进度点：空手→木 1 / 木→石 2 / 石→铁 3 / 铁→钻石 3",
    'UPGRADE 表')
sub("const PROG_REQ = [null, 1, 3, 3];", "const PROG_REQ = [null, 1, 2, 3, 3];", 'PROG_REQ')
sub("const PROG_ICON = ['fist','prog_stone','prog_iron','prog_diamond'];",
    "const PROG_ICON = ['fist','prog_wood','prog_stone','prog_iron','prog_diamond'];", 'PROG_ICON')

# 木级物品回到木进程
for key in ['wood_sword','leather','village']:
    pat = re.compile(r"(\b" + key + r":\s*\{[^}]*?)prog:PROG\.STONE", re.S)
    t, n = pat.subn(r"\1prog:PROG.WOOD", t, count=1)
    notes.append(f'  {"ok" if n else "!"} {key} -> 木进程')

# 提示文案
t = t.replace("if(p.prog===PROG.STONE) log('（石进程：木剑 / 皮革甲 / 石剑 / 钓鱼竿→三叉戟 / 末影珍珠 / 建筑）','l-sys');",
              "if(p.prog===PROG.WOOD) log('（木进程：木剑、皮革甲、村庄）','l-sys');\n    if(p.prog===PROG.STONE) log('（石进程：石剑、钓鱼竿→三叉戟、末影珍珠、林地府邸、女巫小屋）','l-sys');")
t = t.replace("if(next===PROG.STONE) log('（石进程：木剑 / 皮革甲 / 石剑 / 钓鱼竿→三叉戟 / 末影珍珠 / 建筑）','l-sys');",
              "if(next===PROG.WOOD) log('（木进程：木剑、皮革甲、村庄）','l-sys');\n      if(next===PROG.STONE) log('（石进程：石剑、钓鱼竿→三叉戟、末影珍珠、林地府邸、女巫小屋）','l-sys');")

# ================= ② 所有多步物品改为进度式 =================
# 玩家对象加 itemPts
sub("    prog:PROG.HAND, progPts:0, items:{}, weapon:null, armor:null, armorCharges:0, ench:{},",
    "    prog:PROG.HAND, progPts:0, items:{}, itemPts:{}, weapon:null, armor:null, armorCharges:0, ench:{},",
    '玩家对象加 itemPts')

# 物品进度核心函数
sub("""/* --- 进程进度点：每次投入 1 步点亮 1 个小点，满点自动升级，进度保存到 localStorage --- */""",
"""/* --- 物品制作进度点：多步物品也按“进度式”投入，集满才拿到成品 --- */
function itemNeed(k){ const it=ITEMS[k]; return it ? (it.cost||0) : 0; }
function itemProgress(p,k){ return (p.itemPts && p.itemPts[k]) || 0; }
function itemReady(p,k){ return itemProgress(p,k) >= itemNeed(k); }
function itemSave(p){
  try{
    const all = JSON.parse(localStorage.getItem('mcItemProg') || '{}');
    all[p.name] = p.itemPts || {};
    localStorage.setItem('mcItemProg', JSON.stringify(all));
  }catch(e){}
}
function itemLoad(name){
  try{
    const all = JSON.parse(localStorage.getItem('mcItemProg') || '{}');
    const v = all[name];
    if(v && typeof v === 'object') return v;
  }catch(e){}
  return {};
}
/* 投入 1 步物品进度；集满则产出成品并清零该物品进度。返回 true 表示已产出 */
function addItemPoint(p, k){
  const it = ITEMS[k];
  if(!it) return false;
  p.itemPts = p.itemPts || {};
  const need = itemNeed(k);
  p.itemPts[k] = Math.min(need, (p.itemPts[k]||0) + 1);
  let done = false;
  if(p.itemPts[k] >= need){
    delete p.itemPts[k];
    done = true;
    craft(p, k);                       /* 真正产出（不扣 AP，AP 由调用方结算） */
    log(`✅ ${lname(p)} 的 <b>${it.name}</b> 制作完成！`,'l-good');
    sfx.win();
  } else {
    log(`🔧 ${lname(p)} 推进 <b>${it.name}</b>：${p.itemPts[k]}/${need}`,'l-sys');
    sfx.rps();
  }
  itemSave(p);
  renderAll();
  return done;
}
function itemProgRow(p,k){
  const need = itemNeed(k), got = Math.min(itemProgress(p,k), need);
  let dots=''; for(let i=0;i<need;i++) dots += `<i class="dot${i<got?' on':''}"></i>`;
  return `<div class="progrow">${dots}<b>${got}/${need}</b></div>`;
}

/* --- 进程进度点：每次投入 1 步点亮 1 个小点，满点自动升级，进度保存到 localStorage --- */""",
'物品进度核心函数')

# 商店面板：制作改为投入进度
sub("""        const d=document.createElement('div'); d.className='item'+(p.ap<it.cost?' dis':'');
        d.innerHTML=`<div class="it"><span>${it.name}${(it.build&&p.buildings[k])?' ✔':''}</span><span class="cost">${it.cost} 步</span></div>
          <div class="desc">${it.desc}</div>`;
        d.onclick=()=>{ if(p.ap<it.cost) return; craft(p,k); render(); renderAll(); };
        grid.appendChild(d);""",
"""        const got = Math.min(itemProgress(p,k), it.cost);
        const d=document.createElement('div'); d.className='item'+(p.ap<1?' dis':'');
        const ic = itemIcon(k);
        let dots=''; for(let i=0;i<it.cost;i++) dots += `<i class="dot${i<got?' on':''}"></i>`;
        d.innerHTML=`<div class="it"><span>${ic?sprTag(ic,24):''}${got>0?'推进 ':'制作 '}${it.name}</span><span class="cost">1 AP</span></div>
          ${it.cost>0?`<div class="progrow">${dots}<b>${got}/${it.cost}</b></div>`:''}
          <div class="desc">${it.desc}${it.cost>1?`<br><b>进度式</b>：每投入 1 步点亮 1 个点，集满 ${it.cost} 点后自动完成。`:''}</div>`;
        d.onclick=()=>{ if(p.ap<1) return; applyShopAction(p,{type:'craft',key:k}); render(); renderAll(); };
        grid.appendChild(d);""",
'商店面板改为进度式')

# applyShopAction 的 craft 分支改为投入进度
sub("""  if(a.type==='craft'){
    const it = ITEMS[a.key];
    if(!it || p.ap<it.cost) return false;
    p.ap -= it.cost;
    const done = craft(p, a.key);
    renderAll();
    return done;
  }""",
"""  if(a.type==='craft'){
    const it = ITEMS[a.key];
    if(!it || p.ap<1) return false;
    if(it.build && !buildAllowed(p,a.key)) return false;          /* 建筑类仍一次性建造 */
    if(it.build){
      if(p.ap < (it.cost||0)) return false;
      p.ap -= it.cost;
      const done = craft(p, a.key);
      renderAll();
      return done;
    }
    p.ap -= 1;                                                    /* 物品：每步 1 AP，进度式 */
    addItemPoint(p, a.key);
    renderAll();
    return true;
  }""",
'applyShopAction 物品进度式')

# applyAction 的 craftShopItem 分支
sub("""    case 'craftShopItem': case 'craft': {
      const it = ITEMS[a.key];
      if(!it){ break; }
      if(p.ap<it.cost){ log(`${lname(p)} 行动点不足，无法制作 ${it.name}。`,'l-warn'); break; }
      itemCost = it.cost;
      craft(p, a.key);
      break; }""",
"""    case 'craftShopItem': case 'craft': {
      const it = ITEMS[a.key];
      if(!it){ break; }
      if(it.build){
        if(p.ap<it.cost){ log(`${lname(p)} 行动点不足，无法建造 ${it.name}。`,'l-warn'); break; }
        itemCost = it.cost; craft(p, a.key); break;
      }
      if(p.ap<1){ log(`${lname(p)} 行动点不足。`,'l-warn'); break; }
      itemCost = 1;
      addItemPoint(p, a.key);
      break; }""",
'applyAction 物品进度式')

# 商店与玩家选项的标签（显示进度）
sub("""      push({type:'craftShopItem', key:k, cost:it.cost, isAction:false, label:`🛠️ 制作 ${it.name}（${it.cost} 步）`});""",
"""      push({type:'craftShopItem', key:k, cost: (it.build ? it.cost : 1), isAction:false,
        label: it.build ? `🏠 建造 ${it.name}（${it.cost} 步）`
                        : `🔧 ${itemProgress(p,k)>0?'推进':'制作'} ${it.name}（${Math.min(itemProgress(p,k)+1, it.cost)}/${it.cost}）`});""",
'玩家选项标签')

# canPay / canShow 对物品进度式的处理（cost 已改为 1）
sub("""  const c = opt.cost||0;
  const s = (opt.isAction!==false) ? actionSlotCost(p) : 0;   /* 购买类动作不占行动次数 */""",
"""  const c = (opt.type==='craftShopItem' && ITEMS[opt.key] && !ITEMS[opt.key].build) ? 1 : (opt.cost||0);
  const s = (opt.isAction!==false) ? actionSlotCost(p) : 0;   /* 购买类动作不占行动次数 */""",
'canPay 物品 1 AP')

# AI 评分：物品进度式（按每步 1 AP 评估，集满才有效）
sub("""    } else {
      const gain = maxDmgOf({weapon:k}) - maxDmgOf(p);
      if(gain>0) s = 72 + gain*22;""",
"""    } else {
      const gain = maxDmgOf({weapon:k}) - maxDmgOf(p);
      const nearDone = itemProgress(p,k) + 1 >= itemNeed(k) && itemNeed(k) > 1;
      if(gain>0) s = 72 + gain*22 + (nearDone?26:0);""",
'AI 评分：临近完成加权')

# endOfRound / gameLoop 保存物品进度
sub("""  for(const q of G.players) if(q.alive) progSave(q);      /* 回合结束：把进程进度存盘 */""",
"""  for(const q of G.players) if(q.alive){ progSave(q); itemSave(q); }   /* 回合结束：进程与物品进度一起存盘 */""",
'回合末存物品进度')
sub("""    for(const q of G.players) if(q.alive) progSave(q);
    log(`──────── <b>第 ${G.round} 回合</b> ────────`,'l-sys');""",
"""    for(const q of G.players) if(q.alive){ progSave(q); itemSave(q); }
    log(`──────── <b>第 ${G.round} 回合</b> ────────`,'l-sys');""",
'回合开始存物品进度')

# 开局载入物品进度
sub("""  for(const p of players){
    const saved = progLoad(p.name);
    if(saved){ p.prog=saved.prog; p.progPts=saved.pts; }
  }""",
"""  for(const p of players){
    const saved = progLoad(p.name);
    if(saved){ p.prog=saved.prog; p.progPts=saved.pts; }
    p.itemPts = itemLoad(p.name) || {};
  }""",
'开局载入物品进度')

# 开局日志
sub("""    let chain = PROG_NAME[0];
    for(let i=1;i<PROG_NAME.length;i++) chain += ` → ${PROG_NAME[i]}(${UPGRADE[i].cost}点)`;
    log(`进程（进度点制）：${chain}；每投入 1 步点亮 1 个小点，进度会保存。`,'l-sys');""",
"""    let chain = PROG_NAME[0];
    for(let i=1;i<PROG_NAME.length;i++) chain += ` → ${PROG_NAME[i]}(${UPGRADE[i].cost}点)`;
    log(`进程（进度点制）：${chain}；每投入 1 步点亮 1 个小点，进度会保存。`,'l-sys');
    log('物品同样是<b>进度式</b>：多步物品每投入 1 步点亮 1 个点，集满自动完成，进度也会保存。','l-sys');""",
'开局日志')

# ================= ④ 切换手上工具 =================
sub("""/* --- 距离 --- */""",
"""/* --- 切换手上的工具 --- */
function heldWeapons(p){
  return Object.keys(p.items).filter(k=>ITEMS[k] && ['fist','flesh','wood_sword','stone_sword','iron_sword','diamond_sword','trident','crossbow','firework'].includes(k));
}
function switchWeapon(p, k){
  if(k && k!==p.weapon && ITEMS[k]) p.weapon = k;
  log(`🖐 ${lname(p)} 换上 <b>${ITEMS[p.weapon] ? ITEMS[p.weapon].name : '空手'}</b>。`,'l-sys');
  renderAll();
}

/* --- 距离 --- */""",
'切换工具函数')

sub("""  /* 商店入口 + 当前进程可制作的项目（制作/购买只花 AP，不占行动次数） */""",
"""  /* 切换手上的工具：不消耗 AP 与行动次数 */
  for(const k of heldWeapons(p)){
    if(k===p.weapon) continue;
    push({type:'switch_weapon', key:k, cost:0, isAction:false, label:`🖐 换上 ${ITEMS[k].name}`});
  }
  /* 商店入口 + 已解锁进程可制作的项目（制作/购买只花 AP，不占行动次数） */""",
'玩家选项：切换工具')

sub("""    case 'water':
      if(!p.inWater){ p.inWater=true; removeBurn(p); log(`💧 ${lname(p)} 跳入水中（与其它玩家距离和所在建筑无关）。`,'l-good'); }""",
"""    case 'switch_weapon':
      switchWeapon(p, a.key);
      break;

    case 'water':
      if(!p.inWater){ p.inWater=true; removeBurn(p); log(`💧 ${lname(p)} 跳入水中（与其它玩家距离和所在建筑无关）。`,'l-good'); }""",
'applyAction 切换工具')

# 面板上的武器图标可点（用 data 属性 + 委托）
sub("""function gearIcons(p){
  const out = [];
  if(p.weapon && ITEMS[p.weapon]) out.push(sprTag(itemIcon(p.weapon)||'fist', 22) + ' ' + ITEMS[p.weapon].name);
  else out.push(sprTag('fist', 22) + ' 空手');""",
"""function gearIcons(p){
  const out = [];
  if(p.weapon && ITEMS[p.weapon]) out.push(sprTag(itemIcon(p.weapon)||'fist', 22) + ' ' + ITEMS[p.weapon].name);
  else out.push(sprTag('fist', 22) + ' 空手');
  if(heldWeapons(p).length>1) out.push('<span style="color:var(--acc);font-size:11px"></span>');""",
'装备行提示可切换')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
print('文件', round(len(t)/1024,1), 'KB')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
