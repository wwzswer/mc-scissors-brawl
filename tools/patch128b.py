# -*- coding: utf-8 -*-
"""补丁 128b：修复 3 处（避免嵌套引号写法）
   ① 烟花：跳过判定直接造成伤害 → 改为需要判定
   ② 三叉戟文案：删除"无需判定"
   ③ 三叉戟文案：删除"掷出后失去"，改为与当前拾取规则一致
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

FIRE_OLD = "    /* 烟花：0.5 物理 + 1.5 法术；有护甲时 1 法术 */\n" \
           "    if(key==='firework'){\n" \
           "      const arm = armorActive(target);\n" \
           "      const dmg = arm ? [0,0,1,0] : [0.5,0,1.5,0];\n" \
           "      log(`\U0001F386 ${lname(attacker)} 发射【烟花】（发射后需重新装填）。`,'l-warn'); sfx.boom();\n" \
           "      tryDamage(target, dmg, {label:'烟花'});\n" \
           "      for(const v of alivePlayers()){\n" \
           "        if(v!==target && v!==attacker && distanceBetween(target,v)===0)\n" \
           "          tryDamage(v,[0,0,1,0],{label:'烟花（同格溅射）'});\n" \
           "      }\n" \
           "      return true;\n" \
           "    }\n"

if FIRE_OLD in t:
    t = t.replace(FIRE_OLD, '', 1)
    notes.append('  ok 移除烟花免判定块')
else:
    notes.append('  ! 未找到烟花免判定块')

# 判定失败分支：加烟花提示
sub("      if(key==='flint'){\n"
    "        /* 打火石需要判定：判定失败＝没能点燃 */\n"
    "        log(`\U0001F525 打火石没能点燃 ${lname(target)}（判定失败）。`,'l-warn');\n"
    "        return false;\n"
    "      }\n",
    "      if(key==='flint'){\n"
    "        /* 打火石需要判定：判定失败＝没能点燃 */\n"
    "        log(`\U0001F525 打火石没能点燃 ${lname(target)}（判定失败）。`,'l-warn');\n"
    "        return false;\n"
    "      }\n"
    "      if(key==='firework'){\n"
    "        log(`\U0001F386 烟花没能命中 ${lname(target)}（判定失败，未造成伤害）。`,'l-warn');\n"
    "        return false;\n"
    "      }\n",
    '② 烟花判定失败提示')

# 判定成功后：插入烟花结算
sub("    /* 破盾（仅近战物理攻击、且非远程武器） */",
    "    /* 烟花：判定命中后 0.5 物理 + 1.5 法术；目标有护甲时改为 1 法术 */\n"
    "    if(key==='firework'){\n"
    "      const arm = armorActive(target);\n"
    "      const dmg = arm ? [0,0,1,0] : [0.5,0,1.5,0];\n"
    "      log(`\U0001F386 ${lname(attacker)} 发射的【烟花】命中（发射后需重新装填）。`,'l-warn'); sfx.boom();\n"
    "      tryDamage(target, dmg, {label:'烟花'});\n"
    "      for(const v of alivePlayers()){\n"
    "        if(v!==target && v!==attacker && distanceBetween(target,v)===0)\n"
    "          tryDamage(v,[0,0,1,0],{label:'烟花（同格溅射）'});\n"
    "      }\n"
    "      return true;\n"
    "    }\n\n"
    "    /* 破盾（仅近战物理攻击、且非远程武器） */",
    '① 烟花改为判定后结算')

# 三叉戟物品说明
sub("  trident:    { name:'三叉戟', cost:3, prog:PROG.STONE, need:'fishing_rod', desc:'前置：钓鱼竿。① 距离 0 攻击：需判定，胜出 1.5 物理伤害。② 距离 ≥1 掷出：无需判定，1.5 物理伤害，但失去三叉戟（附魔【忠诚】会回到手中）。' },",
    "  trident:    { name:'三叉戟', cost:3, prog:PROG.STONE, need:'fishing_rod', desc:'前置：钓鱼竿。① 距离 0 近战：需判定，胜出 1.5 物理伤害。② 距离 ≥1 掷出：同样需判定，胜出 1.5 物理伤害；判定失败视为未掷出、三叉戟留在手中。掷出后落在目标所在格，与其同格且 AP≥1 的玩家会花 1 AP 拾取（附魔【忠诚】则必定回到手中）。' },",
    '③ 三叉戟物品说明')

# 掷出按钮文案
sub("      label:`\U0001F531 掷出三叉戟 ${e.name}（1 AP，无需判定 1.5，掷出后失去）`});",
    "      label:`\U0001F531 掷出三叉戟 ${e.name}（1 AP，判定 1.5）`});",
    '③ 掷出按钮文案')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print('  长度 %d → %d' % (orig, len(back)))
print('  无「无需判定」残留:', '无需判定' not in back)
print('  无「掷出后失去」残留:', '掷出后失去' not in back)
print('  无「失去三叉戟」残留:', '失去三叉戟' not in back)
print('  烟花判定失败提示:', '烟花没能命中' in back)
print('  烟花在判定后结算:', back.find('发射的【烟花】命中') > back.find('if(!success)'))

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
