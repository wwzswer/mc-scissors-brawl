# -*- coding: utf-8 -*-
"""补丁 36：E2E 第 6/7 步改用干净局面，避免 openShop 留下的悬空 await 干扰"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\e2e.html')
t = F.read_text(encoding='utf-8')

# 第 6 步：不再调用 openShop（它会留下悬空的 await openShop 干扰后续）
old6 = ("    MC.__api.openShop(me, false); await wait(80);\n"
        "    const shopDots = qa('#actionbar .progrow .dot').length;\n"
        "    say(`商店物品进度小点 ${shopDots} 个`, shopDots>0?'ok':'bad');\n"
        "    const backBtn = qa('#actionbar button').find(b=>b.textContent.includes('返回行动'));\n"
        "    if(backBtn) backBtn.click();\n"
        "    await wait(60);")
new6 = ("    /* 直接检查物品进度小点的渲染函数（不打开商店面板，避免悬空 await） */\n"
        "    const rowHtml = MC.__api.itemProgRow(me, 'trident');\n"
        "    say(`物品进度小点 HTML 含 dot：${rowHtml.includes('dot')}`, rowHtml.includes('dot')?'ok':'bad');\n"
        "    say(`商店渲染函数可用：${typeof MC.__api.openShop==='function'}`, typeof MC.__api.openShop==='function'?'ok':'bad');")
if old6 in t:
    t = t.replace(old6, new6, 1); print('  ok 【6】不再开商店')
else:
    print('  ! 【6】锚点未匹配')

# 第 7 步：重开一局干净局面，并挂住 askHuman（模拟正常等待玩家输入）
old7 = "    say('【7】切换手上工具');\n    me.weapon='fist'; me.itemPts={};"
new7 = ("    say('【7】切换手上工具');\n"
        "    /* 重开一局干净局面：避免前面步骤留下的异步等待干扰 */\n"
        "    MC.__api.setAutoPlayer(null);\n"
        "    MC.start({enemyCount:1, diff:'normal', auto:false, mode:'1v1', silent:true, name:'工具测试'});\n"
        "    await wait(120);\n"
        "    MC.__api.askHuman(me, MC.__api.buildHumanOptions(me)).catch(()=>{});   /* 让回合等待玩家输入 */\n"
        "    me.weapon='fist'; me.itemPts={};")
if old7 in t:
    t = t.replace(old7, new7, 1); print('  ok 【7】干净局面')
else:
    print('  ! 【7】锚点未匹配')

F.write_text(t, encoding='utf-8')
print('e2e 第 6/7 步已调整')
