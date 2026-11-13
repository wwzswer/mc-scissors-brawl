// cdp-eval.mjs —— 通过 WebView 的 DevTools 协议在页面里执行一段 JS
// 用法：node tools/cdp-eval.mjs <wsUrl> "<表达式>"
// 只依赖 Node 内置模块（手搓 WebSocket 握手 + 帧）
import net from 'node:net';
import crypto from 'node:crypto';

const [wsUrl, expr] = process.argv.slice(2);
if(!wsUrl || !expr){ console.error('用法: node tools/cdp-eval.mjs <wsUrl> "<表达式>"'); process.exit(2); }

const u = new URL(wsUrl);
const key = crypto.randomBytes(16).toString('base64');
const sock = net.connect({ host: u.hostname, port: Number(u.port || 80) });

function frame(text){
  const payload = Buffer.from(text, 'utf8');
  const len = payload.length;
  const mask = crypto.randomBytes(4);
  let header;
  if(len < 126){ header = Buffer.from([0x81, 0x80 | len]); }
  else if(len < 65536){ header = Buffer.alloc(4); header[0]=0x81; header[1]=0x80|126; header.writeUInt16BE(len,2); }
  else { header = Buffer.alloc(10); header[0]=0x81; header[1]=0x80|127; header.writeUInt32BE(0,2); header.writeUInt32BE(len,6); }
  const masked = Buffer.alloc(len);
  for(let i=0;i<len;i++) masked[i] = payload[i] ^ mask[i % 4];
  return Buffer.concat([header, mask, masked]);
}

let buf = Buffer.alloc(0), handshaken = false;
sock.on('connect', ()=>{
  sock.write(
    `GET ${u.pathname}${u.search} HTTP/1.1\r\n` +
    `Host: ${u.host}\r\n` +
    `Upgrade: websocket\r\nConnection: Upgrade\r\n` +
    `Sec-WebSocket-Key: ${key}\r\nSec-WebSocket-Version: 13\r\n\r\n`
  );
});

function parseFrames(){
  while(true){
    if(buf.length < 2) return;
    const b0 = buf[0], b1 = buf[1];
    const op = b0 & 0x0f;
    let len = b1 & 0x7f, off = 2;
    if(len === 126){ if(buf.length < 4) return; len = buf.readUInt16BE(2); off = 4; }
    else if(len === 127){ if(buf.length < 10) return; len = Number(buf.readBigUInt64BE(2)); off = 10; }
    if(buf.length < off + len) return;
    const payload = buf.subarray(off, off + len);
    buf = buf.subarray(off + len);
    if(op === 0x8){ sock.end(); return; }
    if(op === 0x9){ continue; }            // ping，忽略
    if(op === 0x1 || op === 0x2){
      const txt = payload.toString('utf8');
      try{
        const msg = JSON.parse(txt);
        if(msg.id === 1){
          const r = msg.result || {};
          if(r.exceptionDetails){ console.log('JS 异常: ' + JSON.stringify(r.exceptionDetails.text || r.exceptionDetails)); }
          else console.log(typeof r.result?.value === 'string' ? r.result.value : JSON.stringify(r.result?.value));
          sock.end();
          setTimeout(()=>process.exit(0), 50);
        }
      }catch(e){ /* 忽略非 JSON 帧 */ }
    }
  }
}

sock.on('data', chunk=>{
  buf = Buffer.concat([buf, chunk]);
  if(!handshaken){
    const idx = buf.indexOf('\r\n\r\n');
    if(idx < 0) return;
    handshaken = true;
    buf = buf.subarray(idx + 4);
    sock.write(frame(JSON.stringify({
      id: 1, method: 'Runtime.evaluate',
      params: { expression: expr, returnByValue: true, awaitPromise: true }
    })));
  }
  parseFrames();
});

sock.on('error', e=>{ console.error('连接失败: ' + e.message); process.exit(1); });
setTimeout(()=>{ console.error('超时'); process.exit(1); }, 15000);
