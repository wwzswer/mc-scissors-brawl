# -*- coding: utf-8 -*-
"""补丁 151：让 file:// 打开时的联机提示更醒目 + 明确该怎么做"""
import pathlib, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
P = D / 'index.html'
t = P.read_text(encoding='utf-8')
orig = len(t)

OLD = """    Net.status('当前是用 <code>file://</code> 直接打开页面，浏览器不允许联机。<br>'+
      '请在主机上运行 <code>start-server.cmd</code>，然后所有人用 <code>http://主机IP:8787</code> 打开本页。');"""
NEW = """    Net.status(
      '<div style="border:1px solid #e05555;background:#2a1414;border-radius:8px;padding:10px 12px;line-height:1.9">'+
      '<b style="color:#ff7b7b;font-size:14px">⚠ 现在不能联机：你是在用 file:// 直接打开本页</b><br>'+
      '浏览器安全策略禁止 file:// 页面访问联机服务。<b>联机必须通过服务器地址打开</b>：<br>'+
      '① 双击本文件夹里的 <code>start-server.cmd</code>（会弹一个黑窗口，别关它）<br>'+
      '② 浏览器会自动打开 <code>http://127.0.0.1:8787</code> —— 请在那个页面里玩联机<br>'+
      '③ 朋友在同一局域网，用黑窗口里显示的 <code>http://192.168.x.x:8787</code> 打开<br>'+
      '<span style="color:var(--dim)">（单机模式不受影响，继续双击 index.html 即可）</span>'+
      '</div>');"""

if OLD in t:
    t = t.replace(OLD, NEW, 1)
    P.write_text(t, encoding='utf-8')
    print('✅ 已改进 file:// 提示')
else:
    print('! 锚点未匹配，尝试宽松查找')
    i = t.find("当前是用 <code>file://</code>")
    print('  附近文本:', repr(t[max(0,i-120):i+260]) if i >= 0 else '未找到')

print('长度 %d → %d' % (orig, len(t)))

NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk151.js')
tmp.write_text(js, encoding='utf-8')
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
