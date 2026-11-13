# -*- coding: utf-8 -*-
"""补丁 15：配合「每回合一次猜拳」的收尾
   - rpsPrompt 支持无目标（本回合统一猜拳）
   - 判定改为「平局继续重猜，直到有人胜出」（保留 1 AP 直接闪避的选项）
   - judgeRound / showSlotsMulti 导出（供测试）
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

# 1) rpsPrompt 无目标
sub("""function rpsPrompt(target){
  return new Promise(res=>{
    document.getElementById('rpsArea').classList.remove('hidden');
    document.getElementById('rpsBtns').classList.remove('hidden');
    document.getElementById('rpsStatus').textContent = `与 ${target.name} 猜拳 — 选择你的出拳`;
    rpsResolver=res;
  });
}""",
"""function rpsPrompt(target){
  return new Promise(res=>{
    document.getElementById('rpsArea').classList.remove('hidden');
    document.getElementById('rpsBtns').classList.remove('hidden');
    document.getElementById('rpsStatus').textContent =
      target ? `与 ${target.name} 猜拳 — 选择你的出拳` : '本回合猜拳 — 选择你的出拳（平手会重出）';
    rpsResolver=res;
  });
}""", 'rpsPrompt')

# 2) 判定：平局不结束，继续重猜
old_j = """function doJudgment(attacker, target, opts){
  const o = opts||{};
  return new Promise(resolve=>{
    const a = attacker.isHuman ? pick(['rock','scissors','paper']) : aiRpsMove(attacker, target);
    const b = target.isHuman  ? pick(['rock','scissors','paper']) : aiRpsMove(target, attacker);
    /* 判定用的猜拳也可以由外部指定（便于测试与回放） */
    const ra = o.a || a, rb = o.b || b;
    attacker.lastRps=ra; target.lastRps=rb;
    const tie = ra===rb;
    const win = !tie && BEATS[ra]===rb;
    let dodged=false;
    if(tie && alivePlayers().length>=2){
      const wantsDodge = (o.dodge!==undefined) ? o.dodge : (target.isHuman || R()<0.8);
      if(target.ap>=1 && wantsDodge){ target.ap-=1; dodged=true; }
    }
    log(`⚔️ <b>判定</b>：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → ` +
        (dodged ? `${lname(target)} 消耗 1 AP 直接闪避！` : (win?'攻方胜出，命中！':'攻击失效。')), 'l-rps');
    if(dodged) log('（多人对战中双方同时胜出 → 被攻击方可以消耗行动点直接闪避）','l-sys');
    judgeSlots(ra,rb,win&&!dodged);
    (win&&!dodged) ? sfx.win() : sfx.lose();
    renderAll();
    const finish = ()=>{ hideRpsSlots(); resolve(win&&!dodged); };
    if(o.instant) finish(); else setTimeout(finish, ANIM.judgmentMs);
  });
}"""
new_j = """function doJudgment(attacker, target, opts){
  const o = opts||{};
  return new Promise(async resolve=>{
    let hit = false, dodged = false, rounds = 0;
    /* 判定同样必须分出胜负：平局则一直重猜（除非被攻击方花 1 AP 直接闪避） */
    while(rounds++ < 60){
      const a = attacker.isHuman ? pick(['rock','scissors','paper']) : aiRpsMove(attacker, target);
      const b = target.isHuman  ? pick(['rock','scissors','paper']) : aiRpsMove(target, attacker);
      const ra = (o.a && rounds===1) ? o.a : a;      /* 允许测试指定首轮出拳 */
      const rb = (o.b && rounds===1) ? o.b : b;
      attacker.lastRps = ra; target.lastRps = rb;
      const tie = ra===rb;
      const win = !tie && BEATS[ra]===rb;
      if(tie){
        /* 平局：被攻击方可以消耗 1 AP 直接闪避，否则重猜 */
        const wantsDodge = (o.dodge!==undefined) ? o.dodge : (target.isHuman || R()<0.6);
        log(`⚔️ <b>判定</b>（第 ${rounds} 轮）：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → 平局`,'l-rps');
        if(target.ap>=1 && wantsDodge && rounds===1){
          target.ap -= 1; dodged = true;
          log(`　　${lname(target)} 消耗 1 AP 直接闪避！`,'l-warn');
          break;
        }
        judgeSlots(ra,rb,false); sfx.rps(); renderAll();
        if(!o.instant) await sleep(Math.min(ANIM.judgmentMs, 500));
        continue;
      }
      hit = win;
      log(`⚔️ <b>判定</b>（第 ${rounds} 轮）：${lname(attacker)} 出 ${RPS_NAME[ra]} ｜ ${lname(target)} 出 ${RPS_NAME[rb]} → ` +
          (win ? '攻方胜出，命中！' : '攻击失效。'), 'l-rps');
      judgeSlots(ra,rb,win);
      win ? sfx.win() : sfx.lose();
      renderAll();
      break;
    }
    if(!dodged && rounds>60) log('（判定轮次过多，按攻击失效处理）','l-warn');
    const finish = ()=>{ hideRpsSlots(); resolve(hit); };
    if(o.instant) finish(); else setTimeout(finish, ANIM.judgmentMs);
  });
}"""
sub(old_j, new_j, 'doJudgment 平局重猜')

# 3) 导出
sub("    get Net(){ return Net; }, netCreateRoomWith, netJoinRoomWith, netIsOn, netHandleEvent,",
    "    get Net(){ return Net; }, netCreateRoomWith, netJoinRoomWith, netIsOn, netHandleEvent,\n    judgeRound, rpsPhase, doJudgment, showSlotsMulti,",
    '导出猜拳/判定接口')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
