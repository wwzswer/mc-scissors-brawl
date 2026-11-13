# -*- coding: utf-8 -*-
"""补丁 16：修正进程相关文案与测试断言（4 级进程树）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label, path=IDX):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# 1) 开局日志（动态生成进程串，避免下标越界）
sub("""  log(`进程（进度点制）：空手 → 木(${UPGRADE[1].cost}点) → 石(${UPGRADE[2].cost}点) → 铁(<b>${UPGRADE[3].cost}点</b>) → 钻石(${UPGRADE[4].cost}点)；每投入 1 步点亮 1 个小点，进度会保存。`,'l-sys');""",
"""  {
    let chain = PROG_NAME[0];
    for(let i=1;i<PROG_NAME.length;i++) chain += ` → ${PROG_NAME[i]}(${UPGRADE[i].cost}点)`;
    log(`进程（进度点制）：${chain}；每投入 1 步点亮 1 个小点，进度会保存。`,'l-sys');
  }""", '开局进程日志')

# 2) 规则页基础玩法里的进程串
sub("""      进程树：空手 → 木(${UPGRADE[1].cost}点) → 石(${UPGRADE[2].cost}点) → 铁(${UPGRADE[3].cost}点) → 钻石(${UPGRADE[4].cost}点)。<br>""",
"""      进程树：空手 → 石进程(${UPGRADE[1].cost}点) → 铁进程(${UPGRADE[2].cost}点) → 钻石进程(${UPGRADE[3].cost}点)。<br>""",
'规则页进程串')

# 3) 规则页里“空手到木”的例子
sub("""      例：空手 → 木需要 2 点，投入 1 次只点亮 1 个点，再投入 1 次才会升级。多余的点会结转到下一级。""",
"""      例：空手 → 石进程只需要 <b>1 点</b>（投 1 次即可升级）；石 → 铁需要 3 点。多余的点会结转到下一级。""",
'规则页例子')

# 4) 猜拳说明（每回合一次、平手重出）
sub("""      ① <b>猜拳阶段</b>：你与每个对手各猜一次拳，胜者 <b>+${apPerWin} AP</b>（可在设置里改成 1 AP），平局双方无收益。<br>""",
"""      ① <b>猜拳阶段</b>：每回合所有存活玩家<b>同时出一次拳</b>，招式克制其余所有人者胜出并 <b>+${apPerWin} AP</b>（可设 1 AP）。<b>平手就全部重出，直到有人胜出为止</b>（多人也一样）。<br>""",
'规则页猜拳说明')

# 5) 判定说明
sub("""      攻击时双方再猜一次拳，<b>攻方胜出才造成伤害</b>，失败则攻击失效。判定不产生 AP。<br>
      多人对战中若判定双方同时胜出，被攻击方可以 <b>消耗 1 AP 直接闪避</b>（没有 AP 就只能挨打）。""",
"""      攻击时双方再猜一次拳：<b>平手就一直重猜，直到分出胜负</b>。攻方胜出则命中，攻方失败则攻击失效。判定不产生 AP。<br>
      平手时被攻击方可以选择 <b>消耗 1 AP 直接闪避</b>（结束这次判定，攻击失效）；不闪避就继续重猜。""",
'规则页判定说明')

# 6) 顶部/开始页文案里的进程提示
sub("""        <div><b>生命</b>：每人 4 点（判定不获得 AP）</div>""",
"""        <div><b>生命</b>：每人 4 点（判定不获得 AP）</div>
        <div><b>进程</b>：空手 → 石(1点) → 铁(3点) → 钻石(3点)</div>""",
'开始页进程提示')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')

# ---- 更新 rules-test 断言 ----
F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
r = F.read_text(encoding='utf-8')
r = r.replace("""console.log('\\n【3】玻璃进程已删除；进程树共 5 级');""",
              """console.log('\\n【3】玻璃进程已删除；木进程已并入石进程');""")
r = r.replace("""  ok(MC.PROG_NAME.join('|')==='空手|木进程|石进程|铁进程|钻石进程', '顺序：空手到钻石', MC.PROG_NAME);""",
              """  ok(MC.PROG_NAME.join('|')==='空手|石进程|铁进程|钻石进程', '顺序：空手 → 石 → 铁 → 钻石（木已并入石）', MC.PROG_NAME);
  ok(MC.UPGRADE[1].cost===1, '空手升到石进程只需 1 步', MC.UPGRADE[1].cost);
  ok(MC.UPGRADE[2].cost===3 && MC.UPGRADE[3].cost===3, '石→铁 3 步、铁→钻石 3 步', [MC.UPGRADE[2].cost, MC.UPGRADE[3].cost]);""")
r = r.replace("""  const reqs = [0,1,2,3].map(i=>{ me.prog=i; return API.progNeed(me); });   /* 升到下一级所需点数 */
  ok(reqs[0]===2 && reqs[1]===2 && reqs[2]===3 && reqs[3]===3,
     '所需点数：升木 2 / 升石 2 / 升铁 3 / 升钻石 3', reqs);""",
"""  const reqs = [0,1,2].map(i=>{ me.prog=i; return API.progNeed(me); });   /* 升到下一级所需点数 */
  ok(reqs[0]===1 && reqs[1]===3 && reqs[2]===3,
     '所需点数：升石 1 / 升铁 3 / 升钻石 3', reqs);""")
r = r.replace("""console.log('\\n【2】各级进程所需进度点：木 2 / 石 2 / 铁 3 / 钻石 3');""",
              """console.log('\\n【2】各级进程所需进度点：升石 1 / 升铁 3 / 升钻石 3');""")
r = r.replace("""  me.prog = 0; me.progPts = 0; me.ap = 2;
  const up = API.buildHumanOptions(me).find(o=>o.type==='shop_progress');
  ok(!!up && up.cost===1, '空手能看到「投入 1 步进度」入口（1 AP）', up && up.label);
  await doOpt(API, me, up);
  ok(me.prog===0 && API.progProgress(me)===1, '投入 1 步只点亮 1 个点，进程不变', [me.prog, API.progProgress(me)]);
  ok(me.ap===1, '投入 1 步只扣 1 AP', me.ap);
  await doOpt(API, me, API.buildHumanOptions(me).find(o=>o.type==='shop_progress'));
  ok(me.prog===1, '集满 2 点后升级到木进程', MC.PROG_NAME[me.prog]);
  ok(me.ap===0, '两次投入共扣 2 AP', me.ap);""",
"""  me.prog = 0; me.progPts = 0; me.ap = 2;
  const up = API.buildHumanOptions(me).find(o=>o.type==='shop_progress');
  ok(!!up && up.cost===1, '空手能看到「投入 1 步进度」入口（1 AP）', up && up.label);
  await doOpt(API, me, up);
  ok(me.prog===1, '空手只需投入 1 步就升级到石进程', MC.PROG_NAME[me.prog]);
  ok(me.ap===1, '投入 1 步扣 1 AP', me.ap);""")
r = r.replace("""  me.prog = 1; me.progPts = 0; me.ap = 5;
  const sword = API.buildHumanOptions(me).find(o=>o.type==='craftShopItem'&&o.key==='wood_sword');
  ok(!!sword && sword.cost===2, '木进程能看到木剑（2 步一次性制作）', sword && sword.label);""",
"""  me.prog = 1; me.progPts = 0; me.ap = 5;
  const sword = API.buildHumanOptions(me).find(o=>o.type==='craftShopItem'&&o.key==='wood_sword');
  ok(!!sword && sword.cost===2, '石进程能看到木剑（2 步一次性制作）', sword && sword.label);""")
# 石→铁 用例
r = r.replace("""  me.prog = 2; me.progPts = 0; me.ap = 10;
  await doOpt(API, me, {type:'shop_progress'});
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===2 && API.progProgress(me)===2, '石→铁：投 2 次还不升级', [me.prog, API.progProgress(me)]);
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===3, '投第 3 次升级到铁进程', MC.PROG_NAME[me.prog]);""",
"""  me.prog = 1; me.progPts = 0; me.ap = 10;
  await doOpt(API, me, {type:'shop_progress'});
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===1 && API.progProgress(me)===2, '石→铁：投 2 次还不升级', [me.prog, API.progProgress(me)]);
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===2, '投第 3 次升级到铁进程', MC.PROG_NAME[me.prog]);""")
r = r.replace("""  me.prog = 3; me.progPts = 0; me.ap = 10;
  for(let i=0;i<3;i++) await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===4, '铁→钻石需要 3 点', MC.PROG_NAME[me.prog]);""",
"""  me.prog = 2; me.progPts = 0; me.ap = 10;
  for(let i=0;i<3;i++) await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===3, '铁→钻石需要 3 点', MC.PROG_NAME[me.prog]);""")
r = r.replace("""  me.prog = 4; me.ap = 5;
  ok(API.progMaxed(me), '钻石进程后不可再升级', MC.PROG_NAME[me.prog]);""",
"""  me.prog = 3; me.ap = 5;
  ok(API.progMaxed(me), '钻石进程后不可再升级', MC.PROG_NAME[me.prog]);""")
r = r.replace("""  me.prog = 1; me.progPts = 2; me.ap = 10;      /* 进度点结转到下一级 */
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===1 && API.progProgress(me)===1, '多余的点结转到下一级', [me.prog, API.progProgress(me)]);""",
"""  me.prog = 1; me.progPts = 3; me.ap = 10;      /* 石→铁需要 3 点，已有 3 点：投 1 次就升级且剩 1 点 */
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===2 && API.progProgress(me)===1, '多余的点结转到下一级', [me.prog, API.progProgress(me)]);""")
r = r.replace("""  me.prog = 2; me.progPts = 0; me.ap = 10;      /* 石 → 铁需要 3 点 */""",
"""  me.prog = 1; me.progPts = 0; me.ap = 10;      /* 石 → 铁需要 3 点 */""")
r = r.replace("""  ok(me.prog===2 && API.progProgress(me)===2, '石→铁需要 3 点：投 2 次还不升级', [me.prog, API.progProgress(me)]);
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===3, '第 3 次投入后升级到铁进程', [me.prog]);""",
"""  ok(me.prog===1 && API.progProgress(me)===2, '石→铁需要 3 点：投 2 次还不升级', [me.prog, API.progProgress(me)]);
  await API.applyAction(me, {type:'shop_progress'});
  ok(me.prog===2, '第 3 次投入后升级到铁进程', [me.prog]);""")
F.write_text(r, encoding='utf-8')
print('rules-test.js 断言已更新')
