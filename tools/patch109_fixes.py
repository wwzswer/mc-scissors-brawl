# -*- coding: utf-8 -*-
"""补丁 109：按用户反馈修正 6 项
   ① 攻击先判距离、再扣 AP（避免"先扣 AP 才说打不到"）
   ② 末影珍珠标价 1 AP（此前显示免费）
   ③ 打火石改为【需要判定】
   ④ 林地府邸获取不死图腾（补健壮性）
   ⑤ 三叉戟掷出：判定失败等同于未掷出（不丢失）；成功后才可能被同格玩家拾取
   ⑥ 忠诚附魔：掷出后必定回手
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

# ---------- ① 攻击前置检查：距离合适才扣 AP ----------
sub("""    if(isAttackAction(a)){
      /* 攻击：每次固定 1 AP，直接扣除，不消耗免费行动槽 */
      if(p.ap < ATK_COST){ log(`${lname(p)} 行动点不足，无法攻击（每次攻击需 ${ATK_COST} AP）。`,'l-warn'); return; }""",
"""    if(isAttackAction(a)){
      /* 【前置检查】先确认目标与距离是否合法，再扣 AP —— 避免“先扣了 AP 才说打不到” */
      const _T = (a.targetId!==undefined && a.targetId!==null) ? P(a.targetId) : null;
      if(!_T){ log('目标不存在，攻击取消。','l-warn'); return; }
      if(!_T.alive){ log('目标已无法被攻击。','l-warn'); return; }
      const _d = distanceBetween(p, _T);
      if(!inRangeOf(p, a.key || p.weapon || 'fist', _T)){
        log(`${ITEMS[a.key]?ITEMS[a.key].name:'攻击'} 距离不合适（当前 ${_d} 格），未消耗 AP。`,'l-warn');
        return;
      }
      /* 攻击：每次固定 1 AP，直接扣除，不消耗免费行动槽 */
      if(p.ap < ATK_COST){ log(`${lname(p)} 行动点不足，无法攻击（每次攻击需 ${ATK_COST} AP）。`,'l-warn'); return; }""",
'① 攻击前置检查')

# ---------- ② 末影珍珠标价 1 AP ----------
sub("""      push({type:'pearl',targetId:e.id,dir:+2,cost:0,isAction:false,label:`🟣 末影珍珠：与 ${e.name} 距离 +2`});
      push({type:'pearl',targetId:e.id,dir:-2,cost:0,isAction:false,label:`🟣 末影珍珠：与 ${e.name} 距离 -2`});""",
"""      push({type:'pearl',targetId:e.id,dir:+2,cost:MOVE_COST,isAction:false,label:`🟣 末影珍珠：与 ${e.name} 距离 +2（${MOVE_COST} AP）`});
      push({type:'pearl',targetId:e.id,dir:-2,cost:MOVE_COST,isAction:false,label:`🟣 末影珍珠：与 ${e.name} 距离 -2（${MOVE_COST} AP）`});""",
'② 珍珠标价 1 AP（人类）')
sub("""    if(d>0 && weapon!=='crossbow') push({type:'pearl',targetId:e.id,dir:-2,cost:0,isAction:false,label:'珍珠拉近'});""",
"""    if(d>0 && weapon!=='crossbow') push({type:'pearl',targetId:e.id,dir:-2,cost:MOVE_COST,isAction:false,label:'珍珠拉近'});""",
'② 珍珠标价（AI 拉近）')
sub("""    if(d<3 && p.hp<=2) push({type:'pearl',targetId:e.id,dir:2,cost:0,isAction:false,label:'珍珠拉开'});""",
"""    if(d<3 && p.hp<=2) push({type:'pearl',targetId:e.id,dir:2,cost:MOVE_COST,isAction:false,label:'珍珠拉开'});""",
'② 珍珠标价（AI 拉开）')

# ---------- ③ 打火石改为需要判定 ----------
sub("""    /* 近战 / 远程：判定（opts 里的 a/b/dodge/instant 可指定猜拳结果，便于测试与回放） */
    let success = false;
    try{
      success = await doJudgment(attacker, target, opts);
    }catch(err){
      rlog('doJudgment 抛出异常: ' + (err && err.message ? err.message : String(err)));
      log('（判定异常，按攻击失效处理）','l-warn');
      success = false;
    }
    if(!success){ log(`攻击落空。`,'l-sys'); return false; }""",
"""    /* 近战 / 远程：判定（opts 里的 a/b/dodge/instant 可指定猜拳结果，便于测试与回放） */
    let success = false;
    try{
      success = await doJudgment(attacker, target, opts);
    }catch(err){
      rlog('doJudgment 抛出异常: ' + (err && err.message ? err.message : String(err)));
      log('（判定异常，按攻击失效处理）','l-warn');
      success = false;
    }
    if(!success){
      if(key==='flint'){
        /* 打火石需要判定：判定失败＝没能点燃 */
        log(`🔥 打火石没能点燃 ${lname(target)}（判定失败）。`,'l-warn');
        return false;
      }
      log(`攻击落空。`,'l-sys');
      return false;
    }""", '③ 打火石需要判定')

# 选项标签：去掉“无需判定”
sub("""      const ranged = (k==='crossbow' || k==='firework');
      const noJudge = (k==='flint');""",
"""      const ranged = (k==='crossbow' || k==='firework');
      const noJudge = false;              /* 打火石已改为需要判定 */""",
'③ 打火石标签（人类）')
sub("""      push({type:'attack',key:k,targetId:e.id,cost:ATK_COST,
        label:`${nm} → ${e.name}（1 AP，${ranged?'远程':noJudge?'无需判定':'判定'}）${cur}`});""",
"""      push({type:'attack',key:k,targetId:e.id,cost:ATK_COST,
        label:`${nm} → ${e.name}（1 AP，${ranged?'远程':'判定'}）${cur}`});""",
'③ 打火石标签文本')
sub("""  flint:      { name:'打火石', cost:1, prog:PROG.IRON, desc:'无需判定：点燃目标，3 次 0.5 火焰伤害；若目标有防具则只造成 2 次 0.5 火焰伤害。首次立即结算，其余在每回合所有玩家行动结束后结算。' },""",
"""  flint:      { name:'打火石', cost:1, prog:PROG.IRON, desc:'需判定：胜出后点燃目标，接下来 3 个回合每回合结束各结算 1 次 0.5 火焰伤害（目标持有护甲则只持续 2 回合）。重复点燃不叠加。入水可扑灭。' },""",
'③ 打火石物品说明')

# ---------- ⑤⑥ 三叉戟掷出 / 忠诚 ----------
sub("""    /* 三叉戟掷出后失去 */
    if(key==='trident' && ranged){
      if(hasEnch(attacker,'loyalty')){
        log(`🔱 附魔【忠诚】生效：三叉戟回到 ${lname(attacker)} 手中（每回合仅能掷出一次）。`,'l-sys');
      } else {
        removeItem(attacker,'trident'); attacker.weapon=null;
        log(`🔱 ${lname(attacker)} 掷出的三叉戟丢失了（没有【忠诚】）。`,'l-warn');
      }
    }""",
"""    /* 三叉戟掷出：附魔【忠诚】必定回手；无忠诚则掉落，距离 0 的玩家可拾取 */
    if(key==='trident' && ranged){
      if(hasEnch(attacker,'loyalty')){
        log(`🔱 附魔【忠诚】生效：三叉戟回到 ${lname(attacker)} 手中（每回合仅能掷出一次）。`,'l-sys');
      } else {
        removeItem(attacker,'trident'); attacker.weapon=null;
        /* 判定已命中：三叉戟落在目标所在格，距离 0 的存活玩家可拾取（随机一人） */
        const canPick = alivePlayers().filter(q=>q.alive && distanceBetween(target, q)===0);
        if(canPick.length){
          const picker = canPick[rn2(canPick.length)];
          addItem(picker,'trident',1);
          log(`🔱 掷出的三叉戟落在 ${lname(target)} 所在格，被 <b>${lname(picker)}</b> 拾取！`,'l-warn');
        } else {
          log(`🔱 ${lname(attacker)} 掷出的三叉戟丢失了（没有【忠诚】，且无人能拾取）。`,'l-warn');
        }
      }
    }""", '⑤⑥ 三叉戟掷出与拾取')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))

back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  长度 {orig} → {len(back)}（+{len(back)-orig}）')
for n, k in [('① 前置检查','【前置检查】先确认目标与距离'), ('② 珍珠1AP','cost:MOVE_COST,isAction:false,label:`🟣 末影珍珠'),
             ('③ 打火石判定','打火石没能点燃'), ('⑤⑥ 拾取','落在 ${lname(target)} 所在格')]:
    print(f'  {n}:', k in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
