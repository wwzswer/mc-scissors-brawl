# -*- coding: utf-8 -*-
"""补丁 132：v1.5.2 剩余项
   ② 1v1 模式：取消「是否消耗 AP 进行判定」选择
   ③ 无行动点时提供「跳过回合」选项（设置里可开启自动跳过）
   ④ 距离已达上限时给出提示
   ⑤ 版本号 → v1.5.2
"""
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

# ---------- ② 1v1 取消闪避询问 ----------
sub("""      else if(target.isHuman){ rlog('平局: 等待玩家选择闪避/赌一把…'); wantsDodge = await askDodge(target, attacker); rlog('平局: 玩家已选择 dodge=' + wantsDodge); }""",
"""      else if(target.isHuman){
        /* 1v1：只有你我两人，没有"赌一把"的空间 → 直接重新判定，不弹选择 */
        if(G.players.filter(q=>q.alive).length === 2){
          rlog('平局: 1v1 模式直接重新判定');
          wantsDodge = false;
        } else {
          rlog('平局: 等待玩家选择闪避/赌一把…');
          wantsDodge = await askDodge(target, attacker);
          rlog('平局: 玩家已选择 dodge=' + wantsDodge);
        }
      }""", '② 1v1 取消闪避询问')

# ---------- ④ 距离上限 ----------
sub("""    if(d>=1) push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,label:`👣 靠近 ${e.name} 1 格（1 AP，近战需 0 格）`});
    if(d<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:`👣 后退，与 ${e.name} 拉开 1 格（1 AP）`});""",
"""    if(d>=1) push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,label:`👣 靠近 ${e.name} 1 格（1 AP，近战需 0 格）`});
    if(d>=MAX_DIST) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,disabled:true,label:`📏 与 ${e.name} 已达最远距离（${MAX_DIST} 格）`});
    else if(d<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:`👣 后退，与 ${e.name} 拉开 1 格（1 AP）`});""",
'④ 人类距离上限提示')

sub("""    if(d>=1) push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,label:'靠近 '+e.name+(hasRanged?'':'（必须靠近才能攻击）')});
    if(d<=1 && p.hp<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:'后退拉开距离'});""",
"""    if(d>=1) push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,label:'靠近 '+e.name+(hasRanged?'':'（必须靠近才能攻击）')});
    if(d<MAX_DIST && d<=1 && p.hp<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:'后退拉开距离'});""",
'④ AI 距离上限')

# 按钮渲染支持 disabled
sub("""    const extra = (o.cost||0)+slot;
    const fixed = (extra===Infinity) ? '行动点不足' : (extra>0 ? `${extra} AP` : '免费');
    b.textContent = o.label + ' · ' + fixed;
    b.disabled = (extra===Infinity);""",
"""    const extra = (o.cost||0)+slot;
    const fixed = (extra===Infinity) ? '行动点不足' : (extra>0 ? `${extra} AP` : '免费');
    b.textContent = o.disabled ? o.label : (o.label + ' · ' + fixed);
    b.disabled = !!(o.disabled || extra===Infinity);""", '④ 按钮支持 disabled')

# ---------- ③ 无行动点时的「跳过回合」 ----------
sub("""    const attacks = opts.filter(o=>o.type==='attack'||o.type==='golem_punch'||o.type==='tnt_detonate'||o.type==='tnt_place');""",
"""    const attacks = opts.filter(o=>o.type==='attack'||o.type==='golem_punch'||o.type==='tnt_detonate'||o.type==='tnt_place');""",
'（定位，无改动）')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print('长度 %d → %d' % (orig, len(back)))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
