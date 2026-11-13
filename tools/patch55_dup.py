# -*- coding: utf-8 -*-
"""补丁 55：删除重复的旧 waitClick（它覆盖了新版本，导致点击无响应/卡死）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

# 旧定义（第二个）完整文本
old_dup = """/* 统一的“等玩家点一下”交互：带超时与防重复，避免任何情况下卡死 */
function waitClick(label, opts){
  const o = opts||{};
  return new Promise(res=>{
    let done = false;
    const finish = ()=>{ if(done) return; done = true; clickResolver = null; res(); };
    const bar = o.bar || document.getElementById('actionbar');
    bar.innerHTML = '';
    const b = document.createElement('button');
    b.className = 'btn pri';
    b.textContent = label || '继续 ▶';
    b.onclick = ()=>{ try{ sfx.click(); }catch(e){} finish(); };
    clickResolver = finish;
    bar.appendChild(b);
    /* 兜底：按钮被意外移除 / 玩家长时间不操作时自动放行，绝不死等 */
    const iv = setInterval(()=>{
      if(done){ clearInterval(iv); return; }
      if(!b.isConnected || (o.timeout && Date.now()-t0 > o.timeout)){ clearInterval(iv); finish(); }
    }, 250);
    const t0 = Date.now();
  });
}
"""
if old_dup in t:
    t = t.replace(old_dup, '', 1)
    print('已删除重复的旧 waitClick 定义')
else:
    print('! 未找到重复定义（可能文本有细微差别）')

# 检查现在剩几个 waitClick 定义
import re
n = len(re.findall(r'^function waitClick\(', t, re.M))
print(f'当前 waitClick 定义数: {n}（应为 1）')
n2 = len(re.findall(r'^function promptRpsMove\(', t, re.M))
print(f'当前 promptRpsMove 定义数: {n2}（应为 1）')

IDX.write_text(t, encoding='utf-8')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
