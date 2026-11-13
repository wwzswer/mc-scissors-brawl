# -*- coding: utf-8 -*-
"""补丁 106：按用户反馈修正
   ① 面包/金苹果使用未扣 AP —— eat 分支没设置 itemCost
   ② 腐肉命中：伤害改为回合末结算（不再当回合立即扣），流血按回合结算
   ③ 打火石重复点燃会叠加导致「某回合掉两次」——改为取更长剩余回合，不叠加次数
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

# ① 面包 / 金苹果扣 AP
sub("""    case 'eat': {
      const item=a.item||'bread';
      if(!hasItem(p,item)){ log(`${lname(p)} 没有 ${SPECIALS[item]?SPECIALS[item].name:item}。`,'l-warn'); break; }
      removeItem(p,item);""",
"""    case 'eat': {
      const item=a.item||'bread';
      if(!hasItem(p,item)){ log(`${lname(p)} 没有 ${SPECIALS[item]?SPECIALS[item].name:item}。`,'l-warn'); break; }
      if(p.ap < CONSUME_COST){ log(`${lname(p)} 行动点不足，无法使用（需 ${CONSUME_COST} AP）。`,'l-warn'); break; }
      itemCost = CONSUME_COST;              /* 面包 / 金苹果：各 1 AP */
      removeItem(p,item);""", '面包/金苹果扣 1 AP')

# ② 腐肉：当回合不立即结算，改为回合末（复用 burn 通道但标签为流血）
sub("""      const dmg = prof.dmg.map(x=>rm(x*suit));
      const nm = ITEMS[key] ? ITEMS[key].name : (opts.label||'攻击');
      const dmgTotal = dmg.reduce((a,b)=>a+b,0);
      if(dmgTotal<=0 && prof.burnTicks>0){
        /* 纯点火类（打火石）：本身无直接伤害，不要打印“未造成伤害”以免误会 */
        log(`✅ ${nm} 命中 ${lname(victim)}（无直接伤害，效果见下）。`,'l-sys');
      } else {
        tryDamage(victim, dmg, { label: nm });
      }""",
"""      const dmg = prof.dmg.map(x=>rm(x*suit));
      const nm = ITEMS[key] ? ITEMS[key].name : (opts.label||'攻击');
      const dmgTotal = dmg.reduce((a,b)=>a+b,0);
      if(key==='flesh' && suit===1){
        /* 腐肉：当回合不立即扣血，伤害放到回合末结算（与流血同一通道） */
        log(`✅ ${nm} 命中 ${lname(victim)}（伤害在回合末结算）。`,'l-sys');
      } else if(dmgTotal<=0 && prof.burnTicks>0){
        /* 纯点火类（打火石）：本身无直接伤害，不要打印“未造成伤害”以免误会 */
        log(`✅ ${nm} 命中 ${lname(victim)}（无直接伤害，效果见下）。`,'l-sys');
      } else {
        tryDamage(victim, dmg, { label: nm });
      }""", '腐肉伤害延后')

# 腐肉：改为流血持续 2 回合（当回合末 + 下回合末各 0.5）
sub("""    /* 腐肉流血 */
    if(key==='flesh' && target.alive){
      if(armorActive(target)){
        log(`（目标有防具：腐肉只造成 0.5 物理伤害，不产生流血）`,'l-sys');
      } else {
        addEffect(target,'bleed',1,2,'流血');
        log(`🥩 ${lname(target)} 开始【流血】：下回合结束时再受 0.5 伤害。`,'l-warn');
      }
    }""",
"""    /* 腐肉流血：当回合末与下回合末各结算 0.5（共 2 次） */
    if(key==='flesh' && target.alive){
      if(armorActive(target)){
        log(`（目标有防具：腐肉只造成 0.5 伤害，不产生流血）`,'l-sys');
      } else {
        addEffect(target,'bleed',1,2,'流血');
        log(`🥩 ${lname(target)} 开始【流血】：本回合末与下回合末各再受 0.5 伤害。`,'l-warn');
      }
    }""", '腐肉流血说明')

# ③ 打火石重复点燃：取更长剩余回合，不叠加每回合次数
sub("""      if(key==='flint'){
        const rounds = armorHasAny(target) ? 2 : 3;      /* 有护甲：只持续 2 回合 */
        addEffect(target,'burn',1,rounds,'火焰');         /* 每回合 1 次，持续 rounds 回合 */
        log(`🔥 点燃成功：${lname(target)} 接下来 <b>${rounds} 个回合</b>每回合结束各结算 1 次 0.5 火焰伤害（入水可扑灭）。`,'l-warn');
      } else {""",
"""      if(key==='flint'){
        const rounds = armorHasAny(target) ? 2 : 3;      /* 有护甲：只持续 2 回合 */
        const ex = target.effects.find(e=>e.type==='burn');
        if(ex){
          /* 已经着火：只刷新剩余回合，不叠加每回合次数（避免某回合掉两次） */
          ex.power = 1;
          ex.rounds = Math.max(ex.rounds||0, rounds);
          log(`🔥 目标已在燃烧：刷新为剩余 <b>${ex.rounds} 个回合</b>（每回合仍是 1 次 0.5，不叠加）。`,'l-warn');
        } else {
          addEffect(target,'burn',1,rounds,'火焰');       /* 每回合 1 次，持续 rounds 回合 */
          log(`🔥 点燃成功：${lname(target)} 接下来 <b>${rounds} 个回合</b>每回合结束各结算 1 次 0.5 火焰伤害（入水可扑灭）。`,'l-warn');
        }
      } else {""", '打火石不叠加')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
