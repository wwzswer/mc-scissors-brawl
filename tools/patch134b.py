# -*- coding: utf-8 -*-
"""补丁 134b：距离上限拦截（不消耗 AP）
   先在备份上操作，用清晰的字符串处理避免引号转义问题。
"""
import pathlib, os, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
BAK = D / 'index.prev.html'

t = BAK.read_text(encoding='utf-8')
print('从备份恢复: %.0f KB' % (len(t) / 1024))

# JS 片段用占位符写，最后统一替换，彻底避开引号地狱
BLOCK = """$IND/* 【前置检查】距离已达上限且要拉远 → 拒绝，不消耗 AP */
$INDconst _MT = (a.targetId!==undefined && a.targetId!==null) ? P(a.targetId) : null;
$INDif(_MT && (a.dir===+1 || (a.type===__Q__pearl__Q__ && a.dir===+2))){
$IND  if(distanceBetween(p, _MT) >= MAX_DIST){
$IND    log(__B__📏 与 ${lname(_MT)} 的距离已达上限（${MAX_DIST} 格），无法再拉开，未消耗 AP。__B__,__Q__l-warn__Q__);
$IND    return;
$IND  }
$IND}
"""

lines = t.split('\n')
n = 0
for i, l in enumerate(lines):
    if 'const mc = Math.max(1, a.cost || MOVE_COST);' in l:
        ind = l[:len(l) - len(l.lstrip())]
        blk = BLOCK.replace('$IND', ind).replace('__Q__', "'").replace('__B__', '`')
        for off, b in enumerate(blk.rstrip('\n').split('\n')):
            lines.insert(i + off, b)
        n += 1
        print('L%d 前插入 %d 行' % (i + 1, blk.count('\n')))
        break

t = '\n'.join(lines)
IDX.write_text(t, encoding='utf-8')
print('插入 %d 处' % n)

print()
print('--- 插入内容预览 ---')
for i, l in enumerate(t.split('\n'), 1):
    if '无法再拉开' in l:
        print('  L%d: %s' % (i, l.strip()[:170]))

js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk134b.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print()
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:400])
