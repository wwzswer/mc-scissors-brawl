# -*- coding: utf-8 -*-
"""补丁 113b：设置存取 + 界面开关 + 各处内容门控"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ---------- 存取 ----------
sub("""    localStorage.setItem('mcSettings', JSON.stringify({
      playerName, gameMode, enemyCount, diffKey, autoMode, apPerWin
    }));""",
"""    localStorage.setItem('mcSettings', JSON.stringify({
      playerName, gameMode, enemyCount, diffKey, autoMode, apPerWin, features
    }));""", 'saveSettings 存开关')

sub("""    if(v.apPerWin===1||v.apPerWin===2) apPerWin = v.apPerWin;
  }catch(e){}""",
"""    if(v.apPerWin===1||v.apPerWin===2) apPerWin = v.apPerWin;
    if(v.features && typeof v.features==='object'){
      for(const k of Object.keys(FEATURE_KEYS)) if(k in v.features) features[k] = !!v.features[k];
    }
  }catch(e){}""", 'loadSettings 读开关')

# ---------- UI：设置页开关 ----------
sub("""            <button class="btn small" id="clearProgBtn">🧹 清除进度存档</button>""",
"""            <button class="btn small" id="clearProgBtn">🧹 清除进度存档</button>""", '（定位设置页锚点）')

sub("""          <div style="margin-top:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">""",
"""          <div style="margin-top:14px">
            <div style="font-size:13px;color:var(--txt);margin-bottom:6px"><b>可选内容</b>（取消勾选后该内容不会出现在游戏里）</div>
            <div id="featToggles" style="display:flex;gap:14px;flex-wrap:wrap;font-size:13px"></div>
          </div>
          <div style="margin-top:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">""",
'设置页加入开关容器')

# 渲染开关（放在 syncSettingUI 之后）
sub("""function syncSettingUI(){""",
"""/* 渲染“可选内容”开关 */
function renderFeatureToggles(){
  const box = document.getElementById('featToggles');
  if(!box) return;
  box.innerHTML = '';
  for(const k of Object.keys(FEATURE_KEYS)){
    const lab = document.createElement('label');
    lab.style.cssText = 'display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = featOn(k);
    cb.onchange = ()=>{
      features[k] = cb.checked;
      saveSettings();
      try{
        log(`⚙️ ${FEATURE_KEYS[k]} 已${cb.checked?'<b>启用</b>':'<b>禁用</b>'}（下局生效，或本局立即作用于未出现的选项）`,'l-sys');
      }catch(e){}
      renderFeatureToggles();
    };
    lab.appendChild(cb);
    const sp = document.createElement('span');
    sp.textContent = FEATURE_KEYS[k];
    lab.appendChild(sp);
    box.appendChild(lab);
  }
}
function syncSettingUI(){
  renderFeatureToggles();""", 'renderFeatureToggles')

# ---------- 门控：商店物品 ----------
sub("""      const collectList = Object.keys(ITEMS).filter(k=>{
        const it=ITEMS[k];
        if(it.prog>p.prog || it.build) return false;""",
"""      const blocked = (k)=> (k==='god_apple' && !featOn('god_apple')) || (k==='tnt' && !featOn('tnt'));
      const collectList = Object.keys(ITEMS).filter(k=>{
        const it=ITEMS[k];
        if(blocked(k)) return false;
        if(it.prog>p.prog || it.build) return false;""", '商店：收集组门控')

sub("""      const consumList = Object.keys(ITEMS).filter(k=>{
        const it=ITEMS[k];
        if(it.prog>p.prog || it.build) return false;""",
"""      const consumList = Object.keys(ITEMS).filter(k=>{
        const it=ITEMS[k];
        if(blocked(k)) return false;
        if(it.prog>p.prog || it.build) return false;""", '商店：补给组门控')

sub("""      const buildList = Object.keys(ITEMS).filter(k=>{
        const it=ITEMS[k];
        if(it.prog>p.prog || !it.build) return false;""",
"""      const buildList = Object.keys(ITEMS).filter(k=>{
        const it=ITEMS[k];
        if(k==='pyramid' && !featOn('tnt') && !featOn('god_apple')) return false;
        if(it.prog>p.prog || !it.build) return false;""", '商店：建筑组门控（金字塔）')

# ---------- 门控：行动选项 ----------
sub("""    if(hasItem(p,'god_apple')) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,""",
"""    if(hasItem(p,'god_apple') && featOn('god_apple')) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,""",
'选项：金苹果门控（人类）')
sub("""    if(hasItem(p,'god_apple') && p.hp<=2.5) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,label:'金苹果'});""",
"""    if(hasItem(p,'god_apple') && p.hp<=2.5 && featOn('god_apple')) push({type:'eat',item:'god_apple',targetId:p.id,cost:CONSUME_COST,label:'金苹果'});""",
'选项：金苹果门控（AI）')

# TNT 相关选项
for old, new, lb in [
  ("""      push({type:'tnt_detonate',cost:ATK_COST,label:`💥 引爆 ${P(p.flags.tntOn).name} 头上的 TNT（1 AP）`});""",
   """      if(featOn('tnt')) push({type:'tnt_detonate',cost:ATK_COST,label:`💥 引爆 ${P(p.flags.tntOn).name} 头上的 TNT（1 AP）`});""",
   '选项：TNT 引爆（人类）'),
  ("""      push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:`🧨 把 TNT 黏在 ${e.name} 头上（1 AP，需 0 格）`, needDist0:true});""",
   """      if(featOn('tnt')) push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:`🧨 把 TNT 黏在 ${e.name} 头上（1 AP，需 0 格）`, needDist0:true});""",
   '选项：TNT 粘贴（人类）'),
  ("""      push({type:'tnt_detonate',cost:ATK_COST,label:'引爆 TNT'});""",
   """      if(featOn('tnt')) push({type:'tnt_detonate',cost:ATK_COST,label:'引爆 TNT'});""",
   '选项：TNT 引爆（AI）'),
  ("""      push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:'贴 TNT'});""",
   """      if(featOn('tnt')) push({type:'tnt_place',targetId:e.id,cost:ATK_COST,label:'贴 TNT'});""",
   '选项：TNT 粘贴（AI）'),
]:
    sub(old, new, lb)

# 药水选项
sub("""    if(hasItem(p,'potion_heal'))  push({type:'potion',item:'potion_heal',cost:0,label:'🧪 治疗药水（+2 血）'});
    if(hasItem(p,'potion_str'))   push({type:'potion',item:'potion_str',cost:0,label:'🧪 力量药水（2 回合物理 +1）'});
    if(hasItem(p,'potion_swift')) push({type:'potion',item:'potion_swift',cost:0,label:'🧪 迅捷药水（+2 AP）'});""",
"""    if(hasItem(p,'potion_heal') && featOn('potion'))  push({type:'potion',item:'potion_heal',cost:0,label:'🧪 治疗药水（+2 血）'});
    if(hasItem(p,'potion_str') && featOn('potion'))   push({type:'potion',item:'potion_str',cost:0,label:'🧪 力量药水（2 回合物理 +1）'});
    if(hasItem(p,'potion_swift') && featOn('potion')) push({type:'potion',item:'potion_swift',cost:0,label:'🧪 迅捷药水（+2 AP）'});""",
'选项：药水门控（人类）')
sub("""    if(hasItem(p,'potion_heal') && p.hp<=2) push({type:'potion',item:'potion_heal',cost:0,label:'治疗药水'});
    if(hasItem(p,'potion_str')) push({type:'potion',item:'potion_str',cost:0,label:'力量药水'});
    if(hasItem(p,'potion_swift') && p.slotsLeft<=0 && p.ap<=1) push({type:'potion',item:'potion_swift',cost:0,label:'迅捷药水'});""",
"""    if(hasItem(p,'potion_heal') && p.hp<=2 && featOn('potion')) push({type:'potion',item:'potion_heal',cost:0,label:'治疗药水'});
    if(hasItem(p,'potion_str') && featOn('potion')) push({type:'potion',item:'potion_str',cost:0,label:'力量药水'});
    if(hasItem(p,'potion_swift') && p.slotsLeft<=0 && p.ap<=1 && featOn('potion')) push({type:'potion',item:'potion_swift',cost:0,label:'迅捷药水'});""",
'选项：药水门控（AI）')

# 药水来源：女巫小屋
sub("""      if(k==='witchhut'){""",
"""      if(k==='witchhut' && featOn('potion')){""", '女巫小屋门控')

# 不死图腾：府邸 + 死亡复活的判定
sub("""      if(k==='mansion'){
        if(G.players.some(q=>q.mem.totem)) log('（不死图腾全局仅 1 个，已被取走）','l-sys');
        else { p.mem.totem=true; log('🗿 取得 <b>不死图腾</b>：倒下时复活并回复 2 生命（全局唯一）。','l-good'); }""",
"""      if(k==='mansion'){
        if(!featOn('totem')) log('（不死图腾已在设置中禁用）','l-sys');
        else if(G.players.some(q=>q.mem.totem)) log('（不死图腾全局仅 1 个，已被取走）','l-sys');
        else { p.mem.totem=true; log('🗿 取得 <b>不死图腾</b>：倒下时复活并回复 2 生命（全局唯一）。','l-good'); }""",
'不死图腾门控（府邸）')

sub("""function killPlayer(p){
  if(p.mem.totem){""",
"""function killPlayer(p){
  if(p.mem.totem && featOn('totem')){""", '不死图腾门控（复活）')

# 金字塔两个选项也要门控
sub("""    if(p.buildings.pyramid && p.ap>=1){""",
"""    if(p.buildings.pyramid && p.ap>=1 && (featOn('tnt') || featOn('god_apple'))){""",
'金字塔选项门控')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))

back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  长度 {orig} → {len(back)}（+{len(back)-orig}）')
for n, k in [('开关变量','const FEATURE_KEYS'),
             ('存取','apPerWin, features'),
             ('界面','renderFeatureToggles'),
             ('金苹果门控','featOn(\'god_apple\')'),
             ('TNT门控','featOn(\'tnt\')'),
             ('药水门控','featOn(\'potion\')'),
             ('图腾门控','featOn(\'totem\')')]:
    print(f'  {n}:', k in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
