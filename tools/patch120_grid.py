# -*- coding: utf-8 -*-
"""补丁 120：把商店物品卡片接进标签页，并精简重复的“进度式”备注"""
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

# ① renderOptionTab 支持渲染物品卡片（制作/收集、建筑地形）
sub("""  const row = document.createElement('div');
  row.className = 'actions';
  if(!list.length){
    const hint = document.createElement('span');
    hint.className = 'pill';
    hint.textContent = tabId==='inter' ? '（暂无可交互的对象）' : '（这个分类暂时没有可用动作）';
    row.appendChild(hint);
  } else {
    for(const o of list) row.appendChild(mk(o));
  }
  body.appendChild(row);
}""",
"""  /* 制作 / 建筑 两个标签页：先给出物品卡片网格，再给出行内动作按钮 */
  if(tabId==='craft' || tabId==='build'){
    const grid = renderItemGrid(p, tabId);
    if(grid) body.appendChild(grid);
  }

  const row = document.createElement('div');
  row.className = 'actions';
  if(!list.length){
    if(!(tabId==='craft' || tabId==='build')){
      const hint = document.createElement('span');
      hint.className = 'pill';
      hint.textContent = tabId==='inter' ? '（暂无可交互的对象）' : '（这个分类暂时没有可用动作）';
      row.appendChild(hint);
      body.appendChild(row);
    }
  } else {
    for(const o of list) row.appendChild(mk(o));
    body.appendChild(row);
  }
}

/* 物品卡片网格：制作 / 收集（craft）与 建筑地形（build）
   说明文字精简：进度式提示统一放在网格下方，不再每张卡片重复 */
function renderItemGrid(p, tabId){
  const COLLECT = ['wood_sword','stone_sword','iron_sword','diamond_sword','trident','crossbow',
                   'leather','iron_armor','diamond_armor','shield','golem','fishing_rod','ender_pearl'];
  const blocked = (k)=> (k==='god_apple' && !featOn('god_apple')) || (k==='tnt' && !featOn('tnt'));
  const keys = Object.keys(ITEMS).filter(k=>{
    const it = ITEMS[k];
    if(blocked(k)) return false;
    if(it.prog > p.prog) return false;
    if(tabId==='build') return !!it.build && buildAllowed(p,k);
    if(it.build) return false;
    if(k==='pyramid' && !featOn('tnt') && !featOn('god_apple')) return false;
    if(!it.repeat && hasItem(p,k)) return false;
    if(it.need && !hasItem(p,it.need)) return false;
    return true;
  });
  if(!keys.length) return null;

  const grid = document.createElement('div');
  grid.className = 'shopgrid';
  for(const k of keys){
    const it = ITEMS[k];
    const got = it.build ? 0 : Math.min(itemProgress(p,k), it.cost);
    const d = document.createElement('div');
    d.className = 'item' + (p.ap < (it.build?BUILD_COST:1) ? ' dis' : '');
    const ic = itemIcon(k);
    let dots = '';
    for(let i=0;i<it.cost;i++) dots += `<i class="dot${i<got?' on':''}"></i>`;
    const costTxt = it.build ? `${BUILD_COST} AP` : '1 AP';
    d.innerHTML = `<div class="it"><span>${ic?sprTag(ic,24):''}${it.build?(p.buildings[k]?'已建成 ':'建造 '):(got>0?'推进 ':'制作 ')}${it.name}</span><span class="cost">${costTxt}</span></div>
      ${(!it.build && it.cost>0) ? `<div class="progrow">${dots}<b>${got}/${it.cost}</b></div>` : ''}
      <div class="desc">${it.desc}</div>`;
    d.onclick = ()=>{
      if(p.ap < (it.build?BUILD_COST:1)) return;
      applyShopAction(p, {type:'craft', key:k});
      renderAll();
    };
    grid.appendChild(d);
  }

  const wrap = document.createElement('div');
  if(tabId==='craft'){
    const tip = document.createElement('div');
    tip.className = 'tabtip';
    tip.textContent = '进度式：多步物品每投入 1 步点亮 1 个点，集满后自动完成并保存进度。已解锁进程的物品随时都能再做（升级后腐肉、木剑等不会消失）。';
    wrap.appendChild(tip);
  } else {
    const tip = document.createElement('div');
    tip.className = 'tabtip';
    tip.textContent = '建筑：前往任意建筑统一 1 AP。建成后提供对应功能（铁砧可修复装备与附魔）。';
    wrap.appendChild(tip);
  }
  wrap.appendChild(grid);
  return wrap;
}""", '① 物品卡片接入标签页')

# ② 精简“进度式”重复备注（卡片内不再重复）
sub("""          <div class="desc">${it.desc}${(!it.build && it.cost>1)?`<br><b>进度式</b>：每投入 1 步点亮 1 个点，集满 ${it.cost} 点后自动完成。`:''}</div>`;
        d.onclick=()=>{ if(p.ap<(it.build?BUILD_COST:1)) return; applyShopAction(p,{type:'craft',key:k}); render(); };
        return d;
      };""",
"""          <div class="desc">${it.desc}</div>`;
        d.onclick=()=>{ if(p.ap<(it.build?BUILD_COST:1)) return; applyShopAction(p,{type:'craft',key:k}); render(); };
        return d;
      };""", '② 精简商店卡片重复备注')

# ③ 新增 .tabbody / .tabtip 样式
if '.tabtip{' not in t:
    sub(""".hidden{display:none !important}""",
""".hidden{display:none !important}
.tabbody{margin-top:8px}
.tabtip{font-size:11.5px;color:var(--dim);margin:6px 0 8px;line-height:1.5}""",
'③ tabbody / tabtip 样式')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  长度 {orig} → {len(back)}（{len(back)-orig:+d}）')
print('  renderItemGrid:', 'function renderItemGrid' in back)
print('  精简备注:', '<b>进度式</b>：每投入 1 步点亮 1 个点，集满 ${it.cost} 点后自动完成' not in back)
print('  样式:', '.tabtip{' in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
