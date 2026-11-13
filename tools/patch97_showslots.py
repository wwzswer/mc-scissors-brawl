# -*- coding: utf-8 -*-
"""补丁 97：删除重复的 showSlots，并让其空安全"""
import pathlib, re

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

def fn_span(src, name):
    out = []
    for m in re.finditer(r'(?:^|\n)function ' + name + r'\(', src):
        i = m.start()
        depth = 0; j = i
        while j < len(src):
            if src[j] == '{': depth += 1
            elif src[j] == '}':
                depth -= 1
                if depth == 0: break
            j += 1
        out.append((i, j+1, src[i:j+1]))
    return out

spans = fn_span(t, 'showSlots')
print('showSlots 定义数:', len(spans))

# 删除后面的重复定义
if len(spans) > 1:
    i, j, body = spans[-1]
    t = t[:i] + t[j:]
    print('已删除重复的 showSlots')
    spans = fn_span(t, 'showSlots')

# 空安全重写（保留的那一份）
if spans:
    i, j, old = spans[0]
    new = """
function showSlots(a,b,aWin,bWin){
  try{
    const area = document.getElementById('rpsArea');
    const btns = document.getElementById('rpsBtns');
    if(area) area.classList.remove('hidden');
    if(btns) btns.classList.add('hidden');
    const sa=document.getElementById('slotA'), sb=document.getElementById('slotB');
    if(sa){ sa.textContent = RPS_GLYPH[a] || '❔'; sa.className='slot'+(aWin?' win':(bWin?' lose':'')); }
    if(sb){ sb.textContent = RPS_GLYPH[b] || '❔'; sb.className='slot'+(bWin?' win':(aWin?' lose':'')); }
    const st = document.getElementById('rpsStatus');
    if(st) st.textContent = aWin ? '判定成功：命中！' : (bWin ? '判定失败：攻击失效' : '平局，重新判定…');
  }catch(e){ /* 界面元素缺失也不影响流程 */ }
}"""
    t = t[:i] + new + t[j:]
    print('已重写为安全版本')

IDX.write_text(t, encoding='utf-8')
import re as _re
print('showSlots 现在数量:', len(_re.findall(r'(?:^|\n)function showSlots\(', t)))
print('hideRpsSlots 数量:', len(_re.findall(r'(?:^|\n)function hideRpsSlots\(', t)))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
