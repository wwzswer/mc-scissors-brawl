# -*- coding: utf-8 -*-
"""补丁 69：craft 护甲走 gainArmor；breakArmor 同步 armors 数组"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# craft 里的护甲装备：走 gainArmor（支持储备多件）
sub("""    if(it.armor){ p.armor=k; p.armorCharges=it.armor; }""",
"""    if(it.armor){ gainArmor(p, k); }        /* 进入护甲储备，并按优先级选出生效的那件 */""",
'craft 护甲走 gainArmor')

# breakArmor：把 armors 里对应件的耐久清零，并重新选出生效护甲
sub("""function breakArmor(p){
  const e = p.ench[p.armor];
  if(e){ delete p.ench[p.armor]; log(`${lname(p)} 的护甲破损，附魔【${ENCH[e].name}】随之失效（修复后需重新附魔）。`,'l-warn'); }
  p.armorCharges = 0;
}""",
"""function breakArmor(p){
  const e = p.ench[p.armor];
  if(e){ delete p.ench[p.armor]; log(`${lname(p)} 的护甲破损，附魔【${ENCH[e].name}】随之失效（修复后需重新附魔）。`,'l-warn'); }
  /* 同步储备数组：该件耐久清零，然后换下一件可用的 */
  if(p.armors){
    const a = p.armors.find(x=>x.key===p.armor);
    if(a) a.charges = 0;
  }
  p.armorCharges = 0;
  if(p.armors && p.armors.some(a=>a.charges>0)) equipBest(p);
}""", 'breakArmor 同步 armors')

# repair：修复时同步 armors
sub("""      p.armorCharges = armorMax(p);""",
"""      p.armorCharges = armorMax(p);
      if(p.armors){ const a = p.armors.find(x=>x.key===p.armor); if(a) a.charges = a.max; equipBest(p); }""",
'repair 同步 armors')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
