# -*- coding: utf-8 -*-
"""补丁 38：RULES.md 测试清单补充"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\RULES.md')
t = F.read_text(encoding='utf-8')

old = "| `net-mini.html` | 联机轮询最小验证（浏览器） | 通过 |"
new = ("| `net-mini.html` | 联机轮询最小验证（浏览器） | 通过 |\n"
       "| `tool-check.html` | 切换手上工具 / 攻击选项专项验证（浏览器 iframe realm） | 全过 |\n"
       "| `e2e-net.html` | 双客户端联机流程（浏览器） | 通过 |")

if 'tool-check.html' in t:
    print('已存在，跳过')
else:
    assert old in t, '锚点缺失'
    t = t.replace(old, new, 1)
    F.write_text(t, encoding='utf-8')
    print('RULES.md 已补充测试清单')
