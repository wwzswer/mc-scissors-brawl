# -*- coding: utf-8 -*-
"""补丁 89：给 doJudgment 全流程埋诊断日志（rlog），并对判定循环加防死循环
   目标：精确定位“平局后卡死”停在哪一步
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

# 1) 循环入口 + 每轮记录
sub("""function doJudgment(attacker, target, opts){
  const o = opts||{};
  return new Promise(async resolve=>{
    let hit = false, dodged = false, rounds = 0;
    /* 判定同样必须分出胜负：平局则一直重猜（除非被攻击方花 1 AP 直接闪避） */
    while(rounds++ < 60){
      const a = attacker.isHuman ? pick(['rock','scissors','paper']) : aiRpsMove(attacker, target);
      const b = target.isHuman  ? pick(['rock','scissors','paper']) : aiRpsMove(target, attacker);
      const ra = (o.a && rounds===1) ? o.a : a;      /* 允许测试指定首轮出拳 */
      const rb = (o.b && rounds===1) ? o.b : b;""",
"""function doJudgment(attacker, target, opts){
  const o = opts||{};
  return new Promise(async resolve=>{
    let hit = false, dodged = false, rounds = 0;
    let resolved = false;
    const safeResolve = (v)=>{ if(resolved) return; resolved = true; resolve(v); };
    rlog('doJudgment 进入: ' + lname(attacker) + ' → ' + lname(target) + ' instant=' + !!o.instant);
    /* 【防卡死】无论循环如何结束，20 秒后一定收尾，绝不悬停 */
    const guardTimer = setTimeout(()=>{ rlog('doJudgment 兜底超时收尾'); safeResolve(hit); }, 20000);
    /* 判定同样必须分出胜负：平局则一直重猜（除非被攻击方花 1 AP 直接闪避） */
    while(rounds++ < 60){
      rlog('判定第 ' + rounds + ' 轮');
      const a = attacker.isHuman ? pick(['rock','scissors','paper']) : aiRpsMove(attacker, target);
      const b = target.isHuman  ? pick(['rock','scissors','paper']) : aiRpsMove(target, attacker);
      const ra = (o.a && rounds===1) ? o.a : a;      /* 允许测试指定首轮出拳 */
      const rb = (o.b && rounds===1) ? o.b : b;""", 'doJudgment 入口+兜底')

# 2) 平局分支记录
sub("""        if(rounds===1){
          let wantsDodge = false;
          if(o.dodge!==undefined) wantsDodge = o.dodge;
          else if(target.isHuman) wantsDodge = await askDodge(target, attacker);
          else wantsDodge = (R()<0.5);        /* AI：约一半概率选择闪避 */""",
"""        if(rounds===1){
          let wantsDodge = false;
          if(o.dodge!==undefined){ wantsDodge = o.dodge; rlog('平局: 用 opts.dodge=' + o.dodge); }
          else if(target.isHuman){ rlog('平局: 等待玩家选择闪避/赌一把…'); wantsDodge = await askDodge(target, attacker); rlog('平局: 玩家已选择 dodge=' + wantsDodge); }
          else { wantsDodge = (R()<0.5); rlog('平局: AI 自行决定 dodge=' + wantsDodge); }""",
'平局分支日志')

# 3) 平局后继续/随机裁决/命中 都记录
sub("""        if(rounds >= 10){
          hit = R() < 0.5;                      /* 连续平局过多：随机裁决 */
          log(`　　（连续 ${rounds} 轮平局，随机裁决为「${hit?'命中':'失效'}」）`,'l-warn');
          judgeSlots(ra, rb, hit);
          hit ? sfx.win() : sfx.lose();
          renderAll();
          break;
        }
        judgeSlots(ra,rb,false); sfx.rps(); renderAll();
        if(!o.instant) await sleep(Math.min(ANIM.judgmentMs, 500));
        continue;""",
"""        if(rounds >= 10){
          hit = R() < 0.5;                      /* 连续平局过多：随机裁决 */
          log(`　　（连续 ${rounds} 轮平局，随机裁决为「${hit?'命中':'失效'}」）`,'l-warn');
          rlog('平局过多: 随机裁决 hit=' + hit);
          judgeSlots(ra, rb, hit);
          hit ? sfx.win() : sfx.lose();
          renderAll();
          break;
        }
        judgeSlots(ra,rb,false); try{ sfx.rps(); }catch(e){}
        renderAll();
        rlog('平局: 准备进入下一轮判定');
        if(!o.instant){ rlog('平局: 等待动画'); await sleep(Math.min(ANIM.judgmentMs, 500)); rlog('平局: 动画结束'); }
        continue;""", '平局循环日志')

# 4) 收尾记录 + 清理兜底
sub("""    if(!dodged && rounds>60) log('（判定轮次过多，按攻击失效处理）','l-warn');
    const finish = ()=>{ hideRpsSlots(); resolve(hit); };
    if(o.instant) finish(); else setTimeout(finish, ANIM.judgmentMs);""",
"""    if(!dodged && rounds>60) log('（判定轮次过多，按攻击失效处理）','l-warn');
    rlog('判定结束 hit=' + hit + ' dodged=' + dodged + ' rounds=' + rounds);
    const finish = ()=>{
      clearTimeout(guardTimer);
      hideRpsSlots();
      rlog('hideRpsSlots 完成，resolve 判定');
      safeResolve(hit);
    };
    if(o.instant) finish(); else { rlog('等待最终动画'); setTimeout(finish, ANIM.judgmentMs); }""",
'判定收尾日志')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
