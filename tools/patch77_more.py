# -*- coding: utf-8 -*-
"""补丁 77：补齐剩余改动
   - move 选项标签/成本（人类）
   - 腐肉改法术伤害（找对函数名）
   - 火焰类统一法术伤害但保留叫法
   - 钻石甲修复 2 AP
   - 村庄无限建造
"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ---- move（人类）：用正则批量把 move 的 cost:1 → MOVE_COST ----
before = t
t = re.sub(r"(push\(\{type:'move'[^}]*?)cost:1", r"\1cost:MOVE_COST", t)
if t != before:
    notes.append('  ok move cost → MOVE_COST')
# 标签里的“1 步”改成“1 AP”
before2 = t
t = t.replace("👣 靠近 ${e.name} 1 格（1 步，近战需 0 格）", "👣 靠近 ${e.name} 1 格（1 AP，近战需 0 格）")
t = t.replace("👣 后退，与 ${e.name} 拉开 1 格（1 步）", "👣 后退，与 ${e.name} 拉开 1 格（1 AP）")
if t != before2: notes.append('  ok move 标签改 1 AP')

# ---- 腐肉转法术：找实际函数 ----
m = re.search(r'function (\w*[Pp]rofile\w*)\(', t)
fname = m.group(1) if m else None
notes.append(f'  · 伤害档案函数名: {fname}')
if fname:
    old_body = f"function {fname}(attacker, key){{"
    if old_body in t:
        # 在函数体开头插入腐肉法术转换
        idx = t.index(old_body) + len(old_body)
        inject = """
  /* 腐肉：伤害转为法术类型（名字与流血效果不变） */
  if(key==='flesh' && dmg && dmg[0]>0){ dmg[2]=rm((dmg[2]||0)+dmg[0]); dmg[0]=0; }"""
        # 需要 dmg 先声明，所以插到 dmg 赋值之后
        anchor = re.search(r"function " + fname + r"\(attacker, key\)\{(.*?)\n", t, re.S)
        t = t[:idx] + inject + t[idx:]
        notes.append('  ok 腐肉转法术（插在函数开头）')

# ---- 火焰类统一法术伤害（保留“火焰”叫法）----
# 火焰持续伤害结算处：[0,0.5,0,0] 的物理分量 → 法术
before3 = t
t = t.replace("tryDamage(p,[0,0.5,0,0],{label:'火焰持续伤害'})", "tryDamage(p,[0,0,0.5,0],{label:'火焰持续伤害'})")
if t != before3: notes.append('  ok 火焰持续伤害 → 法术分量')
# 打火石/火焰附加的点燃说明保持不变（仍叫“火焰”）
before4 = t
t = t.replace("props.burnTicks", "props.burnTicks")  # no-op

# 引雷/火焰附加造成的即时 0.5 火焰伤害也要转法术
t = re.sub(r"tryDamage\((\w+),\[0,0\.5,0,0\]", r"tryDamage(\1,[0,0,0.5,0]", t)
t = re.sub(r"tryDamage\((\w+), \[0,0\.5,0,0\]", r"tryDamage(\1, [0,0,0.5,0]", t)
notes.append('  ok 火焰即时伤害 → 法术')

# ---- 钻石甲修复 2 AP，其它护甲也统一 2 AP ----
before5 = t
t = t.replace("push({type:'repair',cost:2,label:`🔨 铁砧修复 ${ITEMS[p.armor].name}（2 步，恢复至 ${armorMax(p)}）`});",
              "push({type:'repair',cost:2,label:`🔨 铁砧修复 ${ITEMS[p.armor].name}（2 AP，恢复至 ${armorMax(p)}）`});")
t = t.replace("push({type:'repair',cost:2,label:'修复护甲'});",
              "push({type:'repair',cost:2,label:'修复护甲（2 AP）'});")
if t != before5: notes.append('  ok 修复护甲 2 AP（文案）')

# repair 的 AP 扣费：确保 2（原来可能走 itemCost）
sub("""    case 'repair':""", """    case 'repair':  /* 修复护甲：固定 2 AP */""", 'repair 注释')

# ---- 村庄：可无限建造，每次 1 AP ----
sub("""village:    { name:'村庄',   cost:0, prog:PROG.WOOD, build:true, repeat:true, max:1, desc:'建筑（免费建造，全局最多 1 座）：立即获得 1 本附魔书（在铁砧处使用）。' },""",
"""village:    { name:'村庄',   cost:1, prog:PROG.WOOD, build:true, repeat:true, desc:'建筑（每次 1 AP，可反复前往）：每次获得 1 本附魔书（在铁砧处使用）。' },""",
'村庄无限建造 1 AP')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
