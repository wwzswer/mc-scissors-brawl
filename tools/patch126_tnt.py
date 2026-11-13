# -*- coding: utf-8 -*-
"""补丁 126：逐行定位 /* TNT */ 块（括号配对找结尾）并规范重写
   备份恢复后立即执行，保证结构正确，再叠加 AI 改进。
"""
import pathlib, os, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'

lines = IDX.read_text(encoding='utf-8').split('\n')

# 找所有 /* TNT */ 起始行
starts = [i for i, l in enumerate(lines) if l.strip() == '/* TNT */']
print('找到 /* TNT */ 起始行:', [s + 1 for s in starts])

# 从后往前替换，避免行号错位
for s in reversed(starts):
    # 用花括号配平找块结尾
    depth = 0
    end = None
    for j in range(s + 1, min(s + 30, len(lines))):
        depth += lines[j].count('{') - lines[j].count('}')
        if depth == 0 and j > s + 1:
            end = j
            break
    if end is None:
        print('  ! L%d 无法配对，跳过' % (s + 1))
        continue

    indent = lines[s][:len(lines[s]) - len(lines[s].lstrip())]
    seg = '\n'.join(lines[s:end + 1])
    is_human = '💥' in seg
    print('  L%d-%d %s' % (s + 1, end + 1, '人类' if is_human else 'AI'))

    if is_human:
        new = [
            indent + '/* TNT */',
            indent + "if(hasItem(p,'tnt') && featOn('tnt')){",
            indent + "  if(p.flags.tntOn!==null && p.flags.tntOn!==undefined && P(p.flags.tntOn) && P(p.flags.tntOn).alive){",
            indent + "    push({type:'tnt_detonate',cost:ATK_COST,label:`💥 引爆 ${P(p.flags.tntOn).name} 头上的 TNT（1 AP）`});",
            indent + "  } else {",
            indent + "    for(const e of enemies) push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:`🧨 把 TNT 黏在 ${e.name} 头上（1 AP，需 0 格）`, needDist0:true});",
            indent + "  }",
            indent + "}",
        ]
    else:
        new = [
            indent + '/* TNT */',
            indent + "if(hasItem(p,'tnt') && featOn('tnt')){",
            indent + "  if(p.flags.tntOn!==null && p.flags.tntOn!==undefined && P(p.flags.tntOn) && P(p.flags.tntOn).alive){",
            indent + "    push({type:'tnt_detonate',cost:ATK_COST,label:'引爆 TNT'});",
            indent + "  } else {",
            indent + "    for(const e of enemies.filter(e=>distanceBetween(p,e)===0)) push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:'贴 TNT'});",
            indent + "  }",
            indent + "}",
        ]
    lines[s:end + 1] = new

IDX.write_text('\n'.join(lines), encoding='utf-8')

t = IDX.read_text(encoding='utf-8')
js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk126.js'
tmp.write_text(js, encoding='utf-8')
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print()
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:400])
print('文件: %.0f KB' % (len(t) / 1024))
