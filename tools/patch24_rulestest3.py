# -*- coding: utf-8 -*-
"""补丁 24：rules-test 适配（5 级进程 + 物品进度式 + 切换工具 + 低级物品可达性）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
r = F.read_text(encoding='utf-8')

# ---------- 【1】物品制作改为进度式 ----------
i = r.index("console.log('\\n【1】")
j = r.index("console.log('\\n【3】")
new12 = r"""console.log('\n【1】进程进度（空手→木只要 1 点）与物品进度式制作');
{
  const { MC, API, me } = fresh();
  me.prog = 0; me.progPts = 0; me.ap = 2;
  const up = API.buildHumanOptions(me).find(o=>o.type==='shop_progress');
  ok(!!up && up.cost===1, '空手能看到「投入 1 步进度」入口（1 AP）', up && up.label);
  await doOpt(API, me, up);
  ok(me.prog===1, '空手只需投入 1 步就升级到木进程', MC.PROG_NAME[me.prog]);
  ok(me.ap===1, '投入 1 步扣 1 AP', me.ap);
}
{
  /* 多步物品：每投入 1 步点亮 1 个点，集满才拿到 */
  const { MC, API, me } = fresh();
  me.prog = 1; me.itemPts = {}; me.ap = 5;
  const lab = () => {
    const o = API.buildHumanOptions(me).find(x=>x.type==='craftShopItem' && x.key==='wood_sword');
    return o ? o.label : '(无入口)';
  };
  ok(lab().includes('1/2'), '木剑入口显示进度 1/2', lab());
  await doOpt(API, me, {type:'craftShopItem', key:'wood_sword'});
  ok(!API.hasItem(me,'wood_sword') && API.itemProgress(me,'wood_sword')===1, '投入 1 步还没拿到木剑', [me.items, me.itemPts]);
  ok(me.ap===4, '投入 1 步只扣 1 AP', me.ap);
  await doOpt(API, me, {type:'craftShopItem', key:'wood_sword'});
  ok(API.hasItem(me,'wood_sword'), '第 2 步后木剑制作完成', me.items);
  ok(me.weapon==='wood_sword', '制作完成后自动装备', me.weapon);
  ok(API.itemProgress(me,'wood_sword')===0, '完成后该物品进度清零', me.itemPts);
}
{
  /* 3 步物品（三叉戟）也是进度式 */
  const { API, me } = fresh();
  me.prog = 2; me.itemPts = {}; me.ap = 10;
  API.addItem(me, 'fishing_rod', 1);           /* 前置 */
  await doOpt(API, me, {type:'craftShopItem', key:'trident'});
  await doOpt(API, me, {type:'craftShopItem', key:'trident'});
  ok(!API.hasItem(me,'trident') && API.itemProgress(me,'trident')===2, '三叉戟 3 步：投 2 次还没完成', API.itemProgress(me,'trident'));
  await doOpt(API, me, {type:'craftShopItem', key:'trident'});
  ok(API.hasItem(me,'trident'), '第 3 步后三叉戟完成', me.items);
}
{
  /* 1 步物品一次到位 */
  const { API, me } = fresh();
  me.ap = 3; me.itemPts = {};
  await doOpt(API, me, {type:'craftShopItem', key:'bread'});
  ok(API.hasItem(me,'bread'), '面包（1 步）投入 1 次即到手', me.items);
}

console.log('\n【2】各级进程所需进度点：升木 1 / 升石 2 / 升铁 3 / 升钻石 3');
{
  const { MC, API, me } = fresh();
  const reqs = [0,1,2,3].map(i=>{ me.prog=i; return API.progNeed(me); });
  ok(reqs[0]===1 && reqs[1]===2 && reqs[2]===3 && reqs[3]===3,
     '所需点数：升木 1 / 升石 2 / 升铁 3 / 升钻石 3', reqs);
  ok(MC.PROG_NAME.join('|')==='空手|木进程|石进程|铁进程|钻石进程', '进程名恢复为 5 级', MC.PROG_NAME);
}
{
  const { MC, API, me } = fresh();
  me.prog = 1; me.progPts = 0; me.ap = 10;
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===1 && API.progProgress(me)===1, '木→石：投 1 次还不升级', [me.prog, API.progProgress(me)]);
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===2, '投第 2 次升级到石进程', MC.PROG_NAME[me.prog]);
}
{
  const { MC, API, me } = fresh();
  me.prog = 2; me.progPts = 0; me.ap = 10;
  for(let i=0;i<3;i++) await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===3, '石→铁需要 3 点', MC.PROG_NAME[me.prog]);
  for(let i=0;i<3;i++) await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===4, '铁→钻石需要 3 点', MC.PROG_NAME[me.prog]);
  ok(API.progMaxed(me), '钻石进程后不可再升级');
  const ups = API.buildHumanOptions(me).filter(o=>o.type==='shop_progress');
  ok(ups.length===1 && ups[0].label.includes('已满级'), '满级后显示「已满级」', ups[0] && ups[0].label);
}

"""
r = r[:i] + new12 + r[j:]

# ---------- 【3】进程树断言（现在已包含在【2】里） ----------
k = r.index("console.log('\\n【3】")
m = r.index("console.log('\\n【4】")
r = r[:k] + """console.log('\\n【3】玻璃进程已删除；木进程保留');
{
  const { MC } = fresh();
  ok(!MC.PROG_NAME.some(n=>String(n).includes('玻璃')), '没有玻璃进程', MC.PROG_NAME);
  ok(MC.PROG_NAME.includes('木进程'), '木进程仍在（空手→木 1 点）', MC.PROG_NAME);
}

""" + r[m:]

# ---------- 【4】钓鱼竿在石进程（prog=2） ----------
r = r.replace("""  const { API, me } = fresh();
  me.prog = 1; me.ap = 10;
  ok(!API.buildHumanOptions(me).some(o=>o.type==='craftShopItem'&&o.key==='trident'), '没有钓鱼竿时看不到三叉戟');""",
"""  const { API, me } = fresh();
  me.prog = 2; me.ap = 10;
  ok(!API.buildHumanOptions(me).some(o=>o.type==='craftShopItem'&&o.key==='trident'), '没有钓鱼竿时看不到三叉戟');""")

# ---------- 【5】末影珍珠 prog=2 ----------
r = r.replace("""  const { API, G, me, ai } = fresh();
  me.prog = 1; me.ap = 2;
  await doOpt(API, me, {type:'craftShopItem', key:'ender_pearl'});""",
"""  const { API, G, me, ai } = fresh();
  me.prog = 2; me.ap = 2;
  await doOpt(API, me, {type:'craftShopItem', key:'ender_pearl'});""")

# ---------- 【6】护甲测试：铁甲在铁进程(3)，钻石甲在钻石(4)，皮革在木(1) ----------
r = r.replace("""  const { API, me } = fresh();
  me.prog=1; me.ap=6;      /* 石进程：皮革甲 */
  await doOpt(API, me, {type:'craftShopItem', key:'leather'});""",
"""  const { API, me } = fresh();
  me.prog=1; me.ap=6;      /* 木进程：皮革甲 */
  await doOpt(API, me, {type:'craftShopItem', key:'leather'});""")
r = r.replace("""  me.prog=2; me.ap=20;     /* 铁进程 */
  await doOpt(API, me, {type:'craftShopItem', key:'iron_armor'});""",
"""  me.prog=3; me.ap=20;     /* 铁进程 */
  await doOpt(API, me, {type:'craftShopItem', key:'iron_armor'});""")
r = r.replace("""  me.prog=3; me.ap=10; API.breakArmor(me);
  await doOpt(API, me, {type:'craftShopItem', key:'diamond_armor'});""",
"""  me.prog=4; me.ap=10; API.breakArmor(me);
  await doOpt(API, me, {type:'craftShopItem', key:'diamond_armor'});""")
r = r.replace("""  const { API, me } = fresh();
  me.prog=2; me.ap=10;
  await doOpt(API, me, {type:'craftShopItem', key:'iron_armor'});
  API.tryDamage(me,[0,0,1.5,0],{});""",
"""  const { API, me } = fresh();
  me.prog=3; me.ap=10;
  await doOpt(API, me, {type:'craftShopItem', key:'iron_armor'});
  API.tryDamage(me,[0,0,1.5,0],{});""")
# 打火石在铁进程(3)
r = r.replace("""  const { API, me, ai } = fresh();
  me.prog=2; me.ap=10;
  await doOpt(API, me, {type:'craftShopItem', key:'flint'});""",
"""  const { API, me, ai } = fresh();
  me.prog=3; me.ap=10;
  await doOpt(API, me, {type:'craftShopItem', key:'flint'});""")

# ---------- 新增【22】低级物品可达性 +【23】切换工具 ----------
tail = "console.log('\\n──────────────────────────────');"
extra = r"""console.log('\n【22】低级物品在高级进程依然可以获取（回归）');
{
  const { MC, API, me } = fresh();
  me.itemPts = {}; me.ap = 30;
  const want = ['flesh','bread','fist'];
  for(const prog of [0,1,2,3,4]){
    me.prog = prog;
    const keys = API.buildHumanOptions(me).filter(o=>o.type==='craftShopItem').map(o=>o.key);
    const miss = want.filter(k=>!keys.includes(k));
    ok(miss.length===0, `${MC.PROG_NAME[prog]} 仍可制作：一拳 / 腐肉 / 面包`, miss);
  }
}
{
  /* 真的能买到：升到铁进程后买腐肉 */
  const { MC, API, me } = fresh();
  me.prog = 3; me.itemPts = {}; me.ap = 5;
  await doOpt(API, me, {type:'craftShopItem', key:'flesh'});
  await doOpt(API, me, {type:'craftShopItem', key:'flesh'});
  ok(API.hasItem(me,'flesh'), '铁进程下成功获取腐肉', me.items);
  await doOpt(API, me, {type:'craftShopItem', key:'bread'});
  ok(API.hasItem(me,'bread'), '铁进程下成功获取面包', me.items);
}
{
  /* 木剑、皮革甲等木级物品在高级进程也可做 */
  const { MC, API, me } = fresh();
  me.prog = 4; me.itemPts = {}; me.ap = 10;
  const keys = API.buildHumanOptions(me).filter(o=>o.type==='craftShopItem').map(o=>o.key);
  ok(['wood_sword','leather','stone_sword','iron_sword'].every(k=>keys.includes(k)),
     '钻石进程下仍能做木剑/皮革甲/石剑/铁剑', keys.filter(k=>['wood_sword','leather','stone_sword','iron_sword'].includes(k)));
}

console.log('\n【23】切换手上的工具');
{
  const { MC, API, me } = fresh();
  me.prog = 3; me.itemPts = {}; me.ap = 12;
  me.weapon = 'fist';
  API.addItem(me,'wood_sword',1); API.addItem(me,'stone_sword',1); API.addItem(me,'iron_sword',1);
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='switch_weapon');
  ok(opts.length===3, '持有 3 把武器 → 出现 3 个「换上」选项', opts.map(o=>o.label));
  ok(opts.every(o=>o.cost===0 && o.isAction===false), '切换武器不消耗 AP 也不占行动次数');
  await doOpt(API, me, {type:'switch_weapon', key:'stone_sword'});
  ok(me.weapon==='stone_sword', '换上了石剑', me.weapon);
  await doOpt(API, me, {type:'switch_weapon', key:'wood_sword'});
  ok(me.weapon==='wood_sword', '再换成木剑', me.weapon);
  /* 换完之后攻击选项用的是手上的武器 */
  API.setDistance(me, G_of(MC).players[1], 0);
  const atk = API.buildHumanOptions(me).find(o=>o.type==='attack');
  ok(!!atk && atk.key==='wood_sword', '攻击用的是当前手上的武器', atk && atk.key);
  ok(!API.buildHumanOptions(me).some(o=>o.type==='switch_weapon'&&o.key==='wood_sword'), '当前武器不再出现在切换列表里');
}
function G_of(MC){ return MC.state(); }

"""
r = r.replace(tail, extra + tail, 1)

F.write_text(r, encoding='utf-8')
print('rules-test 已更新，长度', len(r))
