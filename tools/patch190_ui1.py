import io

p = 'index.html'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label):
    global s
    assert old in s, '锚点不存在: ' + label
    s = s.replace(old, new, 1)
    print('  ok', label)

# ---------------- 1) CSS：返回键 / 悬浮球 / 手机双栏+瘦身 / 结算面板 ----------------
CSS_ANCHOR = """/* ---- 手机 / 窄屏适配 ---- */"""
NEW_CSS = """/* ---- 左上角返回键 ---- */
.backbtn{position:fixed;left:10px;top:calc(8px + env(safe-area-inset-top));z-index:9990;
  width:38px;height:38px;border-radius:12px;border:1px solid var(--line);
  background:rgba(27,33,48,.94);color:var(--txt);font-size:22px;line-height:1;cursor:pointer;
  display:flex;align-items:center;justify-content:center;box-shadow:0 6px 18px rgba(0,0,0,.45);
  -webkit-tap-highlight-color:transparent}
.backbtn:active{background:#2b3550}
@media (min-width:761px){ .backbtn{left:14px;top:14px;width:40px;height:40px} }

/* ---- 右下角悬浮球 + 行动抽屉 ---- */
.fab{position:fixed;right:12px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:9991;
  width:56px;height:56px;border-radius:50%;border:1px solid #3fa872;cursor:pointer;
  background:linear-gradient(180deg,#2f7d55,#205c3d);color:#eafff5;font-size:26px;line-height:1;
  display:flex;align-items:center;justify-content:center;box-shadow:0 10px 28px rgba(0,0,0,.55);
  -webkit-tap-highlight-color:transparent;transition:transform .12s}
.fab:active{transform:scale(.94)}
.fab.attn{box-shadow:0 0 0 3px rgba(110,231,168,.55),0 10px 28px rgba(0,0,0,.55);animation:fabPulse 1.4s infinite}
@keyframes fabPulse{0%,100%{box-shadow:0 0 0 2px rgba(110,231,168,.35),0 10px 28px rgba(0,0,0,.55)}
  50%{box-shadow:0 0 0 6px rgba(110,231,168,.15),0 10px 28px rgba(0,0,0,.55)}}
.fabsheet{position:fixed;right:12px;bottom:calc(80px + env(safe-area-inset-bottom));z-index:9992;
  width:min(440px,calc(100vw - 24px));max-height:min(66vh,560px);overflow:auto;display:none;
  background:linear-gradient(180deg,#1b2130,#151a22);border:1px solid var(--acc);border-radius:16px;
  padding:10px 12px 14px;box-shadow:0 18px 50px rgba(0,0,0,.65)}
.fabsheet.open{display:block}
.fabsheet .fshead{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;
  position:sticky;top:-10px;background:linear-gradient(180deg,#1b2130,#1b2130);padding:4px 0;z-index:2}
.fabsheet .fshead b{font-size:13px;color:var(--acc)}
#fabSheetBody .actionbar{min-height:0}
#fabSheetBody .tabs{margin-bottom:6px}

/* ---- 结算面板：上方悬浮、不占满、右上角关闭 ---- */
#overlay.settle{align-items:flex-start;justify-content:center;padding:max(20px,env(safe-area-inset-top)) 10px 20px;
  overflow:auto}
#overlay .box.settlebox{max-width:720px;width:min(720px,calc(100vw - 20px));max-height:86vh;overflow:auto;
  text-align:left;padding:16px 18px 14px;position:relative;border-color:var(--acc)}
.sp-close{position:absolute;right:8px;top:6px;width:32px;height:32px;border-radius:9px;border:1px solid var(--line);
  background:#1b2230;color:var(--txt);font-size:16px;line-height:1;cursor:pointer}
.sp-close:active{background:#2b3550}
.sp-row{display:flex;justify-content:space-between;gap:10px;padding:5px 2px;border-bottom:1px dashed #1b2231;font-size:13px}
.sp-row .k{color:var(--dim)}
.sp-row .v{font-weight:700;text-align:right}
.sp-badge{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;background:#243a2c;color:#9df3c4;margin-right:6px}

/* ---- 手机 / 窄屏适配 ---- */"""
sub(CSS_ANCHOR, NEW_CSS, 'CSS 新增组件')

# 手机端：更紧凑 + 左右双栏
OLD_MOBILE_TAIL = """@media (max-width:420px){
  .btn.rps{padding:13px 10px;min-width:0;flex:1 1 30%}
  .reveal{font-size:32px;gap:10px}
  h1{font-size:16.5px}
}"""
NEW_MOBILE_TAIL = """@media (max-width:420px){
  .btn.rps{padding:11px 8px;min-width:0;flex:1 1 30%;font-size:15px}
  .reveal{font-size:26px;gap:8px;min-height:44px}
  h1{font-size:16px}
}

/* ===== 手机版：整体瘦身 + 左右两栏（左=玩家，右=日志），操作全进悬浮球 ===== */
@media (max-width:760px){
  #app{padding-top:44px}
  body{padding:6px 6px calc(10px + env(safe-area-inset-bottom))}
  h1{font-size:15.5px;margin:2px 0 0}
  h1 .mono{font-size:10.5px;margin-top:1px}
  .sub{font-size:11.5px;margin-bottom:8px;line-height:1.6}
  .card{padding:8px;border-radius:11px;margin-bottom:6px}
  .sec{font-size:10.5px;margin:0 0 5px;letter-spacing:1px}
  .pill{font-size:10.5px;padding:1px 6px;margin:1px 3px 1px 0}
  .btn{padding:8px 10px;font-size:13px;border-radius:9px}
  .btn.small{padding:6px 9px;font-size:12px;border-radius:8px}
  .mbtn{font-size:15px;padding:11px 13px}

  /* 游戏界面：两栏 */
  #game{display:grid;grid-template-columns:1fr 1fr;column-gap:6px;align-items:start}
  #game > .card:nth-child(1){grid-column:1/-1}
  #game > .players{grid-column:1;grid-row:2;grid-template-columns:1fr;gap:6px;margin-bottom:0}
  #game > .card:nth-child(3){display:none}                /* 行动区 → 悬浮球 */
  #game > .row:nth-child(4){grid-column:2;grid-row:2;display:block;margin:0}
  #game > .row:nth-child(4) > .card{gap:0;margin-bottom:6px}
  #game > .row:nth-child(4) > .card:nth-child(2){display:none}  /* 速查收起 */

  /* 玩家卡片瘦一点 */
  .pcard{padding:7px 8px;border-radius:10px}
  .pcard .head{gap:5px;margin-bottom:4px}
  .pcard .name{font-size:12.5px}
  .tag{font-size:9.5px;padding:1px 5px}
  .tchip{font-size:9.5px;padding:0 5px}
  .hpbar{height:9px;margin:2px 0 4px}
  .stat{font-size:10.5px;gap:1px 6px}
  .stat .v span[style]{font-size:10px !important}
  .progline{font-size:10px}
  .pcard .legend{font-size:10px !important}
  #log{height:auto;max-height:52vh;font-size:10.5px;line-height:1.45;padding:6px 7px;border-radius:9px}
  #log div{padding:1px 0}
  #rpsArea{padding:2px 0;gap:6px}
  .reveal{font-size:28px;gap:10px;min-height:46px}
  #rpsStatus{font-size:11px}
  .btn.rps{font-size:14px;padding:10px 8px;min-width:0;flex:1 1 30%}
  .slot{width:52px;height:52px}
  #overlay .box{padding:12px 14px;border-radius:14px}
}"""
sub(OLD_MOBILE_TAIL, NEW_MOBILE_TAIL, '手机端布局重写')

# ---------------- 2) HTML：返回键 / 继续上局 / 悬浮球 ----------------
sub("""<div id="app">""",
    """<button id="backBtn" class="backbtn hidden" aria-label="返回">‹</button>
<div id="app">""",
    '返回键 DOM')

sub("""        <button class="mbtn" id="mStart">▶ 开始游戏</button>""",
    """        <button class="mbtn" id="mStart">▶ 开始游戏</button>
        <button class="mbtn hidden" id="mResume">⏵ 继续上次对局</button>""",
    '继续上局按钮')

sub("""<div id="overlay" class="hidden"><div class="box" id="overlayBox"></div></div>""",
    """<div id="overlay" class="hidden"><div class="box" id="overlayBox"></div></div>
<!-- 右下角悬浮球：手机端把所有行动/制作/收集塞进这里 -->
<button id="fab" class="fab hidden" aria-label="行动面板">＋</button>
<div id="fabSheet" class="fabsheet">
  <div class="fshead"><b>⚔ 行动 · 制作 · 收集</b><button class="btn small" id="fabClose">✕</button></div>
  <div id="fabSheetBody"></div>
</div>""",
    '悬浮球 DOM')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch1 完成: %d -> %d bytes' % (n0, len(s)))
