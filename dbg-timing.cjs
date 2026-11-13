/* 诊断：统计每个动作的耗时，找出拖慢对局的元凶
   用法： node dbg-timing.cjs [局数] [敌人数]                                  */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const dir = __dirname;
const html = fs.readFileSync(path.join(dir,'index.html'),'utf8');
let js = html.match(/<script>([\s\S]*)<\/script>/)[1];

/* 在 runAction 外面套一层计时（插桩到 takeTurn 的调用处） */
function patch(needle, repl, label){
  if(js.includes(needle)){ js = js.replace(needle, repl); console.log('  插桩 OK:', label); }
  else console.log('  插桩失败:', label);
}
patch('      const ok = await withTimeout(runAction(p, choice), 5000, \'timeout\');\n      if(ok===false || ok===\'timeout\' || repeat[ak] >= 3){\n        avoid.push(ak);\n        if(ok===\'timeout\') log(`（${choice.type} 执行超时，已跳过）`,\'l-warn\');\n      }',
      '      const __t0=Date.now();\n      const ok = await withTimeout(runAction(p, choice), 5000, \'timeout\');\n      globalThis.__TM=globalThis.__TM||{}; const __k=choice.type+(choice.key?":"+choice.key:"");\n      globalThis.__TM[__k]=globalThis.__TM[__k]||{n:0,ms:0,max:0};\n      { const e=globalThis.__TM[__k]; const d=Date.now()-__t0; e.n++; e.ms+=d; if(d>e.max)e.max=d; }\n      if(ok===false || ok===\'timeout\' || repeat[ak] >= 3){\n        avoid.push(ak);\n        if(ok===\'timeout\') log(`（${choice.type} 执行超时，已跳过）`,\'l-warn\');\n      }',
      'AI 动作计时');

function makeEl(tag){
  const el = { tagName:(tag||'div').toUpperCase(), children:[], style:{}, dataset:{}, _attrs:{},
    _text:'', _html:'', disabled:false, className:'', parentNode:null, id:'',
    classList:{ _s:new Set(), add(){}, remove(){}, toggle(){}, contains(){return false;} },
    appendChild(c){ this.children.push(c); return c; }, remove(){}, scrollTop:0, scrollHeight:0,
    getBoundingClientRect(){ return {left:0,top:0,width:100,height:80}; },
    getAttribute(){ return null; }, setAttribute(){}, querySelectorAll(){ return []; },
    querySelector(){ return null; }, onclick:null };
  Object.defineProperty(el,'innerHTML',{get(){return el._html;},set(v){el._html=String(v);el.children.length=0;}});
  Object.defineProperty(el,'textContent',{get(){return el._text;},set(v){el._text=String(v);el.children.length=0;}});
  return el;
}
function loadGame(){
  const reg={}, store={};
  const document={ createElement:makeEl,
    getElementById(id){ if(!reg[id]){ reg[id]=makeEl('div'); reg[id].id=id; } return reg[id]; },
    querySelectorAll(){ return []; }, querySelector(){ return null; }, body:makeEl('body') };
  const localStorage={ getItem:k=>(k in store?store[k]:null), setItem:(k,v)=>{store[k]=String(v);},
    removeItem:k=>{delete store[k];}, clear(){} };
  const sandbox={ document, window:{}, localStorage, setTimeout, clearTimeout, setInterval, clearInterval, console,
    Math, JSON, Date, Object, Array, String, Number, Boolean, Infinity, NaN, isNaN, parseInt, parseFloat,
    Promise, Set, Map, Error, RegExp, Symbol, TypeError, RangeError };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(js, sandbox, {filename:'game.js'});
  return { MC: sandbox.window.MCGame, sandbox, document, g: sandbox };
}
const policy = (MC)=>(p, opts)=>{
  const G = MC.state(); const o = opts||[];
  const dmgOf = k => k==='diamond_sword'?3:k==='iron_sword'?2:(k==='stone_sword'||k==='trident'||k==='crossbow')?1.5:k==='wood_sword'?1:0.5;
  const kill=o.find(x=>x.type==='attack'&&G.players[x.targetId].hp<=dmgOf(p.weapon||'fist'));
  if(kill) return kill;
  if(p.hp<=1.5){ const h=o.find(x=>x.type==='eat'||x.type==='potion'); if(h) return h; }
  if(dmgOf(p.weapon||'fist')<1.5&&p.ap>=1){ const w=o.find(x=>x.type==='craftShopItem'&&['stone_sword','wood_sword'].includes(x.key)); if(w) return w; }
  const atk=o.find(x=>x.type==='attack'&&(x.ranged||G.dist[p.id][x.targetId]===0));
  if(atk&&p.hp>1) return atk;
  if(p.ap>=2){ const w=o.find(x=>x.type==='craftShopItem'&&['iron_sword','crossbow','diamond_sword'].includes(x.key)); if(w) return w; }
  if(!p.armor&&p.ap>=2){ const a=o.find(x=>x.type==='craftShopItem'&&['leather','iron_armor','diamond_armor'].includes(x.key)); if(a) return a; }
  const up=o.find(x=>x.type==='shop_progress'); if(up) return up;
  const mv=o.find(x=>x.type==='move'&&x.dir===-1); if(mv) return mv;
  if(atk) return atk;
  return {type:'pass'};
};

(async ()=>{
  const N = Number(process.argv[2]||6), E = Number(process.argv[3]||2);
  const agg = {};
  let totalMs = 0, rounds = 0;
  for(let i=0;i<N;i++){
    const { MC, sandbox, document, g } = loadGame();
    MC.__api.setFastTiming(); MC.__api.setInstantRps && MC.__api.setInstantRps();
    MC.__api.setAutoPlayer(policy(MC));
    const t0 = Date.now();
    MC.start({enemyCount:E, diff:'normal', auto:true});
    const G = MC.state();
    await new Promise(res=>{
      const iv = setInterval(()=>{ if(G.over || Date.now()-t0 > 90000){ clearInterval(iv); res(); } }, 1);
    });
    totalMs += Date.now()-t0; rounds += G.round;
    for(const [k,v] of Object.entries(g.__TM||{})){
      agg[k] = agg[k] || {n:0, ms:0, max:0};
      agg[k].n += v.n; agg[k].ms += v.ms; agg[k].max = Math.max(agg[k].max, v.max);
    }
    console.log(`第 ${i+1} 局: ${G.over?'结束':'超时'} round=${G.round} 用时=${((Date.now()-t0)/1000).toFixed(1)}s`);
  }
  console.log('');
  console.log(`总计: ${N} 局 / ${rounds} 回合 / ${(totalMs/1000).toFixed(1)}s（平均每回合 ${(totalMs/Math.max(1,rounds)).toFixed(0)}ms）`);
  console.log('各动作耗时（按总耗时排序）:');
  Object.entries(agg).sort((a,b)=>b[1].ms-a[1].ms).slice(0,14).forEach(([k,v])=>{
    console.log(`  ${k.padEnd(26)} 次数 ${String(v.n).padStart(5)}  总 ${String(v.ms).padStart(7)}ms  平均 ${String(Math.round(v.ms/Math.max(1,v.n))).padStart(5)}ms  最慢 ${String(v.max).padStart(6)}ms`);
  });
  process.exit(0);
})();
