# -*- coding: utf-8 -*-
"""补丁 98：修复两处 ReferenceError（我的重构遗留）
   ① settled is not defined —— settle 已移到 buildActionPanel，settled 变量没跟过去
   ② render is not defined  —— 进程/商店按钮回调里调了不存在的 render
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

# ① settle 用函数自身属性做幂等标记（不再依赖外层 settled）
sub("""    let settled = false;
    const settle = (o)=>{
      if(settled) return;
      settled = true;
      pendingChoice = null; pendingChoiceFor = null;    /* 结束等待，停止重绘 */
      res(o);
    };
    buildActionPanel(p, opts, settle);""",
"""    const settle = (o)=>{
      if(settle.__done) return;                          /* 幂等：重绘后仍不会重复结算 */
      settle.__done = true;
      pendingChoice = null; pendingChoiceFor = null;     /* 结束等待，停止重绘 */
      res(o);
    };
    buildActionPanel(p, opts, settle);""", 'settle 幂等标记')

sub("""    setTimeout(()=>{ if(!settled) log('（等待超时，自动结束回合）','l-warn'); settle({type:'pass'}); }, 300000);""",
"""    setTimeout(()=>{ if(!settle.__done) log('（等待超时，自动结束回合）','l-warn'); settle({type:'pass'}); }, 300000);""",
'超时兜底用幂等标记')

# ② 进程按钮回调：render → renderAll
sub("""    pb.onclick = ()=>{
      if(p.ap<1 || progMaxed(p)) return;
      applyShopAction(p, {type:'upgrade'});
      render(); renderAll();
    };""",
"""    pb.onclick = ()=>{
      if(p.ap<1 || progMaxed(p)) return;
      applyShopAction(p, {type:'upgrade'});
      renderAll();                       /* 重建面板：AP 与进度立即刷新 */
    };""", '进程按钮 render → renderAll')

# ③ 兜底：清掉所有遗留的 render() 调用（该函数不存在）
import re
cnt = 0
def fix_render(m):
    global cnt
    cnt += 1
    return 'renderAll()'
t2, n = re.subn(r'\brender\(\);(?!\s*renderAll)', 'renderAll();', t)
if n:
    t = t2
    notes.append(f'  ok 清理遗留 render() 调用 {n} 处')
else:
    notes.append('  - 无遗留 render()')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
# 最终检查是否还有裸 render(/render() 
left = [l.strip()[:110] for l in t.split('\n') if re.search(r'(?<![A-Za-z])render\(\)', l)]
print('剩余裸 render() 调用:', left if left else '无')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
