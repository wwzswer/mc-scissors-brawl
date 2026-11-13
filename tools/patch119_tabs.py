# -*- coding: utf-8 -*-
"""补丁 119：行动区改为与“进程升级”同级的标签页
   标签：攻击/装备 ｜ 制作/收集 ｜ 距离 ｜ 建筑地形 ｜ 交互他人 ｜ 附魔/修复 ｜ 进程升级
   - 不再需要先点“制作/收集”按钮；进回合即见标签页
   - 附魔/修复：未建铁砧时暗色且不可点击
   - 标签页选择在重绘间保持
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
orig = len(t)

start = t.index('function buildActionPanel(p, opts, settle){')
end = t.index('function openShop(', start)

new_fn = r"""/* 行动区当前标签页（重绘时保持） */
let curTab = 'craft';

/* 把行动选项按标签页分组 */
function tabOfOption(o){
  const T = o.type;
  if(['move','pearl','rod','water','water_pull','fish_trident'].includes(T)) return 'dist';
  if(T==='craftShopItem'){
    const it = ITEMS[o.key];
    if(it && it.build) return 'build';
    return 'craft';
  }
  if(T==='attack' || T==='golem_punch' || T==='tnt_place' || T==='tnt_detonate'
     || T==='switch_weapon' || T==='armor_priority') return 'atk';
  if(T==='repair' || T==='enchant') return 'up';
  if(T==='armor_shield') return 'inter';
  return 'craft';                       /* 补给类（面包/金苹果/药水） */
}

function buildActionPanel(p, opts, settle){
  window.__mcOptions = opts;
  pendingChoice = { opts, settle };
  pendingChoiceFor = p;
  const allOpts = opts || [];
  const bar = document.getElementById('actionbar');
  if(!bar) return;

  /* 顶栏信息 */
  const info = document.createElement('div');
  info.innerHTML = `<span class="pill on">你的回合</span>
    <span class="pill">行动点 ${p.ap}</span>
    <span class="pill">免费行动 ${p.slotsLeft}</span>
    <span class="pill">${PROG_NAME[p.prog]}</span>
    <span class="pill">${gearLabel(p)}</span>
    <span class="pill">距离：${G.players.filter(q=>q!==p&&q.alive).map(q=>q.name+' '+distanceBetween(p,q)+'格').join('、')||'—'}</span>`;

  /* 结束回合按钮 */
  const endBtn = document.createElement('button');
  endBtn.className = 'btn small';
  endBtn.textContent = '⏭ 结束回合';
  endBtn.onclick = ()=>{ try{ sfx.click(); }catch(e){} settle({type:'pass'}); };

  /* 按标签页分组 */
  const groups = { atk:[], craft:[], dist:[], build:[], inter:[], up:[], prog:[] };
  for(const o of allOpts){
    if(o.type==='pass') continue;
    if(o.type==='shop_progress' || o.type==='shop_craft') continue;   /* 标签页取代 */
    const g = tabOfOption(o);
    (groups[g] = groups[g] || []).push(o);
  }

  const TABS = [
    { id:'craft', name:'🛠️ 制作 / 收集' },
    { id:'atk',   name:'⚔️ 攻击 / 装备' },
    { id:'dist',  name:'📏 距离' },
    { id:'build', name:'🏠 建筑地形' },
    { id:'inter', name:'👥 交互他人' },
    { id:'up',    name:'✨ 附魔 / 修复', locked: !p.buildings.anvil },
    { id:'prog',  name:'⬆️ 进程升级' },
  ];
  if(!TABS.some(x=>x.id===curTab)) curTab = 'craft';
  if(curTab==='up' && !p.buildings.anvil) curTab = 'craft';

  const tabsRow = document.createElement('div');
  tabsRow.className = 'tabs';
  tabsRow.style.flexWrap = 'wrap';
  for(const tb of TABS){
    const el = document.createElement('div');
    el.className = 'tab' + (curTab===tb.id ? ' on' : '');
    el.textContent = tb.name;
    if(tb.locked){
      el.style.opacity = '.4';
      el.style.cursor = 'not-allowed';
      el.title = '需要先建造铁砧';
      el.onclick = ()=>{ try{ sfx.click(); }catch(e){} log('（附魔 / 修复需要先在“建筑地形”里建造铁砧）','l-sys'); };
    } else {
      el.onclick = ()=>{ try{ sfx.click(); }catch(e){} curTab = tb.id; renderAll(); };
    }
    tabsRow.appendChild(el);
  }

  /* 组装 */
  bar.innerHTML = '';
  bar.appendChild(info);
  bar.appendChild(tabsRow);

  const body = document.createElement('div');
  body.className = 'tabbody';
  bar.appendChild(body);

  const footer = document.createElement('div');
  footer.className = 'actions';
  footer.style.marginTop = '8px';
  footer.appendChild(endBtn);
  bar.appendChild(footer);

  /* 渲染当前页 */
  if(curTab === 'prog'){
    renderProgressTab(body, p, groups.prog);
  } else {
    renderOptionTab(body, p, curTab, groups[curTab] || [], settle);
  }
}

/* 选项类标签页：把按钮分行显示 */
function renderOptionTab(body, p, tabId, list, settle){
  const mk=(o)=>{
    const b=document.createElement('button');
    b.className='btn small';
    const noSlot = isAttackAction(o) || MOBILITY_TYPES.includes(o.type)
                || FREE_TYPES.includes(o.type) || o.isAction===false;
    const slot = noSlot ? 0 : actionSlotCost(p);
    const extra = (o.cost||0)+slot;
    const fixed = (extra===Infinity) ? '行动点不足' : (extra>0 ? `${extra} AP` : '免费');
    b.textContent = o.label + ' · ' + fixed;
    b.disabled = (extra===Infinity);
    b.onclick=()=>{
      try{ sfx.click(); }catch(e){}
      try{ settle(o); }catch(e){ settle({type:'pass'}); }
    };
    return b;
  };
  const row = document.createElement('div');
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
}

/* 进程升级页 */
function renderProgressTab(body, p, extra){
  const wrap = document.createElement('div');
  wrap.className = 'progwrap';
  const nxt = p.prog + 1;
  const pb = document.createElement('button');
  pb.className = 'btn prog';
  if(!UPGRADE[nxt]){
    pb.textContent = `⬆️ 进程：${PROG_NAME[p.prog]}（已满级）`;
    pb.disabled = true;
  } else {
    const need = UPGRADE[nxt].cost;
    const got = Math.min(progProgress(p), need);
    pb.innerHTML = `⬆️ 进程：${PROG_NAME[p.prog]} → ${PROG_NAME[nxt]}　${Math.min(progProgress(p)+1, need)}/${need} 点　（1 AP）`;
    pb.disabled = (p.ap < 1);
    pb.onclick = ()=>{
      if(p.ap < 1) return;
      applyShopAction(p, {type:'upgrade'});
      renderAll();
    };
    const dots = document.createElement('div');
    dots.className = 'progrow';
    let dh = '';
    for(let i=0;i<need;i++) dh += `<i class="dot${i<got?' on':''}"></i>`;
    dots.innerHTML = dh + `<b>${got}/${need}</b>`;
    wrap.appendChild(pb);
    wrap.appendChild(dots);
    body.appendChild(wrap);
    const tip = document.createElement('div');
    tip.className = 'tabtip';
    tip.textContent = `每投入 1 步点亮 1 个点，集满 ${need} 点自动升级到 ${PROG_NAME[nxt]}；进度会在每回合结束时保存。`;
    body.appendChild(tip);
    return;
  }
  wrap.appendChild(pb);
  body.appendChild(wrap);
}

"""
t = t[:start] + new_fn + t[end:]
IDX.write_text(t, encoding='utf-8')
print(f'buildActionPanel 已重建：长度 {orig} → {len(t)}（{len(t)-orig:+d}）')
print('  新函数 renderOptionTab:', 'function renderOptionTab' in t)
print('  新函数 renderProgressTab:', 'function renderProgressTab' in t)
print('  标签页定义:', 'inter' in t and '建筑地形' in t)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
