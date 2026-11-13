# -*- coding: utf-8 -*-
"""补丁 111：修复附魔检测 —— 附魔按【槽位】存储，检查却按【附魔名】
   p.ench[slot] = 附魔名（slot 是武器或护甲）
   因此：
     - 武器附魔（忠诚/火矢/锋利/火焰附加/引雷/横扫/穿透）应查 p.ench[p.weapon]
     - 护甲附魔也应查 p.ench[p.armor]（原来的 hasEnch 恰好"看起来"能用，但语义不一致）
   统一加一个 enchOf(p) 辅助，并修正所有错误调用。
"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# 1) 新增按槽位取附魔的辅助
sub("""const hasEnch = (p,k) => !!p.ench[k];""",
"""const hasEnch = (p,k) => !!p.ench[k];
/* 按“槽位”取附魔：武器附魔存在 p.ench[p.weapon]，护甲附魔存在 p.ench[p.armor] */
const enchOnWeapon = (p) => p && p.ench ? p.ench[p.weapon] : undefined;
const enchOnArmor  = (p) => p && p.ench ? p.ench[p.armor]  : undefined;""",
'新增 enchOnWeapon / enchOnArmor')

# 2) 忠诚
sub("""      if(hasEnch(attacker,'loyalty')){""",
"""      if(enchOnWeapon(attacker)==='loyalty'){""", '忠诚检测')

# 3) 火矢（弩）
sub("""  if(key==='crossbow' && hasEnch(attacker,'flame')) burnTicks=2;""",
"""  if(key==='crossbow' && (enchOnWeapon(attacker)==='flame' || hasEnch(attacker,'flame'))) burnTicks=2;""",
'火矢检测')

# 4) 护甲附魔检测（统一走槽位）
sub("""  if(hasEnch(target,'fire_prot') && fireOnly){ log(`${lname(target)} 的【防火】免疫了火焰伤害。`,'l-sys'); return {dealt:0}; }
  if(hasEnch(target,'blast_prot') && isExplosion){ log(`${lname(target)} 的【防爆】免疫了爆炸伤害。`,'l-sys'); return {dealt:0}; }
  if(hasEnch(target,'fire_prot') && dmg[1]>0){ dmg[1]=0; log(`${lname(target)} 的【防火】抵消了火焰部分。`,'l-sys'); }
  if(target.effects.some(e=>e.type==='fireImmune') && dmg[1]>0){ dmg[1]=0; log(`${lname(target)} 处于火焰免疫状态，火焰伤害被抵消。`,'l-sys'); }
  if(dmg[2]>0 && target.effects.some(e=>e.type==='spellImmune')){ dmg[2]=0; log(`${lname(target)} 处于法术免疫状态，法术伤害被抵消。`,'l-sys'); }
  if(hasEnch(target,'pierce_prot') && dmg[3]>0){ dmg[3]=0; log(`${lname(target)} 的【防穿】使穿甲伤害失效。`,'l-sys'); }""",
"""  const tArmorEnch = enchOnArmor(target);
  if((tArmorEnch==='fire_prot' || hasEnch(target,'fire_prot')) && fireOnly){ log(`${lname(target)} 的【防火】免疫了火焰伤害。`,'l-sys'); return {dealt:0}; }
  if((tArmorEnch==='blast_prot' || hasEnch(target,'blast_prot')) && isExplosion){ log(`${lname(target)} 的【防爆】免疫了爆炸伤害。`,'l-sys'); return {dealt:0}; }
  if((tArmorEnch==='fire_prot' || hasEnch(target,'fire_prot')) && dmg[1]>0){ dmg[1]=0; log(`${lname(target)} 的【防火】抵消了火焰部分。`,'l-sys'); }
  if(target.effects.some(e=>e.type==='fireImmune') && dmg[1]>0){ dmg[1]=0; log(`${lname(target)} 处于火焰免疫状态，火焰伤害被抵消。`,'l-sys'); }
  if(dmg[2]>0 && target.effects.some(e=>e.type==='spellImmune')){ dmg[2]=0; log(`${lname(target)} 处于法术免疫状态，法术伤害被抵消。`,'l-sys'); }
  if((tArmorEnch==='pierce_prot' || hasEnch(target,'pierce_prot')) && dmg[3]>0){ dmg[3]=0; log(`${lname(target)} 的【防穿】使穿甲伤害失效。`,'l-sys'); }""",
'护甲附魔检测')

# 5) AI 评分里的忠诚判断
sub("""  if(k==='trident' && o.ranged && !hasEnch(p,'loyalty')) s -= 8;""",
"""  if(k==='trident' && o.ranged && enchOnWeapon(p)!=='loyalty') s -= 8;""", 'AI 评分忠诚')

# 6) 钻石剑护甲选择：防穿
sub("""  if(target.hp<=1.5 && !hasEnch(target,'pierce_prot')) return Promise.resolve('pierce');""",
"""  if(target.hp<=1.5 && enchOnArmor(target)!=='pierce_prot' && !hasEnch(target,'pierce_prot')) return Promise.resolve('pierce');""",
'防穿检测')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))

back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  长度 {orig} → {len(back)}（+{len(back)-orig}）')
print('  enchOnWeapon 定义:', 'const enchOnWeapon' in back)
chk1 = "if(enchOnWeapon(attacker)==='loyalty'){"
chk2 = "enchOnWeapon(attacker)==='flame'"
print('  忠诚用槽位检测:', chk1 in back)
print('  火矢用槽位检测:', chk2 in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
