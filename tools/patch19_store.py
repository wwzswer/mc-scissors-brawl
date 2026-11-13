# -*- coding: utf-8 -*-
"""补丁 19：rules-test 存档检查改为读 __store"""
import pathlib

F = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\rules-test.js')
r = F.read_text(encoding='utf-8')

r = r.replace(
    "  vm.runInContext(js, sandbox, {filename:'game.js'});\n  return { MC: sandbox.window.MCGame };",
    "  vm.runInContext(js, sandbox, {filename:'game.js'});\n  globalThis.__store = store;                 /* 供测试检查进度存档 */\n  return { MC: sandbox.window.MCGame };")

old = "  const saved = JSON.parse((globalThis.__store && globalThis.__store.mcProg) || localStorage.getItem('mcProg') || '{}');"
new = "  const saved = JSON.parse((globalThis.__store && globalThis.__store.mcProg) || '{}');"
r = r.replace(old, new)

F.write_text(r, encoding='utf-8')
print('已改：', 'globalThis.__store = store' in r, '|', "globalThis.__store.mcProg) || '{}'" in r)
