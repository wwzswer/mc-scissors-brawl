# -*- coding: utf-8 -*-
"""补丁 123：修复 TNT 选项的 if-else 绑定（AI 与人类两处）
   破坏后的结构（else 绑到内层 if）：
     if(已贴TNT) if(featOn) push(引爆);
     else for(...) if(featOn) push(粘贴);
   正确结构：
     if(p.flags.tntOn) push(引爆); else for(...) push(粘贴);
   附带：清理不再需要的多余 featOn 包裹（外层已判断）
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
lines = IDX.read_text(encoding='utf-8').split('\n')
changed = []
i = 0
while i < len(lines):
    l = lines[i]
    # 定位“已贴 TNT”判断行（两种缩进都覆盖）
    if 'tntOn!==null' in l and 'tntOn!==undefined' in l:
        indent = l[:len(l) - len(l.lstrip())]
        nxt = lines[i+1] if i+1 < len(lines) else ''
        nxt2 = lines[i+2] if i+2 < len(lines) else ''
        # 情况：下一行含 featOn + tnt_detonate
        if 'tnt_detonate' in nxt:
            # 合并为一行 if(...) push(引爆);
            merged = indent
            if nxt.strip().startswith("if(featOn('tnt'))"):
                merged += nxt.strip()[len("if(featOn('tnt'))"):].strip()
            else:
                merged += nxt.strip()
            lines[i] = merged
            del lines[i+1]
            changed.append('L%d 引爆分支合并' % (i+1))
            # 处理随后的 else for(...) 行：去掉多余 featOn
            for j in range(i+1, min(i+4, len(lines))):
                if lines[j].strip().startswith('else for('):
                    lines[j] = lines[j]
                    changed.append('L%d else 归位' % (j+1))
                    # 下一行若为 if(featOn) push(粘贴) → 去掉外层 if
                    k = j + 1
                    if k < len(lines) and 'tnt_place' in lines[k] and "if(featOn('tnt'))" in lines[k]:
                        ind2 = lines[k][:len(lines[k]) - len(lines[k].lstrip())]
                        lines[k] = ind2 + lines[k].strip()[len("if(featOn('tnt'))"):].strip()
                        changed.append('L%d 粘贴分支去掉重复 featOn' % (k+1))
                    break
            i += 1
            continue
    i += 1

IDX.write_text('\n'.join(lines), encoding='utf-8')
print('修复：')
for c in changed: print('  ok', c)
if not changed: print('  ! 无修改')

back = IDX.read_text(encoding='utf-8')
js = back.split('<script>')[1].split('</script>')[0]
print()
print('--- 校验 ---')
for n, l in enumerate(js.split('\n'), 1):
    if 'tnt_detonate' in l or ('tnt_place' in l and 'push' in l):
        print('  ', l.strip()[:120])
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(js, encoding='utf-8')
