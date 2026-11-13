# -*- coding: utf-8 -*-
"""补丁 113c：补齐 药水 / 女巫小屋 / 府邸 / 金字塔选项 的门控"""
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

# 药水选项（人类）
sub("""    if(hasItem(p,'potion_heal'))  push({type:'potion',item:'potion_heal',cost:0,label:'🧪 治疗药水（+2 血）'});
    if(hasItem(p,'potion_str'))   push({type:'potion',item:'potion_str',cost:0,label:'🧪 力量药水（2 回合物理 +1）'});
    if(hasItem(p,'potion_swift')) push({type:'potion',item:'potion_swift',cost:0,label:'🧪 迅捷药水（+2 AP）'});""",
"""    if(featOn('potion')){
      if(hasItem(p,'potion_heal'))  push({type:'potion',item:'potion_heal',cost:0,label:'🧪 治疗药水（+2 血）'});
      if(hasItem(p,'potion_str'))   push({type:'potion',item:'potion_str',cost:0,label:'🧪 力量药水（2 回合物理 +1）'});
      if(hasItem(p,'potion_swift')) push({type:'potion',item:'potion_swift',cost:0,label:'🧪 迅捷药水（+2 AP）'});
    }""", '药水选项门控（人类）')

# 药水选项（AI）
sub("""    if(hasItem(p,'potion_heal') && p.hp<=2) push({type:'potion',item:'potion_heal',cost:0,label:'治疗药水'});
    if(hasItem(p,'potion_str')) push({type:'potion',item:'potion_str',cost:0,label:'力量药水'});
    if(hasItem(p,'potion_swift') && p.slotsLeft<=0 && p.ap<=1) push({type:'potion',item:'potion_swift',cost:0,label:'迅捷药水'});""",
"""    if(featOn('potion')){
      if(hasItem(p,'potion_heal') && p.hp<=2) push({type:'potion',item:'potion_heal',cost:0,label:'治疗药水'});
      if(hasItem(p,'potion_str')) push({type:'potion',item:'potion_str',cost:0,label:'力量药水'});
      if(hasItem(p,'potion_swift') && p.slotsLeft<=0 && p.ap<=1) push({type:'potion',item:'potion_swift',cost:0,label:'迅捷药水'});
    }""", '药水选项门控（AI）')

# 女巫小屋（药水来源）
sub("""      if(k==='witchhut'){""",
"""      if(k==='witchhut'){
        if(!featOn('potion')){ log('（药水已在设置中禁用）','l-sys'); }""", '女巫小屋门控')

# 府邸（不死图腾来源）
sub("""      if(k==='mansion'){""",
"""      if(k==='mansion'){
        if(!featOn('totem')){ log('（不死图腾已在设置中禁用）','l-sys'); }""", '府邸门控')

# 金字塔选项
sub("""    if(p.buildings.pyramid && p.ap>=1){""",
"""    if(p.buildings.pyramid && p.ap>=1 && (featOn('tnt') || featOn('god_apple'))){""",
'金字塔选项门控')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))

back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  长度 {orig} → {len(back)}（+{len(back)-orig}）')
print("  featOn('potion') 出现次数:", back.count("featOn('potion')"))
print("  featOn('totem') 出现次数:", back.count("featOn('totem')"))
print("  featOn('tnt') 出现次数:", back.count("featOn('tnt')"))
print("  featOn('god_apple') 出现次数:", back.count("featOn('god_apple')"))
print("  金字塔选项门控:", "featOn('tnt') || featOn('god_apple')" in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
