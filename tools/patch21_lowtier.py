# -*- coding: utf-8 -*-
"""补丁 21：修复「升级后无法再获取低级物品」
   把「只显示当前进程的物品」改为「显示当前进程及以下的物品」。
   受影响的 4 处：aiShopChoice / 商店面板 / aiOptions / buildHumanOptions。
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

pairs = [
    # ai.ShopChoice
    ("""    const it=ITEMS[k];
    if(it.prog!==p.prog || p.ap<it.cost) continue;
    if(it.build){ if(!buildAllowed(p,k)) continue; }""",
     """    const it=ITEMS[k];
    if(it.prog>p.prog || p.ap<it.cost) continue;     /* 当前进程及以下的物品都能做 */
    if(it.build){ if(!buildAllowed(p,k)) continue; }"""),
    # 商店面板
    ("""        const it=ITEMS[k];
        if(it.prog!==p.prog) continue;
        if(it.build){ if(!buildAllowed(p,k)) continue; }""",
     """        const it=ITEMS[k];
        if(it.prog>p.prog) continue;                 /* 低级物品升级后依然可做（如腐肉） */
        if(it.build){ if(!buildAllowed(p,k)) continue; }"""),
    # aiOptions
    ("""      const it=ITEMS[k];
      if(it.prog!==p.prog) continue;
      if(it.build){ if(!buildAllowed(p,k)) continue; }""",
     """      const it=ITEMS[k];
      if(it.prog>p.prog) continue;
      if(it.build){ if(!buildAllowed(p,k)) continue; }"""),
    # buildHumanOptions
    ("""      const it=ITEMS[k];
      if(it.prog!==p.prog) continue;
      if(it.build){ if(!buildAllowed(p,k)) continue; }
      else if(!it.repeat && hasItem(p,k)) continue;
      if(it.need && !hasItem(p,it.need)) continue;
      push({type:'craftShopItem', key:k, cost:it.cost, isAction:false, label:`🛠️ 制作 ${it.name}（${it.cost} 步）`});""",
     """      const it=ITEMS[k];
      if(it.prog>p.prog) continue;                 /* 已解锁的进程物品永久可用 */
      if(it.build){ if(!buildAllowed(p,k)) continue; }
      else if(!it.repeat && hasItem(p,k)) continue;
      if(it.need && !hasItem(p,it.need)) continue;
      push({type:'craftShopItem', key:k, cost:it.cost, isAction:false, label:`🛠️ 制作 ${it.name}（${it.cost} 步）`});"""),
]
n = 0
for a, b in pairs:
    if a in t:
        t = t.replace(a, b, 1); n += 1
    else:
        print('  ! 未匹配:', a.strip().split('\n')[0][:60])
print(f'已替换 {n}/4 处')

# 商店面板加一句说明
t = t.replace("""  const grid=document.createElement('div'); grid.className='shopgrid'; box.appendChild(grid);""",
"""  const grid=document.createElement('div'); grid.className='shopgrid'; box.appendChild(grid);
  const tip=document.createElement('div');
  tip.style.cssText='font-size:11.5px;color:var(--dim);margin:6px 0 2px';
  tip.textContent='提示：已解锁进程的物品随时都能再做（升级后腐肉、木剑等不会消失）。';
  box.appendChild(tip);""", 1)

IDX.write_text(t, encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
