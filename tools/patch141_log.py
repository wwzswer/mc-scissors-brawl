# -*- coding: utf-8 -*-
"""补丁 141：判定日志措辞清晰化（消除"赢了却显示失败"的歧义）
   原来只说"攻方胜出/攻击失效"，防守方玩家看到"攻击失效"会误以为自己输了。
   改为明确指出谁胜出。
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

# 判定结果日志：明确谁胜出
sub("""      log(`⚔️ <b>判定</b>（第 ${rounds} 轮）：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → ` +
          (win ? '攻方胜出，命中！' : '攻击失效。'), 'l-rps');""",
"""      log(`⚔️ <b>判定</b>（第 ${rounds} 轮）：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → ` +
          (win ? `<b>${lname(attacker)} 胜出</b>，攻击命中！`
               : `<b>${lname(target)} 胜出</b>，攻击被挡下（${lname(attacker)} 未命中）。`), 'l-rps');""",
'判定措辞清晰化')

# 平局日志也明确
sub("""        log(`⚔️ <b>判定</b>（第 ${rounds} 轮）：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → 平局`,'l-rps');""",
"""        log(`⚔️ <b>判定</b>（第 ${rounds} 轮）：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → <b>平局</b>，重新出拳`,'l-rps');""",
'平局措辞')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
print('长度 %d → %d' % (orig, len(t)))
js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk141.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
