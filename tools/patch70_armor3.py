# -*- coding: utf-8 -*-
"""补丁 70：护甲系统收尾
   - 破损护甲一定保留在 armors 里（不会变成 null，铁砧可修）
   - 明确“当前生效护甲 = 优先级最高的未破损那件”
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

# equipBest 重写：破损留在身上，生效件取“优先级最高的未破损”
sub("""function equipBest(p){
  if(!p.armors || !p.armors.length){ p.armor=null; p.armorCharges=0; return; }
  const order = (p.armorPriority||[]).slice();
  const sorted = p.armors.slice().sort((a,b)=>{
    const ia = order.indexOf(a.key), ib = order.indexOf(b.key);
    return (ia<0?99:ia) - (ib<0?99:ib);
  });
  const pick = sorted.find(a=>a.charges>0) || sorted[0];
  p.armor = pick.key; p.armorCharges = pick.charges;
}""",
"""function equipBest(p){
  if(!p.armors || !p.armors.length){ p.armor=null; p.armorCharges=0; return; }
  const order = (p.armorPriority||[]).slice();
  const sorted = p.armors.slice().sort((a,b)=>{
    const ia = order.indexOf(a.key), ib = order.indexOf(b.key);
    return (ia<0?99:ia) - (ib<0?99:ib);
  });
  /* 生效件：优先级最高的“未破损”那件；全破损则保留优先最高的那件（便于铁砧修复） */
  const alive = sorted.filter(a=>a.charges>0);
  const pick = alive.length ? alive[0] : sorted[0];
  p.armor = pick.key; p.armorCharges = rm(pick.charges);
}""", 'equipBest 重写')

# 修复：按 key 修好对应那件
sub("""case 'repair':
      if(!p.armor) break;
      p.armorCharges=armorMax(p);
      if(p.armors){ const a = p.armors.find(x=>x.key===p.armor); if(a) a.charges = a.max; equipBest(p); }""",
"""case 'repair': {
      if(!p.armor) break;
      const piece = p.armors ? p.armors.find(x=>x.key===p.armor) : null;
      if(piece){ piece.charges = piece.max || armorMaxOf(piece.key); }
      p.armorCharges = armorMax(p);
      equipBest(p);""", 'repair 按件修复')

# 补上 repair 分支缺失的收尾大括号
sub("""      log(`🔨 ${lname(p)} 在铁砧上修复了 ${ITEMS[p.armor].name}（护甲恢复至 ${p.armorCharges}）。`,'l-good'); sfx.win();
      break;""",
"""      log(`🔨 ${lname(p)} 在铁砧上修复了 ${ITEMS[p.armor].name}（护甲恢复至 ${p.armorCharges}）。`,'l-good'); try{ sfx.win(); }catch(e){}
      break; }""", 'repair 大括号收尾')

# breakArmor：不清空 p.armor，只把对应件耐久置 0
sub("""function breakArmor(p){
  const e = p.ench[p.armor];
  if(e){ delete p.ench[p.armor]; log(`${lname(p)} 的护甲破损，附魔【${ENCH[e].name}】随之失效（修复后需重新附魔）。`,'l-warn'); }
  /* 同步储备数组：该件耐久清零，然后换下一件可用的 */
  if(p.armors){
    const a = p.armors.find(x=>x.key===p.armor);
    if(a) a.charges = 0;
  }
  p.armorCharges = 0;
  if(p.armors && p.armors.some(a=>a.charges>0)) equipBest(p);
}""",
"""function breakArmor(p){
  const brokenKey = p.armor;
  if(!brokenKey) return;
  const e = p.ench[brokenKey];
  if(e){ delete p.ench[brokenKey]; log(`${lname(p)} 的护甲破损，附魔【${ENCH[e].name}】随之失效（修复后需重新附魔）。`,'l-warn'); }
  if(!p.armors) p.armors = [];
  let piece = p.armors.find(x=>x.key===brokenKey);
  if(!piece){ piece = { key:brokenKey, charges:0, max:armorMaxOf(brokenKey) }; p.armors.push(piece); }
  piece.charges = 0;
  /* 换上下一件未破损的；若全破损则保留这件（可修） */
  equipBest(p);
}""", 'breakArmor 保留破损件')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
