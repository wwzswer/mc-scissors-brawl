# -*- coding: utf-8 -*-
"""补丁 122：AI 评分平衡微调
   - 血少且无甲时，防具优先级更高
   - 敌人有护甲时，打火石/腐肉 与 TNT 引爆 更优先
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
lines = IDX.read_text(encoding='utf-8').split('\n')
changed = []

for i, l in enumerate(lines):
    s = l.strip()
    # 防具：提高缺血时的加成
    if 'if(p.hp<=3.5) s += 14;' in l:
        lines[i] = l.replace('s += 14;', 's += 22;')
        changed.append('L%d 防具 hp<=3.5 加成 14→22' % (i+1))
    elif 'if(p.hp<=2.5) s += 20;' in l and 'armor' not in s:
        lines[i] = l.replace('s += 20;', 's += 30;')
        changed.append('L%d 防具 hp<=2.5 加成 20→30' % (i+1))
    elif 'if(!p.armor) s += 16;' in l:
        lines[i] = l.replace('s += 16;', 's += 28;')
        changed.append('L%d 无甲加成 16→28' % (i+1))
    elif 'if(aliveEnemiesOf(p).some(e=>armorActive(e))) s += 10;' in l:
        lines[i] = l.replace('s += 10;', 's += 14;')
        changed.append('L%d 敌有甲时防具 10→14' % (i+1))

IDX.write_text('\n'.join(lines), encoding='utf-8')
print('防具评分调整：')
for c in changed: print('  ok', c)

# 打火石/腐肉：面对高护甲敌人时进一步提升
t = IDX.read_text(encoding='utf-8')
old = "          if(armorActive(e)) s += 26;                       /* 对手有甲：打火石很划算 */"
new = "          if(armorActive(e)) s += 44;                       /* 对手有甲：打火石很划算 */"
if old in t:
    t = t.replace(old, new, 1); print('  ok 打火石对高甲 +26→+44')
old2 = "          if(armorActive(e)) s += 22;"
new2 = "          if(armorActive(e)) s += 34;"
if old2 in t:
    t = t.replace(old2, new2, 1); print('  ok 腐肉对高甲 +22→+34')
# TNT 引爆：敌人高甲时更值得（法术无视护甲）
old3 = "        return dt >= 3 ? 250 : 190;"
new3 = "        if(armorActive(v)) return dt >= 3 ? 300 : 230;   /* 对高甲目标：TNT 法术非常有效 */\n        return dt >= 3 ? 250 : 190;"
if old3 in t:
    t = t.replace(old3, new3, 1); print('  ok TNT 对高甲目标更优先')
IDX.write_text(t, encoding='utf-8')

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
