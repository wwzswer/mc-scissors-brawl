# -*- coding: utf-8 -*-
"""补丁 32：把请求体读取提到最前面（避免 TDZ：join 分支在 const body 之前用了 body）"""
import pathlib

S = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\server.js')
s = S.read_text(encoding='utf-8')

# 1) 在路由分派最开始读取 body
old_head = """      const m = p.match(/^\\/api\\/room\\/([A-Z0-9]{9})\\/(join|ready|start|state|events|action|stream|leave)$/);
      if(!m) return json(res, {ok:false, err:'未知接口'}, 404);
      const r = rooms.get(m[1]);
      if(!r) return json(res, {ok:false, err:'房间不存在或已过期'}, 404);
      const sub = m[2];"""
new_head = """      const m = p.match(/^\\/api\\/room\\/([A-Z0-9]{9})\\/(join|ready|start|state|events|action|stream|leave)$/);
      if(!m) return json(res, {ok:false, err:'未知接口'}, 404);
      const r = rooms.get(m[1]);
      if(!r) return json(res, {ok:false, err:'房间不存在或已过期'}, 404);
      const sub = m[2];
      /* 关键：POST 必须先把请求体读完，否则 keep-alive 连接会挂起 */
      const body = req.method === 'POST' ? await readBody(req) : {};"""
assert old_head in s, '路由头锚点缺失'
s = s.replace(old_head, new_head, 1)

# 2) 删掉后面的重复声明
dup = """      /* 关键：POST 必须先读完请求体，否则 keep-alive 连接会挂起 */
      const body = req.method === 'POST' ? await readBody(req) : {};
"""
if dup in s:
    s = s.replace(dup, '', 1)
    print('  ok 删掉重复声明')

S.write_text(s, encoding='utf-8')
print('server.js 已修正，大小', round(len(s)/1024,1), 'KB')
