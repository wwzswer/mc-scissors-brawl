/* 自动对局测试：用启发式“自动玩家”代替人类点击，跑完整局。
   用途：验证流程能正常结束、检查状态不变量、统计对局时长与胜负。
   用法： node match-test.js [局数] [敌人数量] [难度]                            */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

/* ---------------- 最小 DOM 桩 ---------------- */
function makeEl(tag){
  const el = { tagName:(tag||'div').toUpperCase(), children:[], style:{}, dataset:{}, _attrs:{},
    _text:'', _html:'', disabled:false, className:'', parentNode:null, id:'',
    classList:{ _s:new Set(),
      add(...c){c.forEach(x=>this._s.add(x));},
      remove(...c){c.forEach(x=>this._s.delete(x));},
      toggle(c,f){ if(f===undefined){ this._s.has(c)?this._s.delete(c):this._s.add(c);} else if(f){this._s.add(c);} else {this._s.delete(c);} },
      contains(c){return this._s.has(c);} },
    appendChild(c){ this.children.push(c); c.parentNode=this; return c; },
    remove(){ if(this.parentNode) this.parentNode.children=this.parentNode.children.filter(x=>x!==this); },
    scrollTop:0, scrollHeight:0,
    getBoundingClientRect(){ return {left:0,top:0,width:100,height:80}; },
    getAttribute(n){ return this._attrs[n]===undefined?null:this._attrs[n]; },
    setAttribute(n,v){ this._attrs[n]=String(v); },
    querySelectorAll(){ return []; }, querySelector(){ return null; }, onclick:null };
  Object.defineProperty(el,'innerHTML',{get(){return el._html;},set(v){el._html=String(v);el.children.length=0;}});
  Object.defineProperty(el,'textContent',{get(){return el._text;},set(v){el._text=String(v);el.children.length=0;}});
  return el;
}
function loadGame(){
  const html = fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
  const js = html.match(/<script>([\s\S]*)<\/script>/)[1];
  const reg = {};
  const document = {
    createElement: makeEl,
    getElementById(id){ if(!reg[id]){ reg[id]=makeEl('div'); reg[id].id=id; } return reg[id]; },
    querySelectorAll(){ return []; }, querySelector(){ return null; }, body: makeEl('body'),
  };
  const store = {};
  const localStorage = {
    getItem:k=>(k in store ? store[k] : null),
    setItem:(k,v)=>{ store[k]=String(v); },
    removeItem:k=>{ delete store[k]; }, clear:()=>{ for(const k in store) delete store[k]; },
  };
  const sandbox = { document, window:{}, localStorage, setTimeout, clearTimeout, setInterval, clearInterval, console,
    Math, JSON, Date, Object, Array, String, Number, Boolean, Infinity, NaN, isNaN, parseInt, parseFloat,
    Promise, Set, Map, Error, RegExp, Symbol, TypeError, RangeError };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(js, sandbox, {filename:'game.js'});
  return { MC: sandbox.window.MCGame, sandbox, document };
}

/* ---------------- 自动玩家策略 ----------------
   返回 MC.__api 能直接执行的动作对象；目标是尽快击杀敌人，同时做基本投资 */
function autoHumanPolicy(MC, G, optsIn){
  const me = G.players[0];
  if(!me.alive || G.over) return null;
  const API = MC.__api;
  const opts = optsIn || API.buildHumanOptions(me);
  const find = pred => opts.find(pred);
  const enemies = G.players.filter(p=>p.alive && p.team!==me.team);
  if(!enemies.length) return null;
  const dmgOf = k => k==='diamond_sword'?3:k==='iron_sword'?2:(k==='stone_sword'||k==='trident'||k==='crossbow')?1.5:k==='wood_sword'?1:0.5;
  let myDmg = dmgOf(me.weapon||'fist');
  if(me.ench[me.weapon]==='sharpness') myDmg += 0.5*(me.ench[me.weapon]||1);

  /* 1. 能击杀就打 */
  const kill = find(o=>o.type==='attack' && G.players[o.targetId].hp<=myDmg);
  if(kill) return kill;
  /* 2. 血少先回血 */
  if(me.hp<=1.5){
    const heal = find(o=>o.type==='eat'||o.type==='potion');
    if(heal) return heal;
  }
  /* 3. 受伤时先补护甲（只在有对应进程时） */
  if(me.hp<=2.5 && !me.armor && me.ap>=2){
    const arm = find(o=>o.type==='craftShopItem' && ['leather','iron_armor','diamond_armor'].includes(o.key));
    if(arm && me.ap>=1) return arm;
  }
  /* 4. 没武器先做武器（这是新 AP 规则下的关键一步） */
  if(myDmg<1.5 && me.ap>=1){
    const wp = find(o=>o.type==='craftShopItem' && ['stone_sword','wood_sword'].includes(o.key));
    if(wp) return wp;
  }
  /* 5. 贴脸打人 / 远程 */
  const atk = find(o=>o.type==='attack' && (o.ranged || G.dist[me.id][o.targetId]===0));
  if(atk && me.hp>1) return atk;
  /* 6. 有铁砧就修甲 */
  const rep = find(o=>o.type==='repair');
  if(rep) return rep;
  /* 7. 投资：武器升级 > 进程进度 > 护甲 */
  if(me.ap>=2){
    const wp = find(o=>o.type==='craftShopItem' && ['iron_sword','crossbow','diamond_sword'].includes(o.key));
    if(wp) return wp;
  }
  if(!me.armor && me.ap>=2){
    const arm = find(o=>o.type==='craftShopItem' && ['leather','iron_armor','diamond_armor'].includes(o.key));
    if(arm) return arm;
  }
  const up = find(o=>o.type==='shop_progress');
  if(up && API.progMaxed(me)===false) return up;
  /* 8. 靠近 */
  const mv = find(o=>o.type==='move' && o.dir===-1);
  if(mv) return mv;
  if(atk) return atk;
  /* 9. 免费资源 */
  const free = find(o=>o.type==='pearl'||o.type==='fish_trident');
  if(free) return free;
  return {type:'pass'};
}

/* ---------------- 单局运行 ---------------- */
function playMatch(MC, sandbox, document, cfg){
  const errors = [];
  return new Promise(resolve=>{
    MC.__api.setFastTiming();          /* 无头：删掉所有动画等待 */
    MC.__api.setInstantRps && MC.__api.setInstantRps();
    MC.__api.setAutoPlayer((p, opts)=>{
      global.__apCalls = (global.__apCalls||0)+1;
      try{
        const a = autoHumanPolicy(MC, MC.state(), opts);
        if(!a){ errors.push('policy 返回空动作'); return {type:'pass'}; }
        if(!a.type){ errors.push('policy 返回非法动作: '+JSON.stringify(a)); return {type:'pass'}; }
        return a;
      }
      catch(e){ errors.push('policy: '+(e.stack||String(e))); return {type:'pass'}; }
    });
    MC.start(cfg);
    const G = MC.state();
    const t0 = Date.now();
    let guard = 0;
    const logEl = document.getElementById('log');
    const iv = setInterval(()=>{
      const timeUp = (Date.now() - t0) > 90000;
      if(G.over || guard++ > 60000 || timeUp){
        clearInterval(iv);
        if(timeUp && !G.over){
          errors.push('超时未结束（90s） round=' + G.round + ' turnOwner=' + G.turnOwner + ' calls=' + (global.__apCalls||0));
          const tail = logEl.children.slice(-20).map(d=>(d.children||[]).map(c=>c.innerHTML||c.textContent||'').join(' ').replace(/<[^>]+>/g,''));
          errors.push('日志尾部: ' + tail.join(' ｜ '));
        }
        resolve({G, errors, ms:Date.now()-t0, aborted:!G.over});
        return;
      }
    }, 1);
  });
}

/* ---------------- 主流程 ---------------- */
(async ()=>{
  const rounds = Number(process.argv[2]||6);
  const enemyCount = Number(process.argv[3]||2);
  const diff = process.argv[4]||'normal';
  const results=[];
  for(let i=0;i<rounds;i++){
    const { MC, sandbox, document } = loadGame();
    const r = await playMatch(MC, sandbox, document, {enemyCount, diff, auto:true});
    const G=r.G, me=G.players[0];
    const problems=[];
    for(const p of G.players){
      if(p.hp>p.maxHp) problems.push(`${p.name} HP 超上限`);
      if(p.ap<0) problems.push(`${p.name} AP 为负(${p.ap})`);
      if(p.armorCharges<0) problems.push(`${p.name} 护甲为负`);
      if(p.armor && p.armorCharges>(MC.ITEMS[p.armor].armor||0)) problems.push(`${p.name} 护甲超上限`);
      if(p.weapon && !MC.ITEMS[p.weapon]) problems.push(`${p.name} 武器非法：${p.weapon}`);
      if(p.prog<0||p.prog>4) problems.push(`${p.name} 进程越界`);
    }
    for(const a of G.players) for(const b of G.players){
      if(a===b) continue;
      const d=G.dist[a.id][b.id];
      if(typeof d!=='number'||d<0||!isFinite(d)) problems.push(`距离非法 ${a.name}->${b.name}`);
      if(G.dist[a.id][b.name]!==undefined){}
    }
    results.push({ win:r.G.over && me.alive, rounds:G.round, over:G.over, hp:me.hp,
      prog:MC.PROG_NAME[me.prog], weapon:me.weapon||'空手', armor:me.armor||'无',
      enemyAlive:G.players.filter(p=>p.isEnemy&&p.alive).length, problems, errors:r.errors });
    console.log(`#${i+1} ${r.G.over?(me.alive?'玩家胜':'玩家败'):'未结束'} | 回合 ${G.round} | 玩家 ${me.hp}HP ${MC.PROG_NAME[me.prog]} ${me.weapon||'空手'}/${me.armor||'无'} | 进度点 ${me.progPts||0} | 存活敌人 ${results[i].enemyAlive} | 异常 ${r.errors.length}${problems.length?' | 状态问题: '+problems.join(','):''}`);
    if(r.errors.length) console.log('   err: '+r.errors[0].split('\n')[0]);
  }
  const wins = results.filter(r=>r.win).length;
  const avgRounds = (results.reduce((s,r)=>s+r.rounds,0)/results.length).toFixed(1);
  const notOver = results.filter(r=>!r.over).length;
  const anyErr = results.reduce((s,r)=>s+r.errors.length,0);
  const anyProblem = results.reduce((s,r)=>s+r.problems.length,0);
  const progDist = {};
  for(const r of results) progDist[r.prog] = (progDist[r.prog]||0)+1;
  console.log('');
  console.log('──────────────────────────────');
  console.log(`局数 ${results.length} | 玩家胜率 ${(wins/results.length*100).toFixed(0)}% | 平均回合 ${avgRounds} | 未结束 ${notOver} | 异常 ${anyErr} | 状态问题 ${anyProblem}`);
  console.log(`结束时玩家进程分布：${Object.entries(progDist).map(([k,v])=>k+'×'+v).join('  ')}`);
  const ok = anyErr===0 && anyProblem===0 && notOver===0;
  console.log(ok?'✅ 通过':'❌ 失败');
  process.exit(ok?0:1);
})();
