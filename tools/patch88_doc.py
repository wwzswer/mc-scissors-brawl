# -*- coding: utf-8 -*-
"""补丁 88：文档更新（背包物品直接可用 + 打火石结算方式）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\RULES.md')
t = F.read_text(encoding='utf-8')
n = 0

def rep(old, new, label):
    global t, n
    if old in t:
        t = t.replace(old, new, 1); n += 1; print('  ok', label)
    else:
        print('  ! 未找到', label)

rep("""- **切换手上工具**：持有多个武器时可随时免费切换（**不花 AP、不占行动次数**），攻击用当前手上那件。注意**攻击本身每次要 1 AP**。""",
"""- **切换手上工具**：持有多个武器时可随时免费切换（**不花 AP、不占行动次数**）。
- **背包里的攻击物品直接可用**：只要满足距离要求，**不需要先装备**——腐肉、打火石、弩、烟花、剑等
  都会直接出现在「攻击」区里，点击即可出手，并且**自动切换成该武器**（腐肉/打火石属于道具，不占武器槽）。
  注意**每次攻击都要 1 AP**。""",
'背包物品可用')

rep("""| 铁 | 打火石 | 1 | 0 | — | 无需判定：3 次 0.5 火焰（目标有防具则 2 次）。首次立即结算，其余回合末结算 |""",
"""| 铁 | 打火石 | 1 | 0 | — | 无需判定：点燃目标，**3 次 0.5 火焰**（目标持有护甲则 2 次）。**全部次数在本回合末统一结算**，期间入水可取消 |""",
'打火石说明')

F.write_text(t, encoding='utf-8')
print(f'RULES.md 更新 {n} 处')

# 顺带修正 ITEMS 里打火石的 desc（首次立即结算 → 统一回合末）
IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
s = IDX.read_text(encoding='utf-8')
old_desc = "desc:'无需判定：3 次 0.5 火焰伤害；若目标有防具则只造成 2 次 0.5 火焰伤害。首次立即结算，其余在每回合所有玩家行动结束后结算。'"
new_desc = "desc:'无需判定：点燃目标，3 次 0.5 火焰伤害（目标持有护甲则 2 次）。全部次数在本回合所有玩家行动结束后统一结算，期间入水可取消。'"
if old_desc in s:
    s = s.replace(old_desc, new_desc, 1)
    IDX.write_text(s, encoding='utf-8')
    print('  ok ITEMS 打火石描述已更新')
else:
    print('  ! ITEMS 打火石描述未找到')
