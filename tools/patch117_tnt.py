# -*- coding: utf-8 -*-
"""补丁 117：修复被门控补丁破坏的 if-else 结构（TNT 选项）
   错误结构：
     if(已贴TNT) if(featOn) push(引爆);
     else for(e of enemies) if(featOn) push(粘贴);     ← else 绑到了内层 if
   正确结构：
     if(featOn('tnt')){
       if(已贴TNT) push(引爆);
       else for(e of enemies) push(粘贴);
     }
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
lines = IDX.read_text(encoding='utf-8').split('\n')

start = None
for i, l in enumerate(lines):
    if "/* TNT */" in l:
        start = i
        break

if start is None:
    print('! 未找到 /* TNT */ 标记')
else:
    # 找到该块的结束（下一个 /* 铁砧 */ 或类似注释）
    end = None
    for j in range(start + 1, min(start + 20, len(lines))):
        if '/*' in lines[j] and 'TNT' not in lines[j]:
            end = j
            break
    if end is None:
        print('! 未找到 TNT 块结束')
    else:
        indent = '  '
        new_block = [
            '  /* TNT */',
            "  if(hasItem(p,'tnt') && featOn('tnt')){",
            "    if(p.flags.tntOn!==undefined && p.flags.tntOn!==null && P(p.flags.tntOn) && P(p.flags.tntOn).alive){",
            "      push({type:'tnt_detonate',cost:ATK_COST,label:`💥 引爆 ${P(p.flags.tntOn).name} 头上的 TNT（1 AP）`});",
            "    } else {",
            "      for(const e of enemies) push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:`🧨 把 TNT 黏在 ${e.name} 头上（1 AP，需 0 格）`, needDist0:true});",
            "    }",
            "  }",
        ]
        old_block = lines[start:end]
        lines[start:end] = new_block
        IDX.write_text('\n'.join(lines), encoding='utf-8')
        print(f'已重写 TNT 代码块（原 L{start+1}-{end}）')
        print('  原内容:')
        for x in old_block:
            print('    ', x.strip()[:110])

back = IDX.read_text(encoding='utf-8')
print()
print('--- 校验 ---')
print("  新结构存在:", "if(hasItem(p,'tnt') && featOn('tnt')){" in back)
print("  TNT 选项数:", back.count("type:'tnt_place'"), "place /", back.count("type:'tnt_detonate'"), "detonate")

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
