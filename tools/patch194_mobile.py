import io

p = 'index.html'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label):
    global s
    assert old in s, '锚点不存在: ' + label
    s = s.replace(old, new, 1)
    print('  ok', label)

# 1) 手机端隐藏的次要提示
sub("""  if(ws.length>1) out.push(`<span style="color:var(--acc2);font-size:11px">（可换：${ws.filter(k=>k!==p.weapon).map(k=>ITEMS[k].name).join('/')}）</span>`);""",
    """  if(ws.length>1) out.push(`<span class="mo-hide" style="color:var(--acc2);font-size:11px">（可换：${ws.filter(k=>k!==p.weapon).map(k=>ITEMS[k].name).join('/')}）</span>`);""",
    '可换提示包一层')

sub("""        <span class="k">行动点</span><span class="v">${sprTag('coin',18)} ${p.ap}<span style="color:var(--dim);font-size:11px">（本回合内有效）</span></span>""",
    """        <span class="k">行动点</span><span class="v">${sprTag('coin',18)} ${p.ap}<span class="mo-hide" style="color:var(--dim);font-size:11px">（本回合内有效）</span></span>""",
    'AP 提示包一层')

# 2) 游戏中收起大标题/副标题（手机上省一大截空间）
sub("""  if(id==='screen-start') refreshStartInfo();
  try{ updateBackBtn(); updateFabVisibility(); }catch(e){}""",
    """  if(id==='screen-start') refreshStartInfo();
  try{ document.body.classList.toggle('playing', id==='game'); }catch(e){}
  try{ updateBackBtn(); updateFabVisibility(); }catch(e){}""",
    'body.playing')

# 3) 手机端细节 CSS 补充
sub("""  #overlay .box{padding:12px 14px;border-radius:14px}
}""",
    """  #overlay .box{padding:12px 14px;border-radius:14px}

  /* 玩游戏时收起标题，顶栏一行放下 pills */
  body.playing h1, body.playing .sub{display:none}
  body.playing #app{padding-top:40px}
  #game > .card:nth-child(1){padding:6px 8px}
  #game > .card:nth-child(1) .row{gap:4px}
  #game .pill{font-size:10px;padding:1px 5px;margin:0 2px 0 0}
  #autoToggle{font-size:11px;padding:4px 8px;border-radius:8px}
  .mo-hide{display:none !important}
  .stat .v{font-size:10.5px;line-height:1.45}
  .stat .k{white-space:nowrap}
  /* 抽屉里的商品卡也瘦一点 */
  #fabSheetBody .item{padding:6px 8px;border-radius:9px}
  #fabSheetBody .item .it{font-size:12px}
  #fabSheetBody .item .desc{font-size:10.5px;line-height:1.45}
  #fabSheetBody .progrow .dot{width:8px;height:8px}
  #fabSheetBody .tab{font-size:11px;padding:6px 8px}
}""",
    '手机端细节')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patch194 完成: %d -> %d bytes' % (n0, len(s)))
