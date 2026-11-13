# -*- coding: utf-8 -*-
"""补丁 12：联机辅助接口（供自动化测试与外部脚本调用）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

helper = """/* 联机辅助（供自动化测试 / 外部脚本调用） */
function netCreateRoomWith(name){
  return Net.create(name || playerName, {mode:gameMode, apPerWin, diff:diffKey})
    .then(d=>({ok:true, code:d.code, youId:d.youId}))
    .catch(e=>({ok:false, err:String(e && e.message || e)}));
}
function netJoinRoomWith(code, name){ return Net.join(code, name || playerName); }

"""
if 'function netCreateRoomWith' not in t:
    anchor = 'function netNeedServer(){'
    assert anchor in t
    t = t.replace(anchor, helper + anchor, 1)

# 导出联机接口
old = '    progNeed, progProgress, progMaxed, addProgPoint, setSeed,'
new = ('    progNeed, progProgress, progMaxed, addProgPoint, setSeed,\n'
       '    get Net(){ return Net; }, netCreateRoomWith, netJoinRoomWith, netIsOn, netHandleEvent,\n'
       '    get netIn(){ return netIn; },')
if 'netCreateRoomWith,' not in t:
    assert old in t, '导出锚点缺失'
    t = t.replace(old, new, 1)

IDX.write_text(t, encoding='utf-8')
print('已加联机辅助接口')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
