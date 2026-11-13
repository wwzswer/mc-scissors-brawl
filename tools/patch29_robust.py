# -*- coding: utf-8 -*-
"""补丁 29：健壮性
   ① takeTurn 内每个动作最多等 5 秒，超时则拉黑该动作继续（避免任何单步卡死整局）
   ② switch_weapon / water_pull 等"零成本即时动作"显式标记 isAction:false（不占行动次数）
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

# ① 通用超时包装
sub("""const sleep = ms => new Promise(r=>setTimeout(r,ms));""",
"""const sleep = ms => new Promise(r=>setTimeout(r,ms));
/* 给任意 Promise 加超时：超时返回 fallback，避免单步卡死整局 */
function withTimeout(promise, ms, fallback){
  return Promise.race([
    Promise.resolve(promise).catch(()=>fallback),
    sleep(ms).then(()=>fallback),
  ]);
}""", 'withTimeout')

# AI 分支：runAction 加超时
sub("""      const ak = actionKey(choice);
      repeat[ak] = (repeat[ak]||0) + 1;
      const ok = await runAction(p, choice);
      if(ok===false || repeat[ak] >= 3) avoid.push(ak);
      await sleep(w('action'));
    }""",
"""      const ak = actionKey(choice);
      repeat[ak] = (repeat[ak]||0) + 1;
      const ok = await withTimeout(runAction(p, choice), 5000, 'timeout');
      if(ok===false || ok==='timeout' || repeat[ak] >= 3){
        avoid.push(ak);
        if(ok==='timeout') log(`（${choice.type} 执行超时，已跳过）`,'l-warn');
      }
      await sleep(w('action'));
    }""", 'AI 动作超时')

# 人类(autoPlayer)分支：runAction 加超时
sub("""      const ak = actionKey(choice);
      repeat[ak] = (repeat[ak]||0) + 1;
      const ok = await runAction(p, choice);
      if(ok===false || repeat[ak] >= 3) avoid.push(ak);
      await sleep(w('actionHuman'));
      if(!p.alive || G.over) break;
      continue;""",
"""      const ak = actionKey(choice);
      repeat[ak] = (repeat[ak]||0) + 1;
      const ok = await withTimeout(runAction(p, choice), 5000, 'timeout');
      if(ok===false || ok==='timeout' || repeat[ak] >= 3) avoid.push(ak);
      await sleep(w('actionHuman'));
      if(!p.alive || G.over) break;
      continue;""", 'autoPlayer 动作超时')

# ② switch_weapon 不占行动次数
sub("""    push({type:'switch_weapon', key:k, cost:0, isAction:false, label:`🖐 换上 ${ITEMS[k].name}`});""",
"""    push({type:'switch_weapon', key:k, cost:0, isAction:false, slots:0, label:`🖐 换上 ${ITEMS[k].name}`});""",
'switch_weapon 标记')

# applyAction：即时动作不占行动次数
sub("""  const isPurchase = ['shop_progress','upgrade','craftShopItem','craft','buy_tnt','buy_apple'].includes(a.type);
  let itemCost = 0;                 /* 购买类动作的 AP 消耗，由各分支填写，末尾统一扣除 */
  if(a.type!=='pass' && a.isAction!==false && !isPurchase){""",
"""  const isPurchase = ['shop_progress','upgrade','craftShopItem','craft','buy_tnt','buy_apple'].includes(a.type);
  const isFree = ['switch_weapon','pearl','pass'].includes(a.type);   /* 免费即时动作：不占行动次数 */
  let itemCost = 0;                 /* 购买类动作的 AP 消耗，由各分支填写，末尾统一扣除 */
  if(a.type!=='pass' && a.isAction!==false && !isPurchase && !isFree){""",
'免费即时动作')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
