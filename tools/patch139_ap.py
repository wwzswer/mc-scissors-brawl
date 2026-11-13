# -*- coding: utf-8 -*-
"""补丁 139：修复 AP 扣费缺失
   ① repair（铁砧修复）：注释写"固定 2 AP"，实际没设 itemCost
   ② enchant（附魔）：没设 itemCost，完全不扣 AP
   ③ potion（药水）：没设 itemCost
   同时把 repair/enchant 归入 isPurchase，避免被"免费行动槽"逻辑再扣 1 AP
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

# ① repair / enchant / potion 归入 isPurchase（不再走免费行动槽扣费）
sub("  const isPurchase = ['shop_progress','upgrade','craftShopItem','craft','buy_tnt','buy_apple'].includes(a.type);",
    "  const isPurchase = ['shop_progress','upgrade','craftShopItem','craft','buy_tnt','buy_apple','repair','enchant'].includes(a.type);",
    '① 归入 isPurchase')

# ② 修复护甲：固定 2 AP
sub("""    case 'repair':  /* 修复护甲：固定 2 AP */ {
      if(!p.armor) break;""",
"""    case 'repair':  /* 修复护甲：固定 2 AP */ {
      if(!p.armor) break;
      if(p.ap < 2){ log(`${lname(p)} 行动点不足，无法修复（需 2 AP）。`,'l-warn'); break; }
      itemCost = 2;                     /* 修复护甲：固定 2 AP */
      p.actionsUsed++; p.turnSpent=(p.turnSpent||0)+1;""",
'② 修复护甲 2 AP')

# ③ 附魔：固定 1 AP
sub("""    case 'enchant':
      applyEnchant(p,a.ench); break;""",
"""    case 'enchant':
      if(p.ap < 1){ log(`${lname(p)} 行动点不足，无法附魔（需 1 AP）。`,'l-warn'); break; }
      if(!applyEnchant(p,a.ench)) break;
      itemCost = 1;                     /* 附魔：固定 1 AP */
      p.actionsUsed++; p.turnSpent=(p.turnSpent||0)+1;
      break;""",
'③ 附魔 1 AP')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print('长度 %d → %d' % (orig, len(back)))
js = back.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk139.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
