# -*- coding: utf-8 -*-
"""补丁 87：攻击时自动装备所选武器（保证附魔/面板一致；道具不替换武器）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

old = """    case 'attack': {
      if(!T || !T.alive){ log('目标已无法被攻击。','l-warn'); break; }
      const key=a.key;
      const ranged = !!a.ranged;"""
new = """    case 'attack': {
      if(!T || !T.alive){ log('目标已无法被攻击。','l-warn'); break; }
      const key=a.key;
      /* 用背包里的武器出手时自动装备它：这样附魔、面板显示都与实际一致 */
      if(key && !THROWABLE_KEYS.includes(key) && hasItem(p, key) && p.weapon !== key){
        p.weapon = key;
        log(`🖐 ${lname(p)} 换上 ${ITEMS[key] ? ITEMS[key].name : '空手'}。`,'l-sys');
      }
      const ranged = !!a.ranged;"""

if old in t:
    t = t.replace(old, new, 1)
    IDX.write_text(t, encoding='utf-8')
    print('已加入攻击自动装备')
else:
    print('! 锚点未匹配')

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
