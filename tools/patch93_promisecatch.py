# -*- coding: utf-8 -*-
"""补丁 93：【根治】doJudgment 的 Promise 反模式
   原因：`return new Promise(async resolve => {...})` —— async 执行器里一旦抛异常，
        会被静默吞掉，Promise 永不 resolve → 判定永远不返回 → 游戏卡死。
   修复：在引入处捕获异常并 resolve；同时把攻击/判定的关键步骤包进 try/catch，
        并把异常写进 rlog 便于定位。
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

# 1) 循环体整体包 try/catch：任何异常都记录并结束判定
sub("""    while(rounds++ < 60){
      rlog('判定第 ' + rounds + ' 轮');
      const a = attacker.isHuman ? pick(['rock','scissors','paper']) : aiRpsMove(attacker, target);
      const b = target.isHuman  ? pick(['rock','scissors','paper']) : aiRpsMove(target, attacker);""",
"""    while(rounds++ < 60){
      rlog('判定第 ' + rounds + ' 轮');
      try{
      const a = attacker.isHuman ? pick(['rock','scissors','paper']) : aiRpsMove(attacker, target);
      const b = target.isHuman  ? pick(['rock','scissors','paper']) : aiRpsMove(target, attacker);""",
'循环体 try 开始')

# 2) 循环体结束处补 catch
sub("""      judgeSlots(ra,rb,win);
      win ? sfx.win() : sfx.lose();
      renderAll();
      break;
    }""",
"""      judgeSlots(ra,rb,win);
      try{ win ? sfx.win() : sfx.lose(); }catch(e){}
      renderAll();
      break;
      }catch(err){
        /* 任何异常都不能让判定悬停 */
        rlog('判定异常: ' + (err && err.message ? err.message : String(err)));
        log('（判定过程出现异常，按攻击失效处理）','l-warn');
        hit = false;
        break;
      }
    }""", '循环体 catch')

# 3) 平局分支内的 sfx 也不要中断
sub("""          judgeSlots(ra, rb, hit);
          hit ? sfx.win() : sfx.lose();
          renderAll();
          break;""",
"""          judgeSlots(ra, rb, hit);
          try{ hit ? sfx.win() : sfx.lose(); }catch(e){}
          renderAll();
          break;""", '随机裁决 sfx 保护')

# 4) performAttack 里对 doJudgment 的调用也加保护（双保险）
sub("""    const hit = await doJudgment(attacker, target, o);""",
"""    let hit = false;
    try{
      hit = await doJudgment(attacker, target, o);
    }catch(err){
      rlog('doJudgment 抛出异常: ' + (err && err.message ? err.message : String(err)));
      log('（判定异常，按攻击失效处理）','l-warn');
      hit = false;
    }""", 'performAttack 调用保护')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
