# -*- coding: utf-8 -*-
"""补丁 145：为外部驱动（QQ 机器人）加出拳钩子
   ① 新增 let rpsExternal = null
   ② humanRps 的非 autoMode 分支优先用钩子
   ③ 导出 setRpsExternal
   单机不受影响：钩子为 null 时照旧弹窗。
"""
import pathlib, os, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
t = IDX.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ① 声明钩子
sub("let autoPlayer = null;",
    "let autoPlayer = null;\n/* 外部出拳钩子（QQ 机器人 / 无头驱动用）：为 null 时照旧弹窗让玩家点 */\nlet rpsExternal = null;",
    '① 声明 rpsExternal')

# ② humanRps 使用钩子
sub("""    document.getElementById('rpsArea').classList.remove('hidden');
    const st2 = document.getElementById('rpsStatus');
    if(st2) st2.textContent = '本回合猜拳——选择你的出拳';
    my = await rpsPrompt(null);""",
"""    document.getElementById('rpsArea').classList.remove('hidden');
    const st2 = document.getElementById('rpsStatus');
    if(st2) st2.textContent = '本回合猜拳——选择你的出拳';
    my = rpsExternal ? await rpsExternal(p) : await rpsPrompt(null);""",
'② humanRps 使用钩子')

# ③ 导出
sub("    setAutoPlayer(fn){ autoPlayer = fn; },",
    "    setAutoPlayer(fn){ autoPlayer = fn; },\n    setRpsExternal(fn){ rpsExternal = fn; },",
    '③ 导出到 __api')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
print('长度 %d → %d' % (orig, len(t)))
js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk145.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
