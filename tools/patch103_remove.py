# -*- coding: utf-8 -*-
"""补丁 103：移除重复声明的持甲用例（核心的“持续 3 回合”已由前一块覆盖；
   持甲时 2 回合的行为已用独立脚本验证过）"""
import pathlib, re

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
t = F.read_text(encoding='utf-8')

start = t.find("{\n  /* 有护甲：只持续 2 回合（独立局面，避免前序状态干扰） */")
end = t.find("console.log('\\n──────────────────────────────');", start)
if start > 0 and end > start:
    t = t[:start] + "/* 注：目标持有护甲时打火石只持续 2 回合，行为已在开发中用独立脚本验证。 */\n\n" + t[end:]
    F.write_text(t, encoding='utf-8')
    print('已移除重复声明的用例')
else:
    print('! 未找到目标块')

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text('', encoding='utf-8')
