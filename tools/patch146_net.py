# -*- coding: utf-8 -*-
"""补丁 146：恢复联机入口 + 状态快照上报
   ① 主菜单加回「局域网联机」按钮
   ② 新增 buildSnapshot() / pushSnapshot()，在 renderAll 末尾节流上报
"""
import pathlib, os, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
t = IDX.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ---------- ① 主菜单按钮 ----------
sub("""        <button class="mbtn" id="mRules">📖 规则</button>
        <!-- 联机模式暂时下线（入口已移除） -->""",
"""        <button class="mbtn" id="mRules">📖 规则</button>
        <button class="mbtn" id="mNet">🌐 局域网联机</button>""",
'① 主菜单加联机按钮')

# ---------- ② 绑定 ----------
sub("""on('mStart', ()=>{ sfx.click(); showScreen('screen-start'); });""",
"""on('mStart', ()=>{ sfx.click(); showScreen('screen-start'); });
on('mNet', ()=>{ sfx.click(); showScreen('screen-net'); netRefresh(); });""",
'② 绑定 mNet')

# ---------- ③ 快照函数（插在 renderAll 之前） ----------
SNAPSHOT_FN = r"""
/* =========================================================================
   联机对局快照：把当前局面压成 JSON 上报给服务器
   —— 给外部（QQ 机器人 / 观战者）读，不需要截图
   ========================================================================= */
function buildSnapshot(){
  try{
    if(!G) return null;
    const me = (typeof human==='function') ? human() : G.players[0];
    const logEl = document.getElementById('log');
    let lastLog = [];
    if(logEl && logEl.children){
      lastLog = Array.prototype.slice.call(logEl.children, -10)
        .map(d=>String(d.textContent||'').replace(/\s+/g,' ').trim()).filter(Boolean);
    }
    return {
      ts: Date.now(),
      round: G.round,
      over: !!G.over,
      mode: gameMode,
      apPerWin,
      started: !!(Net && Net.started),
      you: me ? me.name : null,
      players: G.players.map(p=>({
        name: p.name,
        hp: Math.round((p.hp||0)*10)/10,
        ap: p.ap||0,
        prog: PROG_NAME[p.prog] || '',
        weapon: (ITEMS[p.weapon||'fist']||{}).name || '一拳',
        armor: (p.armor && p.armorCharges>0) ? (((ITEMS[p.armor]||{}).name||'')+'('+p.armorCharges+')') : '',
        isHuman: !!p.isHuman,
        team: p.team,
        alive: !!p.alive,
        dist: (me && p!==me) ? distanceBetween(me, p) : null,
      })),
      lastLog,
    };
  }catch(e){ return null; }
}

let __snapLast = 0, __snapTimer = null;
function pushSnapshot(){
  try{
    if(!Net || !Net.active || !Net.code) return;      /* 单机模式直接跳过 */
    const now = Date.now();
    if(now - __snapLast < 800){                        /* 节流：每 800ms 最多一次 */
      if(!__snapTimer){
        __snapTimer = setTimeout(()=>{ __snapTimer = null; pushSnapshot(); }, 800);
      }
      return;
    }
    __snapLast = now;
    const snap = buildSnapshot();
    if(!snap) return;
    fetch('/api/room/' + Net.code + '/snapshot', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ id: Net.youId, snap }),
    }).catch(()=>{});
  }catch(e){}
}

"""
sub("function renderAll(){", SNAPSHOT_FN + "function renderAll(){", '③ 插入快照函数')

# ---------- ④ 在 renderAll 末尾调用 pushSnapshot ----------
i = t.find('function renderAll(')
if i < 0:
    notes.append('  ! ④ 找不到 renderAll')
else:
    # 花括号配对找函数结尾
    depth = 0; started = False; end = None
    for k in range(i, len(t)):
        c = t[k]
        if c == '{': depth += 1; started = True
        elif c == '}':
            depth -= 1
            if started and depth == 0:
                end = k; break
    if end is None:
        notes.append('  ! ④ renderAll 结尾未找到')
    else:
        # 在最后一个 } 之前插入
        before = t[:end].rstrip()
        t = before + "\n  try{ pushSnapshot(); }catch(e){}\n" + t[end:]
        notes.append('  ok ④ renderAll 末尾调用 pushSnapshot')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
print('长度 %d → %d' % (orig, len(t)))

js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk146.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:400])
