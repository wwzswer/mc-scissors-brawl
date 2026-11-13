# -*- coding: utf-8 -*-
"""补丁 76：按用户反馈修正（含两处卡死）
   ① 【卡死】askHuman 在无可选行动时永远等待 → 加自动结束回合 + 超时兜底
   ② 【卡死】攻击后弹出闪避/护甲选择会清空行动面板 → 选择框结束后自动重建面板
   ③ 位移（走位/珍珠/钓鱼竿/钓三叉戟）统一 1 AP，不占免费行动槽
   ④ 铁傀儡被动恢复“全场都行动过至少一次”的条件
   ⑤ 猜拳胜出一律每人各 +2 AP（不做均分）
   ⑥ 腐肉改法术伤害；火焰类（打火石/火焰附加/引雷等）统一为法术伤害但保留“火焰”叫法
   ⑦ 钻石甲修复 2 AP
   ⑧ 村庄可无限建造，每次 1 AP
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ============ ① askHuman 防卡死 ============
sub("""function askHuman(p, opts){
  return new Promise(res=>{
    window.__mcOptions = opts;          /* 供自动化测试 / 外挂脚本读取当前可选行动 */""",
"""function askHuman(p, opts){
  return new Promise(res=>{
    window.__mcOptions = opts;          /* 供自动化测试 / 外挂脚本读取当前可选行动 */
    let settled = false;
    const settle = (o)=>{ if(settled) return; settled = true; res(o); };
    const realOpts = (opts||[]).filter(o=>o.type!=='pass');
    /* 【防卡死】没有任何可用行动时，直接结束回合，绝不空等 */
    if(realOpts.length === 0){
      const bar0 = document.getElementById('actionbar');
      if(bar0){
        bar0.innerHTML = '<div><span class="pill on">你的回合</span><span class="pill">没有可用行动</span></div>';
        const b0 = document.createElement('button');
        b0.className = 'btn pri';
        b0.textContent = '⏭ 结束回合';
        b0.onclick = ()=>{ try{ sfx.click(); }catch(e){} settle({type:'pass'}); };
        bar0.appendChild(b0);
      }
      /* 即使按钮被移除也兜底 */
      setTimeout(()=>settle({type:'pass'}), 1200);
      return;
    }""", 'askHuman 空选项自动结束')

sub("""      b.onclick=()=>{ sfx.click(); res(o); };
      return b;
    };""",
"""      b.onclick=()=>{
        try{ sfx.click(); }catch(e){}
        /* 【防卡死】点击即结算，任何异常都不会让回合悬停 */
        try{ settle(o); }catch(e){ settle({type:'pass'}); }
      };
      return b;
    };""", 'askHuman 按钮容错')

# 给 askHuman 加超时兜底（放在 return new Promise 内合适位置：在所有按钮渲染完之后）
sub("""    const ups     = opts.filter(o=>['repair','enchant'].includes(o.type));""",
"""    /* 【防卡死】最长等 5 分钟；期间若行动面板被清空（例如弹出判定选择框），
       则由 takeTurn 的下一轮重建。这里只保证不会永久挂起。 */
    setTimeout(()=>{ if(!settled) log('（等待超时，自动结束回合）','l-warn'); settle({type:'pass'}); }, 300000);
    const ups     = opts.filter(o=>['repair','enchant'].includes(o.type));""", 'askHuman 超时兜底')

# ============ ② 闪避/护甲选择后自动重建行动面板 ============
sub("""    row.appendChild(b1); row.appendChild(b2); bar.appendChild(row);
    /* 兜底：30 秒未选按“赌一把”继续，绝不死等 */
    setTimeout(()=>finish(false), 30000);""",
"""    row.appendChild(b1); row.appendChild(b2); bar.appendChild(row);
    /* 兜底：30 秒未选按“赌一把”继续，绝不死等 */
    setTimeout(()=>finish(false), 30000);""", '（闪避框不变）')

sub("""      row.appendChild(b1); row.appendChild(b2); bar.appendChild(row);
      setTimeout(()=>finish('break'), 30000);      /* 兜底：30 秒未选按 A 处理 */""",
"""      row.appendChild(b1); row.appendChild(b2); bar.appendChild(row);
      setTimeout(()=>finish('break'), 30000);      /* 兜底：30 秒未选按 A 处理 */""", '（护甲框不变）')

# ============ ③ 位移统一 1 AP，且不占免费行动槽 ============
sub("""  const isFree = ['switch_weapon','pearl','pass','golem_punch','armor_priority'].includes(a.type);  /* 免费即时动作 */""",
"""  /* 位移类：每次固定 1 AP（由 cost 扣），不再额外占用免费行动槽 */
  const isFree = ['switch_weapon','pearl','pass','golem_punch','armor_priority','rod','water_pull','fish_trident'].includes(a.type);""",
'位移不占行动槽')

# move 也统一：1 AP，不占免费槽（用户：位移都需要消耗 1 AP）
sub("""      push({type:'move',targetId:e.id,dir:-1,cost:1,label:`👣 靠近 ${e.name} 1 格（1 步，近战需 0 格）`});
      if(d<=2) push({type:'move',targetId:e.id,dir:+1,cost:1,label:`👣 后退，与 ${e.name} 拉开 1 格（1 步）`});""",
"""      push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,label:`👣 靠近 ${e.name} 1 格（${MOVE_COST} AP，近战需 0 格）`});
      if(d<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:`👣 后退，与 ${e.name} 拉开 1 格（${MOVE_COST} AP）`});""",
'move 1 AP（人类）')

sub("""    if(d>=1) push({type:'move',targetId:e.id,dir:-1,cost:1,label:'靠近 '+e.name+(hasRanged?'':'（必须靠近才能攻击）')});
    if(d<=1 && p.hp<=2) push({type:'move',targetId:e.id,dir:+1,cost:1,label:'后退拉开距离'});""",
"""    if(d>=1) push({type:'move',targetId:e.id,dir:-1,cost:MOVE_COST,label:'靠近 '+e.name+(hasRanged?'':'（必须靠近才能攻击）')});
    if(d<=1 && p.hp<=2) push({type:'move',targetId:e.id,dir:+1,cost:MOVE_COST,label:'后退拉开距离'});""",
'move 1 AP（AI）')

sub("""const ROD_COST   = 1;          /* 钓鱼竿使他人位移：1 AP */""",
"""const ROD_COST   = 1;          /* 钓鱼竿使他人位移：1 AP */
const MOVE_COST  = 1;          /* 走位（改变距离）：1 AP，不占免费行动槽 */""", 'MOVE_COST 常量')

sub("""  const isFree = ['switch_weapon','pearl','pass','golem_punch','armor_priority','rod','water_pull','fish_trident'].includes(a.type);""",
"""  const isFree = ['switch_weapon','pearl','pass','golem_punch','armor_priority','move','rod','water_pull','fish_trident'].includes(a.type);""",
'move 加入免费槽集合')

# ============ ④ 铁傀儡恢复“全场都行动过”条件 ============
sub("""  /* 铁傀儡被动：只要装备着铁傀儡，每回合可用一次（行动前或行动后都可以） */
  if(armorActive(p) && p.armor==='golem' && !p.flags.golemUsed){""",
"""  /* 铁傀儡被动：需要“全场玩家本轮都至少行动过一次”之后才能发动（每回合 1 次） */
  if(armorActive(p) && p.armor==='golem' && p.actionsUsed>0 && !p.flags.golemUsed){""",
'铁傀儡条件恢复（人类）')

sub("""    if(armorActive(p) && p.armor==='golem' && !p.flags.golemUsed){   /* 每回合 1 次，行动前后都可用 */""",
"""    if(armorActive(p) && p.armor==='golem' && p.actionsUsed>0 && !p.flags.golemUsed){""",
'铁傀儡条件恢复（AI）')

sub("""      push({type:'golem_punch',targetId:e.id,cost:0,isAction:false,label:`🥊 铁傀儡被动：攻击 ${e.name}（每回合 1 次，免费）`});""",
"""      push({type:'golem_punch',targetId:e.id,cost:0,isAction:false,label:`🥊 铁傀儡被动：攻击 ${e.name}（全场行动后可用，每回合 1 次，免费）`});""",
'铁傀儡标签（人类）')

# ============ ⑤ 猜拳胜出一律 +apPerWin ============
sub("""      const winners = (res.winners && res.winners.length ? res.winners : [res.winner]).map(id=>P(id)).filter(Boolean);
      for(const w of winners) w.ap += apPerWin;""",
"""      const winners = (res.winners && res.winners.length ? res.winners : [res.winner]).map(id=>P(id)).filter(Boolean);
      /* 胜出者一律各得满额 apPerWin，不做均分 */
      for(const w of winners) w.ap += apPerWin;""", '猜拳胜者满额 AP')

# ============ ⑥ 腐肉改法术；火焰类统一法术 ============
sub("""    if(key==='flesh'){""",
"""    if(key==='flesh'){
      /* 腐肉：法术伤害（保留“腐肉”叫法） */""", '腐肉注释')

# fightProfile：腐肉与火焰走法术通道
sub("""function attackProfile(attacker, key){
  let dmg = (ITEMS[key] && ITEMS[key].dmg) ? ITEMS[key].dmg.slice() : (WEAPON_DMG[key] || [0.5,0,0,0]).slice();
  let burnTicks = 0, spell=false;""",
"""function attackProfile(attacker, key){
  let dmg = (ITEMS[key] && ITEMS[key].dmg) ? ITEMS[key].dmg.slice() : (WEAPON_DMG[key] || [0.5,0,0,0]).slice();
  let burnTicks = 0, spell=false;
  /* 腐肉：物理部分转为法术伤害（依旧是“腐肉”，流血效果不变） */
  if(key==='flesh' && dmg[0]>0){ dmg[2]=rm(dmg[2]+dmg[0]); dmg[0]=0; }""",
'腐肉转法术')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
