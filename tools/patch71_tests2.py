# -*- coding: utf-8 -*-
"""补丁 71：新规则测试用例
   【32】猜拳：三种招式齐＝平局；两种招式时克制方全体得分（含用户给的例子）
   【33】护甲优先级：可指定先消耗哪件
   【34】闪避可选：不花 AP 赌一把
   【35】面包/金苹果/钓鱼竿位移 各 1 AP
"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
r = F.read_text(encoding='utf-8')
tail = "console.log('\\n──────────────────────────────');"
assert tail in r

extra = r"""console.log('\n【32】猜拳结算：三种招式齐＝平局，两种招式克制方全体得分');
{
  const { API } = fresh();
  const J = API.judgeRound;
  const mk = o => Object.fromEntries(Object.entries(o).map(([k,v])=>[+k, v]));
  /* 用户例子 A：我+队友都出石头，两个对手都出剪刀 → 两名石头玩家各得 AP */
  const r1 = J(mk({0:'rock', 1:'rock', 2:'scissors', 3:'scissors'}));
  ok(r1.tie===false, '两石头 vs 两剪刀 → 分出胜负', r1);
  ok(Array.isArray(r1.winners) && r1.winners.length===2 && r1.winners.includes(0) && r1.winners.includes(1),
     '两名石头玩家都胜出（各得 AP）', r1.winners);
  /* 用户例子 B：1,1,1,3 → 第四位玩家获胜 */
  const r2 = J(mk({0:'rock', 1:'rock', 2:'rock', 3:'scissors'}));
  ok(r2.tie===false && r2.winners.length===1 && r2.winners[0]===3,
     '三石头 vs 一剪刀 → 剪刀玩家胜出', r2.winners);
  /* 三种招式同时出现 → 平局重出 */
  const r3 = J(mk({0:'rock', 1:'scissors', 2:'paper'}));
  ok(r3.tie===true, '石头/剪刀/布同时出现 → 平局重出', r3);
  const r4 = J(mk({0:'rock', 1:'rock', 2:'scissors', 3:'paper'}));
  ok(r4.tie===true, '1,1,2,3（三种招式）→ 平局重出', r4);
  /* 全员同招 → 平局 */
  const r5 = J(mk({0:'rock', 1:'rock', 2:'rock'}));
  ok(r5.tie===true, '全员同招 → 平局', r5);
  /* 两人正常判定 */
  const r6 = J(mk({0:'paper', 1:'rock'}));
  ok(r6.tie===false && r6.winners[0]===0, '两人：布胜石头', r6.winners);
  /* 3 石头 vs 1 布 → 布胜 */
  const r7 = J(mk({0:'rock', 1:'rock', 2:'rock', 3:'paper'}));
  ok(r7.tie===false && r7.winners.length===1 && r7.winners[0]===3, '三石头 vs 一布 → 布玩家胜出', r7.winners);
}

console.log('\n【33】护甲优先级：可选择先消耗哪件');
{
  const { API, me } = fresh();
  me.prog = 3; me.ap = 30; me.itemPts = {};
  await invest(API, me, 'leather');        /* 皮革甲 1 次 */
  await invest(API, me, 'iron_armor');     /* 铁甲 2 次 */
  const list = API.armorsOf(me);
  ok(list.length===2, '身上有两件护甲', list.map(a=>a.key));
  ok(me.armor==='iron_armor', '新获得的铁甲立即生效', me.armor);
  /* 指定优先消耗皮革甲 */
  API.setArmorPriority(me, 'leather');
  ok((me.armorPriority||[])[0]==='leather', '皮革甲排到优先位', me.armorPriority);
  ok(me.armor==='leather', '当前生效护甲跟着切换', me.armor);
  /* 打 1 点物理：应扣皮革甲 */
  API.tryDamage(me,[1,0,0,0],{});
  const after = API.armorsOf(me);
  const leather = after.find(a=>a.key==='leather');
  const iron = after.find(a=>a.key==='iron_armor');
  ok(leather && leather.charges===0, '优先消耗的皮革甲被打光', leather && leather.charges);
  ok(iron && iron.charges===2, '铁甲完好无损', iron && iron.charges);
  /* 再打 1 点：这次扣铁甲 */
  API.tryDamage(me,[1,0,0,0],{});
  const iron2 = API.armorsOf(me).find(a=>a.key==='iron_armor');
  ok(iron2 && iron2.charges===1, '皮革甲用尽后改用铁甲', iron2 && iron2.charges);
  /* 切换优先级回铁甲 */
  API.setArmorPriority(me, 'iron_armor');
  ok(me.armor==='iron_armor', '可随时切换优先护甲', me.armor);
}

console.log('\n【34】判定平局：闪避是可选项（不花 AP 赌一把）');
{
  const { API, G, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.weapon='fist'; me.ap = 3;
  const hp0 = me.hp;
  /* dodge:false → 不闪避，继续判定；AP 不该被扣 */
  await API.performAttack(ai, me, 'fist', {instant:true, dodge:false, a:'rock', b:'rock'});
  ok(me.ap===3, '选择不闪避时不消耗 AP', me.ap);
}
{
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.ap = 3;
  const ap0 = me.ap;
  /* dodge:true → 花 1 AP 直接闪避 */
  await API.performAttack(ai, me, 'fist', {instant:true, dodge:true, a:'rock', b:'rock'});
  ok(me.ap===ap0-1, '选择闪避时消耗 1 AP', [ap0, me.ap]);
  ok(me.hp===4, '闪避成功后没有受伤', me.hp);
}

console.log('\n【35】补给与钓鱼竿的 AP 成本');
{
  const { API, me } = fresh();
  me.itemPts = {}; me.ap = 5; me.prog = 3;
  API.addItem(me,'bread',1); API.addItem(me,'god_apple',1);
  const opts = API.buildHumanOptions(me);
  const bread = opts.find(o=>o.type==='eat' && o.item==='bread');
  const apple = opts.find(o=>o.type==='eat' && o.item==='god_apple');
  ok(!!bread && bread.cost===1, '面包 1 AP', bread && bread.cost);
  ok(!!apple && apple.cost===1, '附魔金苹果 1 AP', apple && apple.cost);
}
{
  const { API, me, ai } = fresh();
  me.prog = 2; me.ap = 5; me.itemPts = {};
  await invest(API, me, 'fishing_rod');
  API.setDistance(me, ai, 3);
  const rod = API.buildHumanOptions(me).find(o=>o.type==='rod');
  ok(!!rod && rod.cost===1, '钓鱼竿使他人位移 1 AP', rod && rod.cost);
}

"""
r = r.replace(tail, extra + tail, 1)
F.write_text(r, encoding='utf-8')
print('已补【32】-【35】用例，长度', len(r))
