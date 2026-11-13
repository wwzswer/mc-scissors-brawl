# -*- coding: utf-8 -*-
"""补丁 147：server.js 加对局快照
   POST /api/room/:code/snapshot  —— 网页端上报局面（需在房间内）
   GET  /api/room/:code/peek      —— 凭房间码只读查看（QQ 机器人/观战，不需要 id）
"""
import pathlib, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
P = D / 'server.js'
t = P.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ① 路由正则加两个子路由
sub(r"const m = p.match(/^\/api\/room\/([A-Z0-9]{9})\/(join|ready|start|state|events|action|stream|leave)$/);",
    r"const m = p.match(/^\/api\/room\/([A-Z0-9]{9})\/(join|ready|start|state|events|action|stream|leave|snapshot|peek)$/);",
    '① 路由正则')

# ② peek：公开只读，必须放在 id 校验之前
sub("""      const id = new URL(url, 'http://x').searchParams.get('id') || body.id;""",
"""      /* ---- 凭房间码只读查看（QQ 机器人 / 观战者用，不需要 id）---- */
      if(sub === 'peek' && req.method === 'GET'){
        r.touched = now();
        return json(res, {
          ok: true,
          code: r.code,
          mode: r.mode,
          apPerWin: r.apPerWin,
          started: r.started,
          seats: roomView(r, null).seats,
          snapshot: r.snapshot || null,
          updatedAt: r.snapshotAt || 0,
        });
      }
      const id = new URL(url, 'http://x').searchParams.get('id') || body.id;""",
'② peek 路由')

# ③ snapshot：网页端上报（在 seat 校验之后，替换 events 前的插入点）
sub("""      if(sub === 'ready' && req.method === 'POST'){""",
"""      if(sub === 'snapshot' && req.method === 'POST'){
        /* 网页端上报当前局面；只存不算状态变更，不推版本（避免干扰客户端轮询） */
        r.snapshot = body.snap || null;
        r.snapshotAt = now();
        r.touched = now();
        return json(res, { ok:true });
      }
      if(sub === 'ready' && req.method === 'POST'){""",
'③ snapshot 上报路由')

P.write_text(t, encoding='utf-8')
print('\n'.join(notes))
print('长度 %d → %d' % (orig, len(t)))

NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(P)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
