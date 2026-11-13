# -*- coding: utf-8 -*-
"""补丁 2：前端界面改造
   - 新增初始界面：左侧 开始 / 设置 / 规则，右侧 更改名称
   - 设置项：模式(1v1/2v2)、敌方数量、AI 强度、猜拳方式、每次猜拳获胜 AP(1/2)
   - 规则页：分类介绍各类物品与数值
   - 进度点样式、贴图样式
   - 游戏中显示「本回合猜拳获得 AP」与模式
可重复执行（先删旧块再插）。
"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
html = IDX.read_text(encoding='utf-8')

SETUP_BEGIN = '<!-- ===== SETUPUI:BEGIN ===== -->'
SETUP_END   = '<!-- ===== SETUPUI:END ===== -->'
html = re.sub(re.escape(SETUP_BEGIN) + r'.*?' + re.escape(SETUP_END), '', html, flags=re.S)

# ---------------- 1) 初始界面 DOM ----------------
setup_ui = SETUP_BEGIN + """
<div class="card" id="screen-main">
  <div class="row" style="justify-content:space-between;align-items:flex-start;gap:18px">
    <div style="flex:1 1 260px">
      <div class="sec">主菜单</div>
      <div class="vertmenu">
        <button class="mbtn" id="mStart">▶ 开始游戏</button>
        <button class="mbtn" id="mSetting">⚙ 设置</button>
        <button class="mbtn" id="mRules">📖 规则</button>
        <button class="mbtn" id="mNet">🌐 局域网联机</button>
      </div>
    </div>
    <div style="flex:0 0 300px">
      <div class="sec">你的名称</div>
      <div class="card" style="margin:0;background:#141a26">
        <div class="row" style="gap:8px">
          <span id="nameSprite"></span>
          <input id="nameInput" class="txt" maxlength="10" placeholder="输入名称" value="你">
        </div>
        <div class="desc" style="color:var(--dim);font-size:12px;margin-top:8px">
          名称会显示在战斗中，并与“进程进度存档”绑定（换个名字就是新档）。
        </div>
        <div class="row" style="margin-top:8px">
          <button class="btn small pri" id="nameSave">保存名称</button>
          <span id="nameTip" style="color:var(--acc);font-size:12px"></span>
        </div>
      </div>
      <div class="sec" style="margin-top:12px">当前设置</div>
      <div class="legend" id="curSetting"></div>
    </div>
  </div>
</div>

<div class="card hidden" id="screen-start">
  <div class="sec">开始游戏</div>
  <div class="row" style="gap:14px;align-items:flex-start">
    <div style="flex:1 1 320px">
      <div class="legend" style="line-height:2">
        <div><b>模式</b>：<span id="sModeText"></span></div>
        <div><b>AI 强度</b>：<span id="sDiffText"></span></div>
        <div><b>猜拳方式</b>：<span id="sAutoText"></span></div>
        <div><b>猜拳获胜 AP</b>：<span id="sApText"></span></div>
        <div><b>生命</b>：每人 4 点（判定不获得 AP）</div>
      </div>
      <div class="row" style="margin-top:14px">
        <button class="btn pri" id="startBtn">开始对战</button>
        <button class="btn small" id="sBack">返回主菜单</button>
        <button class="btn small" id="sToSetting">去设置</button>
      </div>
    </div>
  </div>
</div>

<div class="card hidden" id="screen-setting">
  <div class="sec">设置</div>
  <div class="row" style="margin-bottom:10px">
    <span style="flex:0 0 132px">游戏模式</span>
    <button class="btn small" data-mode="1v1">1v1（1 名敌人）</button>
    <button class="btn small" data-mode="2v2">2V2（你 + AI 队友 vs 2 敌）</button>
  </div>
  <div class="row" style="margin-bottom:10px" id="enemyRow">
    <span style="flex:0 0 132px">敌方 AI 数量</span>
    <button class="btn small" data-en="1">1 名</button>
    <button class="btn small" data-en="2">2 名</button>
    <button class="btn small" data-en="3">3 名</button>
  </div>
  <div class="row" style="margin-bottom:10px">
    <span style="flex:0 0 132px">AI 强度</span>
    <button class="btn small" data-diff="easy">简单</button>
    <button class="btn small" data-diff="normal">普通</button>
    <button class="btn small" data-diff="hard">困难</button>
  </div>
  <div class="row" style="margin-bottom:10px">
    <span style="flex:0 0 132px">猜拳方式</span>
    <button class="btn small" data-auto="1">自动（推荐）</button>
    <button class="btn small" data-auto="0">我来点</button>
  </div>
  <div class="row" style="margin-bottom:10px">
    <span style="flex:0 0 132px">猜拳获胜 AP</span>
    <button class="btn small" data-ap="2">2 AP / 次</button>
    <button class="btn small" data-ap="1">1 AP / 次</button>
    <span style="color:var(--dim);font-size:12px">（判定与闪避不产生 AP）</span>
  </div>
  <div class="row">
    <button class="btn small pri" id="setBack">返回主菜单</button>
    <span style="color:var(--dim);font-size:12px">设置会自动保存在本机。</span>
  </div>
</div>

<div class="card hidden" id="screen-rules">
  <div class="sec">规则</div>
  <div class="tabs" id="ruleTabs"></div>
  <div id="ruleBody" class="rulebody"></div>
  <div class="row" style="margin-top:12px"><button class="btn small pri" id="rulesBack">返回主菜单</button></div>
</div>

<div class="card hidden" id="screen-net">
  <div class="sec">局域网联机</div>
  <div class="row" style="align-items:flex-start;gap:16px">
    <div style="flex:1 1 300px">
      <div class="legend" style="line-height:1.9">
        <div>1. 在作为“主机”的电脑上运行 <code>start-server.cmd</code>（或 <code>node server.js</code>）</div>
        <div>2. 你和朋友用浏览器打开提示的地址（形如 <code>http://192.168.x.x:8787</code>）</div>
        <div>3. 一人创建房间并把 <b>9 位房间码</b> 告诉朋友，朋友输入房间码加入</div>
        <div>4. 都准备好后由房主开始对局</div>
      </div>
      <div class="row" style="margin-top:12px">
        <input id="roomCode" class="txt" maxlength="9" placeholder="输入 9 位房间码" style="text-transform:uppercase">
        <button class="btn small pri" id="netJoin">加入房间</button>
        <button class="btn small" id="netCreate">创建房间</button>
      </div>
      <div id="netStatus" class="legend" style="margin-top:10px"></div>
    </div>
  </div>
  <div class="row" style="margin-top:12px"><button class="btn small" id="netBack">返回主菜单</button></div>
</div>
""" + SETUP_END

# 替换原来的 setup 卡片
old_setup = re.search(r'<div class="card" id="setup">.*?\n  </div>\n', html, flags=re.S)
assert old_setup, '找不到原 setup 卡片'
html = html[:old_setup.start()] + setup_ui + '\n' + html[old_setup.end():]

# ---------------- 2) 顶部信息条（模式 / 本回合 AP / 进度） ----------------
old_top = """        <div class="row" style="gap:14px">
          <span class="pill on" id="roundPill">回合 1</span>
          <span class="pill" id="phasePill">猜拳阶段</span>
          <span class="pill" id="turnPill"></span>
        </div>"""
new_top = """        <div class="row" style="gap:10px">
          <span class="pill on" id="roundPill">回合 1</span>
          <span class="pill" id="phasePill">猜拳阶段</span>
          <span class="pill" id="turnPill"></span>
          <span class="pill" id="modePill"></span>
          <span class="pill" id="apPill"></span>
        </div>"""
assert old_top in html
html = html.replace(old_top, new_top, 1)

# ---------------- 3) 追加样式 ----------------
extra_css = """
/* ---- 初始界面 ---- */
.vertmenu{display:flex;flex-direction:column;gap:10px;max-width:280px}
.mbtn{appearance:none;border:1px solid var(--line);background:linear-gradient(180deg,#232b3d,#1a2130);
  color:var(--txt);padding:14px 18px;border-radius:12px;font-size:16px;font-weight:700;cursor:pointer;
  text-align:left;transition:.14s;font-family:inherit}
.mbtn:hover{transform:translateX(3px);border-color:var(--acc);background:linear-gradient(180deg,#2b3550,#1f2740)}
.txt{background:#0c1017;border:1px solid var(--line);color:var(--txt);border-radius:9px;
  padding:9px 11px;font-size:14px;font-family:inherit;outline:none;min-width:170px}
.txt:focus{border-color:var(--acc)}
/* ---- 进度点 ---- */
.progdots{display:inline-flex;align-items:center;gap:4px;margin:2px 6px 2px 0}
.progdots .dot{width:11px;height:11px;border-radius:50%;background:#1b2231;border:1px solid var(--line);display:inline-block}
.progdots .dot.on{background:radial-gradient(circle at 35% 30%, #b6ffd8, var(--acc));border-color:var(--acc);
  box-shadow:0 0 7px rgba(110,231,168,.65)}
.progdots b{color:var(--acc);font-size:11.5px;margin-left:3px}
.prognext{color:var(--dim);font-size:11.5px;margin-left:4px}
.progrow{display:flex;align-items:center;gap:4px;margin-top:6px}
.progrow .dot{width:12px;height:12px;border-radius:50%;background:#1b2231;border:1px solid var(--line);display:inline-block}
.progrow .dot.on{background:radial-gradient(circle at 35% 30%, #b6ffd8, var(--acc));border-color:var(--acc);
  box-shadow:0 0 8px rgba(110,231,168,.7)}
.progrow b{color:var(--acc);font-size:12px;margin-left:4px}
/* ---- 规则页 ---- */
.rulebody{max-height:520px;overflow-y:auto;padding-right:6px}
.rulegrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:10px}
.rulecard{background:#141a26;border:1px solid var(--line);border-radius:11px;padding:10px 11px}
.rulecard h4{margin:0 0 6px;font-size:14px;display:flex;align-items:center;gap:8px}
.rulecard .kv{font-size:12.5px;color:var(--dim);line-height:1.65}
.rulecard .kv b{color:var(--txt)}
.tagrow{margin-top:6px}
.pcard.turn{box-shadow:0 0 0 1px var(--acc),0 10px 34px rgba(110,231,168,.18)}
.teamtag{font-size:10.5px;padding:1px 6px;border-radius:5px;background:#243a2c;color:#9df3c4}
.teamtag.foe{background:#3a2430;color:#ffb0c8}
.distrow{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.distchip{background:#141a26;border:1px solid var(--line);border-radius:8px;padding:3px 7px;font-size:11.5px}
.distchip b{color:var(--acc2)}
"""
anchor_css = '.distchip b{color:var(--acc2)}'
if anchor_css not in html:
    html = html.replace('.hidden{display:none !important}', '.hidden{display:none !important}' + extra_css, 1)

IDX.write_text(html, encoding='utf-8')
print(f'UI 补丁完成，文件 {len(html)/1024:.1f} KB')
print('含 screen-main:', 'id="screen-main"' in html, '| 含 ruleTabs:', 'id="ruleTabs"' in html)
