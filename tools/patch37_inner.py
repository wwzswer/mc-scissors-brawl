# -*- coding: utf-8 -*-
"""补丁 37：在 iframe 内直接验证攻击选项（排除父页面调用的干扰）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\e2e.html')
t = F.read_text(encoding='utf-8')

old = "    const atk = MC.__api.buildHumanOptions(me2).find(o=>o.type==='attack');"
new = ("    /* 在 iframe 自己的 realm 里构建一次选项，排除跨 realm 调用的干扰 */\n"
       "    let inner = null;\n"
       "    try{\n"
       "      inner = W.eval('(function(){ const p = MCGame.state().players[0];'\n"
       "        + ' const opts = MCGame.__api.buildHumanOptions(p);'\n"
       "        + ' return {weapon:p.weapon, types:opts.map(o=>o.type+(o.key?\":\"+o.key:\"\")).join(\",\"),'\n"
       "        + ' inRange: typeof MCGame.__api.inRangeOf===\"function\" ? MCGame.__api.inRangeOf(p, p.weapon, MCGame.state().players[1]) : null,'
       " '\n"
       "        + ' dist: MCGame.__api.distanceBetween(p, MCGame.state().players[1])}; })()');\n"
       "    }catch(e){ say('  iframe 内构建失败: '+e.message, 'warn'); }\n"
       "    if(inner) say('  iframe 内: weapon='+inner.weapon+' inRange='+inner.inRange+' dist='+inner.dist'\n"
       "      +' 选项=['+String(inner.types).slice(0,120)+']');\n"
       "    const atk = MC.__api.buildHumanOptions(me2).find(o=>o.type==='attack');")
if old in t:
    t = t.replace(old, new, 1)
    F.write_text(t, encoding='utf-8')
    print('已加 iframe 内诊断')
else:
    print('! 锚点未匹配')
