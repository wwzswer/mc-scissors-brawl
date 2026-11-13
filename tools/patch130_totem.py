# -*- coding: utf-8 -*-
"""补丁 130：完成 v1.5.2 的③图腾解锁式 + 药水制作
   ① 府邸改为「仅解锁」
   ② craft 完成时：totem → 获得图腾；药水 → 获得对应药水
"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

# ---------- ① 府邸改为仅解锁（逐行） ----------
lines = t.split('\n')
n1 = 0
for i, l in enumerate(lines):
    if "k==='mansion' && featOn('totem')" in l:
        # 找到该 if 块内的三行，整体替换
        j = i + 1
        blk = []
        while j < len(lines) and not lines[j].strip().startswith('}'):
            blk.append(j); j += 1
        ind = l[:len(l) - len(l.lstrip())]
        lines[i] = l  # 保留 if 行
        # 用新内容替换块内旧内容
        newbody = [
            ind + "  log('🏛️ 林地府邸已解锁：可继续投入 1 步取得【不死图腾】（在“制作 / 收集”页）。','l-good');",
        ]
        for k in reversed(blk):
            del lines[k]
        for off, nb in enumerate(newbody):
            lines.insert(i + 1 + off, nb)
        n1 += 1
        print('L%d 府邸改为仅解锁' % (i + 1))
        break

t = '\n'.join(lines)
notes.append('  ok ① 府邸改为仅解锁' if n1 else '  ! ① 府邸锚点未找到')

# ---------- ② craft 完成时给图腾 / 药水 ----------
ANCHOR = "    if(k==='village'){ p.flags.pendingBook=(p.flags.pendingBook||0)+1; log('📖 村庄送来 1 本附魔书（在铁砧处使用）','l-sys'); }"
if ANCHOR in t:
    ADD = ("    if(k==='totem'){\n"
           "      if(!p.mem.totem && !G.players.some(q=>q.mem.totem)){\n"
           "        p.mem.totem=true;\n"
           "        log('🗿 取得 <b>不死图腾</b>：倒下时复活并回复 2 生命（全局唯一）。','l-good');\n"
           "      } else log('（不死图腾全局仅 1 个，已被取走）','l-sys');\n"
           "    }\n"
           "    if(k==='potion_heal'){ addItem(p,'potion_heal',1); log('🧪 获得 <b>治疗药水</b>（立即回复 2 生命）。','l-good'); }\n"
           "    if(k==='potion_str'){ addItem(p,'potion_str',1); log('🧪 获得 <b>力量药水</b>（2 回合物理 +1）。','l-good'); }\n"
           "    if(k==='potion_swift'){ addItem(p,'potion_swift',1); log('🧪 获得 <b>迅捷药水</b>（立即 +2 AP）。','l-good'); }\n"
           + ANCHOR)
    t = t.replace(ANCHOR, ADD, 1)
    notes.append('  ok ② craft 完成时发放图腾/药水')
else:
    notes.append('  ! ② village 锚点未找到')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print('长度 →', len(back))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
