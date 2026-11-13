# -*- coding: utf-8 -*-
"""补丁 50：rps-check 增加现场抓取（rpsResolver / 按钮可见性 / 阶段状态）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rps-check.html')
t = F.read_text(encoding='utf-8')

old = """      if(moveBtn && status.includes('选择你的出拳')){
        moveBtn.click(); clicks++;
        await wait(150);
        continue;
      }"""
new = """      if(moveBtn && status.includes('选择你的出拳')){
        const snap = W.eval(`(function(){
          const G = MCGame.state();
          return { resolver: typeof rpsResolver, resp: (rpsResolver? 'fn':'null'),
                   btnVis: (function(){ const b=document.getElementById('rpsBtns'); return b? !b.classList.contains('hidden') : 'noBtn'; })(),
                   areaVis: (function(){ const a=document.getElementById('rpsArea'); return a? !a.classList.contains('hidden') : 'noArea'; })(),
                   phase: (document.getElementById('phasePill')||{}).textContent,
                   turn: G? G.turnOwner : 'noG', round: G? G.round : -1 };
        })()`);
        say(`  [点击前] ${JSON.stringify(snap)}`);
        moveBtn.click(); clicks++;
        await wait(250);
        const snap2 = W.eval(`(function(){
          const G = MCGame.state();
          return { resp: (typeof rpsResolver), areaVis: (function(){ const a=document.getElementById('rpsArea'); return a? !a.classList.contains('hidden') : 'x'; })(),
                   status: (document.getElementById('rpsStatus')||{}).textContent,
                   barBtns: Array.from(document.querySelectorAll('#actionbar button')).map(b=>b.textContent.trim().slice(0,12)) };
        })()`);
        say(`  [点击后] ${JSON.stringify(snap2)}`);
        if(clicks >= 3) say('  （只抓前几次，后续静默推进）');
        continue;
      }"""
if old in t:
    t = t.replace(old, new, 1)
    F.write_text(t, encoding='utf-8')
    print('已加现场抓取')
else:
    print('! 锚点未匹配')
