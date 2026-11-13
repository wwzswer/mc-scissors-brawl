# -*- coding: utf-8 -*-
"""补丁 48：修正【26】测试（铁傀儡是 4 点进度式，需投满）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
t = F.read_text(encoding='utf-8')

old = """  me.prog = 3; me.itemPts = {}; me.ap = 20;
  await API.applyAction(me, {type:'craftShopItem', key:'golem'});
  ok(API.armorActive(me) && me.armor==='golem', '先装备铁傀儡', me.armor);"""
new = """  me.prog = 3; me.itemPts = {}; me.ap = 20;
  await invest(API, me, 'golem');                    /* 铁傀儡 4 点进度式，需投满 */
  ok(API.armorActive(me) && me.armor==='golem', '先装备铁傀儡（4 点进度式投满）', me.armor);"""
if old in t:
    t = t.replace(old, new, 1)
    F.write_text(t, encoding='utf-8')
    print('已修正【26】')
else:
    print('! 锚点未匹配')
