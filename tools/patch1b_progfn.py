# -*- coding: utf-8 -*-
"""补丁 1b：插入进度点核心函数（幂等）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
html = IDX.read_text(encoding='utf-8')

if 'function progNeed(p)' in html:
    print('已存在，跳过')
else:
    anchor = '/* ----------------------------- 距离 ----------------------------- */'
    assert anchor in html, '找不到距离区块锚点'
    block = """/* --- 进程进度点：每次投入 1 步点亮 1 个小点，满点自动升级，进度保存到 localStorage --- */
function progNeed(p){ const u = UPGRADE[p.prog+1]; return u ? u.cost : 0; }
function progProgress(p){ return p.progPts || 0; }
function progMaxed(p){ return !UPGRADE[p.prog+1]; }
function progSave(p){
  try{
    const all = JSON.parse(localStorage.getItem('mcProg') || '{}');
    all[p.name] = {prog:p.prog, pts:p.progPts||0};
    localStorage.setItem('mcProg', JSON.stringify(all));
  }catch(e){}
}
function progLoad(name){
  try{
    const all = JSON.parse(localStorage.getItem('mcProg') || '{}');
    const v = all[name];
    if(v && typeof v.prog==='number') return {prog:Math.max(0,Math.min(4,v.prog)), pts:Math.max(0,v.pts|0)};
  }catch(e){}
  return null;
}
/* 投入 1 步进度；返回是否发生了升级 */
function addProgPoint(p){
  if(progMaxed(p)) return false;
  p.progPts = (p.progPts||0) + 1;
  let leveled = false;
  while(!progMaxed(p) && p.progPts >= progNeed(p)){
    p.progPts -= progNeed(p);
    p.prog += 1;
    leveled = true;
    log(`⬆️ ${lname(p)} 的进程推进到 <b>${PROG_NAME[p.prog]}</b>！`,'l-good');
    if(p.prog===PROG.STONE) log('（石进程：钓鱼竿是三叉戟的前置；末影珍珠获得后不会消耗）','l-sys');
    if(p.prog===PROG.IRON) log('（铁进程：铁砧可修复护甲；沙漠金字塔可获取 TNT 与附魔金苹果）','l-sys');
  }
  progSave(p);                                   /* 投入即存盘，绝不丢进度 */
  renderAll();
  return leveled;
}
function progPointsHtml(p){
  if(progMaxed(p)) return '<span class="progdots"><i class="dot on"></i><b>已满级</b></span>';
  const need = progNeed(p), got = Math.min(progProgress(p), need);
  let dots = '';
  for(let i=0;i<need;i++) dots += `<i class="dot${i<got?' on':''}"></i>`;
  return `<span class="progdots">${dots}<b>${got}/${need}</b>` +
         `<span class="prognext">→ ${PROG_NAME[p.prog+1]}</span></span>`;
}

"""
    html = html.replace(anchor, block + anchor, 1)
    IDX.write_text(html, encoding='utf-8')
    print(f'已插入进度点核心函数，文件 {len(html)/1024:.1f} KB')
