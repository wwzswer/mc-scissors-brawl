# -*- coding: utf-8 -*-
"""补丁 18：重写 rules-test 的【19】进度点用例（适配 空手→石 1 点）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
r = F.read_text(encoding='utf-8')

i = r.index("console.log('\\n【19】")
j = r.index("console.log('\\n【20】")

new19 = r"""console.log('\n【19】进度点制：每投入 1 步点亮 1 点，满点自动升级');
{
  /* 空手 → 石进程：只需 1 点 */
  const { MC, API, me } = fresh();
  me.prog = 0; me.progPts = 0; me.ap = 10;
  ok(API.progProgress(me)===0, '初始进度点为 0', me.progPts);
  ok(API.progNeed(me)===1, '空手升石进程只需要 1 点', API.progNeed(me));
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===1, '投入 1 步即升级到石进程', MC.PROG_NAME[me.prog]);
  ok(API.progProgress(me)===0, '升级后进度点重新计数', API.progProgress(me));
}
{
  /* 石 → 铁：3 点，前两次只点亮小点 */
  const { API, me } = fresh();
  me.prog = 1; me.progPts = 0; me.ap = 10;
  ok(API.progNeed(me)===3, '石→铁需要 3 点', API.progNeed(me));
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===1 && API.progProgress(me)===1, '投 1 次：点亮 1 点、进程不变', [me.prog, API.progProgress(me)]);
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===1 && API.progProgress(me)===2, '投 2 次：点亮 2 点、仍未升级', [me.prog, API.progProgress(me)]);
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===2, '投第 3 次：升级到铁进程', MC.PROG_NAME[me.prog]);
}
{
  /* 超额投入的进度点结转到下一级 */
  const { API, me } = fresh();
  me.prog = 1; me.progPts = 0; me.ap = 10;
  /* 石→铁要 3 点：先垫到 3 点，再多投 1 次 → 升级后应剩 1 点给铁→钻石 */
  for(let i=0;i<3;i++) await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===2 && API.progProgress(me)===0, '刚好 3 点升级，剩余 0 点', [me.prog, API.progProgress(me)]);
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===2 && API.progProgress(me)===1, '升级后的投入计入下一级（铁→钻石 1/3）', [me.prog, API.progProgress(me)]);
}
{
  /* 进度点会存进 localStorage（每回合结束保存） */
  const { API, me } = fresh();
  me.prog = 1; me.progPts = 0; me.ap = 10;
  await API.applyAction(me, {type:'shop_progress'});
  const saved = JSON.parse((globalThis.__store && globalThis.__store.mcProg) || localStorage.getItem('mcProg') || '{}');
  const own = saved[me.name];
  ok(!!own && own.prog===1 && own.pts===1, '进度点已写入存档（名称 -> {prog,pts}）', own);
}

"""
r = r[:i] + new19 + r[j:]
F.write_text(r, encoding='utf-8')
print('【19】已重写，长度', len(r))
