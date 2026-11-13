# -*- coding: utf-8 -*-
"""补丁 52：音效全面容错（真正的卡死根因）
   按钮 onclick 里若 sfx.*() 抛异常（无音频设备 / AudioContext 被限制），
   后面的 rpsResolver(mv) 就不会执行 → 猜拳点了没反应 → 卡死。
   修复：① sfx 每个方法自身 try/catch；② 关键按键回调里也用 try/catch 包裹音效调用。
"""
import pathlib
import re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

# ① sfx 全部方法包上 try/catch（用安全包装替换定义）
old_sfx = """const sfx = {
  click:()=>beep(420,.05), rps:()=>beep(300,.08,'triangle'),
  win:()=>{beep(660,.09);setTimeout(()=>beep(880,.12),90);},
  lose:()=>beep(200,.12,'sawtooth'),
  hit:()=>beep(150,.14,'sawtooth',.07), block:()=>beep(900,.06,'square',.045),
  heal:()=>{beep(520,.08,'sine',.06);setTimeout(()=>beep(780,.1,'sine',.06),80);},
  boom:()=>beep(90,.3,'sawtooth',.09),
};"""
new_sfx = """/* 音效：任何环境下都不允许抛异常（否则会中断按钮回调，导致界面卡住） */
const sfx = (function(){
  const safe = fn => ()=>{ try{ fn(); }catch(e){} };
  return {
    click: safe(()=>beep(420,.05)),
    rps:   safe(()=>beep(300,.08,'triangle')),
    win:   safe(()=>{ beep(660,.09); setTimeout(()=>{ try{ beep(880,.12); }catch(e){} }, 90); }),
    lose:  safe(()=>beep(200,.12,'sawtooth')),
    hit:   safe(()=>beep(150,.14,'sawtooth',.07)),
    block: safe(()=>beep(900,.06,'square',.045)),
    heal:  safe(()=>{ beep(520,.08,'sine',.06); setTimeout(()=>{ try{ beep(780,.1,'sine',.06); }catch(e){} }, 80); }),
    boom:  safe(()=>beep(90,.3,'sawtooth',.09)),
  };
})();"""
if old_sfx in t:
    t = t.replace(old_sfx, new_sfx, 1); notes.append('  ok sfx 全方法容错')
else:
    notes.append('  ! sfx 定义锚点未匹配')

# ② beep 本身也加固（禁止向外抛）
old_beep = """let AC=null;
function beep(freq,dur=.09,type='square',vol=.05){
  try{"""
new_beep = """let AC=null;
function beep(freq,dur=.09,type='square',vol=.05){
  if(typeof window!=='undefined' && !window.AudioContext && !window.webkitAudioContext) return;
  try{"""
if old_beep in t:
    t = t.replace(old_beep, new_beep, 1); notes.append('  ok beep 前置检查')
else:
    notes.append('  ! beep 锚点未匹配')

# ③ 出拳按钮回调：音效与 resolve 分离，确保一定 resolve
old_btn = """document.querySelectorAll('#rpsBtns .btn').forEach(b=>{
  b.onclick=()=>{ if(rpsResolver){ const r=rpsResolver; rpsResolver=null; rpsPick=b.dataset.mv; sfx.rps(); r(b.dataset.mv); } };
});"""
new_btn = """document.querySelectorAll('#rpsBtns .btn').forEach(b=>{
  b.onclick=()=>{
    const mv = b.dataset.mv;
    const r = rpsResolver;
    rpsResolver = null;
    rpsPick = mv;
    try{ sfx.rps(); }catch(e){}
    /* 先保证流程继续，音效失败也绝不影响 */
    if(typeof r === 'function') r(mv);
  };
});"""
if old_btn in t:
    t = t.replace(old_btn, new_btn, 1); notes.append('  ok 出拳按钮回调加固')
else:
    notes.append('  ! 出拳按钮锚点未匹配')

# ④ 通用：把裸的 sfx.xxx() 调用统一包一层（只处理顶层语句形式，避免嵌套出错）
cnt = 0
def wrap_call(m):
    global cnt
    cnt += 1
    return 'try{ ' + m.group(0) + ' }catch(e){}'
# 形如 `sfx.xxx();` 或 `sfx.xxx()  ` 在语句位置的
t2 = re.sub(r'(?<!try\{ )\bsfx\.(click|rps|win|lose|hit|block|heal|boom)\(\)(?=[;,)\s])', wrap_call, t)
notes.append(f'  ok 兜底包裹 sfx 调用 {cnt} 处')
t = t2

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
