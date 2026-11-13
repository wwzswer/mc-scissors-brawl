/* 精确诊断：给 takeTurn / endOfRound / rpsPhase 插桩，定位卡住的位置
   用法： node dbg-trace.cjs [局数]                                        */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const dir = __dirname;
const html = fs.readFileSync(path.join(dir,'index.html'),'utf8');
let js = html.match(/<script>([\s\S]*)<\/script>/)[1];

/* ---- 插桩 ---- */
function patch(needle, repl, label){
  if(js.includes(needle)){ js = js.replace(needle, repl); console.log('  插桩 OK:', label); }
  else console.log('  插桩失败:', label);
}
patch('async function takeTurn(p){',
      'async function takeTurn(p){ globalThis.__TT=globalThis.__TT||[]; globalThis.__TTT=(globalThis.__TTT||[]); globalThis.__TTT.push("T enter "+p.name+" ap="+p.ap);', 'takeTurn 入口');
patch('  while(p.alive && !G.over && guard++ < 16){',
      '  while(p.alive && !G.over && guard++ < 16){ globalThis.__TTT=(globalThis.__TTT||[]); globalThis.__TTT.push("  T it"+guard+" ap="+p.ap+" spent="+p.turnSpent);', 'takeTurn 迭代');
patch('      const choice = aiPick(p, usable, avoid);',
      '      const choice = aiPick(p, usable, avoid); globalThis.__TTT=(globalThis.__TTT||[]); globalThis.__TTT.push("    pick="+(choice?choice.type+":"+(choice.key||""):"null")+" usable="+usable.length);', 'aiPick');
patch('async function endOfRound(opts){',
      'async function endOfRound(opts){ globalThis.__TTT=(globalThis.__TTT||[]); globalThis.__TTT.push("E enter round="+G.round);', 'endOfRound 入口');
patch('async function rpsPhase(){',
      'async function rpsPhase(){ globalThis.__TTT=(globalThis.__TTT||[]); globalThis.__TTT.push("P enter round="+G.round);', 'rpsPhase 入口');
patch('      if(res.tie){',
      '      if(res.tie){ globalThis.__TTT=(globalThis.__TTT||[]); globalThis.__TTT.push("  P tie round"+round);', '猜拳平局');

/* ---- DOM 桩 ---- */
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

const greedyPolicy = (MC)=>(p, opts)=>{
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
  const N = Number(process.argv[2]||4);  /* 局数 */
  const stuck = [];
  for(let round=0; round<N; round++){
    const { MC, sandbox, document, g } = loadGame();
    MC.__api.setFastTiming(); MC.__api.setInstantRps && MC.__api.setInstantRps();
    MC.__api.setAutoPlayer(greedyPolicy(MC));
    MC.start({enemyCount:Number(process.argv[3]||1), diff:'normal', auto:true});
    const G = MC.state();
    const logEl = document.getElementById('log');
    const t0 = Date.now();
    await new Promise(res=>{
      const iv = setInterval(()=>{
        if(G.over || Date.now()-t0 > 120000){ clearInterval(iv); res(); }
      }, 1);
    });
    const ok = G.over;
    console.log(`第 ${round+1} 局: ${ok?'结束':'卡住'} round=${G.round} 用时=${((Date.now()-t0)/1000).toFixed(1)}s`);
    if(!ok){
      const me=G.players[0];
      console.log('  状态: round='+G.round+' over='+G.over+' turnOwner='+G.turnOwner);
      console.log('  玩家: '+G.players.map(q=>q.name+(q.alive?'('+q.hp+'HP,ap'+q.ap+',dist'+(q===me?'-':G.dist[me.id][q.id])+')':'[亡]')).join(' '));
      console.log('  takeTurn 轨迹（最后 24 条）:');
      (g.__TTT||[]).slice(-24).forEach(x=>console.log('    '+x));
      console.log('  最后 8 行日志:');
      logEl.children.slice(-8).forEach(d=>console.log('    '+(d.children||[]).map(c=>c.innerHTML||c.textContent||'').join(' ').replace(/<[^>]+>/g,'').slice(0,130)));
      stuck.push(round+1);
      break;
    }
  }
  console.log(stuck.length ? '发现卡住，已输出轨迹' : '全部正常结束');
  process.exit(0);
})();
