# -*- coding: utf-8 -*-
"""补丁 33：修掉速查区里未替换的 ${MAX_DIST} 与过时文案"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

old = """          <div><b>距离</b>：初始 1 格、上限 ${MAX_DIST} 格、两两独立；走位 1 步 ±1 格、末影珍珠 ±2、钓鱼竿 ±1、盾 +1。近战需 0 格</div>"""
new = """          <div><b>距离</b>：初始 1 格、上限 <b id="distMaxTxt">7</b> 格、两两独立；走位 1 步 ±1 格、末影珍珠 ±2、钓鱼竿 ±1、盾 +1。近战需 0 格</div>"""
if old in t:
    t = t.replace(old, new, 1); notes.append('  ok 距离文案')
else:
    notes.append('  ! 距离文案未匹配')

old2 = """          <div><b>行动经济</b>：每回合 1 次免费行动；AP 可买额外行动（1 AP / 次），<b>回合末清零、不可存储</b></div>"""
new2 = """          <div><b>行动经济</b>：每回合 1 次免费行动；AP 可买额外行动（1 AP / 次），<b>回合末清零、不可存储</b></div>
          <div><b>进程</b>：空手→木(1点)→石(2点)→铁(3点)→钻石(3点)；<b>物品也是进度式</b></div>
          <div><b>切换工具</b>：持有多个武器时可随时免费切换，不占行动次数</div>"""
if old2 in t:
    t = t.replace(old2, new2, 1); notes.append('  ok 速查补充')
else:
    notes.append('  ! 速查补充未匹配')

# 初始化时写入实际数值
old3 = "loadSettings();\nshowScreen('screen-main');"
new3 = """/* 把界面里的动态数值填上（速查区等静态文案） */
(function fillDynamicText(){
  const d = document.getElementById('distMaxTxt');
  if(d) d.textContent = MAX_DIST;
  const ap = document.getElementById('apRuleTxt');
  if(ap) ap.textContent = apPerWin;
})();
loadSettings();
showScreen('screen-main');"""
if old3 in t:
    t = t.replace(old3, new3, 1); notes.append('  ok 动态数值填充')
else:
    notes.append('  ! 动态填充锚点未匹配')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
