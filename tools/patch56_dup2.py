# -*- coding: utf-8 -*-
"""补丁 56：删除重复的旧 promptRpsMove"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

old_dup = """/* 兼容旧调用名 */
function rpsPrompt(target){ return promptRpsMove(target); }
function promptRpsMove(target){
  return new Promise(res=>{
    let done = false;
    const finish = (mv)=>{ if(done) return; done = true; rpsResolver = null; res(mv); };
    const area = document.getElementById('rpsArea');
    const btns = document.getElementById('rpsBtns');
    if(area) area.classList.remove('hidden');
    if(btns) btns.classList.remove('hidden');
    const st = document.getElementById('rpsStatus');
    if(st) st.textContent = target ? `与 ${target.name} 猜拳 — 选择你的出拳` : '本回合猜拳 — 选择你的出拳（平手会重出）';
    rpsResolver = finish;
    /* 兜底：按钮区异常时随机出拳；最长 90 秒 */
    const iv = setInterval(()=>{
      if(done){ clearInterval(iv); return; }
      if(!btns || !btns.isConnected){ clearInterval(iv); finish(pick(['rock','scissors','paper'])); }
    }, 400);
    setTimeout(()=>{ clearInterval(iv); finish(pick(['rock','scissors','paper'])); }, 90000);
  });
}"""
new_dup = """/* 兼容旧调用名（promptRpsMove 已在上方定义，这里只做别名） */
function rpsPrompt(target){ return promptRpsMove(target); }"""

if old_dup in t:
    t = t.replace(old_dup, new_dup, 1)
    print('已删除重复的旧 promptRpsMove')
else:
    print('! 未匹配，尝试宽松删除')
    # 宽松：找到重复出现的 promptRpsMove 定义块（第二个）
    matches = list(re.finditer(r'function promptRpsMove\(target\)\{', t))
    print('  找到定义数:', len(matches))
    if len(matches) > 1:
        start = matches[1].start()
        # 找到该函数结束（下一个 '}\n' 后跟注释或 function）
        depth = 0; i = start
        while i < len(t):
            if t[i] == '{': depth += 1
            elif t[i] == '}':
                depth -= 1
                if depth == 0: break
            i += 1
        end = i + 1
        t = t[:start] + t[end:]
        print('  已删除第二个定义（字符', start, '-', end, '）')

n = len(re.findall(r'^function promptRpsMove\(target\)\{', t, re.M))
print(f'现在 promptRpsMove 定义数: {n}（应为 1）')
IDX.write_text(t, encoding='utf-8')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
