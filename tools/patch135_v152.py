# -*- coding: utf-8 -*-
"""补丁 135：在当前版本（已含距离上限拦截）上补齐 v1.5.2 其余改动
   ① 去掉制作标签页下方重复按钮行
   ② 标签页网格补沙漠金字塔的 TNT / 金苹果
   ③ 林地府邸改为「仅解锁」，不死图腾需要再投入 1 步
   ④ 1v1 取消「是否消耗 AP 判定」
   ⑤ 距离已达上限时显示提示按钮
   ⑥ 版号 → v1.5.2
"""
import pathlib, os, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
t = IDX.read_text(encoding='utf-8')
orig = len(t)
Q = "'"
B = '`'
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ---------- ① 去掉重复按钮行 ----------
OLD1 = """  /* 制作 / 建筑 两个标签页：先给出物品卡片网格，再给出行内动作按钮 */
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
}"""
NEW1 = """  /* 制作 / 建筑：只显示物品卡片网格（不再重复列出按钮） */
  if(tabId==='craft' || tabId==='build'){
    const grid = renderItemGrid(p, tabId);
    if(grid) body.appendChild(grid);
    else {
      const hint = document.createElement('span');
      hint.className = 'pill';
      hint.textContent = '（暂时没有可制作的内容）';
      body.appendChild(hint);
    }
    return;
  }

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
}"""
sub(OLD1, NEW1, '① 去掉重复按钮行')

# ---------- ② 网格补金字塔选项 ----------
OLD2 = """  const wrap = document.createElement('div');
  if(tabId==='craft'){
    const tip = document.createElement('div');
    tip.className = 'tabtip';
    tip.textContent = '进度式：多步物品每投入 1 步点亮 1 个点，集满后自动完成并保存进度。已解锁进程的物品随时都能再做（升级后腐肉、木剑等不会消失）。';
    wrap.appendChild(tip);
  } else {"""
NEW2 = """  const wrap = document.createElement('div');
  /* 沙漠金字塔：一次性道具（TNT / 附魔金苹果）—— 建好后立即出现在这里 */
  if(tabId==='craft' && p.buildings.pyramid){
    if(featOn('tnt') && !G.players.some(q=>q.flags.tntGlobal)){
      const d = document.createElement('div');
      d.className = 'item' + (p.ap<1?' dis':'');
      d.innerHTML = `<div class="it"><span>\U0001F3DC️ 取 TNT ×4（全局唯一）</span><span class="cost">1 AP</span></div>
        <div class="desc">从沙漠金字塔取得 4 个 TNT。${SPECIALS.tnt.desc}</div>`;
      d.onclick = ()=>{ if(p.ap<1) return; applyShopAction(p,{type:'buy_tnt'}); renderAll(); };
      wrap.appendChild(d);
    }
    if(featOn('god_apple') && !G.players.some(q=>q.flags.godAppleGlobal)){
      const d = document.createElement('div');
      d.className = 'item' + (p.ap<1?' dis':'');
      d.innerHTML = `<div class="it"><span>\U0001F3DC️ 取 附魔金苹果（全局唯一）</span><span class="cost">1 AP</span></div>
        <div class="desc">从沙漠金字塔取得 1 个附魔金苹果。${SPECIALS.god_apple.desc}</div>`;
      d.onclick = ()=>{ if(p.ap<1) return; applyShopAction(p,{type:'buy_apple'}); renderAll(); };
      wrap.appendChild(d);
    }
  }
  if(tabId==='craft'){
    const tip = document.createElement('div');
    tip.className = 'tabtip';
    tip.textContent = '进度式：多步物品每投入 1 步点亮 1 个点，集满后自动完成并保存进度。已解锁进程的物品随时都能再做（升级后腐肉、木剑等不会消失）。';
    wrap.appendChild(tip);
  } else {"""
sub(OLD2, NEW2, '② 网格补金字塔')

# ---------- ③ 府邸仅解锁 ----------
OLD3 = """  if(k==='mansion' && featOn('totem')){
    if(!featOn('totem')) log('（不死图腾已在设置中禁用）','l-sys');
    if(G.players.some(q=>q.mem.totem)) log('（不死图腾全局仅 1 个，已被取走）','l-sys');
    else { p.mem.totem=true; log('\U0001F5FF 取得 <b>不死图腾</b>：倒下时复活并回复 2 生命（全局唯一）。','l-good'); }
  }"""
NEW3 = """  if(k==='mansion' && featOn('totem')){
    log('\U0001F3DB️ 林地府邸已解锁：可继续投入 1 步取得【不死图腾】（在“制作 / 收集”页）。','l-good');
  }"""
sub(OLD3, NEW3, '③ 府邸仅解锁')

# 图腾 / 药水进入制作页 + craft 完成时发放
sub("""    if(tabId==='build') return !!it.build && buildAllowed(p,k);""",
"""    if(k==='totem') return tabId==='craft' && featOn('totem') && p.buildings.mansion
                        && !G.players.some(q=>q.mem.totem);
    if(k==='potion_heal' || k==='potion_str' || k==='potion_swift')
      return tabId==='craft' && featOn('potion') && p.buildings.witchhut
             && !hasItem(p,k) && !G.players.some(q=>hasItem(q,k));
    if(tabId==='build') return !!it.build && buildAllowed(p,k);""", '③ 图腾/药水进入制作页')

sub("""  } else {
    addItem(p,k,1);
    log(`\U0001F6E0️ ${lname(p)} 制作了 <b>${it.name}</b>（-${it.cost} AP）。`,'l-good');""",
"""  } else if(k==='totem'){
    if(G.players.some(q=>q.mem.totem)){ log('（不死图腾全局仅 1 个，已被取走）','l-sys'); return false; }
    p.mem.totem = true;
    log('\U0001F5FF 取得 <b>不死图腾</b>：倒下时复活并回复 2 生命（全局唯一）。','l-good');
  } else if(k==='potion_heal' || k==='potion_str' || k==='potion_swift'){
    if(G.players.some(q=>hasItem(q,k))){ log('（这种药水已被取走）','l-sys'); return false; }
    addItem(p,k,1);
    log(`\U0001F9EA 取得 <b>${it.name}</b>：${it.desc}`,'l-good');
  } else {
    addItem(p,k,1);
    log(`\U0001F6E0️ ${lname(p)} 制作了 <b>${it.name}</b>（-${it.cost} AP）。`,'l-good');""",
'③ 图腾/药水发放')

# ---------- ④ 1v1 取消闪避询问 ----------
sub("""      else if(target.isHuman){ rlog('平局: 等待玩家选择闪避/赌一把…'); wantsDodge = await askDodge(target, attacker); rlog('平局: 玩家已选择 dodge=' + wantsDodge); }""",
"""      else if(target.isHuman){
        /* 1v1：只有两人，没有"赌一把"的空间 → 直接重新判定，不弹选择 */
        if(G.players.filter(q=>q.alive).length === 2){
          rlog('平局: 1v1 模式直接重新判定');
          wantsDodge = false;
        } else {
          rlog('平局: 等待玩家选择闪避/赌一把…');
          wantsDodge = await askDodge(target, attacker);
          rlog('平局: 玩家已选择 dodge=' + wantsDodge);
        }
      }""", '④ 1v1 取消闪避询问')

# ---------- ⑤ 距离上限提示按钮 ----------
sub("""    if(d<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:`\U0001F463 后退，与 ${e.name} 拉开 1 格（1 AP）`});""",
"""    if(d>=MAX_DIST) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,disabled:true,label:`\U0001F4CF 与 ${e.name} 已达最远距离（${MAX_DIST} 格）`});
    else if(d<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:`\U0001F463 后退，与 ${e.name} 拉开 1 格（1 AP）`});""",
'⑤ 距离上限提示（人类）')

sub("""    const extra = (o.cost||0)+slot;
    const fixed = (extra===Infinity) ? '行动点不足' : (extra>0 ? `${extra} AP` : '免费');
    b.textContent = o.label + ' · ' + fixed;
    b.disabled = (extra===Infinity);""",
"""    const extra = (o.cost||0)+slot;
    const fixed = (extra===Infinity) ? '行动点不足' : (extra>0 ? `${extra} AP` : '免费');
    b.textContent = o.disabled ? o.label : (o.label + ' · ' + fixed);
    b.disabled = !!(o.disabled || extra===Infinity);""", '⑤ 按钮支持 disabled')

# ---------- ⑥ 版号 ----------
sub('基础版 v1.5.1', '基础版 v1.5.2', '⑥ 版号 v1.5.2')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print('长度 %d → %d' % (orig, len(back)))
js = back.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk135.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:400])
