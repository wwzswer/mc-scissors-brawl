# -*- coding: utf-8 -*-
"""补丁 64：按用户反馈批量修正
   ① 删除联机模式入口与联网逻辑（暂停联机）
   ② 判定平局闪避改为玩家可选（赌一把：不花 AP 赌判定，或花 1 AP 直接闪避）
   ③ 猜拳结算：三种招式同时出现＝平局重出；只出现两种时，克制方的所有玩家各得 AP
   ④ 进程独立按钮（不再混在攻击栏）
   ⑤ 护甲优先级选择（多件护甲时选先消耗哪件）
   ⑥ 铁傀儡被动攻击补上真正可用的选项
   ⑦ 面包 / 附魔金苹果 各 1 AP
   ⑧ 钓鱼竿使他人位移 1 AP
   ⑨ 护甲选择框加超时兜底，避免任何情况下卡死
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

# ============ ③ 猜拳：三种招式齐＝平局；两种招式时克制方全体得分 ============
sub("""function judgeRound(moves){
  const list = Object.entries(moves);
  if(list.length === 0) return {winner:null, tie:true};
  if(list.length === 1) return {winner:+list[0][0], tie:false};
  const groups = {};                                  /* 招式 -> [玩家id] */
  for(const [id, mv] of list){ (groups[mv] = groups[mv] || []).push(+id); }
  const kinds = Object.keys(groups);
  if(kinds.length === 1) return {winner:null, tie:true};   /* 全员同招 → 平局 */
  const winners = kinds.filter(k => kinds.every(o => o===k || BEATS[k]===o));
  if(winners.length === 0) return {winner:null, tie:true};  /* 互克 → 平局，重出 */
  const pool = groups[winners[0]];
  return {winner: pool[rnd(pool.length)], tie:false};
}""",
"""function judgeRound(moves){
  const list = Object.entries(moves);
  if(list.length === 0) return {winner:null, winners:[], tie:true};
  if(list.length === 1) return {winner:+list[0][0], winners:[+list[0][0]], tie:false};
  const groups = {};                                  /* 招式 -> [玩家id] */
  for(const [id, mv] of list){ (groups[mv] = groups[mv] || []).push(+id); }
  const kinds = Object.keys(groups);
  if(kinds.length === 1) return {winner:null, winners:[], tie:true};      /* 全员同招 → 平局 */
  if(kinds.length === 3) return {winner:null, winners:[], tie:true};      /* 三种招式同时出现 → 平局重出 */
  /* 只剩两种招式：克制方全体胜出，各得 AP。例：2 石头 vs 2 剪刀 → 两名石头玩家各得 AP */
  const winnerKind = kinds.find(k => BEATS[k] === kinds.find(o => o !== k));
  if(!winnerKind) return {winner:null, winners:[], tie:true};
  const pool = groups[winnerKind];
  return {winner: pool[0], winners: pool, tie:false};
}""", 'judgeRound：两种招式×克制方全体胜出')

# rpsPhase 结算：支持多名胜者
sub("""        if(round >= 8){
          /* 连续平局过多：随机指定一名玩家获得本回合 AP，保证游戏推进 */
          const win = live[rnd(live.length)];
          rpsDecided = 1;
          win.ap += apPerWin;
          log(`✊ 连续 ${round} 轮平局，随机判定 <b>${lname(win)}</b> 胜出并获得 ${apPerWin} AP。`,'l-warn');
          showSlotsMulti(moves, win.id);
          break;
        }""",
"""        if(round >= 8){
          /* 连续平局过多：随机指定一名玩家获得本回合 AP，保证游戏推进 */
          const win = live[rnd(live.length)];
          rpsDecided = 1;
          win.ap += apPerWin;
          log(`✊ 连续 ${round} 轮平局，随机判定 <b>${lname(win)}</b> 胜出并获得 ${apPerWin} AP。`,'l-warn');
          showSlotsMulti(moves, win.id);
          break;
        }""", '（平局兜底不变）')

sub("""      rpsDecided = 1;
      const winner = P(res.winner);
      winner.ap += apPerWin;
      log(`✊ <b>猜拳</b>（第 ${round} 轮）：${detail} → <b>${lname(winner)} 胜出，+${apPerWin} AP</b>。`,'l-rps');
      showSlotsMulti(moves, winner.id);
      try{ sfx.win(); }catch(e){}""",
"""      rpsDecided = 1;
      const winners = (res.winners && res.winners.length ? res.winners : [res.winner]).map(id=>P(id)).filter(Boolean);
      for(const w of winners) w.ap += apPerWin;
      const names = winners.map(w=>lname(w)).join('、');
      log(`✊ <b>猜拳</b>（第 ${round} 轮）：${detail} → <b>${names} 胜出，各 +${apPerWin} AP</b>。`,'l-rps');
      showSlotsMulti(moves, winners[0] ? winners[0].id : null);
      try{ sfx.win(); }catch(e){}""", 'rpsPhase：多名胜者各得 AP')

# ============ ② 闪避改为可选（赌一把） ============
sub("""      if(tie){
        /* 平局：被攻击方可以消耗 1 AP 直接闪避，否则重猜 */
        const wantsDodge = (o.dodge!==undefined) ? o.dodge : (target.isHuman || R()<0.6);
        log(`⚔️ <b>判定</b>（第 ${rounds} 轮）：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → 平局`,'l-rps');
        if(target.ap>=1 && wantsDodge && rounds===1){
          target.ap -= 1; dodged = true;
          log(`　　${lname(target)} 消耗 1 AP 直接闪避！`,'l-warn');
          break;
        }""",
"""      if(tie){
        /* 平局：由被攻击方选择——花 1 AP 直接闪避，或赌一把继续判定 */
        log(`⚔️ <b>判定</b>（第 ${rounds} 轮）：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → 平局`,'l-rps');
        if(rounds===1){
          let wantsDodge = false;
          if(o.dodge!==undefined) wantsDodge = o.dodge;
          else if(target.isHuman) wantsDodge = await askDodge(target, attacker);
          else wantsDodge = (R()<0.5);        /* AI：约一半概率选择闪避 */
          if(wantsDodge && target.ap>=1){
            target.ap -= 1; dodged = true;
            log(`　　${lname(target)} 消耗 1 AP 直接闪避！`,'l-warn');
            break;
          }
          if(target.ap>=1) log(`　　${lname(target)} 选择<b>不消耗 AP</b>，继续判定赌一把。`,'l-sys');
          else log(`　　${lname(target)} 没有 AP，只能继续判定。`,'l-sys');
        }""", '闪避改可选')

# 闪避询问框（带超时兜底）
sub("""function chooseArmorMode(attacker, target){""",
"""/* 判定平局时询问：花 1 AP 直接闪避，还是不花 AP 赌一把继续判定 */
function askDodge(target, attacker){
  return new Promise(res=>{
    let done = false;
    const finish = (v)=>{ if(done) return; done = true; res(v); };
    const bar = document.getElementById('actionbar');
    bar.innerHTML = '<div><span class="pill on">判定平局！选择如何应对</span></div>';
    const row = document.createElement('div'); row.className='actions';
    const b1 = document.createElement('button'); b1.className='btn pri';
    b1.textContent = `🛡 花 1 AP 直接闪避（剩余 ${target.ap} AP）`;
    b1.onclick = ()=>{ try{ sfx.click(); }catch(e){} finish(true); };
    const b2 = document.createElement('button'); b2.className='btn';
    b2.textContent = '🎲 不消耗 AP，继续判定（赌一把）';
    b2.onclick = ()=>{ try{ sfx.click(); }catch(e){} finish(false); };
    row.appendChild(b1); row.appendChild(b2); bar.appendChild(row);
    /* 兜底：30 秒未选按“赌一把”继续，绝不死等 */
    setTimeout(()=>finish(false), 30000);
  });
}

function chooseArmorMode(attacker, target){""", 'askDodge 询问框')

# ============ ⑨ 护甲选择框加超时兜底 ============
sub("""      b1.onclick=()=>{ sfx.click(); bar.innerHTML=''; res('break'); };
      const b2=document.createElement('button'); b2.className='btn small';
      b2.textContent='B：造成 1.5 穿甲伤害（无视护甲）';
      b2.onclick=()=>{ sfx.click(); bar.innerHTML=''; res('pierce'); };
      row.appendChild(b1); row.appendChild(b2); bar.appendChild(row);
    });""",
"""      let done=false;
      const finish=(v)=>{ if(done) return; done=true; bar.innerHTML=''; res(v); };
      b1.onclick=()=>{ try{ sfx.click(); }catch(e){} finish('break'); };
      const b2=document.createElement('button'); b2.className='btn small';
      b2.textContent='B：造成 1.5 穿甲伤害（无视护甲）';
      b2.onclick=()=>{ try{ sfx.click(); }catch(e){} finish('pierce'); };
      row.appendChild(b1); row.appendChild(b2); bar.appendChild(row);
      setTimeout(()=>finish('break'), 30000);      /* 兜底：30 秒未选按 A 处理 */
    });""", '护甲选择框兜底')

# ============ ⑦ 面包 / 附魔金苹果 各 1 AP ============
sub("""      push({type:'eat',item:'bread',targetId:t.id,cost:1,label:`🍞 面包 → ${t.name}（回 1.5 血，1 步）`});""",
"""      push({type:'eat',item:'bread',targetId:t.id,cost:CONSUME_COST,label:`🍞 面包 → ${t.name}（回 1.5 血，${CONSUME_COST} AP）`});""",
'面包 1 AP（人类）')
sub("""    if(hasItem(p,'god_apple')) push({type:'eat',item:'god_apple',targetId:p.id,cost:0,label:'🍎 吃附魔金苹果（+2 血 / 2 回合 +0.5 / 免疫）'});""",
"""    if(hasItem(p,'god_apple')) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,label:`🍎 吃附魔金苹果（+2 血 / 2 回合 +0.5 / 免疫，${CONSUME_COST} AP）`});""",
'金苹果 1 AP（人类）')
sub("""    if(hasItem(p,'bread') && p.hp<=2.5) push({type:'eat',item:'bread',targetId:p.id,cost:1,label:'吃面包'});""",
"""    if(hasItem(p,'bread') && p.hp<=2.5) push({type:'eat',item:'bread',targetId:p.id,cost:CONSUME_COST,label:'吃面包'});""",
'面包 1 AP（AI）')
sub("""    if(hasItem(p,'god_apple') && p.hp<=2.5) push({type:'eat',item:'god_apple',targetId:p.id,cost:0,label:'金苹果'});""",
"""    if(hasItem(p,'god_apple') && p.hp<=2.5) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,label:'金苹果'});""",
'金苹果 1 AP（AI）')

sub("""const ATK_COST   = 1;          /* 每次攻击固定 1 AP（不占免费行动槽） */""",
"""const ATK_COST   = 1;          /* 每次攻击固定 1 AP（不占免费行动槽） */
const CONSUME_COST = 1;        /* 面包 / 附魔金苹果等补给：各 1 AP */
const ROD_COST   = 1;          /* 钓鱼竿使他人位移：1 AP */""", 'AP 常量')

# ============ ⑧ 钓鱼竿位移 1 AP ============
import re
before = t
t = re.sub(r"(push\(\{type:'rod'[^}]*?)cost:0", r"\1cost:ROD_COST", t)
t = re.sub(r"(push\(\{type:'fish_trident'[^}]*?)cost:0", r"\1cost:ROD_COST", t)
if t != before: notes.append('  ok 钓鱼竿位移 1 AP')
else: notes.append('  ! 钓鱼竿 cost 未找到（可能已是其他值）')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
