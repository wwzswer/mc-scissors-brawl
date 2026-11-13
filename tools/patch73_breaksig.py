# -*- coding: utf-8 -*-
"""补丁 73：breakArmor 支持指定破损件（上次因异常未写入）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

old = """function breakArmor(p){
  const brokenKey = p.armor;
  if(!brokenKey) return;"""
new = """function breakArmor(p, key){
  /* key 明确指定破损的那件；不传则用当前生效护甲。
     注意：消耗护甲后可能已切换到下一件，所以调用方必须传入破损件，否则会误清好甲。 */
  const brokenKey = key || p.armor;
  if(!brokenKey) return;"""

if 'function breakArmor(p, key){' in t:
    print('已存在，跳过')
else:
    assert old in t, 'breakArmor 锚点缺失'
    t = t.replace(old, new, 1)
    IDX.write_text(t, encoding='utf-8')
    print('已修 breakArmor 签名（支持指定破损件）')

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
