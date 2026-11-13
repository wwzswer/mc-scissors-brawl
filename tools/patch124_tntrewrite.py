# -*- coding: utf-8 -*-
"""补丁 124：整块重写两处 TNT 选项（修复结构损坏）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
lines = IDX.read_text(encoding='utf-8').split('\n')
print('原文行数:', len(lines))

# ---- 第一处（人类）：L1470-1476 ----
# /* TNT */ … } 结尾
start1 = None
for i, l in enumerate(lines):
    if l.strip() == '/* TNT */' and "'tnt_detonate'" in lines[i+1] and '💥' in lines[i+1]:
        start1 = i
        break
if start1 is None:
    print('! 未找到第一处 TNT 块')
else:
    end1 = start1
    for j in range(start1, start1 + 12):
        if lines[j].strip() == '}':
            end1 = j
            break
    print('第一处: L%d-%d' % (start1+1, end1+1))
    for k in range(start1, end1+1):
        print('   旧:', lines[k].strip()[:100])
    new1 = [
        '  /* TNT */',
        "  if(hasItem(p,'tnt') && featOn('tnt')){",
        "    if(p.flags.tntOn!==null && p.flags.tntOn!==undefined && P(p.flags.tntOn) && P(p.flags.tntOn).alive){",
        "      push({type:'tnt_detonate',cost:ATK_COST,label:`💥 引爆 ${P(p.flags.tntOn).name} 头上的 TNT（1 AP）`});",
        "    } else {",
        "      for(const e of enemies) push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:`🧨 把 TNT 黏在 ${e.name} 头上（1 AP，需 0 格）`, needDist0:true});",
        "    }",
        "  }",
    ]
    lines[start1:end1+1] = new1

# ---- 第二处（AI）----
start2 = None
for i, l in enumerate(lines):
    if l.strip() == '/* TNT */' and "'tnt_detonate'" in lines[i+1] and '引爆 TNT' in lines[i+1]:
        start2 = i
        break
if start2 is None:
    print('! 未找到第二处 TNT 块')
else:
    end2 = start2
    for j in range(start2, start2 + 12):
        if lines[j].strip() == '}':
            end2 = j
            break
    print('第二处: L%d-%d' % (start2+1, end2+1))
    for k in range(start2, end2+1):
        print('   旧:', lines[k].strip()[:100])
    new2 = [
        '  /* TNT */',
        "  if(hasItem(p,'tnt') && featOn('tnt')){",
        "    if(p.flags.tntOn!==null && p.flags.tntOn!==undefined && P(p.flags.tntOn) && P(p.flags.tntOn).alive){",
        "      push({type:'tnt_detonate',cost:ATK_COST,label:'引爆 TNT'});",
        "    } else {",
        "      for(const e of enemies.filter(e=>distanceBetween(p,e)===0)) push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:'贴 TNT'});",
        "    }",
        "  }",
    ]
    lines[start2:end2+1] = new2

IDX.write_text('\n'.join(lines), encoding='utf-8')
print('新行数:', len(lines))

back = IDX.read_text(encoding='utf-8')
print()
print('--- 校验 ---')
js = back.split('<script>')[1].split('</script>')[0]
for i, l in enumerate(js.split('\n'), 1):
    if 'tnt_detonate' in l and 'push' in l:
        print('  ', l.strip()[:110])
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(js, encoding='utf-8')
