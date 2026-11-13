# -*- coding: utf-8 -*-
"""补丁 95：doJudgment 调用处加保护；其它 rpsStatus 访问也判空"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# 1) performAttack 调用保护
sub("""    const success = await doJudgment(attacker, target, opts);""",
"""    let success = false;
    try{
      success = await doJudgment(attacker, target, opts);
    }catch(err){
      rlog('doJudgment 抛出异常: ' + (err && err.message ? err.message : String(err)));
      log('（判定异常，按攻击失效处理）','l-warn');
      success = false;
    }""", 'performAttack 调用保护')

# 2) 其它 rpsStatus 直接访问判空
sub("""    document.getElementById('rpsStatus').textContent = (autoMode ? '自动出拳中…' : '本回合猜拳——选择你的出拳');""",
"""    const st0 = document.getElementById('rpsStatus');
    if(st0) st0.textContent = (autoMode ? '自动出拳中…' : '本回合猜拳——选择你的出拳');""",
'rpsStatus 判空 1')
sub("""    document.getElementById('rpsStatus').textContent = '自动出拳中…';""",
"""    const st1 = document.getElementById('rpsStatus');
    if(st1) st1.textContent = '自动出拳中…';""", 'rpsStatus 判空 2')
sub("""    document.getElementById('rpsStatus').textContent = '本回合猜拳——选择你的出拳';""",
"""    const st2 = document.getElementById('rpsStatus');
    if(st2) st2.textContent = '本回合猜拳——选择你的出拳';""", 'rpsStatus 判空 3')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
