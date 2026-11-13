# -*- coding: utf-8 -*-
"""补丁 110：
   ① 定义缺失的 rnd()/rn2() 随机整数函数（此前被调用但未定义）
   ② 攻击前置检查（用正确缩进）
   ③ 打火石物品说明改为“需判定”
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

# ---------- ① 定义随机整数函数 ----------
if 'function rnd(' not in t:
    sub("""const rm = n => Math.round(n*10)/10;""",
"""const rm = n => Math.round(n*10)/10;
/* 随机整数：[0, n) —— 此前被调用但未定义，会导致运行时异常 */
function rnd(n){ return Math.floor(R() * Math.max(1, n||1)); }
function rn2(n){ return rnd(n); }""", '① 定义 rnd/rn2')
else:
    notes.append('  - rnd 已存在')
    if 'function rn2(' not in t:
        sub("const rm = n => Math.round(n*10)/10;",
            "const rm = n => Math.round(n*10)/10;\nfunction rn2(n){ return rnd(n); }", '① 补 rn2')

# ---------- ② 攻击前置检查（2 空格缩进） ----------
sub("""if(isAttackAction(a)){
    /* 攻击：每次固定 1 AP，直接扣除，不消耗免费行动槽 */
    if(p.ap < ATK_COST){ log(`${lname(p)} 行动点不足，无法攻击（每次攻击需 ${ATK_COST} AP）。`,'l-warn'); return; }""",
"""if(isAttackAction(a)){
    /* 【前置检查】先确认目标与距离合法，再扣 AP —— 避免“先扣了 AP 才说打不到” */
    const _T = (a.targetId!==undefined && a.targetId!==null) ? P(a.targetId) : null;
    if(!_T){ log('目标不存在，攻击取消。','l-warn'); return; }
    if(!_T.alive){ log('目标已无法被攻击。','l-warn'); return; }
    if(!inRangeOf(p, a.key || p.weapon || 'fist', _T)){
      log(`${ITEMS[a.key]?ITEMS[a.key].name:'攻击'} 距离不合适（当前 ${distanceBetween(p,_T)} 格），未消耗 AP。`,'l-warn');
      return;
    }
    /* 攻击：每次固定 1 AP，直接扣除，不消耗免费行动槽 */
    if(p.ap < ATK_COST){ log(`${lname(p)} 行动点不足，无法攻击（每次攻击需 ${ATK_COST} AP）。`,'l-warn'); return; }""",
'② 攻击前置检查')

# ---------- ③ 打火石说明 ----------
sub("""  flint:      { name:'打火石', cost:1, prog:PROG.IRON, desc:'无需判定：点燃目标，接下来 3 个回合每回合结束各结算 1 次 0.5 火焰伤害（目标持有护甲则只持续 2 回合）。入水可扑灭。' },""",
"""  flint:      { name:'打火石', cost:1, prog:PROG.IRON, desc:'需判定：胜出后点燃目标，接下来 3 个回合每回合结束各结算 1 次 0.5 火焰伤害（目标持有护甲则只持续 2 回合）。重复点燃不叠加。入水可扑灭。' },""",
'③ 打火石说明')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))

back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  长度 {orig} → {len(back)}（+{len(back)-orig}）')
print('  rnd 已定义:', 'function rnd(n){' in back, '| rn2 已定义:', 'function rn2(n){' in back)
print('  攻击前置检查:', '【前置检查】先确认目标与距离合法' in back)
print('  打火石说明:', '需判定：胜出后点燃目标' in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
