# -*- coding: utf-8 -*-
"""补丁 62：修正 atkap-check 的按钮选择（精确匹配攻击按钮），并修正走位断言"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\atkap-check.html')
t = F.read_text(encoding='utf-8')

# 精确选攻击按钮：用 iframe 内的 options 找到攻击项的 label，再按 label 匹配按钮
old = "    const atkBtn = qa('#actionbar button').find(b=>/判定|远程|一拳/.test(b.textContent));"
new = """    const atkLabel = ev(`(function(){
      const A=MCGame.__api, p=MCGame.state().players[0];
      const a=A.buildHumanOptions(p).find(o=>o.type==='attack');
      return a ? a.label : '';
    })()`);
    const atkBtn = qa('#actionbar button').find(b=>atkLabel && b.textContent.trim().startsWith(atkLabel.replace(/（.*$/,'').trim()));"""
if old in t:
    t = t.replace(old, new, 1); print('  ok 攻击按钮精确匹配')
else:
    print('  ! 锚点未匹配')

# 走位断言：用 canShow（人类面板的可见性）而不是 canPay
old2 = """        movePayable: opts.filter(o=>o.type==='move').filter(o=>A.canPay(p,o)).length"""
new2 = """        movePayable: opts.filter(o=>o.type==='move').filter(o=>A.canShow(p,o)).length"""
if old2 in t:
    t = t.replace(old2, new2, 1); print('  ok 走位改用 canShow')

F.write_text(t, encoding='utf-8')
print('atkap-check 已修正')
