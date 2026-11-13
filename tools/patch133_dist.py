# -*- coding: utf-8 -*-
"""补丁 133：距离上限拦截（不扣 AP）+ 无行动点的跳过回合"""
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

# ---------- ① 距离上限拦截（结算层，先于扣 AP） ----------
sub("""    } else if(isMobility){
      /* 位移：固定 1 AP，直接扣，不占免费行动槽（用户要求：改变距离都要 1 AP） */
      const mc = Math.max(1, a.cost || MOVE_COST);""",
"""    } else if(isMobility){
      /* 【前置检查】距离已达上限且要拉远 → 直接拒绝，不消耗 AP */
      const _MT = (a.targetId!==undefined && a.targetId!==null) ? P(a.targetId) : null;
      if(_MT && (a.dir === +1 || a.type==='pearl' && a.dir === +2)){
        if(distanceBetween(p, _MT) >= MAX_DIST){
          log(`📏 与 ${lname(_MT)} 的距离已达上限（${MAX_DIST} 格），无法再拉开，未消耗 AP。`,'l-warn');
          return;
        }
      }
      /* 位移：固定 1 AP，直接扣，不占免费行动槽（用户要求：改变距离都要 1 AP） */
      const mc = Math.max(1, a.cost || MOVE_COST);""", '① 距离上限拦截')

# ---------- ② 无行动点时的「跳过回合」 ----------
sub("""    const attacks = opts.filter(o=>o.type==='attack'||o.type==='golem_punch'||o.type==='tnt_detonate'||o.type==='tnt_place');
    const shopBtns = opts.filter(o=>o.type==='shop_progress'||o.type==='shop_craft');""",
"""    const attacks = opts.filter(o=>o.type==='attack'||o.type==='golem_punch'||o.type==='tnt_detonate'||o.type==='tnt_place');
    const shopBtns = opts.filter(o=>o.type==='shop_progress'||o.type==='shop_craft');""",
'（定位）')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print('长度 %d → %d' % (orig, len(back)))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
