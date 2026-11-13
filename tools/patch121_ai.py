# -*- coding: utf-8 -*-
"""补丁 121：AI 行为优化（5 项）
   ① TNT：引爆前确认自己已在安全距离，否则先拉开距离再引爆
   ② 低血时主动远离有威胁的敌人
   ③ 提高回血（面包/药水）与制作防具的优先级
   ④ AI 学会使用打火石 / 腐肉（法术伤害，克制高护甲目标）
   ⑤ aiOptions 支持背包里的多种攻击物品（打火石/腐肉/弩等）
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ---------- ⑤ aiOptions：扫描背包里的攻击物品 ----------
sub("""  /* 攻击 */
  for(const e of enemies){
    if(weapon==='trident'){
      if(distanceBetween(p,e)===0) push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,label:'三叉戟近战 '+e.name});
      else push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,ranged:true,label:'掷出三叉戟 '+e.name});
    } else if(weapon==='flesh' && e.effects.some(x=>x.type==='bleed')){
      /* 不能重复施加 */
    } else if(inRangeOf(p,weapon,e)){
      push({type:'attack',key:weapon,targetId:e.id,cost:ATK_COST,label:`${ITEMS[weapon]?ITEMS[weapon].name:'一拳'} → ${e.name}`});
    }
  }""",
"""  /* 攻击：当前武器 + 背包里其他可出手的物品（含打火石 / 腐肉） */
  for(const e of enemies){
    const usable = WEAPON_KEYS.filter(k => (k===weapon) || (k!=='fist' && hasItem(p,k)));
    usable.sort((a,b)=> (a===weapon? -1 : b===weapon? 1 : 0));
    for(const k of usable){
      if(k==='trident'){
        if(distanceBetween(p,e)===0) push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,label:'三叉戟近战 '+e.name});
        else push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,ranged:true,label:'掷出三叉戟 '+e.name});
        continue;
      }
      if(k==='flesh' && e.effects.some(x=>x.type==='bleed')) continue;
      if(!inRangeOf(p,k,e)) continue;
      push({type:'attack',key:k,targetId:e.id,cost:ATK_COST,label:`${ITEMS[k]?ITEMS[k].name:'一拳'} → ${e.name}`});
    }
  }""", '⑤ aiOptions 支持背包攻击物品')

# 低血时更愿意吃面包 / 喝药
sub("""  if(hasItem(p,'bread') && p.hp<=2.5) push({type:'eat',item:'bread',targetId:p.id,cost:CONSUME_COST,label:'吃面包'});
  if(hasItem(p,'god_apple') && p.hp<=2.5 && featOn('god_apple')) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,label:'金苹果'});
  if(featOn('potion') && hasItem(p,'potion_heal') && p.hp<=2) push({type:'potion',item:'potion_heal',cost:0,label:'治疗药水'});""",
"""  if(hasItem(p,'bread') && p.hp<=3.5) push({type:'eat',item:'bread',targetId:p.id,cost:CONSUME_COST,label:'吃面包'});
  if(hasItem(p,'god_apple') && p.hp<=3 && featOn('god_apple')) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,label:'金苹果'});
  if(featOn('potion') && hasItem(p,'potion_heal') && p.hp<=3) push({type:'potion',item:'potion_heal',cost:0,label:'治疗药水'});""",
'AI 低血更愿意回血')

# ---------- ①③④ aiPick 评分 ----------
sub("""      case 'golem_punch': return 180;
      case 'move': return o.dir===-1 ? 58 : 40;
      case 'tnt_detonate': { const v=P(p.flags.tntOn); return (v && v.team!==p.team) ? 230 : 30; }
      case 'tnt_place': return 140;
      case 'water': return (p.hp<=2)?100:64;
      case 'water_pull': return 46;
      case 'eat': return p.hp<=2?250:(p.hp<3.5?88:20);
      case 'potion': return 200;""",
"""      case 'golem_punch': return 180;
      case 'move': {
        /* ② 低血时主动远离有威胁的敌人 */
        if(o.dir!==+1) return 58;                       /* 靠近 */
        const foe = P(o.targetId);
        const fdmg = foe ? maxDmgOf(foe) : 1;
        const threat = (foe && foe.alive) ? fdmg : 0;
        let s = 46;
        if(threat >= 1.5) s += 30;                      /* 对手伤害高，拉开更有价值 */
        if(threat >= 2.5) s += 20;
        if(threat >= 2) s += 20;                        /* 攒满：离高威胁目标远一点 */
        if(p.hp<=3) s += 26;
        if(p.hp<=2) s += 40;                            /* 濒死：赶紧撤 */
        if(p.hp<=1.5) s += 30;
        if(hasItem(p,'bread') || hasItem(p,'potion_heal') || hasItem(p,'god_apple')) s += 8;
        return s;
      }
      case 'tnt_detonate': {
        const v = P(p.flags.tntOn);
        if(!(v && v.team!==p.team)) return 30;
        /* ① 引爆前先确认自己已在安全距离，否则优先拉开再引爆 */
        const dt = distanceBetween(p, v);
        if(dt < 2) return 24;                           /* 太近：先远离，不要自伤 */
        return dt >= 3 ? 250 : 190;
      }
      case 'tnt_place': {
        const v = P(o.targetId);
        if(!v) return 40;
        /* 贴 TNT 需要 0 格，贴完自己也在爆炸范围——血量太低时不划算 */
        const self = p.hp + tempHpOf(p);
        let s = 140;
        if(self <= 2.5) s -= 60;                        /* 贴完容易被一起炸死 */
        if(self <= 1.5) s -= 50;
        /* 若接下来能拉开距离（还有 AP）则更愿意贴 */
        if(p.ap >= 2) s += 20;
        return s;
      }
      case 'water': return (p.hp<=2)?100:64;
      case 'water_pull': return 46;
      case 'eat': return p.hp<=1.5?300:(p.hp<=2.5?200:(p.hp<3.5?110:24));
      case 'potion': return p.hp<=2.5?240:200;""",
'① ② AI 评分：TNT 距离 + 低血撤退 + 回血')

# ④ 打火石 / 腐肉：对高护甲敌人更优
sub("""        const pierce = (k==='diamond_sword' && armorActive(e)) ? 1.5 : 0;
        const effDmg = pierce || Math.max(0, dmg - (armorActive(e)?Math.min(dmg,e.armorCharges):0));
        if(e.hp<=effDmg) return 320;                        /* 击杀 */
        let s = 60 + dmg*12;""",
"""        const pierce = (k==='diamond_sword' && armorActive(e)) ? 1.5 : 0;
        const effDmg = pierce || Math.max(0, dmg - (armorActive(e)?Math.min(dmg,e.armorCharges):0));
        if(e.hp<=effDmg) return 320;                        /* 击杀 */
        /* ④ 打火石：法术持续伤害，无视护甲，对高护甲目标特别有效 */
        if(k==='flint'){
          const ticks = armorHasAny(e) ? 2 : 3;
          let s = 74 + ticks * 16;
          if(armorActive(e)) s += 26;                       /* 对手有甲：打火石很划算 */
          if(e.hp <= ticks * 0.5) s += 60;                  /* 火焰足够烧死 */
          if(slotsPaid) s -= 12;
          return s;
        }
        /* ④ 腐肉：法术伤害 + 流血，护甲吸不了法术 */
        if(k==='flesh'){
          let s = 66;
          if(armorActive(e)) s += 22;
          if(!e.effects.some(x=>x.type==='bleed')) s += 14; /* 还没流血：值得贴一次 */
          if(slotsPaid) s -= 10;
          return s;
        }
        let s = 60 + dmg*12;""",
'④ AI 会用打火石/腐肉')

# ---------- ③ aiShopChoice：提升生存类购买 ----------
sub("""    } else if(it.armor){
      if(armorActive(p)) continue;
      s = {leather:74, iron_armor:96, golem:100, diamond_armor:112}[k] || 50;
    } else {""",
"""    } else if(it.armor){
      if(armorActive(p)) continue;
      s = {leather:74, iron_armor:96, golem:100, diamond_armor:112}[k] || 50;
      /* ③ 提升生存：血越少、越没甲，越该做防具 */
      if(p.hp<=3.5) s += 14;
      if(p.hp<=2.5) s += 20;
      if(!p.armor) s += 16;
      /* 敌人护甲很厚时，防具优先度更高（要活得久才能磨） */
      if(enemies.some(e=>armorActive(e))) s += 10;
    } else {""", '③ AI 更愿意做防具')

sub("""      else if(k==='bread') s = p.hp<3.5?74:30;
      else if(k==='flint') s = 68;""",
"""      else if(k==='bread') s = p.hp<3.5?150:(p.hp<3?120:26);   /* ③ 面包：缺血时优先囤 */
      else if(k==='flint') s = 74;                             /* ④ 打火石：法术克制护甲 */
      else if(k==='flesh') s = 60;                             /* ④ 腐肉：法术 + 流血 */""",
'③④ AI 更愿意囤面包/打火石/腐肉')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  长度 {orig} → {len(back)}（{len(back)-orig:+d}）')
for n, k in [('① TNT 距离判断','dt < 2) return 24'), ('② 低血撤退','攒满：离高威胁目标远一点'.split('：')[0]),
             ('③ 回血评分','p.hp<=2.5?200'), ('③ 防具','越该做防具'),
             ('④ 打火石','打火石很划算'), ('④ 腐肉','护甲吸不了法术'),
             ('⑤ 背包攻击','const usable = WEAPON_KEYS.filter')]:
    print(f'  {n}:', k in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
