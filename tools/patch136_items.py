# -*- coding: utf-8 -*-
"""补丁 136：把 totem / 三种药水加入真正的 ITEMS 对象
   定位方式：找到 ITEMS 对象里 firework 那一行，在其后插入；不再依赖文本匹配。
"""
import pathlib, os, subprocess, re

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
t = IDX.read_text(encoding='utf-8')
js = t.split('<script>')[1].split('</script>')[0]

# 找 ITEMS 对象的起始
i = js.find('const ITEMS = {')
if i < 0:
    raise SystemExit('未找到 ITEMS')
# 找 firework 定义行（ITEMS 内最后一个道具）
seg_end = js.find('const ENCH = {', i)
if seg_end < 0:
    seg_end = js.find('const ENCH_ORDER', i)
if seg_end < 0:
    seg_end = i + 6000
seg = js[i:seg_end]

m = re.search(r"^(\s*)firework:\s*\{[^\n]*\n", seg, re.M)
if not m:
    raise SystemExit('未找到 firework 条目')
ind = m.group(1)
print('firework 缩进: %r' % ind)
print('原行:', m.group(0).strip()[:120])

insert_at = i + m.end()
NEW = (
    ind + "totem:      { name:'不死图腾', cost:1, prog:PROG.WOOD, repeat:false, desc:'前置：建造林地府邸。投入 1 步取得不死图腾：倒下时复活并回复 2 生命（全局仅 1 个）。' },\n"
    + ind + "potion_heal:{ name:'治疗药水', cost:1, prog:PROG.WOOD, repeat:false, desc:'前置：建造女巫小屋。投入 1 步取得：立即回复 2 生命（每种药水全局仅 1 个）。' },\n"
    + ind + "potion_str: { name:'力量药水', cost:1, prog:PROG.WOOD, repeat:false, desc:'前置：建造女巫小屋。投入 1 步取得：接下来 2 回合物理伤害 +1（每种药水全局仅 1 个）。' },\n"
    + ind + "potion_swift:{ name:'迅捷药水', cost:1, prog:PROG.WOOD, repeat:false, desc:'前置：建造女巫小屋。投入 1 步取得：立即获得 2 AP（每种药水全局仅 1 个）。' },\n"
)
t = t[:insert_at] + NEW + t[insert_at:]
IDX.write_text(t, encoding='utf-8')
print('已在 ITEMS 内插入 4 个条目')

back = IDX.read_text(encoding='utf-8')
j2 = back.split('<script>')[1].split('</script>')[0]
print('ITEMS 里有 totem:', "totem:      { name:'不死图腾', cost:1" in j2)

tmp = pathlib.Path(os.environ['TEMP']) / 'chk136.js'
tmp.write_text(j2, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:400])
