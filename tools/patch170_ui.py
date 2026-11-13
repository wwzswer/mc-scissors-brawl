import io

p = 'index.html'
s = io.open(p, encoding='utf-8').read()

# ---------- 1) Net 增加 kick ----------
anchor = "  leave(){\n    const code = this.code, me = this.youId;"
assert anchor in s
s = s.replace(anchor, """  kick(slot){
    return this.api('/api/room/'+this.code+'/kick', {id:this.youId, slot})
      .then(d=>{ if(d.ok) this.applyRoom(d); else this.status('<span style="color:var(--red)">'+esc(d.err||'操作失败')+'</span>');
        this.renderAll(); return d; }).catch(()=>({ok:false}));
  },
""" + anchor, 1)

# ---------- 2) 联机页面按钮 + 座位事件委托 ----------
old_wire = """on('netCreate', ()=>{ netCreateRoom(); });
on('netJoin', ()=>{ netJoinRoom(); });"""
assert old_wire in s
new_wire = """on('netCreate', ()=>{ netCreateRoom(); });
on('netJoin', ()=>{ netJoinRoom(); });
on('netAddr', ()=>{ netAddrDialog(); });
on('netCopy', ()=>{ copyText(Net.code||''); Net.status('<span style="color:var(--acc)">房间码已复制。</span>'); });
on('netCopyBrief', ()=>{ Net.copyBrief(); });
/* 座位表：点选 / 下拉都走事件委托（重绘后不用重新绑定） */
(function netSeatsDelegation(){
  const box = document.getElementById('netSeats');
  if(!box) return;
  box.addEventListener('click', ev=>{
    const el = ev.target.closest ? ev.target.closest('[data-act]') : null;
    if(!el) return;
    const act = el.getAttribute('data-act');
    const slot = Number(el.getAttribute('data-slot'));
    try{ sfx.click(); }catch(e){}
    if(act === 'fill') Net.fillBot(slot);
    else if(act === 'clear') Net.clearBot(slot);
    else if(act === 'kick') Net.kick(slot);
    else if(act === 'host') Net.transferHost(slot);
  });
  box.addEventListener('change', ev=>{
    const el = ev.target;
    if(!el || !el.getAttribute) return;
    const act = el.getAttribute('data-act');
    if(act !== 'team' && act !== 'diff') return;
    const slot = Number(el.getAttribute('data-slot'));
    if(act === 'team') Net.setTeam(slot, Number(el.value));
    else Net.updateBot(slot, {diff: el.value});
  });
})();"""
s = s.replace(old_wire, new_wire, 1)

# ---------- 3) 进联机页时探测服务 ----------
old_mnet = "on('mNet', ()=>{ sfx.click(); showScreen('screen-net');"
if old_mnet in s:
    s = s.replace(old_mnet, "on('mNet', ()=>{ sfx.click(); showScreen('screen-net'); netRefresh();", 1)

# ---------- 4) 版本检查 + 更新窗口 ----------
anchor2 = "/* =========================================================================\n   PWA：装到桌面 / 开始菜单，像 App 一样打开（离线也能玩单机）"
assert anchor2 in s
VERSION_JS = r'''/* =========================================================================
   版本检查 · 更新窗口
   - 服务器根目录的 version.json 是唯一真相：改版本号就能通知所有客户端
   - 发现更新 → 右下角弹窗（含更新说明）；点「立即更新」清缓存 + 更新 SW + 重载
   ========================================================================= */
const APP_VERSION = '1.7.0';
let __verChecking = false;
function parseVer(v){ return String(v||'0').split(/[.\-+_]/).slice(0,3).map(n=>parseInt(n,10)||0); }
function verNewer(a, b){
  const A = parseVer(a), B = parseVer(b);
  for(let i=0;i<3;i++){ if(A[i] !== B[i]) return A[i] > B[i]; }
  return false;
}
function appToast(msg){
  try{
    let t = document.getElementById('appToast');
    if(!t){
      t = document.createElement('div');
      t.id = 'appToast';
      t.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);bottom:22px;z-index:9999;'+
        'background:#1b2130;border:1px solid var(--line);color:var(--txt);padding:9px 16px;border-radius:999px;'+
        'font-size:13px;box-shadow:0 8px 24px rgba(0,0,0,.5);opacity:0;transition:opacity .2s';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.opacity = '1';
    clearTimeout(appToast._t);
    appToast._t = setTimeout(()=>{ t.style.opacity = '0'; }, 2200);
  }catch(e){}
}
const isAndroidApp = (()=>{ try{ return /appassets\.androidplatform\.net/.test(location.hostname); }catch(e){ return false; } })();
function checkUpdate(manual){
  if(__verChecking) return Promise.resolve(null);
  __verChecking = true;
  const base = (typeof apiBase === 'function' ? apiBase() : '');
  const url = base + '/version.json?t=' + Date.now();
  return fetch(url, {cache:'no-store'})
    .then(r=> r.ok ? r.json() : null)
    .catch(()=>null)
    .then(d=>{
      __verChecking = false;
      if(!d || !d.version){ if(manual) appToast('检查更新失败：拿不到 version.json'); return null; }
      if(verNewer(d.version, APP_VERSION)){ showUpdateDialog(d); return d; }
      if(manual) appToast('已经是最新版本 v' + APP_VERSION);
      return null;
    });
}
function showUpdateDialog(d){
  try{
    if(document.getElementById('updBox')) return;
    const notes = Array.isArray(d.notes) ? d.notes : (d.notes ? [d.notes] : []);
    const box = document.createElement('div');
    box.id = 'updBox';
    box.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:9998;max-width:340px;'+
      'background:linear-gradient(180deg,#1b2130,#151a22);border:1px solid var(--acc);border-radius:14px;'+
      'padding:14px;box-shadow:0 12px 40px rgba(0,0,0,.6);font-size:13px;line-height:1.75';
    box.innerHTML = `
      <div style="font-weight:800;font-size:15px;color:var(--acc);margin-bottom:4px">🚀 有新版本 v${esc(d.version)}</div>
      <div class="legend" style="margin-bottom:6px">当前 v${APP_VERSION}${d.date?(' · '+esc(d.date)):''}</div>
      ${notes.length?('<div style="margin:6px 0 8px">'+notes.map(n=>'· '+esc(n)).join('<br>')+'</div>'):''}
      ${isAndroidApp?('<div style="color:var(--acc2);margin-bottom:8px">手机 App 版：请下载新版安装包覆盖安装。</div>'):''}
      <div class="row" style="gap:8px">
        <button class="btn small pri" id="updNow">立即更新</button>
        <button class="btn small" id="updLater">稍后</button>
      </div>`;
    document.body.appendChild(box);
    const now = document.getElementById('updNow');
    if(now) now.onclick = ()=>{ applyUpdate(); };
    const later = document.getElementById('updLater');
    if(later) later.onclick = ()=>{ box.remove(); };
  }catch(e){}
}
function applyUpdate(){
  const btn = document.getElementById('updNow');
  if(btn){ btn.disabled = true; btn.textContent = '更新中…'; }
  const done = ()=> location.replace(location.pathname + '?upd=' + Date.now());
  if(isAndroidApp){ appToast('请下载新版 APK 覆盖安装'); if(btn){ btn.disabled=false; btn.textContent='立即更新'; } return; }
  Promise.resolve()
    .then(()=> (('caches' in window) ? caches.keys().then(ks=>Promise.all(ks.map(k=>caches.delete(k)))) : null))
    .catch(()=>{})
    .then(()=> (('serviceWorker' in navigator) ? navigator.serviceWorker.getRegistrations()
        .then(rs=>Promise.all(rs.map(r=>r.update().catch(()=>{})))) : null))
    .catch(()=>{})
    .then(()=> setTimeout(done, 250));
}
/* 启动时与每隔 5 分钟检查一次；页面回到前台也查一次 */
(function verAutoCheck(){
  try{
    setTimeout(()=>checkUpdate(false), 2500);
    setInterval(()=>checkUpdate(false), 5 * 60 * 1000);
    document.addEventListener('visibilitychange', ()=>{ if(!document.hidden) checkUpdate(false); });
  }catch(e){}
})();

'''
s = s.replace(anchor2, VERSION_JS + anchor2, 1)

# ---------- 5) 设置页加「检查更新 / 版本」 ----------
old_clear = """          <div style="margin-top:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            <button class="btn small" id="clearProgBtn">🧹 清除进度存档</button>"""
assert old_clear in s
s = s.replace(old_clear, """          <div style="margin-top:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            <button class="btn small" id="checkUpdBtn">🔄 检查更新</button>
            <span id="verInfo" style="font-size:12px;color:var(--dim)"></span>
          </div>
          <div style="margin-top:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            <button class="btn small" id="clearProgBtn">🧹 清除进度存档</button>""", 1)

old_on = "on('clearProgBtn', ()=>{"
assert old_on in s
s = s.replace(old_on, """on('checkUpdBtn', ()=>{ try{ sfx.click(); }catch(e){} checkUpdate(true); });
on('clearProgBtn', ()=>{""", 1)

# ---------- 6) 标题版本号 ----------
s = s.replace('基础版 v1.6.0 · <b id="buildTag" style="color:var(--acc2)">队伍编辑 · 人机 · 可安装</b>',
              '基础版 v1.7.0 · <b id="buildTag" style="color:var(--acc2)">联机座位 · 手机版 · 自动更新</b>')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patched: kick / wiring / version-check / settings / title')
