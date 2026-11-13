# -*- coding: utf-8 -*-
"""补丁 68：护甲优先级选择
   - 玩家可持有并储备多件护甲（p.armors 数组）
   - 可选“优先消耗哪一件”，受伤时先扣优先级最高的那件
   - 玩家面板显示护甲列表，点击即可设为优先
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ---------- 1) 玩家对象加护甲储备 ----------
sub("""    prog:PROG.HAND, progPts:0, items:{}, itemPts:{}, weapon:null, armor:null, armorCharges:0, ench:{},""",
"""    prog:PROG.HAND, progPts:0, items:{}, itemPts:{}, weapon:null, armor:null, armorCharges:0,
    armors:[], armorPriority:[], ench:{},""", '玩家对象加 armors/armorPriority')

# ---------- 2) 护甲工具函数 ----------
sub("""/* 是否持有护甲类物品（不论耐久是否耗尽）—— TNT 的伤害档位用它判定 */""",
"""/* ---------- 多件护甲与优先级 ----------
   p.armor / p.armorCharges 仍是“当前正在生效的那件”（兼容旧逻辑）
   p.armors = [{key, charges, max}]  储备的护甲（含正在生效的）
   p.armorPriority = [key,...]       优先消耗顺序（靠前先扣） */
function armorsOf(p){
  if(!p.armors) p.armors = [];
  /* 把旧的单件字段同步进来 */
  if(p.armor && !p.armors.some(a=>a.key===p.armor)){
    p.armors.unshift({ key:p.armor, charges:p.armorCharges||0, max:armorMaxOf(p.armor) });
  }
  return p.armors;
}
function armorMaxOf(key){ return ITEMS[key] ? (ITEMS[key].armor||0) : 0; }
/* 取得一件护甲（可重复持有同种） */
function gainArmor(p, key){
  if(!ITEMS[key] || !ITEMS[key].armor) return false;
  if(!p.armors) p.armors = [];
  const max = armorMaxOf(key);
  const existing = p.armors.find(a=>a.key===key);
  if(existing){ existing.charges = Math.min(max, existing.charges + max); }
  else p.armors.push({ key, charges:max, max });
  if(!p.armorPriority) p.armorPriority = [];
  if(!p.armorPriority.includes(key)) p.armorPriority.push(key);
  equipBest(p);
  return true;
}
/* 选一件“当前生效”的护甲（优先未破损的） */
function equipBest(p){
  if(!p.armors || !p.armors.length){ p.armor=null; p.armorCharges=0; return; }
  const order = (p.armorPriority||[]).slice();
  const sorted = p.armors.slice().sort((a,b)=>{
    const ia = order.indexOf(a.key), ib = order.indexOf(b.key);
    return (ia<0?99:ia) - (ib<0?99:ib);
  });
  const pick = sorted.find(a=>a.charges>0) || sorted[0];
  p.armor = pick.key; p.armorCharges = pick.charges;
}
/* 设置优先消耗顺序 */
function setArmorPriority(p, key){
  if(!p.armorPriority) p.armorPriority = [];
  p.armorPriority = [key, ...p.armorPriority.filter(k=>k!==key)];
  equipBest(p);
  log(`🛡 ${lname(p)} 设定优先消耗：<b>${ITEMS[key] ? ITEMS[key].name : key}</b>`,'l-sys');
  renderAll();
}
/* 扣护甲耐久（按优先级），返回 {key, absorbed} */
function consumeArmorCharges(p, amount){
  if(!p.armors) armorsOf(p);
  const order = (p.armorPriority||[]).slice();
  const sorted = p.armors.slice().sort((a,b)=>{
    const ia = order.indexOf(a.key), ib = order.indexOf(b.key);
    return (ia<0?99:ia) - (ib<0?99:ib);
  });
  let left = amount, absorbed = 0, broke = null;
  for(const a of sorted){
    if(left<=0) break;
    if(a.charges<=0) continue;
    const use = Math.min(a.charges, left);
    a.charges = rm(a.charges - use);
    left = rm(left - use);
    absorbed = rm(absorbed + use);
    if(a.charges<=0) broke = a.key;
  }
  p.armors = p.armors.filter(a=>a.charges>0 || a.key===p.armor);
  equipBest(p);
  return { absorbed, broke };
}

/* 是否持有护甲类物品（不论耐久是否耗尽）—— TNT 的伤害档位用它判定 */""", '护甲工具函数')

# ---------- 3) tryDamage：按优先级扣护甲 ----------
sub("""  if(!ignoreArmor && !noArmorConsume && dmg[0]>0 && armorActive(target)){
    absorbed = Math.min(dmg[0], target.armorCharges);
    target.armorCharges = rm(target.armorCharges - absorbed);
    dmg[0] = rm(dmg[0]-absorbed);
    sfx.block();
    log(`${lname(target)} 的 ${ITEMS[target.armor].name} 抵消了 ${rm(absorbed)} 点物理伤害（护甲剩余 ${rm(target.armorCharges)} 点）。`,'l-sys');
    if(target.armorCharges<=0){
      log(`${lname(target)} 的 ${ITEMS[target.armor].name} 已破损——需要铁砧修复（2 步）。`,'l-warn');
      breakArmor(target);
    }
  }""",
"""  if(!ignoreArmor && !noArmorConsume && dmg[0]>0 && armorActive(target)){
    const res = consumeArmorCharges(target, dmg[0]);
    absorbed = res.absorbed;
    dmg[0] = rm(dmg[0]-absorbed);
    try{ sfx.block(); }catch(e){}
    const usedName = res.broke ? ITEMS[res.broke].name : (target.armor ? ITEMS[target.armor].name : '护甲');
    log(`${lname(target)} 的 ${usedName} 抵消了 ${rm(absorbed)} 点物理伤害（剩余 ${rm(target.armorCharges)} 点）。`,'l-sys');
    if(res.broke){
      log(`${lname(target)} 的 ${ITEMS[res.broke].name} 已破损——需要铁砧修复（2 步）。`,'l-warn');
      breakArmor(target);
    }
  }""", 'tryDamage 按优先级扣护甲')

# ---------- 4) craft 装备护甲时进入储备 ----------
sub("""  if(it.armor){
    p.armor = k; p.armorCharges = it.armor;
    log(`🛡 ${lname(p)} 装备了 ${it.name}（可挡 ${it.armor} 次物理伤害）。`,'l-good');""",
"""  if(it.armor){
    gainArmor(p, k);
    const cnt = armorsOf(p).filter(a=>a.charges>0).length;
    log(`🛡 ${lname(p)} 装备了 ${it.name}（可挡 ${it.armor} 次物理伤害）${cnt>1?`；当前储备 ${cnt} 件护甲`:''}。`,'l-good');""",
'craft 装备护甲走 gainArmor')

# ---------- 5) 人类选项：调整护甲优先 ----------
sub("""  /* 切换手上的工具：不消耗 AP 与行动次数 */""",
"""  /* 护甲优先顺序：持有 2 件以上时可切换先消耗哪件（免费） */
  const myArmors = armorsOf(p).filter(a=>a.charges>0);
  if(myArmors.length >= 2){
    for(const a of myArmors){
      if((p.armorPriority||[])[0] === a.key) continue;
      push({type:'armor_priority', key:a.key, cost:0, isAction:false, slots:0,
        label:`🛡 改为优先消耗 ${ITEMS[a.key].name}（剩 ${a.charges}）`});
    }
  }
  /* 切换手上的工具：不消耗 AP 与行动次数 */""", '护甲优先选项')

# ---------- 6) applyAction 处理 armor_priority ----------
sub("""    case 'switch_weapon':
      switchWeapon(p, a.key);
      break;""",
"""    case 'switch_weapon':
      switchWeapon(p, a.key);
      break;

    case 'armor_priority':
      setArmorPriority(p, a.key);
      break;""", 'applyAction armor_priority')

sub("""  const isFree = ['switch_weapon','pearl','pass','golem_punch'].includes(a.type);  /* 免费即时动作：不占行动次数 */""",
"""  const isFree = ['switch_weapon','pearl','pass','golem_punch','armor_priority'].includes(a.type);  /* 免费即时动作 */""",
'armor_priority 免费')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
