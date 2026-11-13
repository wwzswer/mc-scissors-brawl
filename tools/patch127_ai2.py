# -*- coding: utf-8 -*-
"""补丁 127：在干净版本上叠加 AI 改进（5 项）
   逐行方式，避免多行匹配失败；TNT 结构已由补丁 126 修好。
"""
import pathlib, os, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
t = IDX.read_text(encoding='utf-8')
lines = t.split('\n')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
changed = []

# ---------- ① aiOptions：支持背包里多种攻击物品 ----------
old_atk = """  for(const e of enemies){
    if(weapon==='trident'){
      if(distanceBetween(p,e)===0) push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,label:'三叉戟近战 '+e.name});
      else push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,ranged:true,label:'掷出三叉戟 '+e.name});
    } else if(weapon==='flesh' && e.effects.some(x=>x.type==='bleed')){
      /* 不能重复施加 */
    } else if(inRangeOf(p,weapon,e)){
      push({type:'attack',key:weapon,targetId:e.id,cost:ATK_COST,label:`${ITEMS[weapon]?ITEMS[weapon].name:'一拳'} → ${e.name}`});
    }
  }"""
new_atk = """  for(const e of enemies){
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
  }"""
if old_atk in t:
    t = t.replace(old_atk, new_atk, 1); changed.append('① aiOptions 支持背包攻击物品')
else:
    print('! ① 锚点未匹配')

# ---------- ② AI 补给阈值：血少更愿意吃 ----------
t2 = t
t = t.replace("push({type:'eat',item:'bread',targetId:p.id,cost:CONSUME_COST,label:'吃面包'})",
              "push({type:'eat',item:'bread',targetId:p.id,cost:CONSUME_COST,label:'吃面包'})")
for old, new, lb in [
    ("if(hasItem(p,'bread') && p.hp<=2.5)", "if(hasItem(p,'bread') && p.hp<=3.5)", '② 面包阈值 2.5→3.5'),
    ("if(hasItem(p,'god_apple') && p.hp<=2.5 && featOn('god_apple'))", "if(hasItem(p,'god_apple') && p.hp<=3 && featOn('god_apple'))", '② 金苹果阈值 2.5→3'),
    ("if(featOn('potion') && hasItem(p,'potion_heal') && p.hp<=2)", "if(featOn('potion') && hasItem(p,'potion_heal') && p.hp<=3)", '② 药水阈值 2→3'),
]:
    if old in t:
        t = t.replace(old, new, 1); changed.append(lb)

# ---------- ③ aiPick 评分：TNT 距离 / 低血撤退 / 回血 ----------
old_sc = """      case 'golem_punch': return 180;
      case 'move': return o.dir===-1 ? 58 : 40;
      case 'tnt_detonate': { const v=P(p.flags.tntOn); return (v && v.team!==p.team) ? 230 : 30; }
      case 'tnt_place': return 140;
      case 'water': return (p.hp<=2)?100:64;
      case 'water_pull': return 46;
      case 'eat': return p.hp<=2?250:(p.hp<3.5?88:20);
      case 'potion': return 200;"""
new_sc = """      case 'golem_punch': return 180;
      case 'move': {
        if(o.dir!==+1) return 58;                       /* 靠近 */
        const foe = P(o.targetId);
        const fdmg = foe ? maxDmgOf(foe) : 1;
        const threat = (foe && foe.alive) ? fdmg : 0;
        let s = 46;
        if(threat >= 1.5) s += 30;
        if(threat >= 2.5) s += 20;
        if(threat >= 2) s += 20;
        if(p.hp<=3) s += 26;
        if(p.hp<=2) s += 40;
        if(p.hp<=1.5) s += 30;
        if(hasItem(p,'bread') || hasItem(p,'potion_heal') || hasItem(p,'god_apple')) s += 8;
        return s;
      }
      case 'tnt_detonate': {
        const v = P(p.flags.tntOn);
        if(!(v && v.team!==p.team)) return 30;
        const dt = distanceBetween(p, v);
        if(dt < 2) return 24;                           /* 太近：先远离，别自伤 */
        if(armorActive(v)) return dt >= 3 ? 300 : 230;   /* 对高甲目标：TNT 法术非常有效 */
        return dt >= 3 ? 250 : 190;
      }
      case 'tnt_place': {
        const self = p.hp + tempHpOf(p);
        let s = 140;
        if(self <= 2.5) s -= 60;
        if(self <= 1.5) s -= 50;
        if(p.ap >= 2) s += 20;
        return s;
      }
      case 'water': return (p.hp<=2)?100:64;
      case 'water_pull': return 46;
      case 'eat': return p.hp<=1.5?300:(p.hp<=2.5?200:(p.hp<3.5?110:24));
      case 'potion': return p.hp<=2.5?240:200;"""
if old_sc in t:
    t = t.replace(old_sc, new_sc, 1); changed.append('③ aiPick：TNT 距离 + 低血撤退 + 回血')
else:
    print('! ③ 锚点未匹配')

# ---------- ④ 打火石 / 腐肉 评分 ----------
old_d = """        const pierce = (k==='diamond_sword' && armorActive(e)) ? 1.5 : 0;
        const effDmg = pierce || Math.max(0, dmg - (armorActive(e)?Math.min(dmg,e.armorCharges):0));
        if(e.hp<=effDmg) return 320;                        /* 击杀 */
        let s = 60 + dmg*12;"""
new_d = """        const pierce = (k==='diamond_sword' && armorActive(e)) ? 1.5 : 0;
        const effDmg = pierce || Math.max(0, dmg - (armorActive(e)?Math.min(dmg,e.armorCharges):0));
        if(e.hp<=effDmg) return 320;                        /* 击杀 */
        /* 打火石：法术持续伤害，无视护甲 */
        if(k==='flint'){
          const ticks = armorHasAny(e) ? 2 : 3;
          let s = 84 + ticks * 18;
          if(armorActive(e)) s += 44;
          if(e.hp <= ticks * 0.5) s += 60;
          if(slotsPaid) s -= 12;
          return s;
        }
        /* 腐肉：法术伤害 + 流血 */
        if(k==='flesh'){
          let s = 66;
          if(armorActive(e)) s += 34;
          if(!e.effects.some(x=>x.type==='bleed')) s += 14;
          if(slotsPaid) s -= 10;
          return s;
        }
        let s = 60 + dmg*12;"""
if old_d in t:
    t = t.replace(old_d, new_d, 1); changed.append('④ 打火石/腐肉 评分')
else:
    print('! ④ 锚点未匹配')

# ---------- ⑤ aiShopChoice：更愿意做防具 / 囤面包 / 学打火石腐肉 ----------
old_arm = """    } else if(it.armor){
      if(armorActive(p)) continue;
      s = {leather:74, iron_armor:96, golem:100, diamond_armor:112}[k] || 50;
    } else {"""
new_arm = """    } else if(it.armor){
      if(armorActive(p)) continue;
      s = {leather:74, iron_armor:96, golem:100, diamond_armor:112}[k] || 50;
      if(p.hp<=3.5) s += 22;
      if(p.hp<=2.5) s += 30;
      if(!p.armor) s += 28;
      if(aliveEnemiesOf(p).some(e=>armorActive(e))) s += 14;
    } else {"""
if old_arm in t:
    t = t.replace(old_arm, new_arm, 1); changed.append('⑤ 更愿意做防具')
else:
    print('! ⑤ 锚点未匹配')

old_sup = """      else if(k==='bread') s = p.hp<3.5?74:30;
      else if(k==='flint') s = 68;"""
new_sup = """      else if(k==='bread') s = p.hp<3.5?150:(p.hp<3?120:26);
      else if(k==='flint') s = 84;
      else if(k==='flesh') s = 62;"""
if old_sup in t:
    t = t.replace(old_sup, new_sup, 1); changed.append('⑤ 囤面包/打火石/腐肉')
else:
    print('! ⑤ 补给锚点未匹配')

IDX.write_text(t, encoding='utf-8')

print('已应用：')
for c in changed: print('  ok', c)

# 校验
back = IDX.read_text(encoding='utf-8')
js = back.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk127.js'
tmp.write_text(js, encoding='utf-8')
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print()
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
print('文件: %.0f KB' % (len(back) / 1024))
