# -*- coding: utf-8 -*-
"""补丁 107：测试用例补足 AP（面包/金苹果现在要 1 AP）"""
import pathlib, re

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
t = F.read_text(encoding='utf-8')
n = 0

# 在涉及 eat/potion 的测试里，确保 me.ap 足够。统一：把 fresh() 出来的 me 初始 AP 设为 5
old_fresh = """  MC.start({ enemyCount:1, diff:'normal', auto:true, silent:true });
  const G = MC.state();
  const API = MC.__api;
  const me = G.players[0], ai = G.players[1];
  return { MC, API, G, me, ai };"""
new_fresh = """  MC.start({ enemyCount:1, diff:'normal', auto:true, silent:true });
  const G = MC.state();
  const API = MC.__api;
  const me = G.players[0], ai = G.players[1];
  me.ap = 5; ai.ap = 5;        /* 默认给点 AP：面包/金苹果等现在各需 1 AP */
  return { MC, API, G, me, ai };"""
if old_fresh in t:
    t = t.replace(old_fresh, new_fresh, 1); n += 1
    print('  ok fresh() 默认给 5 AP')
else:
    print('  ! fresh() 锚点未匹配')

F.write_text(t, encoding='utf-8')
print(f'更新 {n} 处')
