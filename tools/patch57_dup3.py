# -*- coding: utf-8 -*-
"""补丁 57：清理剩余重复定义（hideRpsSlots / rpsPrompt）"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

def show(fn):
    for m in re.finditer(r'(?:^|\n)(?:async )?function ' + fn + r'\(', t):
        i = m.start()
        depth = 0; j = i
        while j < len(t):
            if t[j] == '{': depth += 1
            elif t[j] == '}':
                depth -= 1
                if depth == 0: break
            j += 1
        print(f'--- {fn} @{i} ---')
        print(t[i:j+1][:320])
        print()

show('hideRpsSlots')
show('rpsPrompt')

# 删除重复的 hideRpsSlots（保留第一个）
matches = list(re.finditer(r'(?:^|\n)function hideRpsSlots\(\)\{', t))
if len(matches) > 1:
    m = matches[1]
    i = m.start()
    depth = 0; j = i
    while j < len(t):
        if t[j] == '{': depth += 1
        elif t[j] == '}':
            depth -= 1
            if depth == 0: break
        j += 1
    t = t[:i] + t[j+1:]
    print('已删除重复的 hideRpsSlots')

IDX.write_text(t, encoding='utf-8')
print('hideRpsSlots 剩余:', len(re.findall(r'(?:^|\n)function hideRpsSlots\(\)\{', t)))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
