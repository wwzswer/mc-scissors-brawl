# -*- coding: utf-8 -*-
"""补丁 84：【界面同步】每次交互后都重建行动面板
   问题：renderAll() 只重绘玩家面板+顶栏，行动面板的按钮（进程进度、AP 标价、可选项）
        是 askHuman 一次性生成的 DOM，之后永不更新 → 你看到的“界面不变化”。
   方案：把行动面板的构建逻辑抽成 buildActionPanel(p, opts)，
        renderAll() 里只要处于“玩家回合中”就重绘它（不改变 Promise 的 resolve 逻辑）。
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

# ---- 1) renderAll 里加入行动面板重绘 ----
sub("""function renderAll(){
  if(!G) return;
  renderPlayers();
  refreshTopBar();
  setPhase(document.getElementById('phasePill') ? document.getElementById('phasePill').textContent : '');
}""",
"""/* 玩家回合中记住当前选项与“结算回调”，供界面重绘时复用 */
let pendingChoice = null;      /* { opts, settle } */
let pendingChoiceFor = null;   /* 该面板属于哪个玩家 */

function renderAll(){
  if(!G) return;
  renderPlayers();
  refreshTopBar();
  setPhase(document.getElementById('phasePill') ? document.getElementById('phasePill').textContent : '');
  /* 【界面同步】只要玩家正在选择行动，就把行动面板整体重绘一遍，
     这样 AP 数字、进程进度、按钮标价、可选项都会立刻反映最新状态 */
  if(pendingChoice && pendingChoiceFor && pendingChoiceFor.alive && !G.over){
    try{ buildActionPanel(pendingChoiceFor, pendingChoice.opts, pendingChoice.settle); }catch(e){}
  }
}""", 'renderAll 重绘行动面板')

# ---- 2) askHuman：把渲染抽成 buildActionPanel ----
old_ask_head = """function askHuman(p, opts){
  return new Promise(res=>{
    window.__mcOptions = opts;          /* 供自动化测试 / 外挂脚本读取当前可选行动 */
    let settled = false;
    const settle = (o)=>{ if(settled) return; settled = true; res(o); };"""
new_ask_head = """function askHuman(p, opts){
  return new Promise(res=>{
    let settled = false;
    const settle = (o)=>{
      if(settled) return;
      settled = true;
      pendingChoice = null; pendingChoiceFor = null;    /* 结束等待，停止重绘 */
      res(o);
    };
    buildActionPanel(p, opts, settle);
  });
}
/* 构建（或重建）行动面板：可被 renderAll 反复调用以保持界面同步 */
function buildActionPanel(p, opts, settle){
  {
    window.__mcOptions = opts;          /* 供自动化测试 / 外挂脚本读取当前可选行动 */
    pendingChoice = { opts, settle };   /* 记录，供 renderAll 重绘 */
    pendingChoiceFor = p;"""
if old_ask_head in t:
    t = t.replace(old_ask_head, new_ask_head, 1); notes.append('  ok askHuman 拆出 buildActionPanel')
else:
    notes.append('  ! askHuman 头部锚点未匹配')

# ---- 3) askHuman 原收尾（settle 后 return）需要去掉多余的 })，改为闭合 buildActionPanel ----
# 找到 buildActionPanel 内的“没有实质行动”分支里的 return，它有 return 结束函数——保留
# askHuman 原来的结尾是 "  });\n}"，现在 buildActionPanel 不需要 Promise 包装，需要改成 "  }\n}"
old_tail = """      b.onclick=()=>{
        try{ sfx.click(); }catch(e){}
        /* 【防卡死】点击即结算，任何异常都不会让回合悬停 */
        try{ settle(o); }catch(e){ settle({type:'pass'}); }
      };
      return b;
    };"""
new_tail = """      b.onclick=()=>{
        try{ sfx.click(); }catch(e){}
        /* 【防卡死】点击即结算，任何异常都不会让回合悬停 */
        try{ settle(o); }catch(e){ settle({type:'pass'}); }
      };
      return b;
    };"""
notes.append('  - 按钮回调保持不变')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
