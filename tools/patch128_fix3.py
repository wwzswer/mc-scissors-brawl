# -*- coding: utf-8 -*-
"""补丁 128：修复 3 处
   ① 烟花：跳过判定直接造成伤害 → 改为需要判定
   ② 三叉戟文案：删除"无需判定"（掷出仍需判定，判定失败＝未掷出）
   ③ 三叉戟文案：删除"掷出后失去"，改为与当前拾取规则一致
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ---------- ① 烟花需要判定 ----------
sub("""    /* 烟花：0.5 物理 + 1.5 法术；有护甲时 1 法术 */
    if(key==='firework'){
      const arm = armorActive(target);
      const dmg = arm ? [0,0,1,0] : [0.5,0,1.5,0];
      log(`🎆 ${lname(attacker)} 发射【烟花】（发射后需重新装填）。`,'l-warn'); sfx.boom();
      tryDamage(target, dmg, {label:'烟花'});
      for(const v of alivePlayers()){
        if(v!==target && v!==attacker && distanceBetween(target,v)===0)
          tryDamage(v,[0,0,1,0],{label:'烟花（同格溅射）'});
      }
      return true;
    }

    /* 近战 / 远程：判定（opts 里的 a/b/dodge/instant 可指定猜拳结果，便于测试与回放） */
    let success = false;
    try{
      success = await doJudgment(attacker, target, opts);
    }catch(err){
      rlog('doJudgment 抛出异常: ' + (err && err.message ? err.message : String(err)));
      log('（判定异常，按攻击失效处理）','l-warn');
      success = false;
    }
    if(!success){
      if(key==='flint'){
        /* 打火石需要判定：判定失败＝没能点燃 */
        log(`🔥 打火石没能点燃 ${lname(target)}（判定失败）。`,'l-warn');
        return false;
      }
      log(`攻击落空。`,'l-sys');
      return false;
    }""",
"""    /* 近战 / 远程 / 烟花：都要先判定（opts 里的 a/b/dodge/instant 可指定猜拳结果，便于测试与回放） */
    let success = false;
    try{
      success = await doJudgment(attacker, target, opts);
    }catch(err){
      rlog('doJudgment 抛出异常: ' + (err && err.message ? err.message : String(err)));
      log('（判定异常，按攻击失效处理）','l-warn');
      success = false;
    }
    if(!success){
      if(key==='flint'){
        /* 打火石需要判定：判定失败＝没能点燃 */
        log(`🔥 打火石没能点燃 ${lname(target)}（判定失败）。`,'l-warn');
        return false;
      }
      if(key==='firework'){
        log(`🎆 烟花没能命中 ${lname(target)}（判定失败，未造成伤害）。`,'l-warn');
        return false;
      }
      log(`攻击落空。`,'l-sys');
      return false;
    }

    /* 烟花：判定命中后 0.5 物理 + 1.5 法术；目标有护甲时改为 1 法术 */
    if(key==='firework'){
      const arm = armorActive(target);
      const dmg = arm ? [0,0,1,0] : [0.5,0,1.5,0];
      log(`🎆 ${lname(attacker)} 发射的【烟花】命中（发射后需重新装填）。`,'l-warn'); sfx.boom();
      tryDamage(target, dmg, {label:'烟花'});
      for(const v of alivePlayers()){
        if(v!==target && v!==attacker && distanceBetween(target,v)===0)
          tryDamage(v,[0,0,1,0],{label:'烟花（同格溅射）'});
      }
      return true;
    }""", '① 烟花改为需要判定')

# ---------- ②③ 三叉戟文案 ----------
sub("""  trident:    { name:'三叉戟', cost:3, prog:PROG.STONE, need:'fishing_rod', desc:'前置：钓鱼竿。① 距离 0 攻击：需判定，胜出 1.5 物理伤害。② 距离 ≥1 掷出：无需判定，1.5 物理伤害，但失去三叉戟（附魔【忠诚】会回到手中）。' },""",
"""  trident:    { name:'三叉戟', cost:3, prog:PROG.STONE, need:'fishing_rod', desc:'前置：钓鱼竿。① 距离 0 近战：需判定，胜出 1.5 物理伤害。② 距离 ≥1 掷出：同样需判定，胜出 1.5 物理伤害；判定失败视为未掷出、三叉戟留在手中。掷出后落在目标所在格，与其同格且 AP≥1 的玩家会花 1 AP 拾取（附魔【忠诚】则必定回到手中）。' },""",
'②③ 三叉戟物品说明')

sub("""      label:`🔱 掷出三叉戟 ${e.name}（1 AP，无需判定 1.5，掷出后失去）`});""",
"""      label:`🔱 掷出三叉戟 ${e.name}（1 AP，判定 1.5）`});""",
'② 掷出按钮文案')

# AI 侧标签也同步
sub("""        else push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,ranged:true,label:'掷出三叉戟 '+e.name});""",
"""        else push({type:'attack',key:'trident',targetId:e.id,cost:ATK_COST,ranged:true,label:'掷出三叉戟 '+e.name+'（判定）'});""",
'② AI 掷出标签')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  长度 {orig} → {len(back)}（{len(back)-orig:+d}）')
print('  烟花在判定之后:', back.index(\"if(key==='firework'){\") > back.index('if(!success){'))
print('  无「无需判定」残留:', '无需判定' not in back)
print('  无「掷出后失去」残留:', '掷出后失去' not in back)
print('  无「失去三叉戟」残留:', '失去三叉戟' not in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
