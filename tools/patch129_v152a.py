# -*- coding: utf-8 -*-
"""补丁 129：v1.5.2 —— 7 项改动
   ① 制作标签页：去掉下方重复的「制作 XXX」按钮行（只保留卡片）
   ② 标签页里补上沙漠金字塔的 TNT / 附魔金苹果一次性选项
   ③ 不死图腾改为「需要再投入 1 步」而非解锁府邸即得
   ④ 1v1 模式：取消「是否消耗 AP 进行判定」的选择
   ⑤ 无行动点时提供「跳过回合」选项
   ⑥ 距离已达上限时给出提示（不消耗 AP）
   ⑦ 版本号 → v1.5.2
"""
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

# ---------- ① 去掉 craft/build 标签页下方重复按钮 ----------
sub("""  /* 制作 / 建筑 两个标签页：先给出物品卡片网格，再给出行内动作按钮 */
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
}""",
"""  /* 制作 / 建筑 两个标签页：只显示物品卡片网格（不再重复列出按钮） */
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
}""", '① 去掉重复按钮行')

# ---------- ② 标签页网格补上金字塔一次性选项 ----------
sub("""  const wrap = document.createElement('div');
  if(tabId==='craft'){
    const tip = document.createElement('div');
    tip.className = 'tabtip';
    tip.textContent = '进度式：多步物品每投入 1 步点亮 1 个点，集满后自动完成并保存进度。已解锁进程的物品随时都能再做（升级后腐肉、木剑等不会消失）。';
    wrap.appendChild(tip);
  } else {""",
"""  const wrap = document.createElement('div');
  /* 沙漠金字塔：一次性道具（TNT / 附魔金苹果）—— 建好后立即出现在这里 */
  if(tabId==='craft' && p.buildings.pyramid){
    if(featOn('tnt') && !G.players.some(q=>q.flags.tntGlobal)){
      const d = document.createElement('div');
      d.className = 'item' + (p.ap<1?' dis':'');
      d.innerHTML = `<div class="it"><span>🏜️ 取 TNT ×4（全局唯一）</span><span class="cost">1 AP</span></div>
        <div class="desc">从沙漠金字塔取得 4 个 TNT。${SPECIALS.tnt.desc}</div>`;
      d.onclick = ()=>{ if(p.ap<1) return; applyShopAction(p,{type:'buy_tnt'}); renderAll(); };
      wrap.appendChild(d);
    }
    if(featOn('god_apple') && !G.players.some(q=>q.flags.godAppleGlobal)){
      const d = document.createElement('div');
      d.className = 'item' + (p.ap<1?' dis':'');
      d.innerHTML = `<div class="it"><span>🏜️ 取 附魔金苹果（全局唯一）</span><span class="cost">1 AP</span></div>
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
  } else {""", '② 网格补金字塔选项')

# ---------- ③ 不死图腾：需要再投入 1 步 ----------
sub("""      if(k==='mansion' && featOn('totem')){
        if(!featOn('totem')) log('（不死图腾已在设置中禁用）','l-sys');
        if(G.players.some(q=>q.mem.totem)) log('（不死图腾全局仅 1 个，已被取走）','l-sys');
        else { p.mem.totem=true; log('🗿 取得 <b>不死图腾</b>：倒下时复活并回复 2 生命（全局唯一）。','l-good'); }
      }""",
"""      if(k==='mansion' && featOn('totem')){
        log('🏛️ 林地府邸已解锁：可继续投入 1 步取得【不死图腾】（在“制作 / 收集”页）。','l-good');
      }""", '③ 府邸仅解锁')

sub("""  const keys = Object.keys(ITEMS).filter(k=>{
    const it = ITEMS[k];
    if(blocked(k)) return false;
    if(it.prog > p.prog) return false;
    if(tabId==='build') return !!it.build && buildAllowed(p,k);""",
"""  const keys = Object.keys(ITEMS).filter(k=>{
    const it = ITEMS[k];
    if(blocked(k)) return false;
    if(it.prog > p.prog) return false;
    if(k==='totem') return tabId==='craft' && featOn('totem') && p.buildings.mansion
                        && !G.players.some(q=>q.mem.totem);
    if(k==='potion_heal' || k==='potion_str' || k==='potion_swift')
      return tabId==='craft' && featOn('potion');
    if(tabId==='build') return !!it.build && buildAllowed(p,k);""", '③ 图腾/药水进入制作页')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print()
print('长度 %d → %d' % (orig, len(back)))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
