# -*- coding: utf-8 -*-
"""补丁 92：判定 Promise 一定 resolve（把收尾包进 try/catch + 缩短兜底到 6 秒）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# 1) 兜底从 20s 缩到 6s
sub("""    const guardTimer = setTimeout(()=>{
      rlog('doJudgment 兜底超时收尾');
      unlockUI(prevJudgeLock);
      try{ hideRpsSlots(); }catch(e){}
      safeResolve(hit);
    }, 20000);""",
"""    const guardTimer = setTimeout(()=>{
      rlog('doJudgment 兜底超时收尾（说明正常路径未 resolve！）');
      unlockUI(prevJudgeLock);
      try{ hideRpsSlots(); }catch(e){}
      try{ renderAll(); }catch(e){}
      safeResolve(hit);
    }, 6000);""", '兜底缩到 6 秒')

# 2) 收尾全程 try/catch，保证 resolve 一定执行
sub("""    const finish = ()=>{
      clearTimeout(guardTimer);
      hideRpsSlots();
      unlockUI(prevJudgeLock);                 /* 判定结束，恢复面板重绘 */
      try{ renderAll(); }catch(e){}            /* 让行动面板立刻回到正确状态 */
      rlog('hideRpsSlots 完成，resolve 判定');
      safeResolve(hit);
    };
    if(o.instant) finish(); else { rlog('等待最终动画'); setTimeout(finish, ANIM.judgmentMs); }""",
"""    const finish = ()=>{
      clearTimeout(guardTimer);
      try{ hideRpsSlots(); }catch(e){ rlog('hideRpsSlots 异常: ' + e.message); }
      unlockUI(prevJudgeLock);                 /* 判定结束，恢复面板重绘 */
      try{ renderAll(); }catch(e){ rlog('renderAll 异常: ' + e.message); }
      rlog('收尾完成，resolve 判定');
      safeResolve(hit);                        /* 无论如何都要 resolve */
    };
    if(o.instant) finish();
    else { rlog('等待最终动画'); setTimeout(finish, ANIM.judgmentMs || 0); }""",
'收尾全程保护')

# 3) 闪避分支：sfx 与 break 都不允许中断
sub("""          if(wantsDodge && target.ap>=1){
            target.ap -= 1; dodged = true;
            log(`　　${lname(target)} 消耗 1 AP 直接闪避！`,'l-warn');
            break;
          }""",
"""          if(wantsDodge && target.ap>=1){
            target.ap -= 1; dodged = true;
            log(`　　${lname(target)} 消耗 1 AP 直接闪避！`,'l-warn');
            rlog('闪避成功，结束判定');
            break;
          }""", '闪避分支日志')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
