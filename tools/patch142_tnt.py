# -*- coding: utf-8 -*-
"""补丁 142：修复 TNT 引爆被静默拦截
   原因：patch133 加的"攻击前置检查"要求动作必须带 targetId，
        但 tnt_detonate 的目标存在 p.flags.tntOn 里，选项本身没有 targetId
        → if(!_T) return 把引爆直接拦掉（表现为"TNT 泡水了"，毫无伤害）
   修复：只在动作确实指定了目标时才做目标/距离校验
"""
import pathlib, os, subprocess

D = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
IDX = D / 'index.html'
t = IDX.read_text(encoding='utf-8')
orig = len(t)

OLD = """      /* 【前置检查】先确认目标与距离是否合法，再扣 AP —— 避免“先扣了 AP 才说打不到” */
      const _T = (a.targetId!==undefined && a.targetId!==null) ? P(a.targetId) : null;
      if(!_T){ log('目标不存在，攻击取消。','l-warn'); return; }
      if(!_T.alive){ log('目标已无法被攻击。','l-warn'); return; }
      if(!inRangeOf(p, a.key || p.weapon || 'fist', _T)){
        log(`${ITEMS[a.key]?ITEMS[a.key].name:'攻击'} 距离不合适（当前 ${distanceBetween(p,_T)} 格），未消耗 AP。`,'l-warn');
        return;
      }"""
NEW = """      /* 【前置检查】仅在动作确实指定了目标时校验（tnt_detonate 的目标存在 flags 里，选项不带 targetId） */
      const _T = (a.targetId!==undefined && a.targetId!==null) ? P(a.targetId) : null;
      if(_T){
        if(!_T.alive){ log('目标已无法被攻击。','l-warn'); return; }
        if(!inRangeOf(p, a.key || p.weapon || 'fist', _T)){
          log(`${ITEMS[a.key]?ITEMS[a.key].name:'攻击'} 距离不合适（当前 ${distanceBetween(p,_T)} 格），未消耗 AP。`,'l-warn');
          return;
        }
      }"""

if OLD in t:
    t = t.replace(OLD, NEW, 1)
    print('ok 前置检查改为"仅在有目标时校验"')
else:
    print('! 锚点未匹配')
    # 尝试定位实际文本
    i = t.find('【前置检查】先确认目标与距离是否合法')
    print('实际文本:', repr(t[i-40:i+400]) if i >= 0 else '未找到')

IDX.write_text(t, encoding='utf-8')
print('长度 %d → %d' % (orig, len(t)))
js = t.split('<script>')[1].split('</script>')[0]
tmp = pathlib.Path(os.environ['TEMP']) / 'chk142.js'
tmp.write_text(js, encoding='utf-8')
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(tmp)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
