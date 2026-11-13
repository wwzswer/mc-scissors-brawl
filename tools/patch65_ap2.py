# -*- coding: utf-8 -*-
"""补丁 65：金苹果 1 AP、面包（AI）1 AP、钓鱼竿位移 1 AP"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# 金苹果（人类/AI）→ 1 AP
sub("""if(hasItem(p,'god_apple')) push({type:'eat',item:'god_apple',targetId:p.id,cost:0,label:'🍎 吃附魔金苹果（+2 血 / 2 回合 +0.5 / 免疫）'});""",
"""if(hasItem(p,'god_apple')) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,label:`🍎 吃附魔金苹果（+2 血 / 2 回合 +0.5 / 免疫，${CONSUME_COST} AP）`});""",
'金苹果 1 AP（人类）')
sub("""if(hasItem(p,'god_apple') && p.hp<=2.5) push({type:'eat',item:'god_apple',targetId:p.id,cost:0,label:'金苹果'});""",
"""if(hasItem(p,'god_apple') && p.hp<=2.5) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,label:'金苹果'});""",
'金苹果 1 AP（AI）')
# 面包（AI）→ 1 AP
sub("""if(hasItem(p,'bread') && p.hp<=2.5) push({type:'eat',item:'bread',targetId:p.id,cost:1,label:'吃面包'});""",
"""if(hasItem(p,'bread') && p.hp<=2.5) push({type:'eat',item:'bread',targetId:p.id,cost:CONSUME_COST,label:'吃面包'});""",
'面包 1 AP（AI）')

# 钓鱼竿使他人位移 → 1 AP（原来是 2 步）
sub("""      push({type:'rod',targetId:e.id,dir:-1,cost:2,label:`🎣 钓鱼竿：拉近 ${e.name} 1 格（2 步）`});
      push({type:'rod',targetId:e.id,dir:+1,cost:2,label:`🎣 钓鱼竿：推远 ${e.name} 1 格（2 步）`});""",
"""      push({type:'rod',targetId:e.id,dir:-1,cost:ROD_COST,label:`🎣 钓鱼竿：拉近 ${e.name} 1 格（${ROD_COST} AP）`});
      push({type:'rod',targetId:e.id,dir:+1,cost:ROD_COST,label:`🎣 钓鱼竿：推远 ${e.name} 1 格（${ROD_COST} AP）`});""",
'钓鱼竿位移 1 AP（人类）')
sub("""    if(d>0 && d<=6) push({type:'rod',targetId:e.id,dir:-1,cost:2,label:'钓鱼竿拉近'});
    if(d===0) push({type:'rod',targetId:e.id,dir:1,cost:2,label:'钓鱼竿推远'});""",
"""    if(d>0 && d<=6) push({type:'rod',targetId:e.id,dir:-1,cost:ROD_COST,label:'钓鱼竿拉近'});
    if(d===0) push({type:'rod',targetId:e.id,dir:1,cost:ROD_COST,label:'钓鱼竿推远'});""",
'钓鱼竿位移 1 AP（AI）')

# 钓三叉戟（fish_trident）：也是钓鱼竿动作，统一 1 AP
sub("""push({type:'fish_trident',cost:3,label:'🔱 钓鱼竿：花费 3 步钓得三叉戟'});""",
"""push({type:'fish_trident',cost:ROD_COST,label:`🔱 钓鱼竿：钓得三叉戟（${ROD_COST} AP）`});""",
'钓三叉戟 1 AP（人类）')
sub("""push({type:'fish_trident',cost:3,label:'钓三叉戟'});""",
"""push({type:'fish_trident',cost:ROD_COST,label:'钓三叉戟'});""",
'钓三叉戟 1 AP（AI）')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
