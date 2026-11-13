# -*- coding: utf-8 -*-
"""补丁 43：E2E 第 8 步改为正常开局（silent 会不启动主循环）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\e2e.html')
t = F.read_text(encoding='utf-8')

old = """    MC.__api.setFastTiming(); MC.__api.setInstantRps && MC.__api.setInstantRps();
    MC.__api.setAutoPlayer((p,opts)=>{
      const o=opts||[];
      return o.find(x=>x.type==='attack') || o.find(x=>x.type==='craftShopItem')
          || o.find(x=>x.type==='shop_progress') || o.find(x=>x.type==='move') || {type:'pass'};
    });
    const t0 = Date.now();"""
new = """    MC.__api.setFastTiming(); MC.__api.setInstantRps && MC.__api.setInstantRps();
    MC.__api.setAutoPlayer((p,opts)=>{
      const o=opts||[];
      return o.find(x=>x.type==='attack') || o.find(x=>x.type==='craftShopItem')
          || o.find(x=>x.type==='shop_progress') || o.find(x=>x.type==='move') || {type:'pass'};
    });
    /* 重新正常开一局（不传 silent，主循环才会跑起来） */
    MC.start({enemyCount:1, diff:'normal', auto:true, mode:'1v1', name:'测试员'});
    const G8 = MC.state();
    const t0 = Date.now();"""
if old in t:
    t = t.replace(old, new, 1); print('  ok 第8步正常开局')
else:
    print('  ! 第8步锚点未匹配')

# 第 8 步后续引用 G -> G8
t = t.replace("for(let i=0;i<40000 && !G.over && G.round<5;i++) await wait(1);\n    say(`对局推进到第 ${G.round} 回合（已结束=${G.over}）`, (G.round>=3||G.over)?'ok':'bad');",
              "for(let i=0;i<40000 && !G8.over && G8.round<5;i++) await wait(1);\n    say(`对局推进到第 ${G8.round} 回合（已结束=${G8.over}）`, (G8.round>=3||G8.over)?'ok':'bad');")
t = t.replace("say(`面板 ${qa('#players .pcard').length}｜血量块 ${qa('#players .hpblk').length}｜贴图 ${qa('#players .spr').length}`);",
              "say(`面板 ${qa('#players .pcard').length}｜血量块 ${qa('#players .hpblk').length}｜贴图 ${qa('#players .spr').length}`);")
t = t.replace("say(`面板 ${qa('#players .pcard').length}｜血量块 ${qa('#players .hpblk').length}｜贴图 ${qa('#players .spr').length}`);",
              "say(`面板 ${qa('#players .pcard').length}｜血量块 ${qa('#players .hpblk').length}｜贴图 ${qa('#players .spr').length}`);")
t = t.replace("say(`进度点 ${qa('#players .progdots').length} 组｜日志 ${qa('#log div').length} 行`);",
              "say(`进度点 ${qa('#players .progdots').length} 组｜日志 ${qa('#log div').length} 行`);")
t = t.replace("const ovShown = !q('#overlay').classList.contains('hidden');\n    say(`结算弹窗 ${ovShown}（未结束时为 false 属正常）`, (G.over ? ovShown : !ovShown) ?'ok':'bad');",
              "const ovShown = !q('#overlay').classList.contains('hidden');\n    say(`结算弹窗 ${ovShown}（对局结束=${G8.over}）`, (G8.over ? ovShown : !ovShown) ?'ok':'bad');")

F.write_text(t, encoding='utf-8')
print('E2E 第 8 步已调整')
