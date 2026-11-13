# -*- coding: utf-8 -*-
"""补丁 17：rules-test 全面适配（静默开局 + 新判定用例）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
r = F.read_text(encoding='utf-8')

# 1) 全部改为静默开局（不启动主循环，避免异步污染断言）
r = r.replace("MC.start({ enemyCount:1, diff:'normal', auto:true });",
              "MC.start({ enemyCount:1, diff:'normal', auto:true, silent:true });")
r = r.replace("MC.start({enemyCount:2, diff:'normal', auto:true});",
              "MC.start({enemyCount:2, diff:'normal', auto:true, silent:true});")
r = r.replace("MC.start({enemyCount:1, diff:'normal', auto:true, mode:'2v2'});",
              "MC.start({enemyCount:1, diff:'normal', auto:true, mode:'2v2', silent:true});")

# 2) 【1】的 AP 断言改为先固定 AP
r = r.replace("""  await doOpt(API, me, up);
  ok(me.prog===1, '空手只需投入 1 步就升级到石进程', MC.PROG_NAME[me.prog]);
  ok(me.ap===1, '投入 1 步扣 1 AP', me.ap);""",
"""  await doOpt(API, me, up);
  ok(me.prog===1, '空手只需投入 1 步就升级到石进程', MC.PROG_NAME[me.prog]);
  ok(me.ap===1, '投入 1 步扣 1 AP', me.ap);
  me.ap = 6;""")

# 3) 重写【13】
i = r.index("console.log('\\n【13】判定规则")
j = r.index("console.log('\\n【14】")
new13 = r"""console.log('\n【13】判定规则：不发 AP；平局一直重猜直到分出胜负');
{
  const { API, me, ai } = fresh();
  ai.ap = 0;
  ok(await API.doJudgment(me, ai, {instant:true, a:'rock', b:'scissors', dodge:false})===true, '攻方胜出则命中');
  ok(await API.doJudgment(me, ai, {instant:true, a:'rock', b:'paper', dodge:false})===false, '攻方失败则攻击失效');
}
{
  /* 首轮平局且不闪避 → 继续重猜，最终必然给出 true/false，且全程不发 AP */
  const { API, me, ai } = fresh();
  me.ap = 0; ai.ap = 0;
  let hits = 0, misses = 0;
  for(let i=0;i<40;i++){
    const r = await API.doJudgment(me, ai, {instant:true, a:'rock', b:'rock', dodge:false});
    if(r === true) hits++; else if(r === false) misses++; else throw new Error('判定返回非布尔值: ' + r);
  }
  ok(hits + misses === 40, '平局后继续重猜，40 次判定全部给出结果', [hits, misses]);
  ok(hits > 0 && misses > 0, '重猜后胜负都会出现（不是固定结果）', [hits, misses]);
  ok(me.ap === 0 && ai.ap === 0, '判定全程不产生 AP', [me.ap, ai.ap]);
}
{
  /* 平局时被攻击方花 1 AP 直接闪避 */
  const { API, me, ai } = fresh();
  me.ap = 0; ai.ap = 3;
  const r = await API.doJudgment(me, ai, {instant:true, a:'rock', b:'rock', dodge:true});
  ok(r === false, '选择闪避 → 攻击失效', r);
  ok(ai.ap === 2, '闪避消耗 1 AP', ai.ap);
}
{
  /* 没有 AP 时无法闪避，只能继续重猜 */
  const { API, me, ai } = fresh();
  me.ap = 0; ai.ap = 0;
  const r = await API.doJudgment(me, ai, {instant:true, a:'rock', b:'rock', dodge:true});
  ok(typeof r === 'boolean', '没有 AP 时不会闪避，改为继续重猜并给出结果', r);
  ok(ai.ap === 0, 'AP 没有被消耗', ai.ap);
}

"""
r = r[:i] + new13 + r[j:]

# 4) 回合末清 AP 的用例：确认没有被主循环干扰
r = r.replace("""console.log('\\n【18】行动点不可存储：回合末清零');
{
  const { API, me, ai } = fresh();
  me.ap = 5; ai.ap = 3;
  await API.endOfRound({instant:true});
  ok(me.ap===0 && ai.ap===0, '回合结束时未用完的 AP 归零', [me.ap, ai.ap]);
}""",
"""console.log('\\n【18】行动点不可存储：回合末清零');
{
  const { API, me, ai } = fresh();
  me.ap = 5; ai.ap = 3;
  const pBefore = me.progPts;
  await API.endOfRound({instant:true});
  ok(me.ap===0 && ai.ap===0, '回合结束时未用完的 AP 归零', [me.ap, ai.ap]);
  ok(me.progPts===pBefore, '清零的只是 AP，进程进度点不受影响', [pBefore, me.progPts]);
}""")

F.write_text(r, encoding='utf-8')
print('rules-test 已更新，长度', len(r))
