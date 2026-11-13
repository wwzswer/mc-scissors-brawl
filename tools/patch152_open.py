# -*- coding: utf-8 -*-
"""补丁 152：server.js 启动后自动打开浏览器（跨平台、可关闭）"""
import pathlib, subprocess

P = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\server.js')
t = P.read_text(encoding='utf-8')
orig = len(t)

# ① 顶部引入 execFile
old_req = "const crypto = require('node:crypto');"
new_req = "const crypto = require('node:crypto');\nconst { exec } = require('node:child_process');"
if old_req in t and 'node:child_process' not in t:
    t = t.replace(old_req, new_req, 1)
    print('ok 引入 child_process')
else:
    print('- child_process 已引入或锚点不同')

# ② 加 openBrowser 函数（放在启动段之前）
ANCHOR = "/* ------------------------------ 启动 ------------------------------ */"
FN = """/* ------------------------------ 自动打开浏览器 ------------------------------ */
/* 服务器起来后自动打开一次；设 NO_OPEN=1 可关闭（测试/多实例时用） */
function openBrowser(url){
  if(process.env.NO_OPEN === '1') return;
  const cmd = process.platform === 'win32'
    ? `start "" "${url}"`
    : process.platform === 'darwin' ? `open "${url}"` : `xdg-open "${url}"`;
  try{ exec(cmd, {windowsHide:true}, ()=>{}); }catch(e){}
}

"""
if 'function openBrowser' not in t:
    t = t.replace(ANCHOR, FN + ANCHOR, 1)
    print('ok 插入 openBrowser')
else:
    print('- openBrowser 已存在')

# ③ 在 listen 回调里调用
old_listen = """  console.log('  关闭此窗口即停止服务。');
  console.log('');
});"""
new_listen = """  console.log('  关闭此窗口即停止服务。');
  console.log('');
  /* 自动把浏览器打开到本机地址，省得手动复制 */
  setTimeout(()=>{ openBrowser(`http://127.0.0.1:${PORT}`); }, 300);
});"""
if old_listen in t:
    t = t.replace(old_listen, new_listen, 1)
    print('ok listen 后自动打开浏览器')
else:
    print('! listen 锚点未匹配')

P.write_text(t, encoding='utf-8')
print('长度 %d → %d' % (orig, len(t)))

NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(P)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
