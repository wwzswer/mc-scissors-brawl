# -*- coding: utf-8 -*-
"""补丁 10：让 MCGame.start 支持 mode / apPerWin / seed / name（供测试与联机使用）"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

old = ("start(config){ if(config){ if(config.enemyCount)enemyCount=config.enemyCount; "
       "if(config.diff)diffKey=config.diff; if(config.auto!==undefined)autoMode=config.auto; } return startGame(); },")
new = ("start(config){ if(config){ if(config.enemyCount)enemyCount=config.enemyCount; "
       "if(config.diff)diffKey=config.diff; if(config.auto!==undefined)autoMode=config.auto; "
       "if(config.mode)gameMode=config.mode; if(config.apPerWin)apPerWin=config.apPerWin; "
       "if(config.name)playerName=config.name; if(config.seed)setSeed(config.seed); } return startGame(); },")

if 'if(config.mode)gameMode=config.mode' in t:
    print('已支持，跳过')
else:
    assert old in t, 'start 锚点缺失'
    t = t.replace(old, new, 1)
    IDX.write_text(t, encoding='utf-8')
    print('MCGame.start 已支持 mode/apPerWin/name/seed')

pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
