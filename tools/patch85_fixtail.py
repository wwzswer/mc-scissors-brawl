# -*- coding: utf-8 -*-
"""补丁 85：修正 buildActionPanel 重构遗留（res → settle，去掉多余的 });）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
n = 0

# 1) 商店按钮与结束回合按钮：res(o) → settle(o)
pairs = [
    ("    b.onclick=()=>{ sfx.click(); res(o); };",
     "    b.onclick=()=>{ try{ sfx.click(); }catch(e){} settle(o); };"),
    ("    bp.onclick=()=>{ sfx.click(); res({type:'pass'}); };",
     "    bp.onclick=()=>{ try{ sfx.click(); }catch(e){} settle({type:'pass'}); };"),
]
for old, new in pairs:
    if old in t:
        t = t.replace(old, new, 1); n += 1
        print('  ok 替换', old.strip()[:40])
    else:
        print('  ! 未找到', old.strip()[:40])

# 2) buildActionPanel 的收尾：把 "  });\n}" 改成 "  }\n}"
#    精确定位：紧跟 hint 之后的收尾
old_tail = """    bar.appendChild(hint);
  });
}

function openShop(p, craftFirst){"""
new_tail = """    bar.appendChild(hint);
  }
}

function openShop(p, craftFirst){"""
if old_tail in t:
    t = t.replace(old_tail, new_tail, 1); n += 1
    print('  ok 修正函数收尾括号')
else:
    print('  ! 未找到收尾锚点')

IDX.write_text(t, encoding='utf-8')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print(f'共修正 {n} 处')
