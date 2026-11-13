# -*- coding: utf-8 -*-
"""补丁 134：距离上限拦截（不消耗 AP）+ 无行动点的跳过回合"""
import pathlib

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
BAK = D / 'index.prev.html'

# 先用备份恢复（上一次插入把模板字符串写坏了）
t = BAK.read_text(encoding='utf-8')
print('已从备份恢复: %.0f KB' % (len(t)/1024))
IDX.write_text(t, encoding='utf-8')

lines = t.split('\n')
n = 0
for i, l in enumerate(lines):
    if 'const mc = Math.max(1, a.cost || MOVE_COST);' in l:
        ind = l[:len(l) - len(l.lstrip())]
        block = [
            ind + '/* 【前置检查】距离已达上限且要拉远 → 拒绝，不消耗 AP */',
            ind + 'const _MT = (a.targetId!==undefined && a.targetId!==null) ? P(a.targetId) : null;',
            ind + 'if(_MT && (a.dir===+1 || (a.type===' + "'pearl'" + ' && a.dir===+2))){',
            ind + '  if(distanceBetween(p, _MT) >= MAX_DIST){',
            ind + '    log(' + "'" + '\U0001F4CF 与 ' + "' + lname(_MT) + '" + ' 的距离已达上限（' + "' + MAX_DIST + '" + ' 格），无法再拉开，未消耗 AP。' + "'" + ",'l-warn');",
            ind + '    return;',
            ind + '  }',
            ind + '}',
        ]
        for off, b in enumerate(block):
            lines.insert(i + off, b)
        n += 1
        print('L%d 前插入距离上限拦截' % (i + 1))
        break

t = '\n'.join(lines)
IDX.write_text(t, encoding='utf-8')
print('插入 %d 处' % n)
print()
print('--- 插入内容预览 ---')
for i, l in enumerate(t.split('\n'), 1):
    if '距离已达上限（' in l and 'log(' in l:
        print('  L%d: %s' % (i, l.strip()[:160]))

import os, subprocess
js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk134.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print()
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
