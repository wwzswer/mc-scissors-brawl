import io

NL = chr(10)
p = 'index.html'
s = io.open(p, encoding='utf-8').read()

start = s.index('function performAttack(attacker, target, key, opts={}){')
head_end = s.index('    const ranged = !!opts.ranged;', start)

old_head = s[start:head_end]
new_head = ('function performAttack(attacker, target, key, opts={}){' + NL +
            '  const __prevAttacker = CUR_ATTACKER;' + NL +
            '  CUR_ATTACKER = attacker;' + NL +
            '  const __p = (async ()=> {' + NL + '    ')
assert 'const __done' in old_head, '预期是旧版头部'
s = s[:start] + new_head + s[head_end:]
print('头部替换完成')

# 找到该函数体的结尾  "  })();" + NL + "}"
start2 = s.index('function performAttack(attacker, target, key, opts={}){')
tail_pat = '  })();' + NL + '}'
tail_i = s.index(tail_pat, start2)
new_tail = ('  })();' + NL +
            '  __p.finally(()=>{ CUR_ATTACKER = __prevAttacker; });' + NL +
            '  return __p;' + NL + '}')
s = s[:tail_i] + new_tail + s[tail_i + len(tail_pat):]
print('尾部补上 finally 恢复')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
