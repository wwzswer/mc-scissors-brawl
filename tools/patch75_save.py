# -*- coding: utf-8 -*-
"""补丁 75：
   ① 版本号显示（方便确认浏览器是否加载了最新文件）
   ② 设置页加「清除进度存档」按钮 —— 解决“开局就带着上次的进程进度”问题
   ③ 开局日志显示当前进程来源（新档/存档），避免误解
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ① 版本号
sub("const GAME_VERSION = '0.9';", "const GAME_VERSION = '1.0';", '版本常量')
# 若没有该常量则新增
if 'const GAME_VERSION' not in t:
    sub("const SPRITE_CELL = 96;", "const SPRITE_CELL = 96;\nconst GAME_VERSION = '1.0';\nconst BUILD_TAG = 'rps-multi-winner+armor-priority';", '新增版本常量')

# 顶部标题带版本 + 构建标记（用户可据此确认是否最新）
sub("""方块猜拳战场 <span style="font-size:12px;color:var(--dim)">MC 二创桌游 · 基础版 v0.9</span>""",
"""方块猜拳战场 <span style="font-size:12px;color:var(--dim)">MC 二创桌游 · 基础版 v<span id="verNum">1.0</span> <span id="buildTag" style="opacity:.7"></span></span>""",
'顶部版本显示')

# ② 设置页加清除存档按钮
sub("""🌐 局域网联机模式暂时下线（正在改造中），当前为纯单机版本。</div>""",
"""🌐 局域网联机模式暂时下线（正在改造中），当前为纯单机版本。</div>
          <div style="margin-top:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            <button class="btn small" id="clearProgBtn">🧹 清除进度存档</button>
            <span id="progInfo" style="font-size:12px;color:var(--dim)"></span>
          </div>
          <div style="margin-top:6px;font-size:11.5px;color:var(--dim)">
            说明：进程进度与物品进度会按“玩家名称”保存在本机。想重新从空手开始，点上面的按钮清空即可。
          </div>""", '设置页清除存档按钮')

# ③ 清除存档逻辑
sub("""on('mSetting', ()=>{""",
"""/* 清除本机的进度存档（进程点 / 物品进度） */
function refreshProgInfo(){
  const el = document.getElementById('progInfo');
  if(!el) return;
  try{
    const prog = JSON.parse(localStorage.getItem('mcProg') || '{}');
    const item = JSON.parse(localStorage.getItem('mcItemProg') || '{}');
    const n = Object.keys(prog).length + Object.keys(item).length;
    el.textContent = n ? `（当前有 ${Object.keys(prog).length} 份进程存档 / ${Object.keys(item).length} 份物品存档）` : '（暂无存档）';
  }catch(e){ el.textContent = ''; }
}
on('clearProgBtn', ()=>{
  try{ sfx.click(); }catch(e){}
  localStorage.removeItem('mcProg');
  localStorage.removeItem('mcItemProg');
  refreshProgInfo();
  log('🧹 已清除本机的进度存档（下次开局从空手开始）。','l-good');
  alert('已清除进度存档：下次开局所有玩家都从「空手」开始。');
});
on('mSetting', ()=>{""", '清除存档逻辑')

# 打开设置页时刷新存档信息
sub("""showScreen('screen-setting');""",
"""showScreen('screen-setting'); refreshProgInfo();""", '打开设置刷新存档信息')

# ④ 开局日志标注进程来源
sub("""    const saved = progLoad(p.name);
    if(saved){ p.prog=saved.prog; p.progPts=saved.pts; }""",
"""    const saved = progLoad(p.name);
    if(saved && (saved.prog>0 || saved.pts>0)){
      p.prog=saved.prog; p.progPts=saved.pts;
      p.fromSave = true;                       /* 标记：进程来自存档 */
    }""", '标记进程来自存档')

sub("""    log(`进程（进度点制）：${chain}；每投入 1 步点亮 1 个小点，进度会保存。`,'l-sys');""",
"""    log(`进程（进度点制）：${chain}；每投入 1 步点亮 1 个小点，进度会保存。`,'l-sys');
    const fromSave = players.filter(p=>p.fromSave);
    if(fromSave.length){
      log(`📂 本局有 ${fromSave.length} 名玩家沿用了上次的进度存档：` +
          fromSave.map(p=>`${lname(p)}=${PROG_NAME[p.prog]}(${p.progPts}点)`).join('、') +
          `（想从空手开始，可在「设置」里点“清除进度存档”）`,'l-warn');
    }""", '开局提示存档沿用')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
