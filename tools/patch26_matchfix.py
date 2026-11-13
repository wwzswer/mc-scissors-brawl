# -*- coding: utf-8 -*-
"""补丁 26：修复 match-test 的 playMatch（加超时与日志尾部诊断）"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\match-test.js')
lines = F.read_text(encoding='utf-8').split('\n')

# 定位 playMatch 函数范围（从 def 到它的结束 '}'）
start = next(i for i,l in enumerate(lines) if l.startswith('function playMatch('))
end = start
depth = 0
for i in range(start, len(lines)):
    depth += lines[i].count('{') - lines[i].count('}')
    if depth == 0 and i > start:
        end = i; break

new_fn = '''function playMatch(MC, sandbox, document, cfg){
  const errors = [];
  return new Promise(resolve=>{
    MC.__api.setFastTiming();          /* 无头：删掉所有动画等待 */
    MC.__api.setAutoPlayer((p, opts)=>{
      global.__apCalls = (global.__apCalls||0)+1;
      try{
        const a = autoHumanPolicy(MC, MC.state(), opts);
        if(!a){ errors.push('policy 返回空动作'); return {type:'pass'}; }
        if(!a.type){ errors.push('policy 返回非法动作: '+JSON.stringify(a)); return {type:'pass'}; }
        return a;
      }
      catch(e){ errors.push('policy: '+(e.stack||String(e))); return {type:'pass'}; }
    });
    MC.start(cfg);
    const G = MC.state();
    const t0 = Date.now();
    let guard = 0;
    const logEl = document.getElementById('log');
    const iv = setInterval(()=>{
      const timeUp = (Date.now() - t0) > 20000;
      if(G.over || guard++ > 60000 || timeUp){
        clearInterval(iv);
        if(timeUp && !G.over){
          errors.push('超时未结束（20s） round=' + G.round + ' turnOwner=' + G.turnOwner + ' calls=' + (global.__apCalls||0));
          const tail = logEl.children.slice(-20).map(d=>(d.children||[]).map(c=>c.innerHTML||c.textContent||'').join(' ').replace(/<[^>]+>/g,''));
          errors.push('日志尾部: ' + tail.join(' ｜ '));
        }
        resolve({G, errors, ms:Date.now()-t0, aborted:!G.over});
        return;
      }
    }, 1);
  });
}'''

lines[start:end+1] = new_fn.split('\n')
F.write_text('\n'.join(lines), encoding='utf-8')
print(f'playMatch 已重写（原 {start+1}..{end+1} 行）')
