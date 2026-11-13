# -*- coding: utf-8 -*-
"""补丁 45：补齐 armorHasAny 与商店建筑按钮的 1 AP 判定"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

# ① armorHasAny（armorActive 是箭头函数，插在它后面）
old = "const armorActive = p => !!p.armor && p.armorCharges>0;"
new = ("const armorActive = p => !!p.armor && p.armorCharges>0;\n"
       "/* 是否持有护甲类物品（不论耐久是否耗尽）—— TNT 的伤害档位用它判定 */\n"
       "const armorHasAny = p => !!(p && p.armor && ITEMS[p.armor] && ITEMS[p.armor].armor);")
if 'armorHasAny' not in t:
    assert old in t, 'armorActive 锚点缺失'
    t = t.replace(old, new, 1); notes.append('  ok armorHasAny')
else:
    notes.append('  - armorHasAny 已存在')

# ② 商店按钮：建筑按 1 AP 判定
old2 = "        d.onclick=()=>{ if(p.ap<1) return; applyShopAction(p,{type:'craft',key:k}); render(); renderAll(); };"
new2 = "        d.onclick=()=>{ if(p.ap<(it.build?BUILD_COST:1)) return; applyShopAction(p,{type:'craft',key:k}); render(); renderAll(); };"
if old2 in t:
    t = t.replace(old2, new2, 1); notes.append('  ok 商店建筑按钮 1 AP')
else:
    notes.append('  ! 商店按钮锚点未匹配')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
