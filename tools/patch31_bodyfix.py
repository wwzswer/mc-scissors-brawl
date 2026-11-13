# -*- coding: utf-8 -*-
"""补丁 31：修复 /ready、/action 挂起
   根因：`const id = url参数 || (await readBody(req)).id` 在 id 来自查询串时短路，
        请求体永远不被读取 → Node 的 keep-alive 连接挂起，响应无法返回。
   修复：所有 POST 分支先无条件读取请求体，再取 id。
"""
import pathlib

S = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl\server.js')
s = S.read_text(encoding='utf-8')

old = """      const id = new URL(url, 'http://x').searchParams.get('id') || (await readBody(req)).id;
      const seat = r.seats.find(s=>s.id===id);
      if(!seat) return json(res, {ok:false, err:'你不在该房间中'}, 403);
      if(sub === 'ready' && req.method === 'POST'){
        const b = await readBody(req);
        seat.ready = b.ready===undefined ? !seat.ready : !!b.ready;"""
new = """      /* 关键：POST 必须先读完请求体，否则 keep-alive 连接会挂起 */
      const body = req.method === 'POST' ? await readBody(req) : {};
      const id = new URL(url, 'http://x').searchParams.get('id') || body.id;
      const seat = r.seats.find(s=>s.id===id);
      if(!seat) return json(res, {ok:false, err:'你不在该房间中'}, 403);
      if(sub === 'ready' && req.method === 'POST'){
        const b = body;
        seat.ready = b.ready===undefined ? !seat.ready : !!b.ready;"""
assert old in s, 'ready 分支锚点缺失'
s = s.replace(old, new, 1)

old2 = """      if(sub === 'action' && req.method === 'POST'){
        const b = await readBody(req);
        if(!r.started) return json(res, {ok:false, err:'对局未开始'}, 400);"""
new2 = """      if(sub === 'action' && req.method === 'POST'){
        const b = body;
        if(!r.started) return json(res, {ok:false, err:'对局未开始'}, 400);"""
assert old2 in s, 'action 分支锚点缺失'
s = s.replace(old2, new2, 1)

# join / create 也要保证 body 已被消费（它们本来就读了，但统一走一遍更保险）
old3 = """      if(sub === 'join' && req.method === 'POST'){
        const b = await readBody(req);
        if(r.started) return json(res, {ok:false, err:'对局已开始'}, 400);"""
new3 = """      if(sub === 'join' && req.method === 'POST'){
        const b = body;
        if(r.started) return json(res, {ok:false, err:'对局已开始'}, 400);"""
if old3 in s:
    s = s.replace(old3, new3, 1)
    print('  ok join 分支复用 body')

S.write_text(s, encoding='utf-8')
print('server.js 已修复，大小', round(len(s)/1024,1), 'KB')
