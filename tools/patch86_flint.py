# -*- coding: utf-8 -*-
"""补丁 86：背包里的攻击物品直接可用（修“有打火石却用不了”）
   ① 打火石 / 腐肉 等补进武器列表
   ② 攻击选项不再只认“当前武器”：扫描背包里所有攻击物品，满足距离即可直接出手
   ③ 出手时若是武器则自动装备；腐肉/打火石这类道具不占武器槽（一次性使用类）
   ④ 打火石补伤害档案（3 次 0.5 火焰，按新规则统一在回合末结算）
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

# ① 武器列表补全（打火石、TNT 类不计入武器槽，但打火石是“手持道具”）
sub("""const WEAPON_KEYS = ['fist','flesh','wood_sword','stone_sword','iron_sword','diamond_sword','trident','crossbow','firework'];""",
"""/* 可以用“攻击”动作出手的物品（腐肉/打火石是道具，不需要占武器槽） */
const WEAPON_KEYS = ['fist','flesh','wood_sword','stone_sword','iron_sword','diamond_sword',
                     'trident','crossbow','firework','flint'];
/* 这些是消耗型道具：出手时不会替换手上的武器 */
const THROWABLE_KEYS = ['flesh','flint'];""",
'武器列表补全')

# ② 攻击选项：扫描背包里所有攻击物品（不再只看当前武器）
sub("""  /* 攻击 */
  for(const e of enemies){
    if(weapon==='trident'){
      if(distanceBetween(p,e)===0) push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,label:`🔱 三叉戟近战 ${e.name}（1 AP，判定 1.5）`});
      else push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,ranged:true,label:`🔱 掷出三叉戟 ${e.name}（1 AP，无需判定 1.5，掷出后失去）`});
    } else if(weapon==='flesh' && e.effects.some(x=>x.type==='bleed')){
      /* 流血期间不能再次施加腐肉 */
    } else if(inRangeOf(p, weapon, e)){
      const nm = ITEMS[weapon] ? ITEMS[weapon].name : '空手';
      push({type:'attack',key:weapon,targetId:e.id,cost:ATK_COST,
        label:`${nm} → ${e.name}（1 AP${weapon==='crossbow'||weapon==='firework'?'，远程':'，判定'}）`});
    }
  }""",
"""  /* 攻击：背包里所有可出手的物品（含当前武器），只要距离够就能直接打 */
  for(const e of enemies){
    const usable = WEAPON_KEYS.filter(k => (k===weapon) || (k!=='fist' && hasItem(p,k)));
    /* 当前武器排最前，其余按固定顺序 */
    usable.sort((a,b)=> (a===weapon? -1 : b===weapon? 1 : 0));
    for(const k of usable){
      const nm = ITEMS[k] ? ITEMS[k].name : '空手';
      if(k==='trident'){
        if(distanceBetween(p,e)===0) push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,
          label:`🔱 三叉戟近战 ${e.name}（1 AP，判定 1.5）`});
        else push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,ranged:true,
          label:`🔱 掷出三叉戟 ${e.name}（1 AP，无需判定 1.5，掷出后失去）`});
        continue;
      }
      if(k==='flesh' && e.effects.some(x=>x.type==='bleed')) continue;   /* 流血中不能再撒腐肉 */
      if(!inRangeOf(p, k, e)) continue;
      const ranged = (k==='crossbow' || k==='firework');
      const noJudge = (k==='flint');
      const cur = (k===weapon) ? '' : '（切换使用）';
      push({type:'attack',key:k,targetId:e.id,cost:ATK_COST,
        label:`${nm} → ${e.name}（1 AP，${ranged?'远程':noJudge?'无需判定':'判定'}）${cur}`});
    }
  }""", '攻击扫描背包')

# ③ 出手时自动装备武器（道具不占武器槽）
sub("""    case 'attack': {
      /* 攻击：护甲选择在 performAttack 内处理 */
      await performAttack(p, T, a.key||p.weapon||'fist', a); break; }""",
"""    case 'attack': {
      /* 出手前若换成了别的武器则自动装备（腐肉/打火石这类道具不替换武器） */
      const ak = a.key || p.weapon || 'fist';
      if(!THROWABLE_KEYS.includes(ak) && hasItem(p, ak) && p.weapon !== ak){
        p.weapon = ak;
        log(`🖐 ${lname(p)} 换上 ${ITEMS[ak] ? ITEMS[ak].name : '空手'}。`,'l-sys');
      }
      await performAttack(p, T, ak, a); break; }""", '攻击自动装备')

# ④ 打火石伤害档案
sub("""    crossbow:[1.5,0,0,0], firework:[0.5,0,1.5,0], golem_punch:[1.5,0,0,0],""",
"""    crossbow:[1.5,0,0,0], firework:[0.5,0,1.5,0], golem_punch:[1.5,0,0,0],
    flint:[0,0,0,0],        /* 打火石：无直接伤害，靠 burnTicks 点火 */""",
'打火石基础伤害')

sub("""  if(key==='crossbow' && hasEnch(attacker,'flame')) burnTicks=2;""",
"""  if(key==='crossbow' && hasEnch(attacker,'flame')) burnTicks=2;
  if(key==='flint') burnTicks = 3;                    /* 打火石：3 次 0.5 火焰（有甲 2 次） */""",
'打火石点火次数')

# 打火石：目标有防具则只 2 次（按物品说明）
sub("""    if(prof.burnTicks>0 && target.alive){
      addEffect(target,'burn',prof.burnTicks,99,'火焰');""",
"""    if(prof.burnTicks>0 && target.alive){
      const ticks = (key==='flint' && armorHasAny(target)) ? 2 : prof.burnTicks;
      addEffect(target,'burn',ticks,99,'火焰');""", '打火石有甲时 2 次')
sub("""      log(`🔥 ${lname(target)} 被点燃：将在本回合所有玩家行动结束后结算 ${prof.burnTicks} 次 0.5 火焰伤害（此时入水可取消）。`,'l-warn');""",
"""      log(`🔥 ${lname(target)} 被点燃：将在本回合所有玩家行动结束后结算 ${ticks} 次 0.5 火焰伤害（此时入水可取消）。`,'l-warn');""",
'点燃日志用实际次数')

# ⑤ 切换武器列表也补上打火石（方便手动换）
sub("""function heldWeapons(p){
  return WEAPON_KEYS.filter(k=>hasItem(p,k) || (k==='fist'));
}""",
"""function heldWeapons(p){
  /* 只把“真正的武器”算作可装备项；腐肉/打火石是道具，不进武器槽 */
  return WEAPON_KEYS.filter(k=>(k==='fist') || (hasItem(p,k) && !THROWABLE_KEYS.includes(k)));
}""", 'heldWeapons 排除道具')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
