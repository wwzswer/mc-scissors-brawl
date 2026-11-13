# -*- coding: utf-8 -*-
"""修复被转义弄坏的 dbg-bugs.cjs（删掉我追加的坏段落）"""
import pathlib, re

p = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\dbg-bugs.cjs')
t = p.read_text(encoding='utf-8')

# 删掉【8】【9】那两段（用 Python 重新生成干净的版本）
i = t.find("  console.log();\n  console.log('【8】")
if i > 0:
    j = t.find("  process.exit(0);", i)
    t = t[:i] + t[j:]
    p.write_text(t, encoding='utf-8')
    print('已删除损坏的【8】【9】段落')
else:
    print('未找到损坏段落')

# 校验语法
import os, subprocess
NODE = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe'
r = subprocess.run([NODE, '--check', str(p)], capture_output=True, text=True)
print('语法:', 'OK' if r.returncode == 0 else 'ERROR\n' + r.stderr[:300])
