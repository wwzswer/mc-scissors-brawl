# -*- coding: utf-8 -*-
"""补丁 8：行动点不可存储（回合末清零）+ 相关文案
   注意：全部用 Python 源文件（不用 -c 传参），避免反斜杠转义问题。
"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

# ---------- 0) 先清掉上一次失败注入的坏行 ----------
bad_re = re.compile(r'\n *if\(cleared\.length\) log\([^\n]*?\);')
if bad_re.search(t):
    t = bad_re.sub('', t)
    notes.append('  ok 清掉上次失败的坏行')

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ---------- 1) 回合末清零（在 renderAll 之后、sleep 之前） ----------
ok = sub(
"""  renderAll();
  if(o.instant) return;
  if(autoMode) await sleep(w('roundEnd')); else await waitClick('继续 ▶ 下一回合');
}""",
"""  /* 行动点不可存储：本回合未用完的 AP 在结算时清零 */
  const cleared = G.players.filter(q=>q.alive && q.ap>0).map(q=>q.name+'×'+q.ap);
  for(const q of G.players) q.ap = 0;
  if(cleared.length) log('♻️ 行动点不可存储：' + cleared.join('、') + ' 未使用的 AP 已清零。','l-warn');
  renderAll();
  if(o.instant) return;
  if(autoMode) await sleep(w('roundEnd')); else await waitClick('继续 ▶ 下一回合');
}""", 'AP 回合末清零')
if not ok: raise SystemExit('关键补丁失败：找不到 endOfRound 结尾')

# ---------- 2) 开局日志说明 ----------
sub("""  log(`行动经济：每回合 1 次免费行动；之后每 1 AP 可购买一次额外行动（制作/升级的建筑与物品本身也消耗 AP）。`,'l-sys');""",
"""  log(`行动经济：每回合 1 次免费行动；之后每 1 AP 可购买一次额外行动。⚠ <b>行动点不可存储</b>——每回合结束时未用完的 AP 会清零。`,'l-sys');""",
'开局日志说明')

# ---------- 3) 面板 AP 提示 ----------
sub("""        <span class="k">行动点</span><span class="v">${sprTag('coin',18)} ${p.ap}</span>""",
"""        <span class="k">行动点</span><span class="v">${sprTag('coin',18)} ${p.ap}<span style="color:var(--dim);font-size:11px">（本回合内有效）</span></span>""",
'面板 AP 提示')

# ---------- 4) 行动区提示 ----------
sub("""    hint.innerHTML=`额外行动每次消耗 <b>1 AP</b>；制作 / 升级按标注的步数消耗 AP。本回合剩余 <b>${p.ap}</b> AP（可留到下一回合）。`;""",
"""    hint.innerHTML=`额外行动每次消耗 <b>1 AP</b>；制作 / 投入进度按标注步数消耗 AP。本回合剩余 <b>${p.ap}</b> AP，⚠ <b>回合结束即清零（不可存储）</b>。`;""",
'行动区 AP 提示')

# ---------- 5) 规则页 ----------
sub("""      ② <b>行动阶段</b>：每回合每人有 <b>1 次免费行动</b>；之后每 <b>1 AP</b> 可以再买一次行动。制作物品与投入进程进度都只花 AP、不占行动次数。<br>""",
"""      ② <b>行动阶段</b>：每回合每人有 <b>1 次免费行动</b>；之后每 <b>1 AP</b> 可以再买一次行动。制作物品与投入进程进度都只花 AP、不占行动次数。<br>
      ⚠ <b>行动点不可存储</b>：每回合结束时没花完的 AP 立即清零，所以能花就尽量花掉。<br>""",
'规则页 AP 说明')

# ---------- 6) 速查区 ----------
sub("""          <div><b>行动经济</b>：每回合 1 次免费行动；行动点可购买额外行动（1 AP / 次）</div>""",
"""          <div><b>行动经济</b>：每回合 1 次免费行动；AP 可买额外行动（1 AP / 次），<b>回合末清零、不可存储</b></div>""",
'速查区 AP 说明')

# ---------- 7) 开始页也提示一次 ----------
sub("""        <div><b>生命</b>：每人 4 点（判定不获得 AP）</div>""",
"""        <div><b>生命</b>：每人 4 点（判定不获得 AP）</div>
        <div><b>行动点</b>：不可存储，每回合结束时清零</div>""",
'开始页提示')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
print('文件', round(len(t)/1024,1), 'KB')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
