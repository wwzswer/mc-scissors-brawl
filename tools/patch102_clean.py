# -*- coding: utf-8 -*-
"""补丁 102：清理调试输出；持甲用例改为在独立局面中验证（避免前序状态干扰）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
t = F.read_text(encoding='utf-8')

start = t.find("{\n  /* 有护甲：只持续 2 回合 */")
end = t.find("console.log('\\n──────────────────────────────');", start)
if start > 0 and end > start:
    new_block = """{
  /* 有护甲：只持续 2 回合（独立局面，避免前序状态干扰） */
  const { MC, API, G, me, ai } = fresh();
  me.prog = 3; me.ap = 20; me.itemPts = {}; me.weapon = 'fist';
  API.addItem(me, 'flint', 1);
  ai.armor = 'iron_armor'; ai.armorCharges = 2;
  API.setDistance(me, ai, 0);
  const _f = API.buildHumanOptions(me).filter(o=>o.type==='attack').find(o=>o.key==='flint');
  if(_f){
    await API.applyAction(me, _f);
    const b = ai.effects.find(e=>e.type==='burn');
    ok(b && (b.rounds||0)===2, '目标持有护甲时只持续 2 回合', b ? {p:b.power, r:b.rounds} : '(未点燃)');
  } else {
    ok(false, '目标持有护甲时只持续 2 回合', '(没找到打火石选项)');
  }
}

"""
    t = t[:start] + new_block + t[end:]
    F.write_text(t, encoding='utf-8')
    print('已替换持甲用例')
else:
    print('! 未找到目标块')

# 顺带清掉可能残留的调试行
import re
t2 = re.sub(r"\n\s*console\.log\('    \[调试\][^\n]*\n", '\n', F.read_text(encoding='utf-8'))
F.write_text(t2, encoding='utf-8')
print('调试行剩余:', t2.count('[调试]'))
