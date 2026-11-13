# -*- coding: utf-8 -*-
"""补丁 41：E2E 第 7 步前后抓现场（玩家数/runId/全局标记）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\e2e.html')
t = F.read_text(encoding='utf-8')

old = """    MC.__api.setAutoPlayer(null);
    MC.start({enemyCount:1, diff:'normal', auto:false, mode:'1v1', silent:true, name:'工具测试'});
    await wait(150);"""
new = """    MC.__api.setAutoPlayer(null);
    const before = W.eval("(function(){ const G=MCGame.state(); return {players:G?G.players.length:-1, round:G?G.round:-1, over:G?G.over:null, runId:G?G.runId:'-', gRun:globalThis.__MC_RUN}; })()");
    say(`  重开前现场：${JSON.stringify(before)}`);
    MC.start({enemyCount:1, diff:'normal', auto:false, mode:'1v1', silent:true, name:'工具测试'});
    await wait(150);
    const after = W.eval("(function(){ const G=MCGame.state(); return {players:G.players.length, names:G.players.map(p=>p.name+(p.isEnemy?'[敌]':'[我]')).join(' '), round:G.round, over:G.over, runId:G.runId, gRun:globalThis.__MC_RUN, foes:G.players.filter(p=>p.alive&&p.team!==G.players[0].team).length}; })()");
    say(`  重开后现场：${JSON.stringify(after)}`);"""
if old in t:
    t = t.replace(old, new, 1)
    F.write_text(t, encoding='utf-8')
    print('已加现场抓取')
else:
    print('! 锚点未匹配')
