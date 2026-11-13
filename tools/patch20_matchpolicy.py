# -*- coding: utf-8 -*-
"""补丁 20：match-test 的自动玩家改为贴近真实 AI 的策略
   新 AP 规则（不可存储、一次投入 1 点）下，先把武器做出来再谈进度。
"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\match-test.js')
r = F.read_text(encoding='utf-8')

i = r.index('function autoHumanPolicy(')
j = r.index('/* ---------------- 单局运行 ---------------- */')

new = r"""function autoHumanPolicy(MC, G, optsIn){
  const me = G.players[0];
  if(!me.alive || G.over) return null;
  const API = MC.__api;
  const opts = optsIn || API.buildHumanOptions(me);
  const find = pred => opts.find(pred);
  const enemies = G.players.filter(p=>p.alive && p.team!==me.team);
  if(!enemies.length) return null;
  const dmgOf = k => k==='diamond_sword'?3:k==='iron_sword'?2:(k==='stone_sword'||k==='trident'||k==='crossbow')?1.5:k==='wood_sword'?1:0.5;
  let myDmg = dmgOf(me.weapon||'fist');
  if(me.ench[me.weapon]==='sharpness') myDmg += 0.5*(me.ench[me.weapon]||1);

  /* 1. 能击杀就打 */
  const kill = find(o=>o.type==='attack' && G.players[o.targetId].hp<=myDmg);
  if(kill) return kill;
  /* 2. 血少先回血 */
  if(me.hp<=1.5){
    const heal = find(o=>o.type==='eat'||o.type==='potion');
    if(heal) return heal;
  }
  /* 3. 受伤时先补护甲（只在有对应进程时） */
  if(me.hp<=2.5 && !me.armor && me.ap>=2){
    const arm = find(o=>o.type==='craftShopItem' && ['leather','iron_armor','diamond_armor'].includes(o.key));
    if(arm) return arm;
  }
  /* 4. 没武器先做武器（这是新 AP 规则下的关键一步） */
  if(myDmg<1.5 && me.ap>=2){
    const wp = find(o=>o.type==='craftShopItem' && ['stone_sword','wood_sword'].includes(o.key));
    if(wp) return wp;
  }
  /* 5. 贴脸打人 / 远程 */
  const atk = find(o=>o.type==='attack' && (o.ranged || G.dist[me.id][o.targetId]===0));
  if(atk && me.hp>1) return atk;
  /* 6. 有铁砧就修甲 */
  const rep = find(o=>o.type==='repair');
  if(rep) return rep;
  /* 7. 投资：武器升级 > 进程进度 > 护甲 */
  if(me.ap>=2){
    const wp = find(o=>o.type==='craftShopItem' && ['iron_sword','crossbow','diamond_sword'].includes(o.key));
    if(wp) return wp;
  }
  if(!me.armor && me.ap>=2){
    const arm = find(o=>o.type==='craftShopItem' && ['leather','iron_armor','diamond_armor'].includes(o.key));
    if(arm) return arm;
  }
  const up = find(o=>o.type==='shop_progress');
  if(up && API.progMaxed(me)===false) return up;
  /* 8. 靠近 */
  const mv = find(o=>o.type==='move' && o.dir===-1);
  if(mv) return mv;
  if(atk) return atk;
  /* 9. 免费资源 */
  const free = find(o=>o.type==='pearl'||o.type==='fish_trident');
  if(free) return free;
  return {type:'pass'};
}

"""
r = r[:i] + new + r[j:]

# 自动对局也输出武器/护甲信息
r = r.replace("""    console.log(`#${i+1} ${r.G.over?(me.alive?'玩家胜':'玩家败'):'未结束'} | 回合 ${G.round} | 玩家 ${me.hp}HP ${MC.PROG_NAME[me.prog]} ${me.weapon||'空手'}/${me.armor||'无'} | 存活敌人 ${results[i].enemyAlive} | 异常 ${r.errors.length}${problems.length?' | 状态问题: '+problems.join(','):''}`);""",
"""    console.log(`#${i+1} ${r.G.over?(me.alive?'玩家胜':'玩家败'):'未结束'} | 回合 ${G.round} | 玩家 ${me.hp}HP ${MC.PROG_NAME[me.prog]} ${me.weapon||'空手'}/${me.armor||'无'} | 进度点 ${me.progPts||0} | 存活敌人 ${results[i].enemyAlive} | 异常 ${r.errors.length}${problems.length?' | 状态问题: '+problems.join(','):''}`);""")

F.write_text(r, encoding='utf-8')
print('match-test 策略已替换，长度', len(r))
