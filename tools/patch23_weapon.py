# -*- coding: utf-8 -*-
"""补丁 23：补上 switchWeapon / heldWeapons（上次锚点未匹配）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

if 'function heldWeapons' in t:
    print('已存在，跳过')
else:
    anchors = [
        '/* ----------------------------- 距离 ----------------------------- */',
        '/* 统一动作模型',
        'function distanceBetween',
    ]
    block = """/* --- 切换手上的工具：持有多个武器时可自由更换，攻击用当前手上的那件 --- */
const WEAPON_KEYS = ['fist','flesh','wood_sword','stone_sword','iron_sword','diamond_sword','trident','crossbow','firework'];
function heldWeapons(p){
  return WEAPON_KEYS.filter(k=>hasItem(p,k) || (k==='fist'));
}
function switchWeapon(p, k){
  if(k && ITEMS[k] && k!==p.weapon) p.weapon = k;
  log(`🖐 ${lname(p)} 换上 <b>${ITEMS[p.weapon] ? ITEMS[p.weapon].name : '空手'}</b>。`,'l-sys');
  renderAll();
}

"""
    done = False
    for a in anchors:
        if a in t:
            t = t.replace(a, block + a, 1); done = True
            print('已插入到锚点:', a[:40]); break
    if not done:
        # 兜底：插到 renderPlayers 之前
        a = 'function gearIcons(p){'
        t = t.replace(a, block + a, 1); print('已插入（兜底锚点）')

# 装备行提示优化
t = t.replace("""  if(heldWeapons(p).length>1) out.push('<span style="color:var(--acc);font-size:11px"></span>');""",
              """  const ws = heldWeapons(p);
  if(ws.length>1) out.push(`<span style="color:var(--acc2);font-size:11px">（可换：${ws.filter(k=>k!==p.weapon).map(k=>ITEMS[k].name).join('/')}）</span>`);""", 1)

IDX.write_text(t, encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
