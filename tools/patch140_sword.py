# -*- coding: utf-8 -*-
"""补丁 140：钻石剑的 A/B 选择权应属于【攻击方】
   原代码 if(target.isHuman) → 打 AI 时不问玩家、AI 打玩家时反而问玩家（完全反了）
"""
import pathlib, os, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
t = IDX.read_text(encoding='utf-8')
orig = len(t)

OLD = """function chooseArmorMode(attacker, target){
  if(target.isHuman){"""
NEW = """function chooseArmorMode(attacker, target){
  /* 选择权属于【攻击方】：你持钻石剑出手 → 你来选；AI 出手 → AI 自己决定 */
  if(attacker.isHuman){"""
if OLD in t:
    t = t.replace(OLD, NEW, 1)
    print('ok 钻石剑选择权改为攻击方')
else:
    print('! 锚点未匹配')

IDX.write_text(t, encoding='utf-8')
print('长度 %d → %d' % (orig, len(t)))
js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk140.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])

# 顺带查看判定日志的措辞（排查"赢了却显示失败"）
print()
print('=== doJudgment 的日志措辞 ===')
i = js.find('async function doJudgment')
depth = 0; started = False; end = None
for k in range(i, len(js)):
    c = js[k]
    if c == '{':
        depth += 1; started = True
    elif c == '}':
        depth -= 1
        if started and depth == 0:
            end = k; break
seg = js[i:end+1]
import re
for m in re.finditer(r"log\(`([^`]{0,110})`", seg):
    print('  ', m.group(1))
