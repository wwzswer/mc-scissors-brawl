# -*- coding: utf-8 -*-
"""补丁 61：攻击 AP 规则测试用例
   【30】攻击固定消耗 1 AP（不占免费行动槽）
   【31】切换武器仍然免费
"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
r = F.read_text(encoding='utf-8')

tail = "console.log('\\n──────────────────────────────');"
assert tail in r, '结尾锚点缺失'

extra = r"""console.log('\n【30】攻击固定消耗 1 AP');
{
  const { API, G, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.ap = 5; me.slotsLeft = 1; me.weapon = 'fist';
  const atk = API.buildHumanOptions(me).find(o=>o.type==='attack');
  ok(!!atk, '能看到攻击选项', atk && atk.label);
  ok(atk && atk.cost===API.ATK_COST, `攻击选项标价 ${API.ATK_COST} AP`, atk && atk.cost);
  const ap0 = me.ap, slots0 = me.slotsLeft;
  await API.applyAction(me, atk);
  ok(me.ap===ap0-1, '攻击扣 1 AP', [ap0, me.ap]);
  ok(me.slotsLeft===slots0, '攻击不消耗免费行动槽', [slots0, me.slotsLeft]);
}
{
  /* 连续攻击：每次都要 AP */
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.ap = 3; me.weapon = 'fist';
  for(let i=0;i<3;i++){
    const atk = API.buildHumanOptions(me).find(o=>o.type==='attack');
    if(!atk) break;
    await API.applyAction(me, atk);
  }
  ok(me.ap===0, '连续攻击 3 次扣光 3 AP', me.ap);
}
{
  /* AP=0 时无法攻击 */
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.ap = 0; me.slotsLeft = 1; me.weapon = 'fist';
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='attack');
  const payable = opts.filter(o=>API.canPay(me, o));
  ok(payable.length===0, 'AP=0 时攻击不可支付（即使有免费行动槽）', payable.length);
  const hp0 = ai.hp;
  const before = me.ap;
  if(opts[0]) await API.applyAction(me, opts[0]);
  ok(me.ap===before && ai.hp===hp0, 'AP=0 时攻击被拒绝且不生效', [me.ap, ai.hp]);
}
{
  /* 免费行动槽仍在，可用于非攻击动作 */
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 1);
  me.ap = 0; me.slotsLeft = 1;
  const mv = API.buildHumanOptions(me).find(o=>o.type==='move');
  ok(!!mv, 'AP=0 时走位仍可用（走免费行动槽）', mv && mv.label);
  const ap0 = me.ap;
  if(mv) await API.applyAction(me, mv);
  ok(me.ap===ap0, '走位用免费行动槽，不扣 AP', me.ap);
  ok(me.slotsLeft===0, '走位消耗了免费行动槽', me.slotsLeft);
}
{
  /* TNT 也是攻击：固定 1 AP */
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  API.addItem(me,'tnt',2);
  me.ap = 3;
  const place = API.buildHumanOptions(me).find(o=>o.type==='tnt_place');
  ok(!!place && place.cost===API.ATK_COST, 'TNT 粘贴标价 1 AP', place && place.cost);
  const ap0 = me.ap;
  if(place) await API.applyAction(me, place);
  ok(me.ap===ap0-1, 'TNT 粘贴扣 1 AP', me.ap);
}
{
  /* 铁傀儡被动仍免费（用户此前明确要求） */
  const { API, me, ai } = fresh();
  me.prog = 3; me.itemPts = {}; me.ap = 20;
  await invest(API, me, 'golem');
  API.setDistance(me, ai, 1);
  me.actionsUsed = 1; me.slotsLeft = 0; me.ap = 0;
  const gp = API.buildHumanOptions(me).find(o=>o.type==='golem_punch');
  ok(!!gp, '铁傀儡被动可用（AP=0 也能用）', !!gp);
  const ap0 = me.ap;
  if(gp) await API.applyAction(me, gp);
  ok(me.ap===ap0, '铁傀儡被动免费（不扣 AP）', me.ap);
}

console.log('\n【31】切换武器不消耗 AP');
{
  const { API, me } = fresh();
  me.itemPts = {}; me.ap = 0; me.slotsLeft = 0;
  API.addItem(me,'wood_sword',1); API.addItem(me,'stone_sword',1);
  me.weapon = 'fist';
  const sw = API.buildHumanOptions(me).filter(o=>o.type==='switch_weapon');
  ok(sw.length>=2, 'AP=0 时仍能切换武器', sw.length);
  const ap0 = me.ap, slots0 = me.slotsLeft;
  await API.applyAction(me, sw.find(o=>o.key==='stone_sword') || sw[0]);
  ok(me.weapon==='stone_sword', '成功换到石剑', me.weapon);
  ok(me.ap===ap0, '切换武器不扣 AP', me.ap);
  ok(me.slotsLeft===slots0, '切换武器不占免费行动槽', me.slotsLeft);
}

"""
r = r.replace(tail, extra + tail, 1)
F.write_text(r, encoding='utf-8')
print('已补【30】【31】用例，长度', len(r))
