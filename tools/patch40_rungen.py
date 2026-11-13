# -*- coding: utf-8 -*-
"""补丁 40：修复“重复开局导致旧主循环与新局并存”
   startGame 时把上一局标记为结束并递增 runId；
   gameLoop / actionPhase / endOfRound 每步校验 runId，过期立即退出。
   （这既是健壮性修复，也让重复点“开始对战”不会出现两个循环抢状态）
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

# ① startGame：结束上一局 + 递增 runId
sub("""async function startGame(){
  loadSettings();
  showScreen('game');""",
"""let runSeq = 0;                     /* 每开一局递增，用于让旧循环自动退出 */
async function startGame(){
  loadSettings();
  if(G){ G.over = true; }           /* 结束上一局，旧的主循环会自行退出 */
  runSeq += 1;
  const myRun = runSeq;
  showScreen('game');""",
'startGame 代次')

sub("""  G = { players, round:1, dist:{}, roundOrder:[], over:false, turnOwner:null, progSnap:{} };""",
"""  G = { players, round:1, dist:{}, roundOrder:[], over:false, turnOwner:null, progSnap:{}, runId:myRun };
  globalThis.__MC_RUN = myRun;        /* 供旧循环自查是否过期 */""",
'G.runId')

# ② gameLoop 守卫
sub("""async function gameLoop(){
  while(!G.over){
    if(alivePlayers().length<=1){ checkGameEnd(); break; }""",
"""async function gameLoop(){
  const myRun = G.runId;
  while(!G.over){
    if(G.runId !== myRun) return;                      /* 已经开了新的一局，旧循环退出 */
    if(alivePlayers().length<=1){ checkGameEnd(); break; }""",
'gameLoop 守卫')

# ③ actionPhase 守卫
sub("""async function actionPhase(order){
  for(const p of order){
    if(!p.alive || G.over) continue;""",
"""async function actionPhase(order){
  const myRun = G.runId;
  for(const p of order){
    if(G.runId !== myRun) return;
    if(!p.alive || G.over) continue;""",
'actionPhase 守卫')

# ④ endOfRound 守卫
sub("""async function endOfRound(opts){
  const o = opts||{};
  log(`── 所有玩家行动结束：结算持续伤害 ──`,'l-sys');""",
"""async function endOfRound(opts){
  const o = opts||{};
  if(G.runId !== globalThis.__MC_RUN) return;          /* 过期局不再结算 */
  log(`── 所有玩家行动结束：结算持续伤害 ──`,'l-sys');""",
'endOfRound 守卫')

# ⑤ takeTurn 守卫
sub("""async function takeTurn(p){
  p.slotsLeft = 1; p.actionsUsed = 0; p.turnSpent = 0;
  const isHuman = p.isHuman;
  let guard = 0;""",
"""async function takeTurn(p){
  const myRun = G.runId;
  p.slotsLeft = 1; p.actionsUsed = 0; p.turnSpent = 0;
  const isHuman = p.isHuman;
  let guard = 0;""",
'takeTurn 代次')

sub("""  while(p.alive && !G.over && guard++ < 16){
    if(p.turnSpent >= 8){ log(`（${p.name} 本回合行动次数已达上限）`,'l-sys'); break; }""",
"""  while(p.alive && !G.over && guard++ < 16){
    if(G.runId !== myRun) return;                      /* 新局已开始，放弃本回合 */
    if(p.turnSpent >= 8){ log(`（${p.name} 本回合行动次数已达上限）`,'l-sys'); break; }""",
'takeTurn 循环守卫')

# ⑥ rpsPhase 守卫（避免旧局继续猜拳）
sub("""  const live = alivePlayers();
  if(live.length >= 2){
    let round = 0, winner = null;
    while(round++ < 60){""",
"""  const live = alivePlayers();
  if(live.length >= 2){
    const myRun = G.runId;
    let round = 0, winner = null;
    while(round++ < 60){
      if(G.runId !== myRun) return order;              /* 新局已开始 */""",
'rpsPhase 守卫')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
