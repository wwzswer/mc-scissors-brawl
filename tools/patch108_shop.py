# -*- coding: utf-8 -*-
"""补丁 108：修复商店面板空白 + 金字塔选项不刷新
   根因：
     ① openShop 内只调用 renderAll()，从未调用 render() → 商店内容从未渲染
     ② renderAll() 会重建行动面板并 bar.innerHTML='' → 把商店 DOM 冲掉
   方案：
     - openShop 内一律改用 render()（渲染商店自身内容）
     - 打开商店时清空 pendingChoice（阻止 renderAll 重建行动面板），返回时恢复
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
orig = len(t)
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ① 打开商店时禁止行动面板重绘 + 首次渲染商店内容
sub("""  t1.onclick=()=>{ mode='craft'; t1.classList.add('on'); t2.classList.remove('on'); renderAll(); };
  t2.onclick=()=>{ mode='progress'; t2.classList.add('on'); t1.classList.remove('on'); renderAll(); };
  renderAll();""",
"""  /* 商店打开期间禁止 renderAll 重建行动面板（否则会把商店 DOM 冲掉） */
  const savedPending = pendingChoice;
  pendingChoice = null;
  t1.onclick=()=>{ mode='craft'; t1.classList.add('on'); t2.classList.remove('on'); render(); };
  t2.onclick=()=>{ mode='progress'; t2.classList.add('on'); t1.classList.remove('on'); render(); };
  render();                     /* 关键：渲染商店内容（此前误用了 renderAll） */""",
'商店首次渲染 + 锁定面板')

# ② 返回行动时恢复面板
sub("""  b.onclick=()=>{ sfx.click(); resolve(); };
  back.appendChild(b); box.appendChild(back);
  bar.innerHTML=''; bar.appendChild(box);
  });""",
"""  b.onclick=()=>{
    try{ sfx.click(); }catch(e){}
    pendingChoice = savedPending;      /* 恢复：允许行动面板重绘 */
    resolve();
  };
  back.appendChild(b); box.appendChild(back);
  bar.innerHTML=''; bar.appendChild(box);
  });""", '返回时恢复面板')

# ③ 商店内的动作点击后应刷新商店内容（而非重建行动面板）
sub("""        d.onclick=()=>{ if(p.ap<1) return; applyShopAction(p,{type:'upgrade'}); renderAll(); };""",
"""        d.onclick=()=>{ if(p.ap<1) return; applyShopAction(p,{type:'upgrade'}); render(); };""",
'进程投入→刷新商店')
sub("""        d.onclick=()=>{ if(p.ap<(it.build?BUILD_COST:1)) return; applyShopAction(p,{type:'craft',key:k}); renderAll(); };""",
"""        d.onclick=()=>{ if(p.ap<(it.build?BUILD_COST:1)) return; applyShopAction(p,{type:'craft',key:k}); render(); };""",
'制作/建造→刷新商店')
sub("""          d.onclick=()=>{ if(p.ap<1) return; applyEnchant(p,k); renderAll(); };""",
"""          d.onclick=()=>{ if(p.ap<1) return; applyEnchant(p,k); render(); };""",
'附魔→刷新商店')
sub("""    d.onclick=()=>{ if(p.ap<cost) return; p.ap-=cost; fn(); log(`🏜️ ${lname(p)} 从沙漠金字塔取得 <b>${title}</b>。`,'l-good'); sfx.win(); renderAll(); };""",
"""    d.onclick=()=>{
      if(p.ap<cost) return;
      p.ap-=cost; fn();
      log(`🏜️ ${lname(p)} 从沙漠金字塔取得 <b>${title}</b>。`,'l-good');
      try{ sfx.win(); }catch(e){}
      render(); re25();      /* 刷新商店内容，让选项消失 */
    };""", '金字塔选项→刷新商店')

# 修掉上面故意留的占位（保持代码整洁）
t = t.replace('render(); re25();      /* 刷新商店内容，让选项消失 */',
              'render(); renderAll();  /* 刷新商店内容（同时更新玩家面板） */')
notes.append('  ok 修正占位调用')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
back = IDX.read_text(encoding='utf-8')
print()
print('--- 落盘校验 ---')
print(f'  长度 {orig} → {len(back)}（+{len(back)-orig}）')
print('  openShop 调用 render():', 'render();                     /* 关键：渲染商店内容（此前误用了 renderAll） */' in back)
print('  商店锁定面板:', 'const savedPending = pendingChoice;' in back)
print('  金字塔按钮刷新:', 're25' not in back)

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    back.split('<script>')[1].split('</script>')[0], encoding='utf-8')
