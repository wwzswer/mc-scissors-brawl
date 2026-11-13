# -*- coding: utf-8 -*-
"""补丁 49：商店按用途分为 6 类
   进程（只含进程）/ 距离（自己移动、末影珍珠、钓鱼竿位移）/ 收集（制作武器、收集装备）
   / 攻击（切换武器、攻击他人、腐肉、打火石、铁傀儡）/ 建筑（前往建筑）/ 升级（铁砧修复、附魔）
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

# ---------- 1) 商店面板：单页 grid 改为 6 个分组的可折叠区块 ----------
old_shop = """  const tabs=document.createElement('div'); tabs.className='tabs';
  const t1=document.createElement('div'); t1.className='tab'+(mode==='craft'?' on':''); t1.textContent='🛠️ 制作 / 建造';
  const t2=document.createElement('div'); t2.className='tab'+(mode==='progress'?' on':''); t2.textContent='⬆️ 进程升级';
  tabs.appendChild(t1); tabs.appendChild(t2); box.appendChild(tabs);
  const grid=document.createElement('div'); grid.className='shopgrid'; box.appendChild(grid);"""
new_shop = """  const tabs=document.createElement('div'); tabs.className='tabs';
  const t1=document.createElement('div'); t1.className='tab'+(mode==='craft'?' on':''); t1.textContent='🛠️ 制作 / 建造';
  const t2=document.createElement('div'); t2.className='tab'+(mode==='progress'?' on':''); t2.textContent='⬆️ 进程升级';
  tabs.appendChild(t1); tabs.appendChild(t2); box.appendChild(tabs);
  const legend=document.createElement('div');
  legend.style.cssText='font-size:11.5px;color:var(--dim);margin:0 0 8px';
  legend.textContent='分六类：进程（投入进度）｜距离（走位/珍珠/钓鱼竿）｜收集（武器与装备）｜攻击（换武器与出手）｜建筑（前往建筑）｜升级（铁砧修复与附魔）';
  box.appendChild(legend);
  const grid=document.createElement('div'); grid.className='shopgrid'; box.appendChild(grid);"""
if old_shop in t:
    t = t.replace(old_shop, new_shop, 1); notes.append('  ok 商店图例')
else:
    notes.append('  ! 商店 tabs 锚点未匹配（可能已改过）')

# ---------- 2) 商店渲染：分组显示 ----------
old_render = """  const render=()=>{
    grid.innerHTML='';
    if(mode==='progress'){"""
new_render = """  const groupHead = (title, tip)=>{
    const d = document.createElement('div');
    d.className = 'shopgroup';
    d.innerHTML = `<b>${title}</b>${tip?`<span>${tip}</span>`:''}`;
    return d;
  };
  const render=()=>{
    grid.innerHTML='';
    if(mode==='progress'){"""
sub(old_render, new_render, 'render 分组辅助')

# progress 页：包一层“进程”分组
sub("""        d.onclick=()=>{ if(p.ap<1) return; applyShopAction(p,{type:'upgrade'}); render(); renderAll(); };
        grid.appendChild(d);
      }
    } else {""",
"""        d.onclick=()=>{ if(p.ap<1) return; applyShopAction(p,{type:'upgrade'}); render(); renderAll(); };
        grid.appendChild(groupHead('⬆️ 进程', '投入 1 步进度，集满自动升级'));
        grid.appendChild(d);
      }
    } else {""", 'progress 分组标题')

# craft 页：先分好类，再按 收集/建筑/升级 三块渲染（进程与距离、攻击在行动面板里）
old_items = """      for(const k of Object.keys(ITEMS)){
        const it=ITEMS[k];
        if(it.prog>p.prog) continue;                 /* 低级物品升级后依然可做（如腐肉） */
        if(it.build){ if(!buildAllowed(p,k)) continue; }
        else if(!it.repeat && hasItem(p,k)) continue;
        if(it.need && !hasItem(p,it.need)) continue;
        const got = Math.min(itemProgress(p,k), it.cost);
        const d=document.createElement('div'); d.className='item'+(p.ap<1?' dis':'');
        const ic = itemIcon(k);
        let dots=''; for(let i=0;i<it.cost;i++) dots += `<i class="dot${i<got?' on':''}"></i>`;
        d.innerHTML=`<div class="it"><span>${ic?sprTag(ic,24):''}${got>0?'推进 ':'制作 '}${it.name}</span><span class="cost">1 AP</span></div>
          ${it.cost>0?`<div class="progrow">${dots}<b>${got}/${it.cost}</b></div>`:''}
          <div class="desc">${it.desc}${it.cost>1?`<br><b>进度式</b>：每投入 1 步点亮 1 个点，集满 ${it.cost} 点后自动完成。`:''}</div>`;
        d.onclick=()=>{ if(p.ap<(it.build?BUILD_COST:1)) return; applyShopAction(p,{type:'craft',key:k}); render(); renderAll(); };
        grid.appendChild(d);
      }"""
new_items = """      const mkItem = (k)=>{
        const it=ITEMS[k];
        const got = Math.min(itemProgress(p,k), it.cost);
        const d=document.createElement('div'); d.className='item'+(p.ap<(it.build?BUILD_COST:1)?' dis':'');
        const ic = itemIcon(k);
        let dots=''; for(let i=0;i<it.cost;i++) dots += `<i class="dot${i<got?' on':''}"></i>`;
        const costTxt = it.build ? `${BUILD_COST} AP` : `1 AP`;
        d.innerHTML=`<div class="it"><span>${ic?sprTag(ic,24):''}${it.build?(p.buildings[k]?'已建成 ':'前往 '):(got>0?'推进 ':'制作 ')}${it.name}</span><span class="cost">${costTxt}</span></div>
          ${(!it.build && it.cost>0)?`<div class="progrow">${dots}<b>${got}/${it.cost}</b></div>`:''}
          <div class="desc">${it.desc}${(!it.build && it.cost>1)?`<br><b>进度式</b>：每投入 1 步点亮 1 个点，集满 ${it.cost} 点后自动完成。`:''}</div>`;
        d.onclick=()=>{ if(p.ap<(it.build?BUILD_COST:1)) return; applyShopAction(p,{type:'craft',key:k}); render(); renderAll(); };
        return d;
      };
      /* 收集：武器 + 装备（非建筑、非消耗类工具） */
      const COLLECT = ['wood_sword','stone_sword','iron_sword','diamond_sword','trident','crossbow',
                       'leather','iron_armor','diamond_armor','shield','golem','fishing_rod','ender_pearl'];
      const collectList = Object.keys(ITEMS).filter(k=>{
        const it=ITEMS[k];
        if(it.prog>p.prog || it.build) return false;
        if(!COLLECT.includes(k)) return false;
        if(!it.repeat && hasItem(p,k)) return false;
        if(it.need && !hasItem(p,it.need)) return false;
        return true;
      });
      const buildList = Object.keys(ITEMS).filter(k=>{
        const it=ITEMS[k];
        if(it.prog>p.prog || !it.build) return false;
        if(!buildAllowed(p,k)) return false;
        return true;
      });
      const consumList = Object.keys(ITEMS).filter(k=>{
        const it=ITEMS[k];
        if(it.prog>p.prog || it.build) return false;
        if(COLLECT.includes(k)) return false;         /* 其余（腐肉/面包/打火石/一拳）归“补给” */
        if(!it.repeat && hasItem(p,k)) return false;
        if(it.need && !hasItem(p,it.need)) return false;
        return true;
      });
      const addGroup = (title, tip, list)=>{
        if(!list.length) return;
        grid.appendChild(groupHead(title, tip));
        for(const k of list) grid.appendChild(mkItem(k));
      };
      addGroup('🎒 收集', '制作武器与装备', collectList);
      addGroup('🧰 补给', '腐肉、面包等消耗品（可重复获取）', consumList);
      addGroup('🏠 建筑', `前往任意建筑统一 ${BUILD_COST} AP`, buildList);"""
if old_items in t:
    t = t.replace(old_items, new_items, 1); notes.append('  ok 商店分组渲染')
else:
    notes.append('  ! 商店物品循环锚点未匹配')

# ---------- 3) 行动面板：按 距离 / 攻击 / 升级 分组 ----------
old_actions = """    const attacks = opts.filter(o=>o.type==='attack'||o.type==='golem_punch'||o.type==='tnt_detonate');
    const shopBtns = opts.filter(o=>o.type==='shop_progress'||o.type==='shop_craft');
    const others  = opts.filter(o=>!attacks.includes(o) && !shopBtns.includes(o) && o.type!=='pass');
    if(attacks.length){
      const row=document.createElement('div'); row.className='actions';
      for(const o of attacks) row.appendChild(mk(o));
      bar.appendChild(row);
    }
    if(others.length){
      const row2=document.createElement('div'); row2.className='actions';
      for(const o of others) row2.appendChild(mk(o));
      bar.appendChild(row2);
    }"""
new_actions = """    const attacks = opts.filter(o=>o.type==='attack'||o.type==='golem_punch'||o.type==='tnt_detonate'||o.type==='tnt_place');
    const shopBtns = opts.filter(o=>o.type==='shop_progress'||o.type==='shop_craft');
    const moves   = opts.filter(o=>['move','pearl','rod','water','water_pull','water_pull','fish_trident'].includes(o.type) && !attacks.includes(o));
    const ups     = opts.filter(o=>['repair','enchant'].includes(o.type));
    const others  = opts.filter(o=>!attacks.includes(o)&&!shopBtns.includes(o)&&!moves.includes(o)&&!ups.includes(o)&&o.type!=='pass');
    const addRow = (title, list, tip)=>{
      if(!list.length) return;
      const h=document.createElement('div');
      h.className='grouphead';
      h.innerHTML = `<b>${title}</b>${tip?`<span>${tip}</span>`:''}`;
      bar.appendChild(h);
      const row=document.createElement('div'); row.className='actions';
      for(const o of list) row.appendChild(mk(o));
      bar.appendChild(row);
    };
    addRow('🎒 收集 / 补给', others, '腐肉、面包、水、切换工具等');
    addRow('📏 距离', moves, '走位 1 格 = 1 步；末影珍珠 ±2；钓鱼竿可拉人');
    addRow('⚔️ 攻击', attacks, '近战需 0 格；判定平手会一直重出');
    addRow('🔧 升级', ups, '铁砧修复护甲与附魔');"""
if old_actions in t:
    t = t.replace(old_actions, new_actions, 1); notes.append('  ok 行动面板分组')
else:
    notes.append('  ! 行动面板锚点未匹配')

# ---------- 4) 分组标题样式 ----------
if '.shopgroup{' not in t:
    css = """
.shopgroup{grid-column:1/-1;display:flex;align-items:baseline;gap:8px;margin:10px 0 2px;
  padding-bottom:4px;border-bottom:1px dashed var(--line);font-size:13.5px}
.shopgroup b{color:var(--acc2)}
.shopgroup span{color:var(--dim);font-size:11.5px}
.grouphead{display:flex;align-items:baseline;gap:8px;margin:6px 0 0;font-size:12.5px}
.grouphead b{color:var(--acc2)}
.grouphead span{color:var(--dim);font-size:11.5px}
"""
    t = t.replace('.hidden{display:none !important}', '.hidden{display:none !important}' + css, 1)
    notes.append('  ok 分组样式')
else:
    notes.append('  - 分组样式已存在')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
