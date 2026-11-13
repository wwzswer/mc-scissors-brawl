# -*- coding: utf-8 -*-
"""补丁 79：位移类统一“固定 1 AP，不占免费行动槽”
   之前误加入 isFree 导致位移完全不扣 AP，现在改为明确扣费。
   范围：move / rod / pearl / water_pull / rod_water / fish_trident
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

# 1) 从 isFree 里移除位移类
sub("""  /* 位移类：每次固定 1 AP（由 cost 扣），不再额外占用免费行动槽 */
  const isFree = ['switch_weapon','pearl','pass','golem_punch','armor_priority','move','rod','water_pull','fish_trident'].includes(a.type);""",
"""  /* 免费即时动作：不占行动次数、也不花 AP */
  const isFree = ['switch_weapon','armor_priority','pass','golem_punch'].includes(a.type);
  /* 位移类：固定 1 AP（MOVE_COST），不占用免费行动槽 */
  const isMobility = ['move','rod','pearl','water_pull','rod_water','fish_trident'].includes(a.type);""",
'分离 isFree / isMobility')

# 2) 扣费逻辑加入位移分支
sub("""  } else if(a.type!=='pass' && a.isAction!==false && !isPurchase && !isFree){
    if(p.slotsLeft>0) p.slotsLeft--;
    else if(actionSlotCost(p)===1){ p.ap-=1; log(`（额外行动 -1 AP）`,'l-sys'); }
    else { log(`${lname(p)} 行动点不足，无法行动。`,'l-warn'); return; }
    p.actionsUsed++; p.turnSpent=(p.turnSpent||0)+1;
  }""",
"""  } else if(isMobility){
    /* 位移：固定 1 AP，直接扣，不占免费行动槽（用户要求：改变距离都要 1 AP） */
    const mc = Math.max(1, a.cost || MOVE_COST);
    if(p.ap < mc){ log(`${lname(p)} 行动点不足，无法移动（需 ${mc} AP）。`,'l-warn'); return; }
    p.ap -= mc;
    p.actionsUsed++; p.turnSpent=(p.turnSpent||0)+1;
    log(`📏 移动消耗 ${mc} AP（剩余 ${p.ap}）`,'l-sys');
  } else if(a.type!=='pass' && a.isAction!==false && !isPurchase && !isFree){
    if(p.slotsLeft>0) p.slotsLeft--;
    else if(actionSlotCost(p)===1){ p.ap-=1; log(`（额外行动 -1 AP）`,'l-sys'); }
    else { log(`${lname(p)} 行动点不足，无法行动。`,'l-warn'); return; }
    p.actionsUsed++; p.turnSpent=(p.turnSpent||0)+1;
  }""", '位移扣 1 AP')

# 3) 位移选项标记为非“行动槽”动作（isAction:false 只影响 UI 显示与 canPay，不绕过上面的扣费）
sub("""      push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,label:`👣 靠近 ${e.name} 1 格（${MOVE_COST} AP，近战需 0 格）`});
      if(d<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:`👣 后退，与 ${e.name} 拉开 1 格（${MOVE_COST} AP）`});""",
"""      push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,isAction:false,label:`👣 靠近 ${e.name} 1 格（${MOVE_COST} AP，近战需 0 格）`});
      if(d<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,isAction:false,label:`👣 后退，与 ${e.name} 拉开 1 格（${MOVE_COST} AP）`});""",
'move 标记 isAction:false（人类）')

sub("""    if(d>=1) push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,label:'靠近 '+e.name+(hasRanged?'':'（必须靠近才能攻击）')});
    if(d<=1 && p.hp<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:'后退拉开距离'});""",
"""    if(d>=1) push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,isAction:false,label:'靠近 '+e.name+(hasRanged?'':'（必须靠近才能攻击）')});
    if(d<=1 && p.hp<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,isAction:false,label:'后退拉开距离'});""",
'move 标记 isAction:false（AI）')

# 4) 钓鱼竿选项也标 isAction:false（保持与 move 一致）
t = t.replace("push({type:'rod',targetId:e.id,dir:-1,cost:ROD_COST,label:",
              "push({type:'rod',targetId:e.id,dir:-1,cost:ROD_COST,isAction:false,label:")
t = t.replace("push({type:'rod',targetId:e.id,dir:+1,cost:ROD_COST,label:",
              "push({type:'rod',targetId:e.id,dir:+1,cost:ROD_COST,isAction:false,label:")
notes.append('  ok 钓鱼竿标记 isAction:false')

# 5) 钓三叉戟选项文案：说明 3 点进度
sub("""push({type:'fish_trident',cost:ROD_COST,label:`🔱 钓鱼竿：钓得三叉戟（${ROD_COST} AP）`});""",
"""push({type:'fish_trident',cost:ROD_COST,isAction:false,label:`🔱 钓鱼竿：钓得三叉戟（${ROD_COST} AP）`});""",
'钓三叉戟标记')

# 6) 修正 fish_trident 的日志文案（不是"花费 3 步"）
sub("""      log(`🔱 ${lname(p)} 花费 3 步钓得了 <b>三叉戟</b>！`,'l-good'); sfx.win(); break;""",
"""      log(`🔱 ${lname(p)} 用钓鱼竿钓得了 <b>三叉戟</b>！`,'l-good'); try{ sfx.win(); }catch(e){} break;""",
'钓三叉戟文案')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
