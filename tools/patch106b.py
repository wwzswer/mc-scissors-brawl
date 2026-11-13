# -*- coding: utf-8 -*-
"""补丁 106b（重做）：三项修复
   ① 面包/金苹果使用未扣 AP —— eat 分支没设置 itemCost
   ② 腐肉命中：伤害改为回合末结算（不再当回合立即扣）
   ③ 打火石重复点燃不再叠加 —— 只刷新剩余回合
"""
import pathlib, sys

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
orig_len = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ① 面包 / 金苹果扣 AP
ok1 = sub("""    case 'eat': {
      const item=a.item||'bread';
      if(!hasItem(p,item)){ log(`${lname(p)} 没有 ${SPECIALS[item]?SPECIALS[item].name:item}。`,'l-warn'); break; }
      removeItem(p,item);""",
"""    case 'eat': {
      const item=a.item||'bread';
      if(!hasItem(p,item)){ log(`${lname(p)} 没有 ${SPECIALS[item]?SPECIALS[item].name:item}。`,'l-warn'); break; }
      if(p.ap < CONSUME_COST){ log(`${lname(p)} 行动点不足，无法使用（需 ${CONSUME_COST} AP）。`,'l-warn'); break; }
      itemCost = CONSUME_COST;              /* 面包 / 金苹果：各 1 AP */
      removeItem(p,item);""", '① 面包/金苹果扣 1 AP')

# ② 腐肉：当回合不立即扣血
ok2 = sub("""      const dmgTotal = dmg.reduce((a,b)=>a+b,0);
      if(dmgTotal<=0 && prof.burnTicks>0){
        /* 纯点火类（打火石）：本身无直接伤害，不要打印“未造成伤害”以免误会 */
        log(`✅ ${nm} 命中 ${lname(victim)}（无直接伤害，效果见下）。`,'l-sys');
      } else {
        tryDamage(victim, dmg, { label: nm });
      }""",
"""      const dmgTotal = dmg.reduce((a,b)=>a+b,0);
      if(key==='flesh' && suit===1){
        /* 腐肉：当回合不立即扣血，伤害放到回合末结算（与流血同一结算点） */
        log(`✅ ${nm} 命中 ${lname(victim)}（伤害在回合末结算）。`,'l-sys');
      } else if(dmgTotal<=0 && prof.burnTicks>0){
        /* 纯点火类（打火石）：本身无直接伤害，不要打印“未造成伤害”以免误会 */
        log(`✅ ${nm} 命中 ${lname(victim)}（无直接伤害，效果见下）。`,'l-sys');
      } else {
        tryDamage(victim, dmg, { label: nm });
      }""", '② 腐肉伤害延后')

# ②b 腐肉流血措辞
sub("""        addEffect(target,'bleed',1,2,'流血');
        log(`🥩 ${lname(target)} 开始【流血】：下回合结束时再受 0.5 伤害。`,'l-warn');""",
"""        addEffect(target,'bleed',1,2,'流血');
        log(`🥩 ${lname(target)} 开始【流血】：本回合末与下回合末各结算 0.5 伤害。`,'l-warn');""",
'②b 流血措辞')

# ③ 打火石重复点燃不叠加
ok3 = sub("""      if(key==='flint'){
        const rounds = armorHasAny(target) ? 2 : 3;      /* 有护甲：只持续 2 回合 */
        addEffect(target,'burn',1,rounds,'火焰');         /* 每回合 1 次，持续 rounds 回合 */
        log(`🔥 点燃成功：${lname(target)} 接下来 <b>${rounds} 个回合</b>每回合结束各结算 1 次 0.5 火焰伤害（入水可扑灭）。`,'l-warn');
      } else {""",
"""      if(key==='flint'){
        const rounds = armorHasAny(target) ? 2 : 3;      /* 有护甲：只持续 2 回合 */
        const ex = target.effects.find(e=>e.type==='burn');
        if(ex){
          /* 已经在燃烧：只刷新剩余回合，不叠加每回合次数（避免某回合掉两次） */
          ex.power = 1;
          ex.rounds = Math.max(ex.rounds||0, rounds);
          log(`🔥 目标已在燃烧：刷新为剩余 <b>${ex.rounds} 个回合</b>（每回合仍是 1 次 0.5，不叠加）。`,'l-warn');
        } else {
          addEffect(target,'burn',1,rounds,'火焰');       /* 每回合 1 次，持续 rounds 回合 */
          log(`🔥 点燃成功：${lname(target)} 接下来 <b>${rounds} 个回合</b>每回合结束各结算 1 次 0.5 火焰伤害（入水可扑灭）。`,'l-warn');
        }
      } else {""", '③ 打火石不叠加')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))

# 落盘校验
back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  文件长度 {orig_len} → {len(back)}（写入 +{len(back)-orig_len}）')
print('  ① 面包扣 AP:', 'itemCost = CONSUME_COST;              /* 面包' in back)
print('  ② 腐肉延后:', '伤害在回合末结算' in back)
print('  ③ 打火石不叠加:', '目标已在燃烧' in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
