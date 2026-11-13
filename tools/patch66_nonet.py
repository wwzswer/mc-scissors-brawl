# -*- coding: utf-8 -*-
"""补丁 66：暂停联机模式（隐藏入口、改到设置页，主菜单不再显示）"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

# 1) 主菜单移除联机按钮
old_btn = '<button class="mbtn" id="mNet">🌐 局域网联机</button>'
if old_btn in t:
    t = t.replace(old_btn, '<!-- 联机模式暂时下线（入口已移除） -->', 1)
    notes.append('  ok 主菜单移除联机按钮')
else:
    notes.append('  ! 主菜单联机按钮未找到')

# 2) 设置页加一个提示（说明联机暂时下线）
m = re.search(r'(<div class="card hidden" id="screen-setting">.*?)(</div>\s*</div>)', t, re.S)
if m and '联机暂时下线' not in t:
    tip = ('<div style="margin-top:10px;font-size:12px;color:var(--dim)">'
           '🌐 局域网联机模式暂时下线（正在改造中），当前为纯单机版本。</div>\n')
    t = t[:m.end(1)] + tip + t[m.end(1):]
    notes.append('  ok 设置页加联机下线提示')

# 3) 规则页里“联机怎么玩”卡片去掉
old_rule = re.search(r"<div class=\"rulecard\"><h4>\$\{sprTag\('coin',26\)\} 联机怎么玩</h4>.*?</div>\s*`;", t, re.S)
if old_rule:
    t = t[:old_rule.start()] + '`;' + t[old_rule.end():]
    notes.append('  ok 规则页移除联机卡片')
else:
    notes.append('  ! 规则页联机卡片未找到（可能格式不同）')

# 4) on('mNet', ...) 绑定保留（元素不存在时 on() 应该安全），但加个保护
old_on = "on('mNet', ()=>{ sfx.click(); showScreen('screen-net'); netRefresh(); });"
if old_on in t:
    t = t.replace(old_on, "/* on('mNet', ...) 已移除：联机模式暂时下线 */", 1)
    notes.append('  ok 移除 mNet 事件绑定')

# 5) 快捷键/其它入口里的联机跳转
old_nav = "showScreen('screen-net')"
if old_nav in t:
    cnt = t.count(old_nav)
    t = t.replace(old_nav, "showScreen('screen-main')")
    notes.append(f"  ok 屏蔽 showScreen('screen-net') {cnt} 处")

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
