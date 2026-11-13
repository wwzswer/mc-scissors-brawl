# -*- coding: utf-8 -*-
"""补丁 100：打火石改为「每回合结算 1 次、持续 3 回合」
   现状：addEffect(burn, 3, 99) → 同一回合结算 3 次
   改为：power=每回合次数(1)，rounds=持续回合数(3，有护甲 2)，
        回合末结算 power 次并递减 rounds，归零才移除
   入水：把剩余回合数设为 0（取消后续所有跳）
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

# ① 点燃处：打火石 = 每回合 1 次 × 3 回合
sub("""    /* 点燃：本回合不立即扣血，效果次数留到回合结束统一结算（入水可取消） */
    if(prof.burnTicks>0 && target.alive){
      const ticks = (key==='flint' && armorHasAny(target)) ? 2 : prof.burnTicks;
      addEffect(target,'burn',ticks,99,'火焰');
      log(`🔥 ${lname(target)} 被点燃：将在本回合所有玩家行动结束后结算 ${ticks} 次 0.5 火焰伤害（此时入水可取消）。`,'l-warn');
    }""",
"""    /* 点燃：打火石 = 持续若干回合的点燃（每回合末结算 1 次）；
       其它火焰来源（火焰附加/引雷/烟花）仍是当回合结算完 burnTicks 次 */
    if(prof.burnTicks>0 && target.alive){
      if(key==='flint'){
        const rounds = armorHasAny(target) ? 2 : 3;      /* 有护甲：只持续 2 回合 */
        addEffect(target,'burn',1,rounds,'火焰');         /* 每回合 1 次，持续 rounds 回合 */
        log(`🔥 ${lname(target)} 被点燃：接下来 <b>${rounds} 个回合</b>每回合结束各结算 1 次 0.5 火焰伤害（入水可扑灭）。`,'l-warn');
      } else {
        addEffect(target,'burn',prof.burnTicks,1,'火焰');
        log(`🔥 ${lname(target)} 被点燃：本回合结束结算 ${prof.burnTicks} 次 0.5 火焰伤害（此时入水可取消）。`,'l-warn');
      }
    }""", '打火石持续点燃')

# ② 回合末结算：每回合结算 power 次，递减 rounds，归零移除
sub("""    /* 火焰：统一在回合结束结算；层数 = 待结算次数（入水会把它设为 0） */
    const burn = p.effects.find(e=>e.type==='burn');
    if(burn && burn.power > 0 && !p.inWater){
      log(`🔥 ${lname(p)} 的火焰结算（${burn.power} 次）。`,'l-warn');
      for(let i=0;i<burn.power && p.alive;i++) await tryDamage(p,[0,0,0.5,0],{label:'火焰持续伤害'});
    }
    if(burn){ burn.power = 0; p.effects = p.effects.filter(e=>e!==burn); }""",
"""    /* 火焰：每回合结束结算 power 次；rounds = 还能持续几个回合，归零才熄灭
       （打火石：power=1, rounds=3 → 每回合 0.5，共 3 个回合） */
    const burn = p.effects.find(e=>e.type==='burn');
    if(burn && burn.power > 0 && (burn.rounds||1) > 0 && !p.inWater){
      log(`🔥 ${lname(p)} 的火焰结算（${burn.power} 次，剩余 ${burn.rounds} 回合）。`,'l-warn');
      for(let i=0;i<burn.power && p.alive;i++) await tryDamage(p,[0,0,0.5,0],{label:'火焰持续伤害'});
      burn.rounds = (burn.rounds||1) - 1;
    }
    if(burn && (burn.rounds||0) <= 0) p.effects = p.effects.filter(e=>e!==burn);""",
'火焰按回合持续')

# ③ 入水：把剩余回合设为 0（扑灭）
sub("""function removeBurn(p){
  const had = p.effects.some(e=>e.type==='burn'||e.type==='bleed');
  for(const e of p.effects) if(e.type==='burn') e.power = 0;      /* 剩余次数置 0：本回合不再结算 */""",
"""function removeBurn(p){
  const had = p.effects.some(e=>e.type==='burn'||e.type==='bleed');
  for(const e of p.effects) if(e.type==='burn'){ e.power = 0; e.rounds = 0; }   /* 入水直接扑灭 */""",
'入水扑灭')

# ④ 效果展示：显示剩余回合
sub("""    if(e.type==='burn') return `<span class="pill fire">🔥 火焰 ${e.power}</span>`;""",
"""    if(e.type==='burn') return `<span class="pill fire">🔥 火焰 ${e.power}×${e.rounds||1}回合</span>`;""",
'火焰效果显示')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
