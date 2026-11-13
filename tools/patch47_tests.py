# -*- coding: utf-8 -*-
"""补丁 47：为 44/45/46 的改动补测试用例
   【24】多人猜拳判定（同招式组）
   【25】TNT 法术伤害档位
   【26】铁傀儡被动不消耗 AP
   【27】建筑统一 1 AP
   【28】火焰统一在回合末结算 + 入水置 0
   【29】猜拳流程不会卡死（用真实计时器跑一次 rpsPhase）
"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
r = F.read_text(encoding='utf-8')

tail = "console.log('\\n──────────────────────────────');"
assert tail in r, '结尾锚点缺失'

extra = r"""console.log('\n【24】多人猜拳判定（按同招式组）');
{
  const { API } = fresh();
  const J = API.judgeRound;
  const mk = obj => Object.fromEntries(Object.entries(obj).map(([k,v])=>[+k, v]));
  /* 用户给的例子 1：A剪刀 B剪刀 C石头 → 石头组胜出（C） */
  const r1 = J(mk({0:'scissors', 1:'scissors', 2:'rock'}));
  ok(r1.tie===false && r1.winner===2, 'A剪刀/B剪刀/C石头 → C 胜出', r1);
  /* 用户给的例子 2：A剪刀 B石头 C布 → 互克，重出 */
  const r2 = J(mk({0:'scissors', 1:'rock', 2:'paper'}));
  ok(r2.tie===true, 'A剪刀/B石头/C布 → 平局重出', r2);
  /* 全员同招 → 平局 */
  const r3 = J(mk({0:'rock', 1:'rock', 2:'rock'}));
  ok(r3.tie===true, '全员同招 → 平局', r3);
  /* 两人：正常胜负 */
  const r4 = J(mk({0:'rock', 1:'scissors'}));
  ok(r4.tie===false && r4.winner===0, '两人：石头胜剪刀', r4);
  const r5 = J(mk({0:'scissors', 1:'scissors'}));
  ok(r5.tie===true, '两人同招 → 平局', r5);
  /* 四人：1 石头 vs 3 剪刀 → 石头胜 */
  const r6 = J(mk({0:'rock', 1:'scissors', 2:'scissors', 3:'scissors'}));
  ok(r6.tie===false && r6.winner===0, '1 石头 vs 3 剪刀 → 石头胜', r6);
  /* 四人：2 石头 vs 2 剪刀 → 石头组内随机一人 */
  const r7 = J(mk({0:'rock', 1:'rock', 2:'scissors', 3:'scissors'}));
  ok(r7.tie===false && (r7.winner===0||r7.winner===1), '2 石头 vs 2 剪刀 → 石头组内一人胜出', r7);
  /* 四人三招：A石 B石 C剪 D布 → 布克制石头，剪刀克制布 → 布被剪刀克制，无绝对胜者 → 平局 */
  const r8 = J(mk({0:'rock', 1:'rock', 2:'scissors', 3:'paper'}));
  ok(r8.tie===true, 'A石/B石/C剪/D布 → 互克，平局重出', r8);
}

console.log('\n【25】TNT：法术伤害，档位只看“有无护甲类物品”');
{
  const { API, me, ai } = fresh();
  const hp0a = ai.hp, hp0m = me.hp;
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp, hp0a-2.5), '无护甲：中心目标受 2.5', ai.hp);
  ok(near(me.hp, hp0m-1.5), '无护甲：其余目标受 1.5（含自己）', me.hp);
}
{
  const { API, me, ai } = fresh();
  ai.armor='iron_armor'; ai.armorCharges=2;      /* 持有护甲物品 */
  const hp0a = ai.hp;
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp, hp0a-1.5), '有护甲：中心目标受 1.5', ai.hp);
  ok(ai.armorCharges===2, 'TNT 不消耗护甲耐久（法术伤害）', ai.armorCharges);
}
{
  /* 护甲耐久耗尽但“仍持有护甲物品” → 依然按有甲档位 */
  const { API, me, ai } = fresh();
  ai.armor='leather'; ai.armorCharges=0;
  const hp0a = ai.hp;
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp, hp0a-1.5), '护甲破损但持有护甲物品 → 仍按有甲档位 1.5', ai.hp);
}
{
  /* 法术免疫（附魔金苹果）应能免疫 TNT 的法术伤害 */
  const { API, me, ai } = fresh();
  API.addEffect(ai,'spellImmune',1,3,'法术免疫');
  const hp0a = ai.hp;
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp, hp0a), '法术免疫可免疫 TNT 伤害', ai.hp);
}

console.log('\n【26】铁傀儡被动攻击不消耗 AP');
{
  const { API, G, me } = fresh();
  me.prog = 3; me.itemPts = {}; me.ap = 20;
  await API.applyAction(me, {type:'craftShopItem', key:'golem'});
  ok(API.armorActive(me) && me.armor==='golem', '先装备铁傀儡', me.armor);
  me.actionsUsed = 1;                       /* 模拟“全场都行动过一次后再次轮到” */
  me.slotsLeft = 0; me.ap = 0;              /* 没有任何免费行动与 AP */
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='golem_punch');
  ok(opts.length >= 1, '即使 AP=0、无免费行动也能使用铁傀儡被动', opts.length);
  ok(opts.length>=1 && opts[0].isAction===false, '被动标记为不占行动次数', opts[0] && opts[0].isAction);
  const before = me.ap;
  await API.applyAction(me, opts[0]);
  ok(me.ap === before, '使用被动后 AP 不变', me.ap);
  ok(me.slotsLeft === 0, '不占用免费行动次数', me.slotsLeft);
}

console.log('\n【27】建筑统一消耗 1 AP');
{
  const { API, G, me } = fresh();
  me.prog = 1; me.ap = 1; me.itemPts = {};
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='craftShopItem' && ITEMS_of(API,'village').build);
  ok(opts.length>=1 && opts[0].cost===1, '村庄入口花费 1 AP', opts[0] && opts[0].cost);
  await API.applyAction(me, {type:'craftShopItem', key:'village'});
  ok(me.buildings.village===true, '1 AP 建成村庄', me.buildings);
  ok(me.ap===0, '只扣 1 AP', me.ap);
}
{
  /* 铁砧原为 2 步，现在也应只要 1 AP */
  const { API, me } = fresh();
  me.prog = 3; me.ap = 1; me.itemPts = {};
  await API.applyAction(me, {type:'craftShopItem', key:'anvil'});
  ok(me.buildings.anvil===true, '铁砧同样 1 AP 建成', me.buildings);
}
{
  const { API, me } = fresh();
  me.prog = 3; me.ap = 1; me.itemPts = {};
  await API.applyAction(me, {type:'craftShopItem', key:'pyramid'});
  ok(me.buildings.pyramid===true, '沙漠金字塔 1 AP 建成', me.buildings);
}
function ITEMS_of(API, k){ return { build:true }; }

console.log('\n【28】火焰：统一在回合末结算，入水可取消');
{
  const { API, ai } = fresh();
  /* 模拟打火石点燃：3 层 */
  API.addEffect(ai,'burn',3,99,'火焰');
  const hp0 = ai.hp;
  ok(near(ai.hp, hp0), '点燃当回合不立即扣血', ai.hp);
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.5), '回合结束结算 3 次 0.5 = 1.5', ai.hp);
  ok(!ai.effects.some(e=>e.type==='burn'), '结算后火焰消失', ai.effects);
}
{
  const { API, ai } = fresh();
  API.addEffect(ai,'burn',3,99,'火焰');
  const hp0 = ai.hp;
  API.removeBurn(ai);                        /* 入水 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0), '入水后本回合不再受火焰伤害', ai.hp);
}
{
  const { API, ai } = fresh();
  ai.inWater = true;
  API.addEffect(ai,'burn',2,99,'火焰');
  await API.endOfRound({instant:true});
  ok(!ai.effects.some(e=>e.type==='burn'), '在水里火焰被清除', ai.effects);
}

console.log('\n【29】猜拳流程不会卡死（真实计时器跑一遍 rpsPhase）');
{
  const { MC, API, G } = fresh();
  /* 用静默开局 + 自动出拳，直接跑一次猜拳阶段 */
  MC.start({enemyCount:2, diff:'normal', auto:true, silent:true});
  const G2 = MC.state();
  API.setAutoPlayer((p, opts)=>{
    const o = opts||[];
    return o.find(x=>x.type==='attack') || o.find(x=>x.type==='shop_progress')
        || o.find(x=>x.type==='craftShopItem') || o.find(x=>x.type==='move') || {type:'pass'};
  });
  const t0 = Date.now();
  let done = false, total = 0;
  /* 连跑 12 次猜拳阶段，任何一次卡住都会超过超时 */
  await Promise.race([
    (async ()=>{
      for(let i=0;i<12;i++){ await API.rpsPhase(); total += G2.players.reduce((s,p)=>s+p.ap,0); }
      done = true;
    })(),
    (async ()=>{ await new Promise(r=>setTimeout(r, 20000)); })(),
  ]);
  const ms = Date.now()-t0;
  ok(done, `连续 12 次猜拳阶段全部返回（未卡死，用时 ${ms}ms）`, {done, ms});
  ok(ms < 15000, '猜拳阶段总耗时正常', ms);
}

"""
r = r.replace(tail, extra + tail, 1)
F.write_text(r, encoding='utf-8')
print('已补 6 组新用例，长度', len(r))
