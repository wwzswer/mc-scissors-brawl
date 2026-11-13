# -*- coding: utf-8 -*-
"""补丁 60：攻击固定消耗 1 AP（不再占用免费行动槽）；切换武器保持免费
   规则来源：用户反馈「攻击都需要消耗1AP，切换武器不需要消耗AP」
   - 攻击类动作：attack / tnt_place / tnt_detonate → 每次固定 1 AP，直接扣，不占免费行动槽
   - 铁傀儡被动 golem_punch：保持免费（用户此前明确要求）
   - 切换武器 switch_weapon：保持免费
   - 其余动作（走位/吃/喝/修复/附魔/制作）：仍走「每回合 1 次免费行动 + 之后 1 AP」
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label, count=1):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, count); notes.append('  ok ' + label); return True

# ---------- 1) 攻击选项 cost 0 -> 1（人类） ----------
sub("""    if(weapon==='trident'){
      if(distanceBetween(p,e)===0) push({type:'attack',key:'trident',targetId:e.id,cost:0,label:`三叉戟近战 ${e.name}（判定 1.5）`});
      else push({type:'attack',key:'trident',targetId:e.id,cost:0,ranged:true,label:`掷出三叉戟 ${e.name}（无需判定 1.5，掷出后失去）`});
    } else if(weapon==='flesh' && e.effects.some(x=>x.type==='bleed')){""",
"""    if(weapon==='trident'){
      if(distanceBetween(p,e)===0) push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,label:`🔱 三叉戟近战 ${e.name}（1 AP，判定 1.5）`});
      else push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,ranged:true,label:`🔱 掷出三叉戟 ${e.name}（1 AP，无需判定 1.5，掷出后失去）`});
    } else if(weapon==='flesh' && e.effects.some(x=>x.type==='bleed')){""",
'人类：三叉戟攻击 1 AP')

sub("""      const nm = ITEMS[weapon] ? ITEMS[weapon].name : '空手';
      push({type:'attack',key:weapon,targetId:e.id,cost:0,label:`${nm} → ${e.name}${weapon==='crossbow'||weapon==='firework'?'（远程）':'（判定）'}`});""",
"""      const nm = ITEMS[weapon] ? ITEMS[weapon].name : '空手';
      push({type:'attack',key:weapon,targetId:e.id,cost:ATK_COST,
        label:`${nm} → ${e.name}（1 AP${weapon==='crossbow'||weapon==='firework'?'，远程':'，判定'}）`});""",
'人类：普通攻击 1 AP')

# ---------- 2) 攻击选项 cost（AI） ----------
sub("""    if(distanceBetween(p,e)===0) push({type:'attack',key:'trident',targetId:e.id,cost:0,label:'三叉戟近战 '+e.name});
    else push({type:'attack',key:'trident',targetId:e.id,cost:0,ranged:true,label:'掷出三叉戟 '+e.name});""",
"""    if(distanceBetween(p,e)===0) push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,label:'三叉戟近战 '+e.name});
    else push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,ranged:true,label:'掷出三叉戟 '+e.name});""",
'AI：三叉戟攻击 1 AP')

sub("""    push({type:'attack',key:weapon,targetId:e.id,cost:0,label:`${ITEMS[weapon]?ITEMS[weapon].name:'一拳'} → ${e.name}`});""",
"""    push({type:'attack',key:weapon,targetId:e.id,cost:ATK_COST,label:`${ITEMS[weapon]?ITEMS[weapon].name:'一拳'} → ${e.name}`});""",
'AI：普通攻击 1 AP')

# ---------- 3) TNT 贴/引爆：改为固定 1 AP（人类 + AI） ----------
sub("""      push({type:'tnt_detonate',cost:1,label:`💥 引爆 ${P(p.flags.tntOn).name} 头上的 TNT（1 步）`});""",
"""      push({type:'tnt_detonate',cost:ATK_COST,label:`💥 引爆 ${P(p.flags.tntOn).name} 头上的 TNT（1 AP）`});""",
'人类：TNT 引爆 1 AP')
sub("""      push({type:'tnt_place',targetId:e.id,cost:1,label:`🧨 把 TNT 黏在 ${e.name} 头上（1 步，需 0 格）`, needDist0:true});""",
"""      push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:`🧨 把 TNT 黏在 ${e.name} 头上（1 AP，需 0 格）`, needDist0:true});""",
'人类：TNT 放置 1 AP')
sub("""      push({type:'tnt_detonate',cost:1,label:'引爆 TNT'});""",
"""      push({type:'tnt_detonate',cost:ATK_COST,label:'引爆 TNT'});""", 'AI：TNT 引爆 1 AP')
sub("""      push({type:'tnt_place',targetId:e.id,cost:1,label:'贴 TNT'});""",
"""      push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:'贴 TNT'});""", 'AI：TNT 放置 1 AP')

# ---------- 4) ATK_COST 常量 ----------
sub("""const BUILD_COST = 1;""",
"""const BUILD_COST = 1;          /* 前往任意建筑统一 1 AP */
const ATK_COST   = 1;          /* 每次攻击固定 1 AP（不占免费行动槽） */""",
'ATK_COST 常量')

# 攻击类判定工具
sub("""/* 是否持有护甲类物品（不论耐久是否耗尽）—— TNT 的伤害档位用它判定 */""",
"""/* 攻击类动作：固定消耗 ATK_COST 点 AP，不占用每回合的免费行动槽 */
const ATTACK_TYPES = ['attack','tnt_place','tnt_detonate'];
function isAttackAction(a){ return !!a && ATTACK_TYPES.includes(a.type); }

/* 是否持有护甲类物品（不论耐久是否耗尽）—— TNT 的伤害档位用它判定 */""",
'isAttackAction 工具')

# ---------- 5) applyAction：攻击直接扣 1 AP，不占免费行动槽 ----------
sub("""  let itemCost = 0;                 /* 购买类动作的 AP 消耗，由各分支填写，末尾统一扣除 */
  if(a.type!=='pass' && a.isAction!==false && !isPurchase && !isFree){
    if(p.slotsLeft>0) p.slotsLeft--;
    else if(actionSlotCost(p)===1){ p.ap-=1; log(`（额外行动 -1 AP）`,'l-sys'); }
    else { log(`${lname(p)} 行动点不足，无法行动。`,'l-warn'); return; }
    p.actionsUsed++; p.turnSpent=(p.turnSpent||0)+1;
  }""",
"""  let itemCost = 0;                 /* 购买类动作的 AP 消耗，由各分支填写，末尾统一扣除 */
  if(isAttackAction(a)){
    /* 攻击：每次固定 1 AP，直接扣除，不消耗免费行动槽 */
    if(p.ap < ATK_COST){ log(`${lname(p)} 行动点不足，无法攻击（每次攻击需 ${ATK_COST} AP）。`,'l-warn'); return; }
    p.ap -= ATK_COST;
    p.actionsUsed++; p.turnSpent=(p.turnSpent||0)+1;
    log(`⚔️ 攻击消耗 ${ATK_COST} AP（剩余 ${p.ap}）`,'l-sys');
  } else if(a.type!=='pass' && a.isAction!==false && !isPurchase && !isFree){
    if(p.slotsLeft>0) p.slotsLeft--;
    else if(actionSlotCost(p)===1){ p.ap-=1; log(`（额外行动 -1 AP）`,'l-sys'); }
    else { log(`${lname(p)} 行动点不足，无法行动。`,'l-warn'); return; }
    p.actionsUsed++; p.turnSpent=(p.turnSpent||0)+1;
  }""",
'applyAction：攻击固定 1 AP')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
