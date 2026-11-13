# -*- coding: utf-8 -*-
"""补丁 153：联机失败时给可操作的提示（替换裸 Failed to fetch）"""
import pathlib, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
P = D / 'index.html'
t = P.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# 公共提示函数（插在 netCreateRoom 之前）
HELPER = r"""
/* 联机请求失败的友好提示：区分「服务没开」和「其它错误」 */
function netFailHint(kind, err){
  const msg = String((err && err.message) || err || '');
  const offline = /Failed to fetch|NetworkError|Load failed|fetch/i.test(msg);
  if(offline){
    return '<div style="border:1px solid #e05555;background:#2a1414;border-radius:8px;padding:10px 12px;line-height:1.9">'+
      '<b style="color:#ff7b7b">连不上联机服务（'+kind+'失败）</b><br>'+
      '① 确认 <code>start-server.cmd</code> 开着的那个黑窗口还在（关掉 = 服务停）<br>'+
      '② 没有就重新双击 <code>start-server.cmd</code>，等浏览器自动打开<br>'+
      '③ 服务重启后，按 F5 刷新本页再试'+
      '</div>';
  }
  return kind + '失败：' + msg;
}

"""
sub("function netCreateRoom(){", HELPER + "function netCreateRoom(){", '① 插入失败提示函数')

# 创建房间的 catch
sub("     .catch(e=>Net.status('创建失败：'+e.message));",
    "     .catch(e=>Net.status(netFailHint('创建房间', e)));",
    '② 创建房间失败提示')

# 加入房间的 catch
sub("     .catch(e=>Net.status('加入失败：'+e.message));",
    "     .catch(e=>Net.status(netFailHint('加入房间', e)));",
    '③ 加入房间失败提示')

# netRefresh 的探测失败提示
OLD_REFRESH = """    Net.status('没有连上联机服务。请先运行 <code>start-server.cmd</code>。');"""
NEW_REFRESH = """    Net.status(
      '<div style="border:1px solid #e05555;background:#2a1414;border-radius:8px;padding:10px 12px;line-height:1.9">'+
      '<b style="color:#ff7b7b">没有连上联机服务</b><br>'+
      '请先双击 <code>start-server.cmd</code>（黑窗口别关），它会自动打开浏览器；<br>'+
      '如果窗口已经在跑还是这样，按 F5 刷新本页。'+
      '</div>');"""
sub(OLD_REFRESH, NEW_REFRESH, '④ 探测失败提示')

P.write_text(t, encoding='utf-8')
print('\n'.join(notes))
print('长度 %d → %d' % (orig, len(t)))

NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk153.js')
tmp.write_text(js, encoding='utf-8')
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
