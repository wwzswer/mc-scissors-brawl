# -*- coding: utf-8 -*-
"""补丁 78：把腐肉转法术的代码移到 dmg 声明之后（上次插在声明前，等于没生效）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

# 1) 删除插错位置的代码
wrong = """  /* 腐肉：伤害转为法术类型（名字与流血效果不变） */
  if(key==='flesh' && dmg && dmg[0]>0){ dmg[2]=rm((dmg[2]||0)+dmg[0]); dmg[0]=0; }
"""
if wrong in t:
    t = t.replace(wrong, '', 1)
    print('已移除错位代码')
else:
    print('! 未找到错位代码')

# 2) 插到 let dmg = base.slice(); 之后
anchor = """  let dmg = base.slice();
  const e = attacker.ench[attacker.weapon];"""
inject = """  let dmg = base.slice();
  /* 腐肉：伤害类型转为法术（名字与流血效果不变） */
  if(key==='flesh' && dmg[0]>0){ dmg[2]=rm(dmg[2]+dmg[0]); dmg[0]=0; }
  const e = attacker.ench[attacker.weapon];"""
if anchor in t:
    t = t.replace(anchor, inject, 1)
    print('已插入到 dmg 声明之后')
else:
    print('! 未找到 dmg 声明锚点')

IDX.write_text(t, encoding='utf-8')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
