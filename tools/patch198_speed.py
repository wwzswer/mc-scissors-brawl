import io

p = 'index.html'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label):
    global s
    assert old in s, '锚点不存在: ' + label
    s = s.replace(old, new, 1)
    print('  ok', label)

# ================= 1) 联机时整体加速：动画时间减半、阶段不再等点击 =================
sub("""async function startGame(){
  loadSettings();""",
    """async function startGame(){
  loadSettings();
  /* 联机对局把节奏调快：等待对方时已经耗掉不少时间，别再把动画拖长 */
  if(typeof Net !== 'undefined' && Net && Net.active){
    try{
      ANIM.judgmentMs = 320;
      for(const k of Object.keys(ANIM.wait)) ANIM.wait[k] = Math.max(60, Math.round(ANIM.wait[k] * 0.4));
    }catch(e){}
  }""",
    '联机加速动画')

# waitClick 在联机里自动继续（800ms 后点掉），不用人守着点
sub("""function waitClick(label, opts){
  const o = opts || {};
  return new Promise(res=>{""",
    """function waitClick(label, opts){
  const o = opts || {};
  /* 联机时不再等人点：1 秒后自动继续（否则另一端会白等一个"继续"） */
  if(typeof netIsOn === 'function' && netIsOn()){
    return sleep(900);
  }
  return new Promise(res=>{""",
    '联机自动继续')

# ================= 2) 提问超时缩短 + 超时用默认值继续 =================
sub("""const NET_ASK_TIMEOUT = 180000;""",
    """const NET_ASK_TIMEOUT = 20000;      /* 等远端 20 秒，超时就用默认动作继续（房主权威，不会失步） */
const netPlans = {};                 /* 远端一次交来的"整回合计划"：seatId -> [选项id/序号/标签] */""",
    '超时 20s + 计划表')

sub("""async function netAskRps(p){
  const ans = await netAskSeat(p, 'rps', [
    {id:'rock',     label:'✊ 石头', move:'rock'},
    {id:'scissors', label:'✌️ 剪刀', move:'scissors'},
    {id:'paper',    label:'✋ 布',   move:'paper'},
  ]);
  setNetWaitHint('');
  return (ans && ans.move) || null;
}""",
    """async function netAskRps(p){
  const ans = await netAskSeat(p, 'rps', [
    {id:'rock',     label:'✊ 石头', move:'rock'},
    {id:'scissors', label:'✌️ 剪刀', move:'scissors'},
    {id:'paper',    label:'✋ 布',   move:'paper'},
  ]);
  setNetWaitHint('');
  if(!ans){ log(`⏱ ${lname(p)} 没在 20 秒内出拳，先按石头算（他还能在行动阶段补操作）。`, 'l-warn'); return 'rock'; }
  /* 她可以顺便把这一回合的行动计划一起交上来，省掉后面的来回 */
  if(Array.isArray(ans.plan) && ans.plan.length) netPlans[p.seatId] = ans.plan.slice();
  return ans.move || 'rock';
}
/* 按"整回合计划"一口气执行；遇到做不了的条目就跳过 */
async function netApplyPlan(p, plan){
  let done = 0;
  for(const raw of plan){
    if(!p.alive || G.over || p.turnSpent >= 8 || done >= 12) break;
    const key = String(raw == null ? '' : raw).trim();
    if(!key) continue;
    if(/^(pass|跳过|结束|结束行动)$/i.test(key)){ log(`⏭ ${lname(p)} 按计划结束行动。`, 'l-sys'); return true; }
    const list = netOptionList(p);
    const byId = list.find(x => x.id === key);
    const idx = Number(key);
    const byIdx = (Number.isFinite(idx) && idx >= 1 && idx <= list.length) ? list[idx-1] : null;
    const byLabel = list.find(x => String(x.label).includes(key));
    const item = byId || byIdx || byLabel;
    if(!item){ log(`（计划里的「${key}」现在做不了，跳过）`, 'l-warn'); continue; }
    try{
      if(item.shop){
        if(item.shop.type === 'armorPriority') setArmorPriority(p, item.shop.key);
        else applyShopAction(p, item.shop);
      }else{
        await runAction(p, item.opt);
      }
      done++;
    }catch(e){ log('（计划执行出错：' + (e && e.message) + '）', 'l-warn'); }
    renderAll();
  }
  return true;
}""",
    'rps 带计划 + 计划执行')

sub("""async function netRemoteTurn(p){
  let guard = 0;
  const avoid = new Set();       /* 试过但做不成的选项，别让它无限重问 */""",
    """async function netRemoteTurn(p){
  /* 已经拿到"整回合计划"：一次执行完，不用再问（这是省时间的关键） */
  const plan = netPlans[p.seatId];
  if(plan && plan.length){
    delete netPlans[p.seatId];
    const okPlan = await netApplyPlan(p, plan);
    if(okPlan){ log(`⚡ ${lname(p)} 用了预先排好的行动序列。`, 'l-sys'); return true; }
  }
  let guard = 0;
  const avoid = new Set();       /* 试过但做不成的选项，别让它无限重问 */""",
    '远端回合优先用计划')

sub("""    const ans = await netAskSeat(p, 'act', list);
    setNetWaitHint('');
    if(!ans){ log(`⌛ ${lname(p)} 太久没回应，跳过他的行动。`, 'l-warn'); return false; }""",
    """    const ans = await netAskSeat(p, 'act', list);
    setNetWaitHint('');
    if(!ans){ log(`⏱ ${lname(p)} 20 秒没回应，这一回合的行动跳过。`, 'l-warn'); return true; }""",
    '行动超时默认结束')

# 行动提问里也接受 plan（后续条目）
sub("""    if(ans.pass) return true;
    const item = list.find(x=>x.id === ans.id) || all.find(x=>x.id === ans.id);""",
    """    if(ans.pass) return true;
    if(Array.isArray(ans.plan) && ans.plan.length){
      netPlans[p.seatId] = ans.plan.slice();
      return true;                       /* 下一圈会走 netApplyPlan */
    }
    const item = list.find(x=>x.id === ans.id) || all.find(x=>x.id === ans.id);""",
    '行动里接收 plan')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch 加速: %d -> %d bytes' % (n0, len(s)))
