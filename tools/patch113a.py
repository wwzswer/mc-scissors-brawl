# -*- coding: utf-8 -*-
"""补丁 113：设置里新增 4 个开关（不死图腾 / 药水 / TNT / 附魔金苹果）
   - 关闭后：相关物品不再出现在商店与行动选项里，也无法获得
   - 偏好保存到 localStorage，并在开局日志里说明
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

# ---------- 1) 开关变量 ----------
sub("""let playerName = '你';""",
"""let playerName = '你';
/* 可选内容开关（设置里可分别启用/禁用） */
const FEATURE_KEYS = { totem:'不死图腾', potion:'药水', tnt:'TNT', god_apple:'附魔金苹果' };
let features = { totem:true, potion:true, tnt:true, god_apple:true };
function featOn(k){ return features[k] !== false; }""", '① 开关变量')

# ---------- 2) 保存 / 读取设置 ----------
sub("""function saveSettings(){
  try{
    localStorage.setItem('mcSettings', JSON.stringify({ name:playerName, mode:gameMode, enemy:enemyCount, diff:diffKey, auto:autoMode, ap:apPerWin }));""",
"""function saveSettings(){
  try{
    localStorage.setItem('mcSettings', JSON.stringify({ name:playerName, mode:gameMode, enemy:enemyCount, diff:diffKey, auto:autoMode, ap:apPerWin, features }));""",
'② saveSettings 存开关')

sub("""    const s = JSON.parse(localStorage.getItem('mcSettings') || 'null');
    if(s){}""",
"""    const s = JSON.parse(localStorage.getItem('mcSettings') || 'null');
    if(s && s.features && typeof s.features === 'object'){
      for(const k of Object.keys(FEATURE_KEYS)) if(k in s.features) features[k] = !!s.features[k];
    }""", '② loadSettings 读开关')

IDX.write_text(t, encoding='utf-8')
print('第一段：')
print('\n'.join(notes))
print(f'  长度 {orig} → {len(t)}')
