# -*- coding: utf-8 -*-
"""补丁 28：修多人猜拳无法收敛的问题
   - judgeRound：优先「克制其余所有人者胜出」；否则取多数派里的胜者；
     再不行（三人互克）则按随机方式决出一名胜者，避免无限平局。
   - 猜拳与判定都加轮次上限，超出后强制给出结果。
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

# ---- 1) judgeRound 改为必定收敛 ----
sub("""/* 判定胜负：唯一且克制其余所有招式者为胜者；全部相同为平局 */
function judgeRound(moves){
  const list = Object.entries(moves);
  if(list.length < 2) return {winner: list.length ? +list[0][0] : null, tie: list.length < 2};
  const uniq = new Set(list.map(([,m])=>m));
  if(uniq.size === 1) return {winner:null, tie:true};                    /* 所有人同招 → 平局 */
  for(const [id, mv] of list){
    if(list.every(([oid, omv]) => oid===id || BEATS[mv]===omv)){
      /* 该玩家的招式克制其余所有人 */
      return {winner:+id, tie:false};
    }
  }
  /* 没有唯一胜者（三方互克等）→ 也算平局，重出 */
  return {winner:null, tie:true};
}""",
"""/* 判定本回合猜拳的胜者
   ① 有人克制其余所有人 → 该玩家胜出（标准情况）
   ② 所有人同招 → 平局，重出
   ③ 三人互克（没有 ①）→ 从“赢过至少一人”的玩家里随机决出一名胜者，
      避免多人局永远分不出胜负（例如 A>B>C>A 这种循环） */
function judgeRound(moves){
  const list = Object.entries(moves);
  if(list.length === 0) return {winner:null, tie:true};
  if(list.length === 1) return {winner:+list[0][0], tie:false};
  const uniq = new Set(list.map(([,m])=>m));
  if(uniq.size === 1) return {winner:null, tie:true};                    /* 所有人同招 → 平局 */
  /* ① 克制其余所有人 */
  for(const [id, mv] of list){
    if(list.every(([oid, omv]) => oid===id || BEATS[mv]===omv)) return {winner:+id, tie:false};
  }
  /* ③ 没有绝对胜者：在“至少赢过一人”的玩家里随机选一个 */
  const scored = list.map(([id,mv])=>({id:+id, win: list.filter(([oid,omv])=>oid!==id && BEATS[mv]===omv).length}));
  const cand = scored.filter(s=>s.win>0);
  if(cand.length === 0) return {winner:null, tie:true};
  const best = Math.max(...cand.map(c=>c.win));
  const top = cand.filter(c=>c.win===best);
  return {winner: top[rnd(top.length)].id, tie:false};
}""", 'judgeRound 收敛')

# ---- 2) 猜拳阶段：轮次上限后强制结算 ----
sub("""        if(instantRps){ /* 无头：直接下一轮 */ }
        else if(autoMode) await sleep(w('rpsAi')||120); else await waitClick('平局！继续出拳 ▶');
        continue;""",
"""        if(round >= 8){
          /* 连续平局过多：随机指定一名玩家获得本回合 AP，保证游戏推进 */
          winner = live[rnd(live.length)];
          log(`✊ <b>猜拳</b>：连续 ${round} 轮平局，随机判定 <b>${lname(winner)}</b> 胜出并获得 ${apPerWin} AP。`,'l-warn');
          showSlotsMulti(moves, winner.id);
          sfx.win();
          break;
        }
        if(instantRps){ /* 无头：直接下一轮 */ }
        else if(autoMode) await sleep(w('rpsAi')||120); else await waitClick('平局！继续出拳 ▶');
        continue;""", '猜拳轮次上限')

# ---- 3) 判定：轮次上限后强制出结果 ----
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
        /* 平局：被攻击方可以消耗 1 AP 直接闪避，否则重猜 */
        const wantsDodge = (o.dodge!==undefined) ? o.dodge : (target.isHuman || R()<0.6);
        log(`⚔️ <b>判定</b>（第 ${rounds} 轮）：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → 平局`,'l-rps');
        if(target.ap>=1 && wantsDodge && rounds===1){
          target.ap -= 1; dodged = true;
          log(`　　${lname(target)} 消耗 1 AP 直接闪避！`,'l-warn');
          break;
        }
        if(rounds >= 10){
          hit = R() < 0.5;                      /* 连续平局过多：随机裁决 */
          log(`　　（连续 ${rounds} 轮平局，随机裁决为「${hit?'命中':'失效'}」）`,'l-warn');
          judgeSlots(ra, rb, hit);
          hit ? sfx.win() : sfx.lose();
          renderAll();
          break;
        }""", '判定轮次上限')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
