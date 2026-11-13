# -*- coding: utf-8 -*-
"""补丁 35：给 E2E 的攻击选项断言加详细调试（定位浏览器里的差异）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\e2e.html')
t = F.read_text(encoding='utf-8')

old = "    if(!atk) say('  调试信息: weapon='+me.weapon+' dist='+MC.__api.distanceBetween(me,G.players[1])+' items='+JSON.stringify(me.items), 'warn');"
new = ("    if(!atk){\n"
       "      const types = MC.__api.buildHumanOptions(me).map(o=>o.type+(o.key?':'+o.key:'')).join(',');\n"
       "      const foes = G.players.filter(q=>q.alive && q.team!==me.team).map(q=>q.name+'/'+q.hp);\n"
       "      say('  调试: weapon='+me.weapon+' alive='+me.alive+' dist='+MC.__api.distanceBetween(me,G.players[1])\n"
       "        +' 敌人=['+foes.join(' ')+'] 选项=['+types.slice(0,160)+']', 'warn');\n"
       "    }")
if old in t:
    t = t.replace(old, new, 1)
    F.write_text(t, encoding='utf-8')
    print('已加详细调试')
else:
    print('! 锚点未匹配')
