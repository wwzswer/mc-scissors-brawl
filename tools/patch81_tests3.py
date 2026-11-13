# -*- coding: utf-8 -*-
"""补丁 81：更新测试断言以匹配新规则
   - 走位/位移：固定 1 AP，不占免费行动槽
   - AP 不足时不能位移
"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
t = F.read_text(encoding='utf-8')
n = 0

def rep(old, new, label):
    global t, n
    if old in t:
        t = t.replace(old, new, 1); n += 1; print('  ok', label)
    else:
        print('  ! 未找到', label)

# ① 走位相关断言
rep("""  const mv = API.buildHumanOptions(me).find(o=>o.type==='move');
  ok(!!mv, 'AP=0 时走位仍可用（走免费行动槽）', mv && mv.label);
  const ap0 = me.ap;
  if(mv) await API.applyAction(me, mv);
  ok(me.ap===ap0, '走位用免费行动槽，不扣 AP', me.ap);
  ok(me.slotsLeft===0, '走位消耗了免费行动槽', me.slotsLeft);""",
"""  const mv = API.buildHumanOptions(me).find(o=>o.type==='move');
  ok(!mv || !API.canPay(me, mv), 'AP=0 时无法走位（走位需 1 AP）', mv && API.canPay(me, mv));""",
'走位需 AP（AP=0 时不可用）')

# ② AP=0 时攻击/走位都不可支付
rep("""  const opts = API.buildHumanOptions(me).filter(o=>o.type==='attack');
  const payable = opts.filter(o=>API.canPay(me, o));
  ok(payable.length===0, 'AP=0 时攻击不可支付（即使有免费行动槽）', payable.length);""",
"""  const opts = API.buildHumanOptions(me).filter(o=>o.type==='attack');
  const payable = opts.filter(o=>API.canPay(me, o));
  ok(payable.length===0, 'AP=0 时攻击不可支付（即使有免费行动槽）', payable.length);
  const mvOpts = API.buildHumanOptions(me).filter(o=>o.type==='move');
  ok(mvOpts.every(o=>!API.canPay(me,o)), 'AP=0 时走位也不可支付', mvOpts.length);""",
'AP=0 走位不可支付')

F.write_text(t, encoding='utf-8')
print(f'更新 {n} 处')
