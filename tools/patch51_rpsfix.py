# -*- coding: utf-8 -*-
"""补丁 51：修正 rps-check 的按钮可见性判断（改用 rpsBtns 的 hidden class）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rps-check.html')
t = F.read_text(encoding='utf-8')

# 用清晰可靠的判定替换整段循环
start = t.index('    let clicks=0, rounds=0, enteredAction=false, stuck=false;')
end = t.index("    say(`  点击 ${clicks} 次，平局 ${rounds} 轮")

new_loop = """    let clicks=0, rounds=0, enteredAction=false, stuck=false;
    const t0=Date.now();
    const stateOf = ()=> W.eval(`(function(){
      const G = MCGame.state();
      const area = document.getElementById('rpsArea');
      const btns = document.getElementById('rpsBtns');
      return {
        areaVis: area ? !area.classList.contains('hidden') : false,
        btnsVis: btns ? !btns.classList.contains('hidden') : false,
        hasResolver: typeof rpsResolver === 'function',
        barBtns: Array.from(document.querySelectorAll('#actionbar button')).map(b=>b.textContent.trim()),
        turn: G ? G.turnOwner : null,
        round: G ? G.round : -1
      };
    })()`);
    while(Date.now()-t0 < 25000){
      const st = stateOf();
      /* 出拳按钮可见 → 点它 */
      if(st.btnsVis && st.hasResolver){
        const b = qa('#rpsBtns .btn')[0];
        if(b){ b.click(); clicks++; await wait(200); continue; }
      }
      /* 有“继续”按钮 → 点它 */
      const cont = qa('#actionbar button').find(b=>b.textContent.includes('继续'));
      if(cont){
        const label = cont.textContent.trim();
        cont.click(); clicks++;
        if(label.includes('进入行动阶段')){ enteredAction = true; break; }
        rounds++;
        await wait(200);
        continue;
      }
      /* 行动面板已出现（有攻击/走位/制作等按钮）→ 进入行动阶段 */
      if(st.barBtns.some(x=>/靠近|制作|投入|一拳|攻击|铁剑/.test(x))){ enteredAction = true; break; }
      if(Date.now()-t0 > 20000){ stuck = true; break; }
      await wait(120);
    }
"""
t = t[:start] + new_loop + t[end:]
F.write_text(t, encoding='utf-8')
print('已重写猜拳推进循环')
