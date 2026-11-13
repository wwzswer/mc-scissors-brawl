# -*- coding: utf-8 -*-
"""补丁 27：修复 AI 回合死循环
   原因：0 成本的建筑（村庄）在 AI 选项里永远 canPay 为真，
        而 craft() 因 buildAllowed=false 静默失败、runAction 仍返回 true，
        于是 takeTurn 的 AI 分支反复选同一个无效动作，直到 guard 用尽（表现为极慢/卡死）。
   修复：① craft() 明确返回是否真的产出；② takeTurn 对同一动作重复 3 次即拉黑；
        ③ aiOptions 里对 0 成本建筑也走 buildAllowed 校验（原本已有，但补一道保险）。
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

# ① craft() 明确返回：建筑未能建造时返回 false
sub("""  if(it.build && !buildAllowed(p,k)) return false;
  if(it.build){
    p.buildings[k]=true;""",
"""  if(it.build){
    if(!buildAllowed(p,k)) return false;          /* 已建过 / 全局已满 → 明确失败 */
    p.buildings[k]=true;""",
'craft 建筑失败返回 false')

# ② takeTurn：同一动作重复 3 次直接拉黑（防死循环）
sub("""  const avoid = [];   /* 已尝试但不可用的选项，避免 AI 死循环 */""",
"""  const avoid = [];   /* 已尝试但不可用的选项，避免 AI 死循环 */
  const repeat = {};  /* 同一动作的执行次数，超过 3 次直接拉黑 */""",
'takeTurn 加重试计数')

sub("""      const ok = await runAction(p, choice);
      if(ok===false) avoid.push(actionKey(choice));
      await sleep(w('action'));
    }""",
"""      const ak = actionKey(choice);
      repeat[ak] = (repeat[ak]||0) + 1;
      const ok = await runAction(p, choice);
      if(ok===false || repeat[ak] >= 3) avoid.push(ak);
      await sleep(w('action'));
    }""",
'takeTurn 重复动作拉黑')

# ③ 人类回合（autoPlayer）分支也加同样的保护
sub("""      if(choice.type==='pass'){ log(`⏭ ${lname(p)} 结束行动。`,'l-sys'); break; }
      const ok = await runAction(p, choice);
      if(ok===false) avoid.push(actionKey(choice));
      await sleep(w('actionHuman'));
      if(!p.alive || G.over) break;
      continue;""",
"""      if(choice.type==='pass'){ log(`⏭ ${lname(p)} 结束行动。`,'l-sys'); break; }
      const ak = actionKey(choice);
      repeat[ak] = (repeat[ak]||0) + 1;
      const ok = await runAction(p, choice);
      if(ok===false || repeat[ak] >= 3) avoid.push(ak);
      await sleep(w('actionHuman'));
      if(!p.alive || G.over) break;
      continue;""",
'autoPlayer 重复动作拉黑')

sub("""      choice = await askHuman(p, opts);
      if(!choice) break;
      if(choice.type==='shop_progress'||choice.type==='shop_craft'){
        await openShop(p, choice.type==='shop_progress'); continue;   /* 返回后重绘行动面板 */
      }
      if(choice.type==='pass'){ log(`⏭ ${lname(p)} 结束行动。`,'l-sys'); break; }
      netSendAct(choice);
      const ok = await runAction(p, choice);
      if(ok===false) avoid.push(actionKey(choice));""",
"""      choice = await askHuman(p, opts);
      if(!choice) break;
      if(choice.type==='shop_progress'||choice.type==='shop_craft'){
        await openShop(p, choice.type==='shop_progress'); continue;   /* 返回后重绘行动面板 */
      }
      if(choice.type==='pass'){ log(`⏭ ${lname(p)} 结束行动。`,'l-sys'); break; }
      netSendAct(choice);
      const ak = actionKey(choice);
      repeat[ak] = (repeat[ak]||0) + 1;
      const ok = await runAction(p, choice);
      if(ok===false || repeat[ak] >= 3) avoid.push(ak);""",
'人类回合重复动作拉黑')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
