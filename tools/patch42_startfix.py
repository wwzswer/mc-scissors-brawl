# -*- coding: utf-8 -*-
"""补丁 42：修复 MC.start 传入的设置被 localStorage 覆盖
   startGame 内部会 loadSettings()，若传入的 mode/diff/ap/enemyCount 未先落盘，
   就会被旧设置覆盖（表现为“设为 1v1 却仍是 2v2”）。
   修复：MC.start 应用参数后立即 saveSettings()。
"""
import pathlib

IDX = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\index.html')
t = IDX.read_text(encoding='utf-8')

old = ("start(config){ if(config){ if(config.enemyCount)enemyCount=config.enemyCount; "
       "if(config.diff)diffKey=config.diff; if(config.auto!==undefined)autoMode=config.auto; "
       "if(config.mode)gameMode=config.mode; if(config.apPerWin)apPerWin=config.apPerWin; "
       "if(config.name)playerName=config.name; if(config.seed)setSeed(config.seed); "
       "if(config.silent!==undefined)silentStart=!!config.silent; } return startGame(); },")
new = ("start(config){ if(config){ if(config.enemyCount)enemyCount=config.enemyCount; "
       "if(config.diff)diffKey=config.diff; if(config.auto!==undefined)autoMode=config.auto; "
       "if(config.mode)gameMode=config.mode; if(config.apPerWin)apPerWin=config.apPerWin; "
       "if(config.name)playerName=config.name; if(config.seed)setSeed(config.seed); "
       "if(config.silent!==undefined)silentStart=!!config.silent; "
       "saveSettings(); }   /* 先落盘，避免 startGame 里的 loadSettings 把参数覆盖回去 */\n"
       "  return startGame(); },")

assert old in t, 'MC.start 锚点缺失'
t = t.replace(old, new, 1)

IDX.write_text(t, encoding='utf-8')
print('已修复：MC.start 参数立即持久化，不再被 loadSettings 覆盖')
pathlib.Path(r'C:\Users\Administrator\AppData\Local\Temp\chk.js').write_text(
    t.split('<script>')[1].split('</script>')[0], encoding='utf-8')
