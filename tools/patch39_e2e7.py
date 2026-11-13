# -*- coding: utf-8 -*-
"""补丁 39：E2E 第 7 步改为在 iframe 自身 realm 内验证（排除父页面变量遮蔽）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\e2e.html')
t = F.read_text(encoding='utf-8')

# 找到第 7 步整段，替换为 iframe 内验证版本
start = t.index("    say('【7】切换手上工具');")
end = t.index("    say('');\n    say('【8】", start)

new7 = r"""    say('【7】切换手上工具');
    /* 重开一局干净局面，并在 iframe 自己的 realm 内验证（避免父页面变量/异步等待干扰） */
    MC.__api.setAutoPlayer(null);
    MC.start({enemyCount:1, diff:'normal', auto:false, mode:'1v1', silent:true, name:'工具测试'});
    await wait(150);
    const tool = W.eval(`(function(){
      const A = MCGame.__api, G = MCGame.state(), p = G.players[0], foe = G.players[1];
      p.prog = 3; p.itemPts = {}; p.ap = 20; p.weapon = 'fist';
      A.addItem(p,'wood_sword',1); A.addItem(p,'stone_sword',1);
      const sw = A.buildHumanOptions(p).filter(o=>o.type==='switch_weapon').map(o=>o.key);
      A.switchWeapon(p,'stone_sword');
      const w1 = p.weapon;
      A.setDistance(p, foe, 0);
      const atk = A.buildHumanOptions(p).filter(o=>o.type==='attack').map(o=>o.key);
      A.switchWeapon(p,'wood_sword');
      const atk2 = A.buildHumanOptions(p).filter(o=>o.type==='attack').map(o=>o.key);
      A.switchWeapon(p,'fist');
      const atk3 = A.buildHumanOptions(p).filter(o=>o.type==='attack').map(o=>o.key);
      A.setDistance(p, foe, 4);
      const atk4 = A.buildHumanOptions(p).filter(o=>o.type==='attack').length;
      const mv = A.buildHumanOptions(p).filter(o=>o.type==='move'&&o.dir===-1).length;
      return { sw: sw.join(','), w1, atk: atk.join(','), atk2: atk2.join(','), atk3: atk3.join(','), far: atk4, mv, dist: A.distanceBetween(p,foe) };
    })()`);
    say(`  可换上：${tool.sw}`, tool.sw.includes('stone_sword')&&tool.sw.includes('wood_sword')?'ok':'bad');
    say(`  切换到石剑：${tool.w1}`, tool.w1==='stone_sword'?'ok':'bad');
    say(`  距离 0 攻击选项：石剑=${tool.atk} 木剑=${tool.atk2} 空手=${tool.atk3}`,
        tool.atk==='stone_sword'&&tool.atk2==='wood_sword'&&tool.atk3==='fist'?'ok':'bad');
    say(`  距离 4 格：攻击 ${tool.far} 个、靠近 ${tool.mv} 个`, tool.far===0&&tool.mv===1?'ok':'bad');
    say('  （切换工具不花 AP、不占行动次数：由 rules-test.js 断言）');

"""
t = t[:start] + new7 + t[end:]
F.write_text(t, encoding='utf-8')
print('E2E 第 7 步已改为 iframe 内验证')
