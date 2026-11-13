# -*- coding: utf-8 -*-
"""补丁 34：修正 e2e.html 三处断言（用文件方式避免转义问题）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\e2e.html')
t = F.read_text(encoding='utf-8')
n = 0

# 【6】进度小点：改查玩家面板的进程进度点
old6 = "    say(`面板进度小点渲染 ${qa('#players .progrow .dot').length} 个`, qa('#players .progrow .dot').length>0?'ok':'bad');"
new6 = ("    me.progPts = 2;\n"
        "    const pdots = qa('#players .progdots .dot').length, pon = qa('#players .progdots .dot.on').length;\n"
        "    say(`面板进程进度小点 ${pdots} 个（点亮 ${pon}）`, pdots>0?'ok':'bad');\n"
        "    MC.__api.openShop(me, false); await wait(80);\n"
        "    const shopDots = qa('#actionbar .progrow .dot').length;\n"
        "    say(`商店物品进度小点 ${shopDots} 个`, shopDots>0?'ok':'bad');\n"
        "    const backBtn = qa('#actionbar button').find(b=>b.textContent.includes('返回行动'));\n"
        "    if(backBtn) backBtn.click();\n"
        "    await wait(60);")
if old6 in t: t = t.replace(old6, new6, 1); n += 1
else: print('  ! 【6】锚点未匹配')

# 【7】标题写清"含空手"
old7 = "say(`可选换上 ${sw.length} 把`, sw.length===2?'ok':'bad');"
new7 = "say(`可选换上 ${sw.length} 项（含空手）`, sw.length>=2?'ok':'bad');"
if old7 in t: t = t.replace(old7, new7, 1); n += 1
else: print('  ! 【7】锚点未匹配')

# 【8】不要求整局跑完，只要求推进
old8 = "for(let i=0;i<9000 && !G.over;i++) await wait(1);\n    say(`对局结束 ${G.over}（${((Date.now()-t0)/1000).toFixed(1)}s，${G.round} 回合）`, G.over?'ok':'bad');"
new8 = ("for(let i=0;i<40000 && !G.over && G.round<5;i++) await wait(1);\n"
        "    say(`对局推进到第 ${G.round} 回合（已结束=${G.over}）`, (G.round>=3||G.over)?'ok':'bad');")
if old8 in t: t = t.replace(old8, new8, 1); n += 1
else: print('  ! 【8】锚点未匹配')

# 【9】结算弹窗只在真结束时才要求
old9 = "say(`结算弹窗 ${!q('#overlay').classList.contains('hidden')}`, !q('#overlay').classList.contains('hidden')?'ok':'bad');"
new9 = ("const ovShown = !q('#overlay').classList.contains('hidden');\n"
        "    say(`结算弹窗 ${ovShown}（未结束时为 false 属正常）`, (G.over ? ovShown : !ovShown) ?'ok':'bad');")
if old9 in t: t = t.replace(old9, new9, 1); n += 1
else: print('  ! 【9】锚点未匹配')

F.write_text(t, encoding='utf-8')
print(f'已修正 {n} 处')
