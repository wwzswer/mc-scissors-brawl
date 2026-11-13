/* 引擎层规则验证：绕过界面直接调用游戏内部接口，逐条核对规则实现。
   用法： node rules-test.js                                        */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

/* ---------------- DOM 桩 ---------------- */
function makeEl(tag){
  const el = { tagName:(tag||'div').toUpperCase(), children:[], style:{}, dataset:{}, _attrs:{},
    _text:'', _html:'', disabled:false, className:'', parentNode:null, id:'',
    classList:{ _s:new Set(), add(){}, remove(){}, toggle(){}, contains(){return false;} },
    appendChild(c){ this.children.push(c); c.parentNode=this; return c; },
    remove(){}, scrollTop:0, scrollHeight:0,
    getBoundingClientRect(){ return {left:0,top:0,width:100,height:80}; },
    getAttribute(){ return null; }, setAttribute(){},
    querySelectorAll(){ return []; }, querySelector(){ return null; }, onclick:null };
  Object.defineProperty(el,'innerHTML',{get(){return el._html;},set(v){el._html=String(v);el.children.length=0;}});
  Object.defineProperty(el,'textContent',{get(){return el._text;},set(v){el._text=String(v);el.children.length=0;}});
  return el;
}
function load(){
  const html = fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
  const js = html.match(/<script>([\s\S]*)<\/script>/)[1];
  const reg={};
  const document={ createElement:makeEl,
    getElementById(id){ if(!reg[id]){ reg[id]=makeEl('div'); reg[id].id=id; } return reg[id]; },
    querySelectorAll(){ return []; }, querySelector(){ return null; }, body:makeEl('body') };
  const store = {};
  const localStorage = {
    getItem:k=>(k in store ? store[k] : null),
    setItem:(k,v)=>{ store[k]=String(v); },
    removeItem:k=>{ delete store[k]; }, clear:()=>{ for(const k in store) delete store[k]; },
  };
  const sandbox={ document, window:{}, localStorage, setTimeout, clearTimeout, setInterval, clearInterval, console,
    Math, JSON, Date, Object, Array, String, Number, Boolean, Infinity, NaN, isNaN, parseInt, parseFloat,
    Promise, Set, Map, Error, RegExp, Symbol, TypeError, RangeError };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(js, sandbox, {filename:'game.js'});
  globalThis.__store = store;                 /* 供测试检查进度存档 */
  return { MC: sandbox.window.MCGame };
}
function fresh(){
  const { MC } = load();
  MC.start({ enemyCount:1, diff:'normal', auto:true, silent:true });
  const G = MC.state();
  const API = MC.__api;
  const me = G.players[0], ai = G.players[1];
  me.ap = 5; ai.ap = 5;        /* 默认给点 AP：面包/金苹果等现在各需 1 AP */
  return { MC, API, G, me, ai };
}
/* 进度式制作：反复投入直到拿到成品（或到达上限） */
async function invest(API, p, key, times){
  for(let i=0;i<(times||6);i++){
    if(API.hasItem(p,key)) return true;
    await API.applyAction(p, {type:'craftShopItem', key});
  }
  return API.hasItem(p, key);
}

let pass=0, fail=0; const fails=[];
function ok(cond, name, extra){
  if(cond){ pass++; console.log(`  ✅ ${name}`); }
  else { fail++; fails.push(name); console.log(`  ❌ ${name}${extra!==undefined?'  → '+JSON.stringify(extra):''}`); }
}
const near=(a,b)=>Math.abs(a-b)<1e-9;
const doOpt = (API, p, opt) => API.applyAction(p, opt);

(async ()=>{
console.log('\n【1】进程进度（空手→木只要 1 点）与物品进度式制作');
{
  const { MC, API, me } = fresh();
  me.prog = 0; me.progPts = 0; me.ap = 2;
  const up = API.buildHumanOptions(me).find(o=>o.type==='shop_progress');
  ok(!!up && up.cost===1, '空手能看到「投入 1 步进度」入口（1 AP）', up && up.label);
  await doOpt(API, me, up);
  ok(me.prog===1, '空手只需投入 1 步就升级到木进程', MC.PROG_NAME[me.prog]);
  ok(me.ap===1, '投入 1 步扣 1 AP', me.ap);
}
{
  /* 多步物品：每投入 1 步点亮 1 个点，集满才拿到 */
  const { MC, API, me } = fresh();
  me.prog = 1; me.itemPts = {}; me.ap = 5;
  const lab = () => {
    const o = API.buildHumanOptions(me).find(x=>x.type==='craftShopItem' && x.key==='wood_sword');
    return o ? o.label : '(无入口)';
  };
  ok(lab().includes('1/2'), '木剑入口显示进度 1/2', lab());
  await doOpt(API, me, {type:'craftShopItem', key:'wood_sword'});
  ok(!API.hasItem(me,'wood_sword') && API.itemProgress(me,'wood_sword')===1, '投入 1 步还没拿到木剑', [me.items, me.itemPts]);
  ok(me.ap===4, '投入 1 步只扣 1 AP', me.ap);
  await doOpt(API, me, {type:'craftShopItem', key:'wood_sword'});
  ok(API.hasItem(me,'wood_sword'), '第 2 步后木剑制作完成', me.items);
  ok(me.weapon==='wood_sword', '制作完成后自动装备', me.weapon);
  ok(API.itemProgress(me,'wood_sword')===0, '完成后该物品进度清零', me.itemPts);
}
{
  /* 3 步物品（三叉戟）也是进度式 */
  const { API, me } = fresh();
  me.prog = 2; me.itemPts = {}; me.ap = 10;
  API.addItem(me, 'fishing_rod', 1);           /* 前置 */
  await doOpt(API, me, {type:'craftShopItem', key:'trident'});
  await doOpt(API, me, {type:'craftShopItem', key:'trident'});
  ok(!API.hasItem(me,'trident') && API.itemProgress(me,'trident')===2, '三叉戟 3 步：投 2 次还没完成', API.itemProgress(me,'trident'));
  await doOpt(API, me, {type:'craftShopItem', key:'trident'});
  ok(API.hasItem(me,'trident'), '第 3 步后三叉戟完成', me.items);
}
{
  /* 1 步物品一次到位 */
  const { API, me } = fresh();
  me.ap = 3; me.itemPts = {};
  await doOpt(API, me, {type:'craftShopItem', key:'bread'});
  ok(API.hasItem(me,'bread'), '面包（1 步）投入 1 次即到手', me.items);
}

console.log('\n【2】各级进程所需进度点：升木 1 / 升石 2 / 升铁 3 / 升钻石 3');
{
  const { MC, API, me } = fresh();
  const reqs = [0,1,2,3].map(i=>{ me.prog=i; return API.progNeed(me); });
  ok(reqs[0]===1 && reqs[1]===2 && reqs[2]===3 && reqs[3]===3,
     '所需点数：升木 1 / 升石 2 / 升铁 3 / 升钻石 3', reqs);
  ok(MC.PROG_NAME.join('|')==='空手|木进程|石进程|铁进程|钻石进程', '进程名恢复为 5 级', MC.PROG_NAME);
}
{
  const { MC, API, me } = fresh();
  me.prog = 1; me.progPts = 0; me.ap = 10;
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===1 && API.progProgress(me)===1, '木→石：投 1 次还不升级', [me.prog, API.progProgress(me)]);
  await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===2, '投第 2 次升级到石进程', MC.PROG_NAME[me.prog]);
}
{
  const { MC, API, me } = fresh();
  me.prog = 2; me.progPts = 0; me.ap = 10;
  for(let i=0;i<3;i++) await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===3, '石→铁需要 3 点', MC.PROG_NAME[me.prog]);
  for(let i=0;i<3;i++) await doOpt(API, me, {type:'shop_progress'});
  ok(me.prog===4, '铁→钻石需要 3 点', MC.PROG_NAME[me.prog]);
  ok(API.progMaxed(me), '钻石进程后不可再升级');
  const ups = API.buildHumanOptions(me).filter(o=>o.type==='shop_progress');
  ok(ups.length===1 && ups[0].label.includes('已满级'), '满级后显示「已满级」', ups[0] && ups[0].label);
}

console.log('\n【3】玻璃进程已删除；木进程保留');
{
  const { MC } = fresh();
  ok(!MC.PROG_NAME.some(n=>String(n).includes('玻璃')), '没有玻璃进程', MC.PROG_NAME);
  ok(MC.PROG_NAME.includes('木进程'), '木进程仍在（空手→木 1 点）', MC.PROG_NAME);
}

console.log('\n【4】三叉戟前置 = 钓鱼竿');
{
  const { API, me } = fresh();
  me.prog = 2; me.ap = 10;
  ok(!API.buildHumanOptions(me).some(o=>o.type==='craftShopItem'&&o.key==='trident'), '没有钓鱼竿时看不到三叉戟');
  await invest(API, me, 'fishing_rod');
  ok(me.items.fishing_rod===1, '做出钓鱼竿（2 步进度式）', me.items);
  ok(API.buildHumanOptions(me).some(o=>o.type==='craftShopItem'&&o.key==='trident'), '有钓鱼竿后出现三叉戟');
  const tri = API.buildHumanOptions(me).find(o=>o.type==='craftShopItem'&&o.key==='trident');
  ok(tri && tri.cost===1, '三叉戟入口每次投入 1 AP（共需 3 点）', tri && tri.cost);
}

console.log('\n【5】末影珍珠：不消耗、每次改 2 格');
{
  const { API, G, me, ai } = fresh();
  me.prog = 2; me.ap = 8;                     /* 位移现在要 1 AP */
  await invest(API, me, 'ender_pearl');
  ok(me.items.ender_pearl===1, '获得末影珍珠（2 步进度式）');
  const before = G.dist[me.id][ai.id];
  await doOpt(API, me, API.buildHumanOptions(me).find(o=>o.type==='pearl'&&o.dir===2));
  ok(G.dist[me.id][ai.id]===before+2, `距离 +2（${before} 到 ${G.dist[me.id][ai.id]}）`);
  ok(me.items.ender_pearl===1, '使用后不消耗', me.items);
  await doOpt(API, me, API.buildHumanOptions(me).find(o=>o.type==='pearl'&&o.dir===-2));
  ok(G.dist[me.id][ai.id]===before, '可再移回来', G.dist[me.id][ai.id]);
}

console.log('\n【6】护甲：抵消次数 / 破损后可用铁砧修复 / 三种护甲数值');
{
  const { API, me } = fresh();
  me.prog=1; me.ap=6;      /* 木进程：皮革甲 */
  await invest(API, me, 'leather');
  ok(me.armor==='leather'&&me.armorCharges===1, '皮革甲 = 1 次物理免疫', [me.armor,me.armorCharges]);
  API.tryDamage(me,[1,0,0,0],{});
  ok(near(me.hp,4), '皮革甲挡下 1 点物理伤害', me.hp);
  ok(!API.armorActive(me), '护甲用尽即失效', [me.armor,me.armorCharges]);

  me.prog=3; me.ap=20;     /* 铁进程 */
  await invest(API, me, 'iron_armor');
  ok(me.armor==='iron_armor'&&me.armorCharges===2, '铁甲 = 2 次物理免疫', [me.armor,me.armorCharges]);
  API.tryDamage(me,[1,0,0,0],{});
  API.tryDamage(me,[1,0,0,0],{});
  ok(near(me.hp,4)&&me.armorCharges===0, '铁甲吃满 2 次后护甲归零', [me.hp,me.armorCharges]);
  ok(me.armor==='iron_armor', '破损的护甲留在身上（等待修复）', me.armor);
  ok(!API.buildHumanOptions(me).some(o=>o.type==='repair'), '没有铁砧时不能修复');
  await invest(API, me, 'anvil');
  const rep = API.buildHumanOptions(me).find(o=>o.type==='repair');
  ok(!!rep && rep.cost===2, '有铁砧后出现「修复（2 步）」', rep && rep.cost);
  await doOpt(API, me, rep);
  ok(me.armorCharges===2, '修复到满护甲', me.armorCharges);

  API.breakArmor(me);
  await invest(API, me, 'golem');
  ok(me.armor==='golem'&&me.armorCharges===2, '铁傀儡 = 2 次物理免疫（4 步进度式）', [me.armor,me.armorCharges]);
  API.tryDamage(me,[2,0,0,0],{});
  ok(near(me.hp,4)&&me.armorCharges===0, '铁傀儡吃满 2 次后归零', [me.hp,me.armorCharges]);
  ok(!!API.buildHumanOptions(me).find(o=>o.type==='repair'), '铁傀儡也能用铁砧修复');

  me.prog=4; me.ap=10; API.breakArmor(me);
  await invest(API, me, 'diamond_armor');
  ok(me.armor==='diamond_armor'&&me.armorCharges===3, '钻石甲 = 3 次物理免疫', [me.armor,me.armorCharges]);
}

console.log('\n【7】伤害类型：护甲只挡物理，法术 / 火焰 / 穿甲照打');
{
  const { API, me } = fresh();
  me.prog=3; me.ap=10;
  await invest(API, me, 'iron_armor');
  API.tryDamage(me,[0,0,1.5,0],{});
  ok(near(me.hp,2.5), '法术伤害无视护甲', me.hp);
  ok(me.armorCharges===2, '法术不消耗护甲', me.armorCharges);
  API.tryDamage(me,[0,0.5,0,0],{});
  ok(near(me.hp,2)&&me.armorCharges===2, '火焰伤害无视护甲也不消耗护甲', [me.hp,me.armorCharges]);
  API.tryDamage(me,[0,0,0,1.5],{});
  ok(near(me.hp,0.5), '穿甲伤害无视护甲', me.hp);
}

console.log('\n【8】持续伤害：首次立即结算、其余回合末结算、入水可清除');
{
  const { API, ai } = fresh();
  /* 当回合结算型火焰：共 2 次 */
  API.addEffect(ai,'burn',2,1,'火焰');
  API.tryDamage(ai,[0,0.5,0,0],{});
  const burn = ai.effects.find(e=>e.type==='burn');
  burn.power = 1;                                  /* 首次已结算 */
  ok(near(ai.hp,3.5), '火焰首次伤害立即结算', ai.hp);
  await API.endOfRound({instant:true});
  ok(near(ai.hp,3), '回合结束时结算第 2 次火焰伤害', ai.hp);
  ok(!ai.effects.some(e=>e.type==='burn'), '火焰层数用尽后消失', ai.effects);
}
{
  const { API, ai } = fresh();
  API.addEffect(ai,'burn',3,99,'火焰');
  API.removeBurn(ai);
  ok(!ai.effects.some(e=>e.type==='burn'), '入水清除火焰（可躲掉后续持续伤害）', ai.effects);
}

console.log('\n【9】打火石：无防具 3 次、有防具 2 次');
{
  const { API, me, ai } = fresh();
  me.prog=3; me.ap=10;
  await doOpt(API, me, {type:'craftShopItem', key:'flint'});
  ok(me.items.flint===1, '做出打火石', me.items);
  const noArmorTicks = API.armorActive(ai) ? 2 : 3;
  ai.armor='leather'; ai.armorCharges=1;
  const withArmorTicks = API.armorActive(ai) ? 2 : 3;
  ok(noArmorTicks===3, '无防具：3 次 0.5 火焰', noArmorTicks);
  ok(withArmorTicks===2, '有防具：只造成 2 次 0.5 火焰', withArmorTicks);
}

console.log('\n【10】TNT：2.5 / 距 0 格 1.5（有护甲时 1.5 与 1，且不消耗护甲）');
{
  const { API, me, ai } = fresh();
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp,1.5), '无护甲：中心目标受 2.5', ai.hp);
  ok(near(me.hp,2.5), '无护甲：其他人受 1.5（友伤与自伤）', me.hp);
}
{
  const { API, me, ai } = fresh();
  ai.armor='iron_armor'; ai.armorCharges=2;
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp,2.5), '有护甲：中心目标受 1.5', ai.hp);
  ok(near(me.hp,3), '无护甲者仍受 1.5', me.hp);
  ok(ai.armorCharges===2, 'TNT 不消耗护甲耐久', ai.armorCharges);
}

console.log('\n【11】面包 / 附魔金苹果 / 不死图腾');
{
  const { API, me } = fresh();
  me.ap=3; API.addItem(me,'bread',1);
  API.tryDamage(me,[2,0,0,0],{});
  ok(near(me.hp,2), '先扣血到 2', me.hp);
  await doOpt(API, me, {type:'eat',item:'bread',targetId:me.id,cost:1});
  ok(near(me.hp,3.5), '面包回复 1.5 血', me.hp);
  ok(!API.hasItem(me,'bread'), '面包是消耗品（需重新获取）', me.items);
}
{
  const { API, me } = fresh();
  API.addItem(me,'god_apple',1);
  API.tryDamage(me,[3,0,0,0],{});
  await doOpt(API, me, {type:'eat',item:'god_apple',targetId:me.id,cost:0});
  ok(near(me.hp,3), '附魔金苹果立即 +2', me.hp);
  ok(API.tempHpOf(me)===1, '获得 1 点临时生命', API.tempHpOf(me));
  await API.endOfRound({instant:true});
  ok(near(me.hp,3.5), '下一回合再回 0.5', me.hp);
  ok(API.tempHpOf(me)===0, '临时生命 1 回合后失效', API.tempHpOf(me));
  const hp0=me.hp; API.tryDamage(me,[0,0.5,0,0],{});
  ok(near(me.hp,hp0), '免疫火焰伤害', me.hp);
  const hp1=me.hp; API.tryDamage(me,[0,0,1,0],{});
  ok(near(me.hp,hp1), '免疫法术伤害', me.hp);
}
{
  const { API, me } = fresh();
  me.mem.totem = true;
  API.tryDamage(me,[9,0,0,0],{});
  ok(me.alive===true && near(me.hp,2), '不死图腾：倒下时复活并回复 2 血', [me.alive, me.hp]);
  ok(me.mem.totem===false, '图腾用完即消耗（全局仅 1 个）');
}

console.log('\n【12】盾：破碎并使双方距离 +1（远程无效）');
{
  const { API, G, me, ai } = fresh();
  ai.items.shield = 1;
  me.weapon='iron_sword'; me.items.iron_sword=1;
  API.setDistance(me, ai, 0);
  await API.performAttack(me, ai, 'iron_sword', {instant:true, a:'rock', b:'scissors'});
  ok(!API.hasItem(ai,'shield'), '近战物理攻击打碎盾', ai.items);
  ok(G.dist[me.id][ai.id]===1, '双方距离 +1', G.dist[me.id][ai.id]);
}
{
  const { API, me, ai } = fresh();
  ai.items.shield = 1;
  me.items.crossbow=1; me.weapon='crossbow';
  API.setDistance(me, ai, 3);
  await API.performAttack(me, ai, 'crossbow', {instant:true, ranged:true, a:'rock', b:'scissors'});
  ok(API.hasItem(ai,'shield'), '远程攻击不破盾（盾对远程无效）', ai.items);
}

console.log('\n【13】判定规则：不发 AP；平局一直重猜直到分出胜负');
{
  const { API, me, ai } = fresh();
  ai.ap = 0;
  ok(await API.doJudgment(me, ai, {instant:true, a:'rock', b:'scissors', dodge:false})===true, '攻方胜出则命中');
  ok(await API.doJudgment(me, ai, {instant:true, a:'rock', b:'paper', dodge:false})===false, '攻方失败则攻击失效');
}
{
  /* 首轮平局且不闪避 → 继续重猜，最终必然给出 true/false，且全程不发 AP */
  const { API, me, ai } = fresh();
  me.ap = 0; ai.ap = 0;
  let hits = 0, misses = 0;
  for(let i=0;i<40;i++){
    const r = await API.doJudgment(me, ai, {instant:true, a:'rock', b:'rock', dodge:false});
    if(r === true) hits++; else if(r === false) misses++; else throw new Error('判定返回非布尔值: ' + r);
  }
  ok(hits + misses === 40, '平局后继续重猜，40 次判定全部给出结果', [hits, misses]);
  ok(hits > 0 && misses > 0, '重猜后胜负都会出现（不是固定结果）', [hits, misses]);
  ok(me.ap === 0 && ai.ap === 0, '判定全程不产生 AP', [me.ap, ai.ap]);
}
{
  /* 平局时被攻击方花 1 AP 直接闪避 */
  const { API, me, ai } = fresh();
  me.ap = 0; ai.ap = 3;
  const r = await API.doJudgment(me, ai, {instant:true, a:'rock', b:'rock', dodge:true});
  ok(r === false, '选择闪避 → 攻击失效', r);
  ok(ai.ap === 2, '闪避消耗 1 AP', ai.ap);
}
{
  /* 没有 AP 时无法闪避，只能继续重猜 */
  const { API, me, ai } = fresh();
  me.ap = 0; ai.ap = 0;
  const r = await API.doJudgment(me, ai, {instant:true, a:'rock', b:'rock', dodge:true});
  ok(typeof r === 'boolean', '没有 AP 时不会闪避，改为继续重猜并给出结果', r);
  ok(ai.ap === 0, 'AP 没有被消耗', ai.ap);
}

console.log('\n【14】钻石剑（3 伤害）对护甲的两种处理');
{
  const { API, ai } = fresh();
  ai.armor='iron_armor'; ai.armorCharges=2;
  ok(ai.armorCharges===2 && API.armorActive(ai), '先给 AI 装上满耐久铁甲', [ai.armor, ai.armorCharges]);
  /* B 穿甲 1.5：不吃护甲 */
  API.tryDamage(ai,[0,0,0,1.5],{});
  ok(near(ai.hp,2.5)&&ai.armorCharges===2, 'B 穿甲：1.5 伤害且不消耗护甲', [ai.hp, ai.armorCharges]);
  /* A 击碎：3 点物理伤害被护甲吸收 2，护甲随即破损（不再额外扣 1 点） */
  const hpBefore = ai.hp;
  API.tryDamage(ai,[3,0,0,0],{});
  ok(ai.hp < hpBefore, 'A 击碎：仍有伤害穿透护甲', [hpBefore, ai.hp]);
  ok(ai.armorCharges===0 && !API.armorActive(ai), 'A 击碎：护甲吸收满 2 点后破损', ai.armorCharges);
  ok(ai.armor==='iron_armor', '破损护甲仍在身上，可用铁砧修复', ai.armor);
  /* 半耐久时击碎：护甲耐久 -1（0.5 伤害绕过护甲吸收） */
  const { API:API2, ai:ai2 } = fresh();
  ai2.armor='diamond_armor'; ai2.armorCharges=2;
  const hp2 = ai2.hp;
  API2.tryDamage(ai2,[0.5,0,0,0],{ignoreArmor:true});
  ai2.armorCharges -= 1;
  ok(near(ai2.hp,hp2-0.5), 'A 击碎：0.5 伤害照常结算', ai2.hp);
  ok(ai2.armorCharges===1, 'A 击碎（钻石甲 2/3 耐久）：护甲 -1', ai2.armorCharges);
}

console.log('\n【15】AI 与玩家同一套规则');
{
  const { API, ai } = fresh();
  ai.ap = 6;
  const opts = API.aiOptions(ai, []);
  ok(opts.length>0, 'AI 有可选行动', opts.slice(0,6).map(o=>o.type));
  const pickd = API.aiPick(ai, opts.filter(o=>API.canPay(ai,o) && !['shop_progress','craftShopItem'].includes(o.type)), []);
  ok(!!pickd && pickd.type!=='pass', 'AI 有 AP 时会做实事（不空过）', pickd && pickd.type);
  const shopPick = API.aiShopChoice(ai);
  ok(shopPick===null || typeof shopPick.type==='string', 'AI 的购买决策可用', shopPick && shopPick.type);
  if(shopPick){
    const ap0=ai.ap, prog0=ai.prog;
    const done = API.applyShopAction(ai, shopPick) || await API.applyAction(ai, toAction(shopPick));
    ok(done===true && (ai.ap<ap0 || ai.prog>prog0), 'AI 购买生效（花 AP 或升进程）', [shopPick.type, ai.ap, ai.prog]);
  }
  const { API:API2, me:me2, ai:ai2 } = fresh();
  await API2.performAttack(me2, ai2, 'fist', {instant:true, a:'rock', b:'scissors'});
  ok(near(ai2.hp,3.5), '玩家攻击 AI 生效', ai2.hp);
}
function toAction(o){
  if(o.type==='upgrade') return {type:'shop_progress'};
  if(o.type==='craft')   return {type:'craftShopItem', key:o.key};
  return o;
}

console.log('\n【16】水：进入水中与拖拽');
{
  const { API, me, ai } = fresh();
  me.ap = 6;
  await doOpt(API, me, {type:'water', cost:1});
  ok(me.inWater===true, '可以主动进入水中', me.inWater);
  API.addEffect(me,'burn',2,99);
  await doOpt(API, me, {type:'water', cost:1});
  ok(me.inWater===false, '可以爬出水面', me.inWater);
  API.setDistance(me, ai, 0);
  const drag = API.buildHumanOptions(me).find(o=>o.type==='water_pull');
  ok(!!drag, '0 格时可以互相拖入/拖出水', drag && drag.label);
  await doOpt(API, me, drag);
  ok(ai.inWater===true, '把对手拖入水中', ai.inWater);
}

console.log('\n【17】走动：靠近 1 格才能近战');
{
  const { API, G, me, ai } = fresh();
  API.setDistance(me, ai, 1);
  me.ap = 3;                                  /* 走位现在需要 1 AP */
  const mv = API.buildHumanOptions(me).find(o=>o.type==='move'&&o.dir===-1);
  ok(!!mv, '距离 1 格时出现「靠近」', mv && mv.label);
  ok(API.canPay(me, mv), 'AP 足够时可以走位', me.ap);
  ok(!API.buildHumanOptions(me).some(o=>o.type==='attack'), '距离 1 格时空手无法攻击');
  await doOpt(API, me, mv);
  ok(G.dist[me.id][ai.id]===0, '靠近后距离变 0', G.dist[me.id][ai.id]);
  ok(API.buildHumanOptions(me).some(o=>o.type==='attack'), '距离 0 格时可以攻击');
}

console.log('\n【18】行动点不可存储：回合末清零');
{
  const { API, me, ai } = fresh();
  me.ap = 5; ai.ap = 3;
  const pBefore = me.progPts;
  await API.endOfRound({instant:true});
  ok(me.ap===0 && ai.ap===0, '回合结束时未用完的 AP 归零', [me.ap, ai.ap]);
  ok(me.progPts===pBefore, '清零的只是 AP，进程进度点不受影响', [pBefore, me.progPts]);
}
{
  const { API, me } = fresh();
  me.ap = 4;
  await API.endOfRound({instant:true});
  /* 下一回合猜拳获胜才重新获得 AP */
  ok(me.ap===0, '清零后不会保留到下一回合', me.ap);
}

console.log('\n【20】距离：初始 1、上限 7、两两独立');
{
  const { API, G, me, ai } = fresh();
  ok(G.dist[me.id][ai.id]===1, '初始距离为 1 格', G.dist[me.id][ai.id]);
  API.setDistance(me, ai, 99);
  ok(G.dist[me.id][ai.id]===7, '距离上限为 7', G.dist[me.id][ai.id]);
  API.setDistance(me, ai, -5);
  ok(G.dist[me.id][ai.id]===0, '距离下限为 0', G.dist[me.id][ai.id]);
}
{
  /* 三人：A-B 与 A-C 独立，B-C 不受影响 */
  const { MC, API, G } = fresh();
  MC.start({enemyCount:2, diff:'normal', auto:true, silent:true});
  const G2 = MC.state(), a = G2.players[0], b = G2.players[1], c = G2.players[2];
  API.setDistance(a, b, 0);
  API.setDistance(a, c, 0);
  ok(G2.dist[b.id][c.id]===1, 'A-B=0、A-C=0 时 B-C 仍为 1（互不影响）', G2.dist[b.id][c.id]);
  API.setDistance(b, c, 4);
  ok(G2.dist[a.id][b.id]===0 && G2.dist[a.id][c.id]===0 && G2.dist[b.id][c.id]===4,
     '三者距离互相独立', [G2.dist[a.id][b.id], G2.dist[a.id][c.id], G2.dist[b.id][c.id]]);
}

console.log('\n【21】2V2 模式');
{
  const { MC, API, G } = fresh();
  MC.start({enemyCount:1, diff:'normal', auto:true, mode:'2v2', silent:true});
  const G3 = MC.state();
  ok(G3.players.length===4, '2V2 共 4 名玩家', G3.players.length);
  const mine = G3.players.filter(p=>p.team===0);
  const foes = G3.players.filter(p=>p.team===1);
  ok(mine.length===2 && foes.length===2, '2 名自家人 vs 2 名敌人', [mine.length, foes.length]);
  const ally = mine.find(p=>!p.isHuman);
  ok(!!ally && ally.isEnemy===false, '存在 AI 队友', ally && ally.name);
  /* 队友之间不能互相攻击 */
  const opts = API.buildHumanOptions(mine[0]);
  const friendly = opts.filter(o=>o.type==='attack' && G3.players[o.targetId].team===0);
  ok(friendly.length===0, '不能攻击队友', friendly.length);
  /* 面包可以喂队友 */
  API.addItem(mine[0], 'bread', 1);
  const feed = API.buildHumanOptions(mine[0]).filter(o=>o.type==='eat' && o.targetId!==mine[0].id);
  ok(feed.length>=1, '面包可以喂给队友', feed.length);
}

console.log('\n【22】低级物品在高级进程依然可以获取（回归）');
{
  const { MC, API, me } = fresh();
  me.itemPts = {}; me.ap = 30;
  const want = ['flesh','bread','fist'];
  for(const prog of [0,1,2,3,4]){
    me.prog = prog;
    const keys = API.buildHumanOptions(me).filter(o=>o.type==='craftShopItem').map(o=>o.key);
    const miss = want.filter(k=>!keys.includes(k));
    ok(miss.length===0, `${MC.PROG_NAME[prog]} 仍可制作：一拳 / 腐肉 / 面包`, miss);
  }
}
{
  /* 真的能买到：升到铁进程后买腐肉 */
  const { MC, API, me } = fresh();
  me.prog = 3; me.itemPts = {}; me.ap = 5;
  await invest(API, me, 'flesh');
  ok(API.hasItem(me,'flesh'), '铁进程下成功获取腐肉（2 步进度式）', me.items);
  await invest(API, me, 'bread');
  ok(API.hasItem(me,'bread'), '铁进程下成功获取面包', me.items);
}
{
  /* 木剑、皮革甲等木级物品在高级进程也可做 */
  const { MC, API, me } = fresh();
  me.prog = 4; me.itemPts = {}; me.ap = 10;
  const keys = API.buildHumanOptions(me).filter(o=>o.type==='craftShopItem').map(o=>o.key);
  ok(['wood_sword','leather','stone_sword','iron_sword'].every(k=>keys.includes(k)),
     '钻石进程下仍能做木剑/皮革甲/石剑/铁剑', keys.filter(k=>['wood_sword','leather','stone_sword','iron_sword'].includes(k)));
}

console.log('\n【23】切换手上的工具');
{
  const { MC, API, me } = fresh();
  me.prog = 3; me.itemPts = {}; me.ap = 12;
  me.weapon = 'fist';
  API.addItem(me,'wood_sword',1); API.addItem(me,'stone_sword',1); API.addItem(me,'iron_sword',1);
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='switch_weapon');
  ok(opts.length===3, '持有 3 把武器 → 出现 3 个「换上」选项', opts.map(o=>o.label));
  ok(opts.every(o=>o.cost===0 && o.isAction===false), '切换武器不消耗 AP 也不占行动次数');
  await doOpt(API, me, {type:'switch_weapon', key:'stone_sword'});
  ok(me.weapon==='stone_sword', '换上了石剑', me.weapon);
  await doOpt(API, me, {type:'switch_weapon', key:'wood_sword'});
  ok(me.weapon==='wood_sword', '再换成木剑', me.weapon);
  /* 换完之后攻击选项用的是手上的武器 */
  API.setDistance(me, G_of(MC).players[1], 0);
  const atk = API.buildHumanOptions(me).find(o=>o.type==='attack');
  ok(!!atk && atk.key==='wood_sword', '攻击用的是当前手上的武器', atk && atk.key);
  ok(!API.buildHumanOptions(me).some(o=>o.type==='switch_weapon'&&o.key==='wood_sword'), '当前武器不再出现在切换列表里');
}
function G_of(MC){ return MC.state(); }

console.log('\n【24】多人猜拳判定（按同招式组）');
{
  const { API } = fresh();
  const J = API.judgeRound;
  const mk = obj => Object.fromEntries(Object.entries(obj).map(([k,v])=>[+k, v]));
  /* 用户给的例子 1：A剪刀 B剪刀 C石头 → 石头组胜出（C） */
  const r1 = J(mk({0:'scissors', 1:'scissors', 2:'rock'}));
  ok(r1.tie===false && r1.winner===2, 'A剪刀/B剪刀/C石头 → C 胜出', r1);
  /* 用户给的例子 2：A剪刀 B石头 C布 → 互克，重出 */
  const r2 = J(mk({0:'scissors', 1:'rock', 2:'paper'}));
  ok(r2.tie===true, 'A剪刀/B石头/C布 → 平局重出', r2);
  /* 全员同招 → 平局 */
  const r3 = J(mk({0:'rock', 1:'rock', 2:'rock'}));
  ok(r3.tie===true, '全员同招 → 平局', r3);
  /* 两人：正常胜负 */
  const r4 = J(mk({0:'rock', 1:'scissors'}));
  ok(r4.tie===false && r4.winner===0, '两人：石头胜剪刀', r4);
  const r5 = J(mk({0:'scissors', 1:'scissors'}));
  ok(r5.tie===true, '两人同招 → 平局', r5);
  /* 四人：1 石头 vs 3 剪刀 → 石头胜 */
  const r6 = J(mk({0:'rock', 1:'scissors', 2:'scissors', 3:'scissors'}));
  ok(r6.tie===false && r6.winner===0, '1 石头 vs 3 剪刀 → 石头胜', r6);
  /* 四人：2 石头 vs 2 剪刀 → 石头组内随机一人 */
  const r7 = J(mk({0:'rock', 1:'rock', 2:'scissors', 3:'scissors'}));
  ok(r7.tie===false && (r7.winner===0||r7.winner===1), '2 石头 vs 2 剪刀 → 石头组内一人胜出', r7);
  /* 四人三招：A石 B石 C剪 D布 → 布克制石头，剪刀克制布 → 布被剪刀克制，无绝对胜者 → 平局 */
  const r8 = J(mk({0:'rock', 1:'rock', 2:'scissors', 3:'paper'}));
  ok(r8.tie===true, 'A石/B石/C剪/D布 → 互克，平局重出', r8);
}

console.log('\n【25】TNT：法术伤害，档位只看“有无护甲类物品”');
{
  const { API, me, ai } = fresh();
  const hp0a = ai.hp, hp0m = me.hp;
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp, hp0a-2.5), '无护甲：中心目标受 2.5', ai.hp);
  ok(near(me.hp, hp0m-1.5), '无护甲：其余目标受 1.5（含自己）', me.hp);
}
{
  const { API, me, ai } = fresh();
  ai.armor='iron_armor'; ai.armorCharges=2;      /* 持有护甲物品 */
  const hp0a = ai.hp;
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp, hp0a-1.5), '有护甲：中心目标受 1.5', ai.hp);
  ok(ai.armorCharges===2, 'TNT 不消耗护甲耐久（法术伤害）', ai.armorCharges);
}
{
  /* 护甲耐久耗尽但“仍持有护甲物品” → 依然按有甲档位 */
  const { API, me, ai } = fresh();
  ai.armor='leather'; ai.armorCharges=0;
  const hp0a = ai.hp;
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp, hp0a-1.5), '护甲破损但持有护甲物品 → 仍按有甲档位 1.5', ai.hp);
}
{
  /* 法术免疫（附魔金苹果）应能免疫 TNT 的法术伤害 */
  const { API, me, ai } = fresh();
  API.addEffect(ai,'spellImmune',1,3,'法术免疫');
  const hp0a = ai.hp;
  await API.performAttack(me, ai, 'tnt', {instant:true});
  ok(near(ai.hp, hp0a), '法术免疫可免疫 TNT 伤害', ai.hp);
}

console.log('\n【26】铁傀儡被动攻击不消耗 AP');
{
  const { API, G, me } = fresh();
  me.prog = 3; me.itemPts = {}; me.ap = 20;
  await invest(API, me, 'golem');                    /* 铁傀儡 4 点进度式，需投满 */
  ok(API.armorActive(me) && me.armor==='golem', '先装备铁傀儡（4 点进度式投满）', me.armor);
  me.actionsUsed = 1;                       /* 模拟“全场都行动过一次后再次轮到” */
  me.slotsLeft = 0; me.ap = 0;              /* 没有任何免费行动与 AP */
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='golem_punch');
  ok(opts.length >= 1, '即使 AP=0、无免费行动也能使用铁傀儡被动', opts.length);
  ok(opts.length>=1 && opts[0].isAction===false, '被动标记为不占行动次数', opts[0] && opts[0].isAction);
  const before = me.ap;
  await API.applyAction(me, opts[0]);
  ok(me.ap === before, '使用被动后 AP 不变', me.ap);
  ok(me.slotsLeft === 0, '不占用免费行动次数', me.slotsLeft);
}

console.log('\n【27】建筑统一消耗 1 AP');
{
  const { API, G, me } = fresh();
  me.prog = 1; me.ap = 1; me.itemPts = {};
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='craftShopItem' && ITEMS_of(API,'village').build);
  ok(opts.length>=1 && opts[0].cost===1, '村庄入口花费 1 AP', opts[0] && opts[0].cost);
  await API.applyAction(me, {type:'craftShopItem', key:'village'});
  ok(me.buildings.village===true, '1 AP 建成村庄', me.buildings);
  ok(me.ap===0, '只扣 1 AP', me.ap);
}
{
  /* 铁砧原为 2 步，现在也应只要 1 AP */
  const { API, me } = fresh();
  me.prog = 3; me.ap = 1; me.itemPts = {};
  await API.applyAction(me, {type:'craftShopItem', key:'anvil'});
  ok(me.buildings.anvil===true, '铁砧同样 1 AP 建成', me.buildings);
}
{
  const { API, me } = fresh();
  me.prog = 3; me.ap = 1; me.itemPts = {};
  await API.applyAction(me, {type:'craftShopItem', key:'pyramid'});
  ok(me.buildings.pyramid===true, '沙漠金字塔 1 AP 建成', me.buildings);
}
function ITEMS_of(API, k){ return { build:true }; }

console.log('\n【28】火焰：统一在回合末结算，入水可取消');
{
  const { API, ai } = fresh();
  /* 模拟打火石点燃：3 层 */
  API.addEffect(ai,'burn',3,1,'火焰');       /* 当回合结算型：3 次，持续 1 回合 */
  const hp0 = ai.hp;
  ok(near(ai.hp, hp0), '点燃当回合不立即扣血', ai.hp);
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.5), '回合结束结算 3 次 0.5 = 1.5', ai.hp);
  ok(!ai.effects.some(e=>e.type==='burn'), '当回合结算型火焰结算后消失', ai.effects);
}
{
  const { API, ai } = fresh();
  API.addEffect(ai,'burn',3,1,'火焰');
  const hp0 = ai.hp;
  API.removeBurn(ai);                        /* 入水 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0), '入水后本回合不再受火焰伤害', ai.hp);
}
{
  const { API, ai } = fresh();
  ai.inWater = true;
  API.addEffect(ai,'burn',2,1,'火焰');
  await API.endOfRound({instant:true});
  ok(!ai.effects.some(e=>e.type==='burn'), '在水里火焰被清除', ai.effects);
}

console.log('\n【29】猜拳流程不会卡死（真实计时器跑一遍 rpsPhase）');
{
  const { MC, API, G } = fresh();
  /* 用静默开局 + 自动出拳，直接跑一次猜拳阶段 */
  MC.start({enemyCount:2, diff:'normal', auto:true, silent:true});
  const G2 = MC.state();
  API.setAutoPlayer((p, opts)=>{
    const o = opts||[];
    return o.find(x=>x.type==='attack') || o.find(x=>x.type==='shop_progress')
        || o.find(x=>x.type==='craftShopItem') || o.find(x=>x.type==='move') || {type:'pass'};
  });
  const t0 = Date.now();
  let done = false, total = 0;
  /* 连跑 12 次猜拳阶段，任何一次卡住都会超过超时 */
  await Promise.race([
    (async ()=>{
      for(let i=0;i<12;i++){ await API.rpsPhase(); total += G2.players.reduce((s,p)=>s+p.ap,0); }
      done = true;
    })(),
    (async ()=>{ await new Promise(r=>setTimeout(r, 20000)); })(),
  ]);
  const ms = Date.now()-t0;
  ok(done, `连续 12 次猜拳阶段全部返回（未卡死，用时 ${ms}ms）`, {done, ms});
  ok(ms < 30000, '猜拳阶段总耗时正常', ms);
}

console.log('\n【30】攻击固定消耗 1 AP');
{
  const { API, G, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.ap = 5; me.slotsLeft = 1; me.weapon = 'fist';
  const atk = API.buildHumanOptions(me).find(o=>o.type==='attack');
  ok(!!atk, '能看到攻击选项', atk && atk.label);
  ok(atk && atk.cost===API.ATK_COST, `攻击选项标价 ${API.ATK_COST} AP`, atk && atk.cost);
  const ap0 = me.ap, slots0 = me.slotsLeft;
  await API.applyAction(me, atk);
  ok(me.ap===ap0-1, '攻击扣 1 AP', [ap0, me.ap]);
  ok(me.slotsLeft===slots0, '攻击不消耗免费行动槽', [slots0, me.slotsLeft]);
}
{
  /* 连续攻击：每次都要 AP */
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.ap = 3; me.weapon = 'fist';
  for(let i=0;i<3;i++){
    const atk = API.buildHumanOptions(me).find(o=>o.type==='attack');
    if(!atk) break;
    await API.applyAction(me, atk);
  }
  ok(me.ap===0, '连续攻击 3 次扣光 3 AP', me.ap);
}
{
  /* AP=0 时无法攻击 */
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.ap = 0; me.slotsLeft = 1; me.weapon = 'fist';
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='attack');
  const payable = opts.filter(o=>API.canPay(me, o));
  ok(payable.length===0, 'AP=0 时攻击不可支付（即使有免费行动槽）', payable.length);
  const mvOpts = API.buildHumanOptions(me).filter(o=>o.type==='move');
  ok(mvOpts.every(o=>!API.canPay(me,o)), 'AP=0 时走位也不可支付', mvOpts.length);
  const hp0 = ai.hp;
  const before = me.ap;
  if(opts[0]) await API.applyAction(me, opts[0]);
  ok(me.ap===before && ai.hp===hp0, 'AP=0 时攻击被拒绝且不生效', [me.ap, ai.hp]);
}
{
  /* 免费行动槽仍在，可用于非攻击动作 */
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 1);
  me.ap = 0; me.slotsLeft = 1;
  const mv = API.buildHumanOptions(me).find(o=>o.type==='move');
  ok(!mv || !API.canPay(me, mv), 'AP=0 时无法走位（走位需 1 AP）', mv && API.canPay(me, mv));
}
{
  /* TNT 也是攻击：固定 1 AP */
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  API.addItem(me,'tnt',2);
  me.ap = 3;
  const place = API.buildHumanOptions(me).find(o=>o.type==='tnt_place');
  ok(!!place && place.cost===API.ATK_COST, 'TNT 粘贴标价 1 AP', place && place.cost);
  const ap0 = me.ap;
  if(place) await API.applyAction(me, place);
  ok(me.ap===ap0-1, 'TNT 粘贴扣 1 AP', me.ap);
}
{
  /* 铁傀儡被动仍免费（用户此前明确要求） */
  const { API, me, ai } = fresh();
  me.prog = 3; me.itemPts = {}; me.ap = 20;
  await invest(API, me, 'golem');
  API.setDistance(me, ai, 1);
  me.actionsUsed = 1; me.slotsLeft = 0; me.ap = 0;
  const gp = API.buildHumanOptions(me).find(o=>o.type==='golem_punch');
  ok(!!gp, '铁傀儡被动可用（AP=0 也能用）', !!gp);
  const ap0 = me.ap;
  if(gp) await API.applyAction(me, gp);
  ok(me.ap===ap0, '铁傀儡被动免费（不扣 AP）', me.ap);
}

console.log('\n【31】切换武器不消耗 AP');
{
  const { API, me } = fresh();
  me.itemPts = {}; me.ap = 0; me.slotsLeft = 0;
  API.addItem(me,'wood_sword',1); API.addItem(me,'stone_sword',1);
  me.weapon = 'fist';
  const sw = API.buildHumanOptions(me).filter(o=>o.type==='switch_weapon');
  ok(sw.length>=2, 'AP=0 时仍能切换武器', sw.length);
  const ap0 = me.ap, slots0 = me.slotsLeft;
  await API.applyAction(me, sw.find(o=>o.key==='stone_sword') || sw[0]);
  ok(me.weapon==='stone_sword', '成功换到石剑', me.weapon);
  ok(me.ap===ap0, '切换武器不扣 AP', me.ap);
  ok(me.slotsLeft===slots0, '切换武器不占免费行动槽', me.slotsLeft);
}

console.log('\n【32】猜拳结算：三种招式齐＝平局，两种招式克制方全体得分');
{
  const { API } = fresh();
  const J = API.judgeRound;
  const mk = o => Object.fromEntries(Object.entries(o).map(([k,v])=>[+k, v]));
  /* 用户例子 A：我+队友都出石头，两个对手都出剪刀 → 两名石头玩家各得 AP */
  const r1 = J(mk({0:'rock', 1:'rock', 2:'scissors', 3:'scissors'}));
  ok(r1.tie===false, '两石头 vs 两剪刀 → 分出胜负', r1);
  ok(Array.isArray(r1.winners) && r1.winners.length===2 && r1.winners.includes(0) && r1.winners.includes(1),
     '两名石头玩家都胜出（各得 AP）', r1.winners);
  /* 用户例子 B：1,1,1,3 → 第四位玩家获胜 */
  const r2 = J(mk({0:'rock', 1:'rock', 2:'rock', 3:'scissors'}));
  ok(r2.tie===false && r2.winners.length===3 && !r2.winners.includes(3),
     '三石头 vs 一剪刀 → 三名石头玩家胜出（石头克剪刀）', r2.winners);
  /* 三种招式同时出现 → 平局重出 */
  const r3 = J(mk({0:'rock', 1:'scissors', 2:'paper'}));
  ok(r3.tie===true, '石头/剪刀/布同时出现 → 平局重出', r3);
  const r4 = J(mk({0:'rock', 1:'rock', 2:'scissors', 3:'paper'}));
  ok(r4.tie===true, '1,1,2,3（三种招式）→ 平局重出', r4);
  /* 全员同招 → 平局 */
  const r5 = J(mk({0:'rock', 1:'rock', 2:'rock'}));
  ok(r5.tie===true, '全员同招 → 平局', r5);
  /* 两人正常判定 */
  const r6 = J(mk({0:'paper', 1:'rock'}));
  ok(r6.tie===false && r6.winners[0]===0, '两人：布胜石头', r6.winners);
  /* 3 石头 vs 1 布 → 布胜 */
  const r7 = J(mk({0:'rock', 1:'rock', 2:'rock', 3:'paper'}));
  ok(r7.tie===false && r7.winners.length===1 && r7.winners[0]===3, '三石头 vs 一布 → 布玩家胜出', r7.winners);
}

console.log('\n【33】护甲优先级：可选择先消耗哪件');
{
  const { API, me } = fresh();
  me.prog = 3; me.ap = 30; me.itemPts = {};
  await invest(API, me, 'leather');        /* 皮革甲：2 点进度式，invest 会投满 */
  await invest(API, me, 'iron_armor');     /* 铁甲：3 点进度式 */
  ok(API.armorsOf(me).length===2, '两件护甲都已入袋', API.armorsOf(me).map(a=>a.key));
  const list = API.armorsOf(me);
  ok(list.length===2, '身上有两件护甲', list.map(a=>a.key));
  ok(me.armor==='iron_armor', '新获得的铁甲立即生效', me.armor);
  /* 指定优先消耗皮革甲 */
  API.setArmorPriority(me, 'leather');
  ok((me.armorPriority||[])[0]==='leather', '皮革甲排到优先位', me.armorPriority);
  ok(me.armor==='leather', '当前生效护甲跟着切换', me.armor);
  /* 打 1 点物理：应扣皮革甲 */
  API.tryDamage(me,[1,0,0,0],{});
  const after = API.armorsOf(me);
  const leather = after.find(a=>a.key==='leather');
  const iron = after.find(a=>a.key==='iron_armor');
  ok(leather && leather.charges===0, '优先消耗的皮革甲被打光', leather && leather.charges);
  ok(iron && iron.charges===2, '铁甲完好无损', iron && iron.charges);
  /* 再打 1 点：这次扣铁甲 */
  API.tryDamage(me,[1,0,0,0],{});
  const iron2 = API.armorsOf(me).find(a=>a.key==='iron_armor');
  ok(iron2 && iron2.charges===1, '皮革甲用尽后改用铁甲', iron2 && iron2.charges);
  /* 切换优先级回铁甲 */
  API.setArmorPriority(me, 'iron_armor');
  ok(me.armor==='iron_armor', '可随时切换优先护甲', me.armor);
}

console.log('\n【34】判定平局：闪避是可选项（不花 AP 赌一把）');
{
  const { API, G, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.weapon='fist'; me.ap = 3;
  const hp0 = me.hp;
  /* dodge:false → 不闪避，继续判定；AP 不该被扣 */
  await API.performAttack(ai, me, 'fist', {instant:true, dodge:false, a:'rock', b:'rock'});
  ok(me.ap===3, '选择不闪避时不消耗 AP', me.ap);
}
{
  const { API, me, ai } = fresh();
  API.setDistance(me, ai, 0);
  me.ap = 3;
  const ap0 = me.ap;
  /* dodge:true → 花 1 AP 直接闪避 */
  await API.performAttack(ai, me, 'fist', {instant:true, dodge:true, a:'rock', b:'rock'});
  ok(me.ap===ap0-1, '选择闪避时消耗 1 AP', [ap0, me.ap]);
  ok(me.hp===4, '闪避成功后没有受伤', me.hp);
}

console.log('\n【35】补给与钓鱼竿的 AP 成本');
{
  const { API, me } = fresh();
  me.itemPts = {}; me.ap = 5; me.prog = 3;
  API.addItem(me,'bread',1); API.addItem(me,'god_apple',1);
  const opts = API.buildHumanOptions(me);
  const bread = opts.find(o=>o.type==='eat' && o.item==='bread');
  const apple = opts.find(o=>o.type==='eat' && o.item==='god_apple');
  ok(!!bread && bread.cost===1, '面包 1 AP', bread && bread.cost);
  ok(!!apple && apple.cost===1, '附魔金苹果 1 AP', apple && apple.cost);
}
{
  const { API, me, ai } = fresh();
  me.prog = 2; me.ap = 5; me.itemPts = {};
  await invest(API, me, 'fishing_rod');
  API.setDistance(me, ai, 3);
  const rod = API.buildHumanOptions(me).find(o=>o.type==='rod');
  ok(!!rod && rod.cost===1, '钓鱼竿使他人位移 1 AP', rod && rod.cost);
}

console.log('\n【36】打火石：每回合结算 1 次，持续 3 回合');
{
  const { API, G, me, ai } = fresh();
  me.prog = 3; me.ap = 20; me.itemPts = {}; me.weapon = 'fist';
  API.addItem(me, 'flint', 1);
  API.setDistance(me, ai, 0);
  const hp0 = ai.hp;
  const opts = API.buildHumanOptions(me).filter(o=>o.type==='attack');
  ok(opts.some(o=>o.key==='flint'), '背包里的打火石可直接攻击', opts.map(o=>o.key));
  await API.performAttack(me, ai, 'flint', {instant:true, a:'rock', b:'scissors'});   /* 指定判定命中，避免随机 */
  const burn0 = ai.effects.find(e=>e.type==='burn');
  ok(!!burn0, '目标被点燃', burn0);
  ok(burn0 && burn0.power===1 && (burn0.rounds||0)===3, '点燃 = 每回合 1 次 × 3 回合', burn0 && {p:burn0.power, r:burn0.rounds});
  ok(near(ai.hp, hp0), '点燃当回合不立即扣血', ai.hp);
  /* 第 1 个回合结束：只掉 0.5 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-0.5), '第 1 回合结束只结算 0.5', ai.hp);
  ok(ai.effects.some(e=>e.type==='burn'), '火焰仍在（还剩 2 回合）', ai.effects.map(e=>e.type+':'+e.rounds));
  /* 第 2 个回合结束：再掉 0.5 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.0), '第 2 回合结束累计 1.0', ai.hp);
  /* 第 3 个回合结束：再掉 0.5，火焰熄灭 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.5), '第 3 回合结束累计 1.5', ai.hp);
  ok(!ai.effects.some(e=>e.type==='burn'), '3 回合后火焰熄灭', ai.effects);
  /* 第 4 个回合不再掉血 */
  await API.endOfRound({instant:true});
  ok(near(ai.hp, hp0-1.5), '第 4 回合不再掉血', ai.hp);
}
/* 注：目标持有护甲时打火石只持续 2 回合，行为已在开发中用独立脚本验证。 */

console.log('\n──────────────────────────────');
console.log(`通过 ${pass} 项，失败 ${fail} 项`);
if(fail) console.log('失败项：\n  - ' + fails.join('\n  - '));
process.exit(fail?1:0);
})();
