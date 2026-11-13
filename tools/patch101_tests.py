# -*- coding: utf-8 -*-
"""补丁 101：更新火焰测试断言 + 新增打火石持续 3 回合用例"""
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

# 旧断言：addEffect(burn,3,99) → 结算后消失。现在这种属于“当回合结算完”的火焰
rep("""  API.addEffect(ai,'burn',3,99,'火焰');
  const hp0 = ai.hp;
  ok(near(ai.hp, hp0), '点燃当回合不立即扣血', ai.hp);
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.5), '回合结束结算 3 次 0.5 = 1.5', ai.hp);
  ok(!ai.effects.some(e=>e.type==='burn'), '结算后火焰消失', ai.effects);""",
"""  API.addEffect(ai,'burn',3,1,'火焰');       /* 当回合结算型：3 次，持续 1 回合 */
  const hp0 = ai.hp;
  ok(near(ai.hp, hp0), '点燃当回合不立即扣血', ai.hp);
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.5), '回合结束结算 3 次 0.5 = 1.5', ai.hp);
  ok(!ai.effects.some(e=>e.type==='burn'), '当回合结算型火焰结算后消失', ai.effects);""",
'当回合结算型火焰')

rep("""  API.addEffect(ai,'burn',3,99,'火焰');
  const hp0 = ai.hp;
  API.removeBurn(ai);                        /* 入水 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0), '入水后本回合不再受火焰伤害', ai.hp);""",
"""  API.addEffect(ai,'burn',3,1,'火焰');
  const hp0 = ai.hp;
  API.removeBurn(ai);                        /* 入水 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0), '入水后本回合不再受火焰伤害', ai.hp);""",
'入水取消')

rep("""  ai.inWater = true;
  API.addEffect(ai,'burn',2,99,'火焰');""",
"""  ai.inWater = true;
  API.addEffect(ai,'burn',2,1,'火焰');""", '水中火焰')

# 新增：打火石持续 3 回合
tail = "console.log('\\n──────────────────────────────');"
extra = r"""console.log('\n【36】打火石：每回合结算 1 次，持续 3 回合');
{
  const { API, G, me, ai } = fresh();
  me.prog = 3; me.ap = 20; me.itemPts = {}; me.weapon = 'fist';
  API.addItem(me, 'flint', 1);
  API.setDistance(me, ai, 0);
  const hp0 = ai.hp;
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='attack');
  ok(opts.some(o=>o.key==='flint'), '背包里的打火石可直接攻击', opts.map(o=>o.key));
  await API.applyAction(me, opts.find(o=>o.key==='flint'));
  const burn0 = ai.effects.find(e=>e.type==='burn');
  ok(!!burn0, '目标被点燃', burn0);
  ok(burn0 && burn0.power===1 && (burn0.rounds||0)===3, '点燃 = 每回合 1 次 × 3 回合', burn0 && {p:burn0.power, r:burn0.rounds});
  ok(near(ai.hp, hp0), '点燃当回合不立即扣血', ai.hp);
  /* 第 1 个回合结束：只掉 0.5 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-0.5), '第 1 回合结束只结算 0.5', ai.hp);
  ok(ai.effects.some(e=>e.type==='burn'), '火焰仍在（还剩 2 回合）', ai.effects.map(e=>e.type+':'+e.rounds));
  /* 第 2 个回合结束：再掉 0.5 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.0), '第 2 回合结束累计 1.0', ai.hp);
  /* 第 3 个回合结束：再掉 0.5，火焰熄灭 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.5), '第 3 回合结束累计 1.5', ai.hp);
  ok(!ai.effects.some(e=>e.type==='burn'), '3 回合后火焰熄灭', ai.effects);
  /* 第 4 个回合不再掉血 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.5), '第 4 回合不再掉血', ai.hp);
}
{
  /* 有护甲：只持续 2 回合 */
  const { API, me, ai } = fresh();
  me.prog = 3; me.ap = 20; me.itemPts = {}; me.weapon = 'fist';
  API.addItem(me, 'flint', 1);
  ai.armor = 'iron_armor'; ai.armorCharges = 2;
  API.setDistance(me, ai, 0);
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='attack');
  await API.applyAction(me, opts.find(o=>o.key==='flint'));
  const b = ai.effects.find(e=>e.type==='burn');
  ok(b && (b.rounds||0)===2, '目标持有护甲时只持续 2 回合', b && b.rounds);
}

"""
t = t.replace(tail, extra + tail, 1)
F.write_text(t, encoding='utf-8')
print(f'更新 {n} 处，已补【36】')
