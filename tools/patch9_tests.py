# -*- coding: utf-8 -*-
"""补丁 9：测试脚本适配新功能
   - DOM 桩补 localStorage（进度存盘需要）
   - rules-test 增加：AP 回合末清零 / 进度点制 / 2V2 / 距离上限与独立性
"""
import pathlib

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')

# ---------------- rules-test.js ----------------
f = D / 'rules-test.js'
t = f.read_text(encoding='utf-8')

# 1) localStorage 桩
if 'localStorage' not in t:
    old = "  const sandbox={ document, window:{}, setTimeout, clearTimeout, setInterval, clearInterval, console,"
    new = """  const store = {};
  const localStorage = {
    getItem:k=>(k in store ? store[k] : null),
    setItem:(k,v)=>{ store[k]=String(v); },
    removeItem:k=>{ delete store[k]; }, clear:()=>{ for(const k in store) delete store[k]; },
  };
  const sandbox={ document, window:{}, localStorage, setTimeout, clearTimeout, setInterval, clearInterval, console,"""
    assert old in t, 'rules-test 锚点缺失'
    t = t.replace(old, new, 1)

# 2) 追加新用例（在最后的汇总之前插入）
if '【18】' not in t:
    tail = "console.log('\\n──────────────────────────────');"
    assert tail in t, 'rules-test 结尾锚点缺失'
    extra = r"""console.log('\n【18】行动点不可存储：回合末清零');
{
  const { API, me, ai } = fresh();
  me.ap = 5; ai.ap = 3;
  await API.endOfRound({instant:true});
  ok(me.ap===0 && ai.ap===0, '回合结束时未用完的 AP 归零', [me.ap, ai.ap]);
}
{
  const { API, me } = fresh();
  me.ap = 4;
  await API.endOfRound({instant:true});
  /* 下一回合猜拳获胜才重新获得 AP */
  ok(me.ap===0, '清零后不会保留到下一回合', me.ap);
}

console.log('\n【19】进度点制：每投入 1 步点亮 1 点，满点自动升级');
{
  const { MC, API, me } = fresh();
  me.prog = 0; me.progPts = 0; me.ap = 10;
  const need0 = API.progNeed ? API.progNeed(me) : 2;
  ok(me.progPts===0 && API.progProgress(me)===0, '初始进度点为 0', me.progPts);
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===0 && API.progProgress(me)===1, '投入 1 步后只点亮 1 点、进程不变', [me.prog, API.progProgress(me)]);
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===1, '集满所需点数后自动升级到木进程', MC.PROG_NAME[me.prog]);
  ok(API.progProgress(me)===0, '升级后进度点重新计数', API.progProgress(me));
}
{
  const { API, me } = fresh();
  me.prog = 2; me.progPts = 0; me.ap = 10;      /* 石 → 铁需要 3 点 */
  await API.applyAction(me, {type:'shop_progress'});
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===2 && API.progProgress(me)===2, '石→铁需要 3 点：投 2 次还不升级', [me.prog, API.progProgress(me)]);
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===3, '第 3 次投入后升级到铁进程', [me.prog]);
}
{
  const { API, me } = fresh();
  me.prog = 0; me.progPts = 2; me.ap = 10;      /* 进度点结转到下一级 */
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===1 && API.progProgress(me)===1, '多余的点结转到下一级', [me.prog, API.progProgress(me)]);
}

console.log('\n【20】距离：初始 1、上限 7、两两独立');
{
  const { API, G, me, ai } = fresh();
  ok(G.dist[me.id][ai.id]===1, '初始距离为 1 格', G.dist[me.id][ai.id]);
  API.setDistance(me, ai, 99);
  ok(G.dist[me.id][ai.id]===7, '距离上限为 7', G.dist[me.id][ai.id]);
  API.setDistance(me, ai, -5);
  ok(G.dist[me.id][ai.id]===0, '距离下限为 0', G.dist[me.id][ai.id]);
}
{
  /* 三人：A-B 与 A-C 独立，B-C 不受影响 */
  const { MC, API, G } = fresh();
  MC.start({enemyCount:2, diff:'normal', auto:true});
  const G2 = MC.state(), a = G2.players[0], b = G2.players[1], c = G2.players[2];
  API.setDistance(a, b, 0);
  API.setDistance(a, c, 0);
  ok(G2.dist[b.id][c.id]===1, 'A-B=0、A-C=0 时 B-C 仍为 1（互不影响）', G2.dist[b.id][c.id]);
  API.setDistance(b, c, 4);
  ok(G2.dist[a.id][b.id]===0 && G2.dist[a.id][c.id]===0 && G2.dist[b.id][c.id]===4,
     '三者距离互相独立', [G2.dist[a.id][b.id], G2.dist[a.id][c.id], G2.dist[b.id][c.id]]);
}

console.log('\n【21】2V2 模式');
{
  const { MC, API, G } = fresh();
  MC.start({enemyCount:1, diff:'normal', auto:true, mode:'2v2'});
  const G3 = MC.state();
  ok(G3.players.length===4, '2V2 共 4 名玩家', G3.players.length);
  const mine = G3.players.filter(p=>p.team===0);
  const foes = G3.players.filter(p=>p.team===1);
  ok(mine.length===2 && foes.length===2, '2 名自家人 vs 2 名敌人', [mine.length, foes.length]);
  const ally = mine.find(p=>!p.isHuman);
  ok(!!ally && ally.isEnemy===false, '存在 AI 队友', ally && ally.name);
  /* 队友之间不能互相攻击 */
  const opts = API.buildHumanOptions(mine[0]);
  const friendly = opts.filter(o=>o.type==='attack' && G3.players[o.targetId].team===0);
  ok(friendly.length===0, '不能攻击队友', friendly.length);
  /* 面包可以喂队友 */
  API.addItem(mine[0], 'bread', 1);
  const feed = API.buildHumanOptions(mine[0]).filter(o=>o.type==='eat' && o.targetId!==mine[0].id);
  ok(feed.length>=1, '面包可以喂给队友', feed.length);
}

"""
    t = t.replace(tail, extra + tail, 1)

f.write_text(t, encoding='utf-8')
print('rules-test.js 已更新，长度', len(t))

# ---------------- match-test.js：补 localStorage ----------------
f2 = D / 'match-test.js'
t2 = f2.read_text(encoding='utf-8')
if 'localStorage' not in t2:
    old2 = "  const sandbox = { document, window:{}, setTimeout, clearTimeout, setInterval, clearInterval, console,"
    new2 = """  const store = {};
  const localStorage = {
    getItem:k=>(k in store ? store[k] : null),
    setItem:(k,v)=>{ store[k]=String(v); },
    removeItem:k=>{ delete store[k]; }, clear:()=>{ for(const k in store) delete store[k]; },
  };
  const sandbox = { document, window:{}, localStorage, setTimeout, clearTimeout, setInterval, clearInterval, console,"""
    assert old2 in t2, 'match-test 锚点缺失'
    t2 = t2.replace(old2, new2, 1)
    f2.write_text(t2, encoding='utf-8')
    print('match-test.js 已补 localStorage 桩')
else:
    print('match-test.js 已有 localStorage')
