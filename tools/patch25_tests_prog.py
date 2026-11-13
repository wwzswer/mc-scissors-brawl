# -*- coding: utf-8 -*-
"""补丁 25：rules-test 里所有"一次性制作"的调用改为进度式（多次投入）"""
import pathlib, re

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
r = F.read_text(encoding='utf-8')

# 通用的多步物品投入助手：在文件开头的 fresh() 之后插入
if 'async function invest(' not in r:
    anchor = "let pass=0, fail=0; const fails=[];"
    helper = """/* 进度式制作：反复投入直到拿到成品（或到达上限） */
async function invest(API, p, key, times){
  for(let i=0;i<(times||6);i++){
    if(API.hasItem(p,key)) return true;
    await API.applyAction(p, {type:'craftShopItem', key});
  }
  return API.hasItem(p, key);
}

"""
    r = r.replace(anchor, helper + anchor, 1)

# 【4】钓鱼竿（2 步）与三叉戟（3 步）
r = r.replace("""  await doOpt(API, me, API.buildHumanOptions(me).find(o=>o.type==='craftShopItem'&&o.key==='fishing_rod'));
  ok(me.items.fishing_rod===1, '做出钓鱼竿', me.items);
  ok(API.buildHumanOptions(me).some(o=>o.type==='craftShopItem'&&o.key==='trident'), '有钓鱼竿后出现三叉戟');
  const tri = API.buildHumanOptions(me).find(o=>o.type==='craftShopItem'&&o.key==='trident');
  ok(tri.cost===3, '三叉戟 3 步', tri.cost);""",
"""  await invest(API, me, 'fishing_rod');
  ok(me.items.fishing_rod===1, '做出钓鱼竿（2 步进度式）', me.items);
  ok(API.buildHumanOptions(me).some(o=>o.type==='craftShopItem'&&o.key==='trident'), '有钓鱼竿后出现三叉戟');
  const tri = API.buildHumanOptions(me).find(o=>o.type==='craftShopItem'&&o.key==='trident');
  ok(tri && tri.cost===1, '三叉戟入口每次投入 1 AP（共需 3 点）', tri && tri.cost);""")

# 【5】末影珍珠
r = r.replace("""  await doOpt(API, me, {type:'craftShopItem', key:'ender_pearl'});
  ok(me.items.ender_pearl===1, '获得末影珍珠');""",
"""  await invest(API, me, 'ender_pearl');
  ok(me.items.ender_pearl===1, '获得末影珍珠（2 步进度式）');""")

# 【6】护甲：皮革甲(2)/铁甲(3)/铁傀儡(4)/钻石甲(3)/铁砧(2)
r = r.replace("""  await doOpt(API, me, {type:'craftShopItem', key:'leather'});
  ok(me.armor==='leather'&&me.armorCharges===1, '皮革甲 = 1 次物理免疫', [me.armor,me.armorCharges]);""",
"""  await invest(API, me, 'leather');
  ok(me.armor==='leather'&&me.armorCharges===1, '皮革甲 = 1 次物理免疫', [me.armor,me.armorCharges]);""")
r = r.replace("""  await doOpt(API, me, {type:'craftShopItem', key:'iron_armor'});
  ok(me.armor==='iron_armor'&&me.armorCharges===2, '铁甲 = 2 次物理免疫', [me.armor,me.armorCharges]);""",
"""  await invest(API, me, 'iron_armor');
  ok(me.armor==='iron_armor'&&me.armorCharges===2, '铁甲 = 2 次物理免疫', [me.armor,me.armorCharges]);""")
r = r.replace("""  await doOpt(API, me, {type:'craftShopItem', key:'anvil'});""",
"""  await invest(API, me, 'anvil');""")
r = r.replace("""  await doOpt(API, me, {type:'craftShopItem', key:'golem'});
  ok(me.armor==='golem'&&me.armorCharges===2, '铁傀儡 = 2 次物理免疫', [me.armor,me.armorCharges]);""",
"""  await invest(API, me, 'golem');
  ok(me.armor==='golem'&&me.armorCharges===2, '铁傀儡 = 2 次物理免疫（4 步进度式）', [me.armor,me.armorCharges]);""")
r = r.replace("""  await doOpt(API, me, {type:'craftShopItem', key:'diamond_armor'});
  ok(me.armor==='diamond_armor'&&me.armorCharges===3, '钻石甲 = 3 次物理免疫', [me.armor,me.armorCharges]);""",
"""  await invest(API, me, 'diamond_armor');
  ok(me.armor==='diamond_armor'&&me.armorCharges===3, '钻石甲 = 3 次物理免疫', [me.armor,me.armorCharges]);""")

# 【7】铁甲
r = r.replace("""  await doOpt(API, me, {type:'craftShopItem', key:'iron_armor'});
  API.tryDamage(me,[0,0,1.5,0],{});""",
"""  await invest(API, me, 'iron_armor');
  API.tryDamage(me,[0,0,1.5,0],{});""")

# 【9】打火石（1 步，无需改）与【22】腐肉(2 步)/面包(1 步)
r = r.replace("""  await doOpt(API, me, {type:'craftShopItem', key:'flesh'});
  await doOpt(API, me, {type:'craftShopItem', key:'flesh'});
  ok(API.hasItem(me,'flesh'), '铁进程下成功获取腐肉', me.items);
  await doOpt(API, me, {type:'craftShopItem', key:'bread'});
  ok(API.hasItem(me,'bread'), '铁进程下成功获取面包', me.items);""",
"""  await invest(API, me, 'flesh');
  ok(API.hasItem(me,'flesh'), '铁进程下成功获取腐肉（2 步进度式）', me.items);
  await invest(API, me, 'bread');
  ok(API.hasItem(me,'bread'), '铁进程下成功获取面包', me.items);""")

F.write_text(r, encoding='utf-8')
print('已改为进度式投入，长度', len(r))
