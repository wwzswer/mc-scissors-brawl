# -*- coding: utf-8 -*-
"""补丁 99：彻底清掉未定义的 render() 调用（商店内部的 local render 除外）"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
n = 0

# 形如 “render(); renderAll();” → “renderAll();”（这些位置的 render 未定义）
t2, a = re.subn(r'\brender\(\);\s*renderAll\(\);', 'renderAll();', t)
n += a
# 形如 “fn(); render(); renderAll();” 之类已含分号的情况
t2, b = re.subn(r'\brender\(\);(?!\s*renderAll)', '/* render() 已移除 */', t2)
n += b
t = t2

IDX.write_text(t, encoding='utf-8')
print(f'共清理 {n} 处')

# 复查：列出所有还引用 render() 的行，人工判断
rest = [l.strip()[:120] for l in t.split('\n') if re.search(r'(?<![A-Za-z_.])render\(\)', l)]
print('\n剩余引用 render() 的行：')
for l in rest:
    print('  ', l)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
