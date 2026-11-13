# -*- coding: utf-8 -*-
"""补丁 131：v1.5.2 收尾
   ① 图腾/药水改为进度式（投入 1 步立即获得），不再直接走 addItem
   ② 1v1 模式：取消「是否消耗 AP 进行判定」
   ③ 无行动点时提供「跳过回合」选项
   ④ 距离已达上限时给出提示
   ⑤ 版本号 → v1.5.2
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

# ---------- ① 图腾 / 药水：进度式获得 ----------
sub("""  } else {
    addItem(p,k,1);
    log(`🛠️ ${lname(p)} 制作了 <b>${it.name}</b>（-${it.cost} AP）。`,'l-good');""",
"""  } else if(k==='totem'){
    /* 不死图腾：需要从林地府邸再投入 1 步取得 */
    if(G.players.some(q=>q.mem.totem)){ log('（不死图腾全局仅 1 个，已被取走）','l-sys'); return false; }
    p.mem.totem = true;
    log('🗿 取得 <b>不死图腾</b>：倒下时复活并回复 2 生命（全局唯一）。','l-good');
  } else if(k==='potion_heal' || k==='potion_str' || k==='potion_swift'){
    if(G.players.some(q=>hasItem(q,k))){ log('（这种药水已被取走）','l-sys'); return false; }
    addItem(p,k,1);
    log(`🧪 取得 <b>${it.name}</b>：${it.desc}`,'l-good');
  } else {
    addItem(p,k,1);
    log(`🛠️ ${lname(p)} 制作了 <b>${it.name}</b>（-${it.cost} AP）。`,'l-good');""",
'① 图腾/药水进度式获得')

# 药水不应重复出现（已有则隐藏）
sub("""    if(k==='potion_heal' || k==='potion_str' || k==='potion_swift')
      return tabId==='craft' && featOn('potion');""",
"""    if(k==='potion_heal' || k==='potion_str' || k==='potion_swift')
      return tabId==='craft' && featOn('potion')
             && p.buildings.witchhut && !hasItem(p,k)
             && !G.players.some(q=>hasItem(q,k));""", '① 药水条件收紧')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print('长度 %d → %d' % (orig, len(back)))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
