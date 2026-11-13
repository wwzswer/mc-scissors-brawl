# -*- coding: utf-8 -*-
"""补丁 67：
   ① 进程独立成大按钮「⬆️ 进程」，不再混在攻击/收集栏里
   ② 铁傀儡被动放宽条件：只要装备铁傀儡，每回合可用一次（不再要求“本回合已行动过”）
   ③ 行动面板分类说明同步更新
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

# ---------- ① 进程独立成大按钮 ----------
sub("""    addRow('🎒 收集 / 补给', others, '腐肉、面包、水、切换工具等');
    addRow('📏 距离', moves, '走位 1 格 = 1 步；末影珍珠 ±2；钓鱼竿可拉人');
    addRow('⚔️ 攻击', attacks, '近战需 0 格；判定平手会一直重出');
    addRow('🔧 升级', ups, '铁砧修复护甲与附魔');

    const row3=document.createElement('div'); row3.className='actions';
    for(const o of shopBtns){
      const b=document.createElement('button');
      b.className='btn small pri';
      b.textContent=o.label;
      b.disabled = (o.type==='shop_progress') ? !canShow(p,o) : false;
      b.onclick=()=>""",
"""    /* 进程单独一行，独立于其它分类 */
    const progBtn = document.createElement('div');
    progBtn.className = 'progwrap';
    const pb = document.createElement('button');
    pb.className = 'btn prog';
    const cur = PROG_NAME[p.prog];
    const nxt = PROG_NAME[p.prog+1];
    pb.innerHTML = progMaxed(p)
      ? `⬆️ 进程：${cur}（已满级）`
      : `⬆️ 进程：${cur} → ${nxt}　${Math.min(progProgress(p)+1, progNeed(p))}/${progNeed(p)} 点　（1 AP）`;
    pb.disabled = !canShow(p, {type:'shop_progress'});
    pb.onclick = ()=>{
      if(p.ap<1 || progMaxed(p)) return;
      applyShopAction(p, {type:'upgrade'});
      render(); renderAll();
    };
    progBtn.appendChild(pb);
    bar.appendChild(progBtn);

    addRow('📏 距离', moves, '走位 1 格 = 1 步；末影珍珠 ±2；钓鱼竿可拉人');
    addRow('⚔️ 攻击', attacks, '近战需 0 格；判定平手会一直重出');
    addRow('🔧 升级', ups, '铁砧修复护甲与附魔');
    addRow('🎒 收集 / 补给', others, '腐肉、面包、水、切换工具等');

    const row3=document.createElement('div'); row3.className='actions';
    for(const o of shopBtns){
      if(o.type==='shop_progress') continue;        /* 进程已单独成按钮 */
      const b=document.createElement('button');
      b.className='btn small pri';
      b.textContent=o.label;
      b.disabled = false;
      b.onclick=()=>""",
'进程独立按钮')

# ---------- ② 铁傀儡被动放宽 ----------
sub("""  if(armorActive(p) && p.armor==='golem' && p.actionsUsed>0 && !p.flags.golemUsed){""",
"""  /* 铁傀儡被动：只要装备着铁傀儡，每回合可用一次（行动前或行动后都可以） */
  if(armorActive(p) && p.armor==='golem' && !p.flags.golemUsed){""",
'铁傀儡被动放宽（人类）')

sub("""    if(armorActive(p) && p.armor==='golem' && p.actionsUsed>0 && !p.flags.golemUsed){""",
"""    if(armorActive(p) && p.armor==='golem' && !p.flags.golemUsed){""",
'铁傀儡被动放宽（AI）')

sub("""      push({type:'golem_punch',targetId:e.id,cost:0,isAction:false,label:`🥊 铁傀儡被动：攻击 ${e.name}（免费，不占行动）`});""",
"""      push({type:'golem_punch',targetId:e.id,cost:0,isAction:false,label:`🥊 铁傀儡被动：攻击 ${e.name}（每回合 1 次，免费）`});""",
'铁傀儡被动标签（人类）')

sub("""      push({type:'golem_punch',targetId:e.id,cost:0,isAction:false,label:'铁傀儡攻击（免费）'});""",
"""      push({type:'golem_punch',targetId:e.id,cost:0,isAction:false,label:'铁傀儡攻击（免费）'});""",
'铁傀儡被动标签（AI）')

# ---------- ③ 进程按钮样式 ----------
if '.progwrap{' not in t:
    css = """
.progwrap{margin:8px 0 2px}
.btn.prog{width:100%;text-align:left;font-size:13.5px;padding:10px 14px;
  background:linear-gradient(180deg,rgba(110,231,168,.16),rgba(110,231,168,.06));
  border:1px solid rgba(110,231,168,.45);color:var(--txt)}
.btn.prog:hover:not(:disabled){background:linear-gradient(180deg,rgba(110,231,168,.26),rgba(110,231,168,.12))}
.btn.prog:disabled{opacity:.45;cursor:not-allowed}
"""
    t = t.replace('.hidden{display:none !important}', '.hidden{display:none !important}' + css, 1)
    notes.append('  ok 进程按钮样式')
else:
    notes.append('  - 进程按钮样式已存在')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
