# -*- coding: utf-8 -*-
"""补丁 112：文档与版本更新（v1.3）"""
import pathlib

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')

# --- index.html：版本号 ---
P = D / 'index.html'
t = P.read_text(encoding='utf-8')
old_v = '基础版 v1.2 · <b id="buildTag" style="color:var(--acc2)">商店修复+补给AP</b>'
new_v = '基础版 v1.3 · <b id="buildTag" style="color:var(--acc2)">附魔修正+攻击校验</b>'
if old_v in t:
    t = t.replace(old_v, new_v, 1)
    print('ok 版本号 → v1.3')
else:
    print('! 版本号锚点未匹配')
P.write_text(t, encoding='utf-8')

# --- RULES.md ---
F = D / 'RULES.md'
r = F.read_text(encoding='utf-8')
n = 0

pairs = [
    ("| 铁 | 打火石 | 1 | 0 | — | 无需判定：点燃目标，**接下来 3 个回合每回合结束各结算 1 次 0.5 火焰**（合计 1.5；目标持有护甲则只持续 2 回合）。**重复点燃只刷新剩余回合，不叠加每回合次数**。入水可扑灭 |",
     "| 铁 | 打火石 | 1 | 0 | — | **需判定**：胜出后点燃目标，**接下来 3 个回合每回合结束各结算 1 次 0.5 火焰**（合计 1.5；目标持有护甲则只持续 2 回合）。**重复点燃只刷新剩余回合，不叠加每回合次数**。入水可扑灭 |"),
    ("| 石 | 末影珍珠 | 2 | — | — | **获得后永不消耗**：每次使与某人距离 ±2 格（免费） |",
     "| 石 | 末影珍珠 | 2 | — | — | **获得后永不消耗**：每次使与某人距离 ±2 格（**1 AP**） |"),
    ("| 石 | 三叉戟 | 3 | 1 | **钓鱼竿** | ① 0 格近战：判定 1.5 物理 ② 掷出（≥1 格）：无需判定 1.5 物理但失去它（【忠诚】会回手） |",
     "| 石 | 三叉戟 | 3 | 1 | **钓鱼竿** | ① 0 格近战：判定 1.5 物理 ② 掷出（≥1 格）：无需判定 1.5 物理。**无【忠诚】时掷出后掉落，落在目标所在格，与其同格的存活玩家随机一人拾取**（无人同格则丢失）；**有【忠诚】必定回手** |"),
    ("- **切换手上工具**：持有多个武器时可随时免费切换（**不花 AP、不占行动次数**）。",
     "- **攻击前会先校验距离**：距离不够时**不消耗 AP**，只提示打不到。\n- **切换手上工具**：持有多个武器时可随时免费切换（**不花 AP、不占行动次数**）。"),
]
for old, new in pairs:
    if old in r:
        r = r.replace(old, new, 1); n += 1; print('  ok', old[:32].replace('\n',' '))
    else:
        print('  ! 未找到', old[:32].replace('\n',' '))

F.write_text(r, encoding='utf-8')
print(f'RULES.md 更新 {n} 处')

# --- 清理临时文件 ---
for nm in ['index.prev.html', 'dbg-issues.cjs', 'dbg-trident.cjs']:
    q = D / nm
    if q.exists():
        q.unlink(); print('已删除', nm)
print('index.html %.0f KB' % ((D/'index.html').stat().st_size/1024))
