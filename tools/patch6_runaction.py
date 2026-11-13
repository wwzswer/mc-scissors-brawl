# -*- coding: utf-8 -*-
"""补丁 6：补回被覆盖的 runAction 定义，并检查其它缺失函数"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
html = IDX.read_text(encoding='utf-8')

RUN = """/* 统一的“执行一个动作”入口：按类型分派（人类点击与 AI 决策共用同一条结算路径） */
async function runAction(p, a){
  if(!a) return false;
  if(a.type==='shop_progress' || a.type==='upgrade') return applyShopAction(p, {type:'upgrade', cost:a.cost});
  if(a.type==='craftShopItem' || a.type==='craft') return applyShopAction(p, {type:'craft', key:a.key, cost:a.cost});
  if(a.type==='buy_tnt' || a.type==='buy_apple') return applyShopAction(p, a);
  await applyAction(p, a);
  return true;
}
"""
if 'function runAction(' not in html:
    anchor = '/* 自动化测试入口（浏览器控制台或 Node 冒烟测试均可调用） */'
    assert anchor in html, '缺少导出锚点'
    html = html.replace(anchor, RUN + anchor, 1)
    print('已补回 runAction')
else:
    print('runAction 已存在')

IDX.write_text(html, encoding='utf-8')

# ---- 检查所有被调用的顶层函数是否都有定义 ----
js = html.split('<script>')[1].split('</script>')[0]
called = set(re.findall(r'(?<![\w.$])([a-zA-Z_$][\w$]*)\s*\(', js))
defined = set(re.findall(r'function\s+([a-zA-Z_$][\w$]*)\s*\(', js))
defined |= set(re.findall(r'(?:const|let|var)\s+([a-zA-Z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*=>', js))
defined |= set(re.findall(r'(?:const|let|var)\s+([a-zA-Z_$][\w$]*)\s*=\s*function', js))
BUILTIN = {'if','for','while','switch','catch','return','typeof','function','new','await','then','map','filter',
 'forEach','find','findIndex','some','every','reduce','join','split','replace','slice','concat','push','pop',
 'shift','unshift','splice','indexOf','includes','trim','toUpperCase','toLowerCase','padStart','padEnd','round',
 'floor','ceil','abs','min','max','random','stringify','parse','keys','values','entries','assign','from','isArray',
 'setTimeout','clearTimeout','setInterval','clearInterval','fetch','parseInt','parseFloat','isNaN','Number','String',
 'Array','Object','JSON','Math','Promise','Set','Map','Date','Error','RegExp','resolve','reject','sort','test',
 'match','matchAll','search','charAt','charCodeAt','substring','substr','repeat','startsWith','endsWith','at',
 'addEventListener','removeEventListener','querySelector','querySelectorAll','getElementById','createElement',
 'appendChild','remove','toggle','add','contains','getAttribute','setAttribute','click','focus','blur','open',
 'close','write','end','send','json','text','item','getItem','setItem','has','delete','clear','entries','fill',
 'keys','call','apply','bind','toString','valueOf','toFixed','toPrecision','localeCompare','fromCharCode',
 'requestAnimationFrame','alert','confirm','prompt','encodeURIComponent','decodeURIComponent','isFinite','Boolean',
 'Symbol','WeakMap','Proxy','Reflect','structuredClone','queueMicrotask','finally','catch','constructor'}
missing = sorted(x for x in called if x not in defined and x not in BUILTIN and not x.startswith('_') and len(x)>2)
print('可能缺失的顶层函数:', missing if missing else '（无）')
