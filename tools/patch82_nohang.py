# -*- coding: utf-8 -*-
"""补丁 82：【卡死根治】askHuman 在“没有实质可选行动”时总是给出「结束回合」按钮
   问题：攻击后若 AP/免费行动耗尽，面板里只剩下 换武器/制作面板 这类免费动作，
        而“结束回合”按钮在 pass 过滤中丢失 → 玩家无按钮可点 → 界面卡死。
   修复：只要没有任何“花 AP 或占行动槽”的实质行动，就立刻补一个醒目的「结束回合」按钮。
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

old = """    const realOpts = (opts||[]).filter(o=>o.type!=='pass');
    /* 【防卡死】没有任何可用行动时，直接结束回合，绝不空等 */
    if(realOpts.length === 0){
      const bar0 = document.getElementById('actionbar');
      if(bar0){
        bar0.innerHTML = '<div><span class="pill on">你的回合</span><span class="pill">没有可用行动</span></div>';
        const b0 = document.createElement('button');
        b0.className = 'btn pri';
        b0.textContent = '⏭ 结束回合';
        b0.onclick = ()=>{ try{ sfx.click(); }catch(e){} settle({type:'pass'}); };
        bar0.appendChild(b0);
      }
      /* 即使按钮被移除也兜底 */
      setTimeout(()=>settle({type:'pass'}), 1200);
      return;
    }"""

new = """    const allOpts = opts || [];
    /* 实质行动 = 需要花 AP 或占行动槽的动作（换武器/制作面板/结束回合都不算） */
    const substantive = allOpts.filter(o=>
      o.type !== 'pass' && o.type !== 'shop_craft' && o.type !== 'switch_weapon'
      && o.type !== 'armor_priority' && (o.cost||0) + (o.isAction!==false ? 1 : 0) > 0);
    /* 【防卡死】没有任何实质行动可做 → 立刻只给一个「结束回合」，绝不空等 */
    if(substantive.length === 0){
      const bar0 = document.getElementById('actionbar');
      if(bar0){
        bar0.innerHTML = '<div><span class="pill on">你的回合</span>'
          + `<span class="pill">行动点 ${p.ap}</span>`
          + '<span class="pill">本回合已无可做的行动</span></div>';
        const b0 = document.createElement('button');
        b0.className = 'btn pri';
        b0.textContent = '⏭ 结束回合';
        b0.onclick = ()=>{ try{ sfx.click(); }catch(e){} settle({type:'pass'}); };
        bar0.appendChild(b0);
      }
      /* 即使按钮被移除也兜底自动结束 */
      setTimeout(()=>settle({type:'pass'}), 1500);
      return;
    }"""

if old in t:
    t = t.replace(old, new, 1)
    IDX.write_text(t, encoding='utf-8')
    print('已修：无实质行动时总是给出「结束回合」按钮')
else:
    print('! 锚点未匹配')

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
