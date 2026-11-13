# -*- coding: utf-8 -*-
"""补丁 138：用花括号配对精确定位，把 totem / 药水插入 ITEMS 对象末尾"""
import pathlib, os, subprocess, re

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
t = IDX.read_text(encoding='utf-8')
orig = len(t)

# 精确定位 ITEMS 对象
i = t.find('const ITEMS = {')
depth = 0; started = False; end = None
for k in range(i, len(t)):
    c = t[k]
    if c == '{':
        depth += 1; started = True
    elif c == '}':
        depth -= 1
        if started and depth == 0:
            end = k; break
if end is None:
    raise SystemExit('无法定位 ITEMS 对象结尾')

# 在结尾 '}' 之前插入（end 指向 '}'，前面有换行）
insert_at = t.rfind('\n', i, end) + 1
print('ITEMS 对象: %d ~ %d，插入点 %d' % (i, end, insert_at))
print('插入点前一行: %s' % t[:insert_at].rsplit('\n', 2)[-2].strip()[:90])

NEW = (
    "  /* 一次性道具（需先解锁对应建筑） */\n"
    "  totem:      { name:'不死图腾', cost:1, prog:PROG.WOOD, desc:'前置：建造林地府邸。投入 1 步取得：倒下时复活并回复 2 生命（全局仅 1 个）。' },\n"
    "  potion_heal:{ name:'治疗药水', cost:1, prog:PROG.WOOD, desc:'前置：建造女巫小屋。投入 1 步取得：立即回复 2 生命（每种药水全局仅 1 个）。' },\n"
    "  potion_str: { name:'力量药水', cost:1, prog:PROG.WOOD, desc:'前置：建造女巫小屋。投入 1 步取得：接下来 2 回合物理伤害 +1（每种药水全局仅 1 个）。' },\n"
    "  potion_swift:{ name:'迅捷药水', cost:1, prog:PROG.WOOD, desc:'前置：建造女巫小屋。投入 1 步取得：立即获得 2 AP（每种药水全局仅 1 个）。' },\n"
)
t = t[:insert_at] + NEW + t[insert_at:]
IDX.write_text(t, encoding='utf-8')
print('已插入 4 个条目，长度 %d → %d' % (orig, len(t)))

# 校验：插入点必须在 ITEMS 对象内部
k2 = t.find("totem:      { name:'不死图腾'")
i2 = t.find('const ITEMS = {')
depth = 0; started = False; end2 = None
for k in range(i2, len(t)):
    c = t[k]
    if c == '{':
        depth += 1; started = True
    elif c == '}':
        depth -= 1
        if started and depth == 0:
            end2 = k; break
print('totem 在 ITEMS 对象内:', i2 < k2 < end2)

js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk138.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
