# -*- coding: utf-8 -*-
"""补丁 125：从备份恢复 → 整块重写两处 TNT 选项 → 叠加 AI 改进
   步骤清晰，每步都验证。
"""
import pathlib, re

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
BAK = D / 'index.prev.html'

# ---------- 1) 恢复 ----------
t = BAK.read_text(encoding='utf-8')
print('① 已从备份恢复: %.0f KB' % (len(t)/1024))

# ---------- 2) 整块重写两处 TNT 选项 ----------
# 用正则匹配：注释 /* TNT */ 起，到配对的 '  }' 结束（两种内部写法都兼容）
pat = re.compile(
    r"( *)//\* TNT \*/\n( *)if\(hasItem\(p,'tnt'\)[^\n]*\)\{\n(?:.*?\n)*?\2\}",
    re.M
)

def repl_ai(m):
    ind, ind2 = m.group(1), m.group(2)
    return (f"{ind}/* TNT */\n"
            f"{ind}if(hasItem(p,'tnt') && featOn('tnt')){{\n"
            f"{ind}  if(p.flags.tntOn!==null && p.flags.tntOn!==undefined && P(p.flags.tntOn) && P(p.flags.tntOn).alive){{\n"
            f"{ind}    push({{type:'tnt_detonate',cost:ATK_COST,label:'引爆 TNT'}});\n"
            f"{ind}  }} else {{\n"
            f"{ind}    for(const e of enemies.filter(e=>distanceBetween(p,e)===0)) push({{type:'tnt_place',targetId:e.id,cost:ATK_COST,label:'贴 TNT'}});\n"
            f"{ind}  }}\n"
            f"{ind}}}")

def repl_human(m):
    ind = m.group(1)
    return (f"{ind}/* TNT */\n"
            f"{ind}if(hasItem(p,'tnt') && featOn('tnt')){{\n"
            f"{ind}  if(p.flags.tntOn!==null && p.flags.tntOn!==undefined && P(p.flags.tntOn) && P(p.flags.tntOn).alive){{\n"
            f"{ind}    push({{type:'tnt_detonate',cost:ATK_COST,label:`💥 引爆 ${{P(p.flags.tntOn).name}} 头上的 TNT（1 AP）`}});\n"
            f"{ind}  }} else {{\n"
            f"{ind}    for(const e of enemies) push({{type:'tnt_place',targetId:e.id,cost:ATK_COST,label:`🧨 把 TNT 黏在 ${{e.name}} 头上（1 AP，需 0 格）`, needDist0:true}});\n"
            f"{ind}  }}\n"
            f"{ind}}}")

# 找所有 /* TNT */ 块
matches = list(pat.finditer(t))
print('② 找到 TNT 块:', len(matches))
for m in reversed(matches):
    seg = m.group(0)
    is_human = '💥' in seg
    new_seg = repl_human(m) if is_human else repl_ai(m)
    t = t[:m.start()] + new_seg + t[m.end():]
    print('   ok 重写 %s 处（L%d）' % ('人类' if is_human else 'AI', t[:m.start()].count('\n') + 1))

IDX.write_text(t, encoding='utf-8')

# ---------- 3) 验证 TNT 结构 ----------
js = t.split('<script>')[1].split('</script>')[0]
import subprocess, os
tmp = pathlib.Path(os.environ['TEMP']) / 'chk125.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('③ 语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])

print()
print('--- TNT 块现状 ---')
for i, l in enumerate(js.split('\n'), 1):
    if 'tnt_detonate' in l and 'push' in l:
        print('  ', l.strip()[:110])
