# -*- coding: utf-8 -*-
"""补丁 105：消除打火石的误导日志
   现象：判定命中后出现「打火石 未造成伤害」，紧接着又「被点燃」——看起来自相矛盾。
   原因：打火石物理伤害为 0，tryDamage 照常打印“未造成伤害”。
   修复：伤害为 0 但带点燃效果的攻击，跳过“未造成伤害”提示，改为明确的点燃说明。
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

# 1) 点火类攻击不再打印“未造成伤害”，改为“命中：点燃”
sub("""      const dmg = prof.dmg.map(x=>rm(x*suit));
      tryDamage(victim, dmg, { label: ITEMS[key] ? ITEMS[key].name : (opts.label||'攻击') });""",
"""      const dmg = prof.dmg.map(x=>rm(x*suit));
      const nm = ITEMS[key] ? ITEMS[key].name : (opts.label||'攻击');
      const dmgTotal = dmg.reduce((a,b)=>a+b,0);
      if(dmgTotal<=0 && prof.burnTicks>0){
        /* 纯点火类（打火石）：本身无直接伤害，不要打印“未造成伤害”以免误会 */
        log(`✅ ${nm} 命中 ${lname(victim)}（无直接伤害，效果见下）。`,'l-sys');
      } else {
        tryDamage(victim, dmg, { label: nm });
      }""", '点火类不打印未造成伤害')

# 2) 点燃日志措辞更明确：区分“判定命中后点燃”
sub("""        log(`🔥 ${lname(target)} 被点燃：接下来 <b>${rounds} 个回合</b>每回合结束各结算 1 次 0.5 火焰伤害（入水可扑灭）。`,'l-warn');""",
"""        log(`🔥 点燃成功：${lname(target)} 接下来 <b>${rounds} 个回合</b>每回合结束各结算 1 次 0.5 火焰伤害（入水可扑灭）。`,'l-warn');""",
'打火石点燃措辞')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
