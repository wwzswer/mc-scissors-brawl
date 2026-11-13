# -*- coding: utf-8 -*-
"""补丁 118：文档与版本（v1.4）"""
import pathlib

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')

# 版本号
P = D / 'index.html'
t = P.read_text(encoding='utf-8')
for old_v in ['基础版 v1.3 · <b id="buildTag" style="color:var(--acc2)">附魔修正+攻击校验</b>']:
    if old_v in t:
        t = t.replace(old_v, '基础版 v1.4 · <b id="buildTag" style="color:var(--acc2)">内容开关+拾取AP</b>', 1)
        print('ok 版本 → v1.4')
        break
else:
    print('! 版本锚点未匹配')
P.write_text(t, encoding='utf-8')

# RULES.md
F = D / 'RULES.md'
r = F.read_text(encoding='utf-8')
n = 0

pairs = [
    ("| **设置项** | 游戏模式（1v1 / **2V2**）、敌方数量、AI 强度、猜拳方式、**猜拳获胜 AP（1 或 2）** |",
     "| **设置项** | 游戏模式（1v1 / **2V2**）、敌方数量、AI 强度、猜拳方式、**猜拳获胜 AP（1 或 2）**、**可选内容开关**（不死图腾 / 药水 / TNT / 附魔金苹果，可分别禁用；改动在下局生效） |"),
    ("**无【忠诚】时掷出后掉落，落在目标所在格，与其同格的存活玩家随机一人拾取**（无人同格则丢失）；**有【忠诚】必定回手** |",
     "**无【忠诚】时掷出后掉落，落在目标所在格：与其同格且 AP≥1 的玩家会花 1 AP 拾取**（AP 不足则无人拾取、三叉戟丢失）；**有【忠诚】必定回手** |"),
]
for old, new in pairs:
    if old in r:
        r = r.replace(old, new, 1); n += 1; print('  ok', old[:30].replace('\n', ' '))
    else:
        print('  ! 未找到', old[:30].replace('\n', ' '))

# 追加“可选内容开关”小节
if '可选内容开关' not in r:
    r = r.rstrip() + """

## 13. 可选内容开关（设置页）

设置页可**分别启用/禁用**以下内容，取消勾选后它们不会出现在商店与行动选项里：

| 开关 | 影响范围 |
|---|---|
| **不死图腾** | 林地府邸不再提供图腾；复活效果同样失效 |
| **药水** | 女巫小屋不再提供药水，药水选项消失 |
| **TNT** | 商店不再出售 TNT；沙漠金字塔不再提供「4 个 TNT」；粘贴/引爆选项消失 |
| **附魔金苹果** | 沙漠金字塔不再提供附魔金苹果，食用选项消失 |

> 开关保存在本机（按浏览器），**改动在下局开始时生效**。
"""
    n += 1
    print('  ok 追加「可选内容开关」小节')

F.write_text(r, encoding='utf-8')
print(f'RULES.md 更新 {n} 处')

# 清理
for nm in ['index.prev.html', 'dbg-feat.cjs', 'dbg-feat2.cjs']:
    q = D / nm
    if q.exists():
        q.unlink(); print('已删除', nm)
print('index.html %.0f KB' % ((D / 'index.html').stat().st_size / 1024))
