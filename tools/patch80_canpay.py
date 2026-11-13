# -*- coding: utf-8 -*-
"""补丁 80：canPay 与按钮标价对齐新规则
   - 攻击 / 位移 / 免费动作：不叠加免费行动槽成本
   - 其余动作：仍按“1 次免费行动，之后 1 AP”
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')
notes = []

def sub(old, new, label):
    global t
    if old not in t:
        notes.append('  ! 未找到 ' + label); return False
    t = t.replace(old, new, 1); notes.append('  ok ' + label); return True

# ---- canPay ----
sub("""function canPay(p, opt){
  const c = (opt.type==='craftShopItem' && ITEMS[opt.key] && !ITEMS[opt.key].build) ? 1 : (opt.cost||0);
  const s = (opt.isAction!==false) ? actionSlotCost(p) : 0;   /* 购买类动作不占行动次数 */
  if(c+s===Infinity) return false;
  return p.ap >= c+s;
}""",
"""function canPay(p, opt){
  const c = (opt.type==='craftShopItem' && ITEMS[opt.key] && !ITEMS[opt.key].build) ? 1 : (opt.cost||0);
  /* 攻击 / 位移 / 免费即时动作：只按各自标价，不叠加免费行动槽 */
  const noSlot = (typeof isAttackAction==='function' && isAttackAction(opt))
              || MOBILITY_TYPES.includes(opt.type)
              || FREE_TYPES.includes(opt.type)
              || opt.isAction===false;
  const s = noSlot ? 0 : actionSlotCost(p);
  if(c+s===Infinity) return false;
  return p.ap >= c+s;
}""", 'canPay 对齐')

# 常量集合
sub("""const ATTACK_TYPES = ['attack','tnt_place','tnt_detonate'];""",
"""const ATTACK_TYPES   = ['attack','tnt_place','tnt_detonate'];
const MOBILITY_TYPES = ['move','rod','pearl','water_pull','rod_water','fish_trident'];   /* 位移：固定 1 AP */
const FREE_TYPES     = ['switch_weapon','armor_priority','pass','golem_punch'];          /* 免费即时动作 */""",
'常量集合')

# applyAction 用同一套常量
sub("""  /* 免费即时动作：不占行动次数、也不花 AP */
  const isFree = ['switch_weapon','armor_priority','pass','golem_punch'].includes(a.type);
  /* 位移类：固定 1 AP（MOVE_COST），不占用免费行动槽 */
  const isMobility = ['move','rod','pearl','water_pull','rod_water','fish_trident'].includes(a.type);""",
"""  /* 免费即时动作：不占行动次数、也不花 AP */
  const isFree = FREE_TYPES.includes(a.type);
  /* 位移类：固定 1 AP（MOVE_COST），不占用免费行动槽 */
  const isMobility = MOBILITY_TYPES.includes(a.type);""", 'applyAction 复用常量')

# ---- 按钮标价 ----
sub("""    const mk=(o)=>{
      const b=document.createElement('button');
      b.className='btn small';
      const slot = o.isAction!==false ? actionSlotCost(p) : 0;
      const extra = (o.cost||0)+slot;
      b.textContent = o.label + (extra>0?` · ${extra} AP`:' · 免费');""",
"""    const mk=(o)=>{
      const b=document.createElement('button');
      b.className='btn small';
      /* 标价与 canPay 保持一致：攻击/位移/免费动作不叠加免费行动槽 */
      const noSlot = isAttackAction(o) || MOBILITY_TYPES.includes(o.type)
                  || FREE_TYPES.includes(o.type) || o.isAction===false;
      const slot = noSlot ? 0 : actionSlotCost(p);
      const extra = (o.cost||0)+slot;
      const fixed = (extra===Infinity) ? '行动点不足'
                  : (extra>0 ? `${extra} AP` : '免费');
      b.textContent = o.label + ' · ' + fixed;
      b.disabled = (extra===Infinity);""", '按钮标价对齐')

IDX.write_text(t, encoding='utf-8')
print('\n'.join(notes))
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
print('文件', round(len(t)/1024,1), 'KB')
