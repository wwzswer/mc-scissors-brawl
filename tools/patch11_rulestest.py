# -*- coding: utf-8 -*-
"""补丁 11：把 rules-test 里旧的“一次性升级”用例改写为进度点制"""
import pathlib, re

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
t = F.read_text(encoding='utf-8')

# 定位【1】与【2】两节，整体替换为进度点制版本
start = t.index("console.log('\\n【1】")
end = t.index("console.log('\\n【3】")

new = r"""console.log('\n【1】进程升级（进度点制）与制作');
{
  const { MC, API, me } = fresh();
  me.prog = 0; me.progPts = 0; me.ap = 2;
  const up = API.buildHumanOptions(me).find(o=>o.type==='shop_progress');
  ok(!!up && up.cost===1, '空手能看到「投入 1 步进度」入口（1 AP）', up && up.label);
  await doOpt(API, me, up);
  ok(me.prog===0 && API.progProgress(me)===1, '投入 1 步只点亮 1 个点，进程不变', [me.prog, API.progProgress(me)]);
  ok(me.ap===1, '投入 1 步只扣 1 AP', me.ap);
  await doOpt(API, me, API.buildHumanOptions(me).find(o=>o.type==='shop_progress'));
  ok(me.prog===1, '集满 2 点后升级到木进程', MC.PROG_NAME[me.prog]);
  ok(me.ap===0, '两次投入共扣 2 AP', me.ap);
}
{
  const { MC, API, me } = fresh();
  me.prog = 1; me.progPts = 0; me.ap = 5;
  const sword = API.buildHumanOptions(me).find(o=>o.type==='craftShopItem'&&o.key==='wood_sword');
  ok(!!sword && sword.cost===2, '木进程能看到木剑（2 步一次性制作）', sword && sword.label);
  await doOpt(API, me, sword);
  ok(me.weapon==='wood_sword', '制作后自动装备木剑', me.weapon);
  ok(me.ap===3, '木剑扣 2 AP（5-2=3）', me.ap);
}

console.log('\n【2】各级进程所需进度点：木 2 / 石 2 / 铁 3 / 钻石 3');
{
  const { MC, API, me } = fresh();
  const reqs = [null,1,2,3,4].map(i=>{ me.prog=i; return API.progNeed(me); });
  ok(reqs[1]===2 && reqs[2]===2 && reqs[3]===3 && reqs[4]===3,
     '所需点数：木2 / 石2 / 铁3 / 钻石3', reqs);
}
{
  const { MC, API, me } = fresh();
  me.prog = 2; me.progPts = 0; me.ap = 10;
  await doOpt(API, me, {type:'shop_progress'});
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===2 && API.progProgress(me)===2, '石→铁：投 2 次还不升级', [me.prog, API.progProgress(me)]);
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===3, '投第 3 次升级到铁进程', MC.PROG_NAME[me.prog]);
}
{
  const { MC, API, me } = fresh();
  me.prog = 3; me.progPts = 0; me.ap = 10;
  for(let i=0;i<3;i++) await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===4, '铁→钻石需要 3 点', MC.PROG_NAME[me.prog]);
}
{
  const { MC, API, me } = fresh();
  me.prog = 4; me.ap = 5;
  ok(API.progMaxed(me), '钻石进程后不可再升级', MC.PROG_NAME[me.prog]);
  ok(!API.buildHumanOptions(me).some(o=>o.type==='shop_progress'), '满级后不再显示投入进度入口');
}

"""
t = t[:start] + new + t[end:]
F.write_text(t, encoding='utf-8')
print('rules-test 用例已改写，长度', len(t))
