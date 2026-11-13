# -*- coding: utf-8 -*-
"""补丁 137：正确地在 ITEMS 内插入 totem / 药水（修正偏移量错误）"""
import pathlib, os, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
BAK = D / 'index.prev.html'

t = BAK.read_text(encoding='utf-8')
print('从备份恢复: %.0f KB' % (len(t) / 1024))

# 在【整个文件】里定位 firework 那一行（文件级偏移，避免 js 内偏移与文件偏移混用）
key = "  firework:   { name:'烟花'"
pos = t.find(key)
if pos < 0:
    # 退化：只找 firework: { name:'烟花'
    key = "firework:   { name:'烟花'"
    pos = t.find(key)
if pos < 0:
    raise SystemExit('未找到 firework 条目')
line_end = t.find('\n', pos) + 1
print('firework 行位置(文件级): %d' % pos)
print('原行: %s' % t[pos:line_end].strip()[:110])

NEW = (
    "  totem:      { name:'不死图腾', cost:1, prog:PROG.WOOD, desc:'前置：建造林地府邸。投入 1 步取得：倒下时复活并回复 2 生命（全局仅 1 个）。' },\n"
    "  potion_heal:{ name:'治疗药水', cost:1, prog:PROG.WOOD, desc:'前置：建造女巫小屋。投入 1 步取得：立即回复 2 生命（每种药水全局仅 1 个）。' },\n"
    "  potion_str: { name:'力量药水', cost:1, prog:PROG.WOOD, desc:'前置：建造女巫小屋。投入 1 步取得：接下来 2 回合物理伤害 +1（每种药水全局仅 1 个）。' },\n"
    "  potion_swift:{ name:'迅捷药水', cost:1, prog:PROG.WOOD, desc:'前置：建造女巫小屋。投入 1 步取得：立即获得 2 AP（每种药水全局仅 1 个）。' },\n"
)
t = t[:line_end] + NEW + t[line_end:]
IDX.write_text(t, encoding='utf-8')
print('已在 firework 行后插入 4 个条目')

# 校验：确认插入点在 ITEMS 对象内部
seg_start = t.find('const ITEMS = {')
seg_end = t.find('const ENCH_ORDER', seg_start)
ins = t.find("totem:      { name:'不死图腾'")
ok_inside = seg_start < ins < seg_end
print('插入点在 ITEMS 对象内:', ok_inside)

js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk137.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
