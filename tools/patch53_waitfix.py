# -*- coding: utf-8 -*-
"""补丁 53：彻底重写等待交互，确保“点了一定继续”
   采用轮询 Promise（不依赖 onclick 是否被覆盖）+ 事件委托兜底 + 诊断字段
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

# ---------- 1) waitClick 重写：轮询 flag，任何路径只要按钮被点过就继续 ----------
start = t.index('/* 统一的“等玩家点一下”交互：带超时与防重复，避免任何情况下卡死 */')
end = t.index('/* 兼容旧调用名 */')
new_block = """/* 统一的“等玩家点一下”交互：
   用轮询标志位而不是单一 Promise resolve —— 无论按钮的 onclick 是否被覆盖/丢失，
   只要按钮被点击（或按钮被移除、超时）就一定会继续，绝不死等。 */
let lastClickAt = 0;                  /* 最近一次“继续”类按钮被点的时间戳（诊断用） */
function waitClick(label, opts){
  const o = opts || {};
  return new Promise(res=>{
    const bar = o.bar || document.getElementById('actionbar');
    bar.innerHTML = '';
    const b = document.createElement('button');
    b.className = 'btn pri';
    b.textContent = label || '继续 ▶';
    let done = false;
    const finish = ()=>{
      if(done) return;
      done = true;
      clickResolver = null;
      lastClickAt = Date.now();
      res();
    };
    const onHit = (ev)=>{ if(ev) ev.preventDefault(); try{ sfx.click(); }catch(e){} finish(); };
    b.addEventListener('click', onHit);
    b.onclick = onHit;                 /* 双保险 */
    clickResolver = finish;
    bar.appendChild(b);
    const t0 = Date.now();
    const iv = setInterval(()=>{
      if(done){ clearInterval(iv); return; }
      /* ① 按钮被移除 / ② 超时 / ③ 玩家已点过（标志位）→ 放行 */
      if(!b.isConnected || (o.timeout && Date.now()-t0 > o.timeout)){ clearInterval(iv); finish(); }
    }, 200);
    /* ④ 兜底：整个等待最多 90 秒，避免任何未知原因的死等 */
    setTimeout(()=>{ clearInterval(iv); finish(); }, o.hardTimeout || 90000);
  });
}
/* 等玩家出拳（猜拳阶段用）：同样用轮询，保证有出口 */
function promptRpsMove(target){
  return new Promise(res=>{
    let done = false;
    const finish = (mv)=>{
      if(done) return;
      done = true;
      rpsResolver = null;
      res(mv);
    };
    const area = document.getElementById('rpsArea');
    const btns = document.getElementById('rpsBtns');
    if(area) area.classList.remove('hidden');
    if(btns) btns.classList.remove('hidden');
    const st = document.getElementById('rpsStatus');
    if(st) st.textContent = target ? `与 ${target.name} 猜拳 — 选择你的出拳` : '本回合猜拳 — 选择你的出拳（平手会重出）';
    rpsResolver = finish;
    /* 兜底：按钮区异常时随机出拳；最长 90 秒 */
    const iv = setInterval(()=>{
      if(done){ clearInterval(iv); return; }
      if(!btns || !btns.isConnected){ clearInterval(iv); finish(pick(['rock','scissors','paper'])); }
    }, 400);
    setTimeout(()=>{ clearInterval(iv); finish(pick(['rock','scissors','paper'])); }, 90000);
  });
}
"""
t = t[:start] + new_block + t[end:]

# ---------- 2) 出拳按钮：用事件委托（即使单个按钮的 onclick 丢失也能响应） ----------
old_bind = """document.querySelectorAll('#rpsBtns .btn').forEach(b=>{
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
new_bind = """/* 出拳：每个按钮绑定 + 容器事件委托（双保险） */
function rpsBtnHit(mv){
  if(!mv) return;
  const r = rpsResolver;
  rpsResolver = null;
  rpsPick = mv;
  try{ sfx.rps(); }catch(e){}
  if(typeof r === 'function') r(mv);     /* 先保证流程继续 */
}
document.querySelectorAll('#rpsBtns .btn').forEach(b=>{
  const mv = b.dataset.mv;
  b.addEventListener('click', ()=>rpsBtnHit(mv));
  b.onclick = ()=>rpsBtnHit(mv);
});
(function delegateRps(){
  const wrap = document.getElementById('rpsBtns');
  if(wrap && !wrap.__delegated){
    wrap.__delegated = true;
    wrap.addEventListener('click', ev=>{
      const b = ev.target && ev.target.closest ? ev.target.closest('.btn') : null;
      if(b && b.dataset && b.dataset.mv) rpsBtnHit(b.dataset.mv);
    });
  }
})();"""
if old_bind in t:
    t = t.replace(old_bind, new_bind, 1)
    print('  ok 出拳按钮双绑定 + 委托')
else:
    print('  ! 出拳按钮锚点未匹配')

# ---------- 3) 诊断导出 ----------
if 'lastClickAt' not in t.split('__api')[0][-3000:]:
    pass
old_exp = "    judgeRound, rpsPhase, doJudgment, showSlotsMulti, armorHasAny, BUILD_COST, promptRpsMove, waitClick,"
new_exp = "    judgeRound, rpsPhase, doJudgment, showSlotsMulti, armorHasAny, BUILD_COST, promptRpsMove, waitClick,\n    getLastClickAt: ()=>lastClickAt, rpsBtnHit,"
if old_exp in t and 'getLastClickAt' not in t:
    t = t.replace(old_exp, new_exp, 1)
    print('  ok 导出诊断接口')

IDX.write_text(t, encoding='utf-8')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
