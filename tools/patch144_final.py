# -*- coding: utf-8 -*-
"""补丁 144：
   ① 附魔替换时给出明确提示（每个武器/护甲只能有 1 个附魔，再次附魔会替换）
   ② 版号 → v1.5.3
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

# ① 附魔替换提示
sub("""  const useArmor = ENCH[k].apply.includes('armor');
  const slot = useArmor ? (p.armor||'armor') : (p.weapon||'fist');
  p.ench[slot]=k;""",
"""  const useArmor = ENCH[k].apply.includes('armor');
  const slot = useArmor ? (p.armor||'armor') : (p.weapon||'fist');
  const prev = p.ench[slot];
  if(prev && prev !== k && ENCH[prev]){
    log(`（${useArmor?'护甲':'武器'}已有【${ENCH[prev].name}】，本次附魔会替换掉它）`,'l-sys');
  }
  p.ench[slot]=k;""", '① 附魔替换提示')

# ② 版号
sub('基础版 v1.5.2', '基础版 v1.5.3', '② 版号 v1.5.3')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
print('长度 %d → %d' % (orig, len(t)))
js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk144.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
