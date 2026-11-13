# -*- coding: utf-8 -*-
"""目标验收：对 8 项需求逐条给出源码级证据（只读检查，不改文件）"""
import pathlib, re

ROOT = pathlib.Path(r'D:\Documents\deepseek-harness\default-workspace\mc-scissors-brawl')
idx = (ROOT / 'index.html').read_text(encoding='utf-8')
js = idx.split('<script>')[1].split('</script>')[0]
srv_path = ROOT / 'server.js'
srv = srv_path.read_text(encoding='utf-8') if srv_path.exists() else ''
rules = (ROOT / 'RULES.md').read_text(encoding='utf-8')

ok_n = bad_n = 0
def chk(cond, name, extra=''):
    global ok_n, bad_n
    if cond: ok_n += 1; print(f'  ✅ {name}' + (f'  [{extra}]' if extra else ''))
    else:    bad_n += 1; print(f'  ❌ {name}' + (f'  [{extra}]' if extra else ''))

print('【1】解压素材 + 游戏贴图')
assets = ROOT / 'assets' / 'MC素材'
atlas = ROOT / 'assets' / 'sprites' / 'atlas.png'
chk(assets.exists() and len(list(assets.glob('*'))) >= 30, '原始素材已解压', f'{len(list(assets.glob("*")))} 个文件')
chk(atlas.exists() and atlas.stat().st_size > 50000, '雪碧图已生成', f'{atlas.stat().st_size//1024} KB')
chk('const SPRITE_SHEET = "data:image/png;base64,' in js, '贴图已内联进 index.html（data URI）')
icons = len(set(re.findall(r'"([a-z_0-9]+)":\s*\[', js)))
chk(icons >= 40, '图标坐标表', f'{icons} 个图标')
chk('const SPRITE_SHEET = "data:image/png;base64,' in js and 'ATLAS_W' in js, '雪碧图尺寸常量')
chk('function sprTag' in js and 'function sprStyle' in js, '渲染辅助函数存在')
# 实际使用：物品图标
chk('sprTag(itemIcon(' in js or 'sprTag(ic,' in js, '物品/装备使用贴图渲染')

print('\n【2】距离：上限7 / 初始1 / 两两独立')
chk('const MAX_DIST = 7;' in js, '上限常量为 7')
m = re.search(r'function setDistance\(a,b,v\)\{(.*?)\}', js, re.S)
chk(bool(m) and 'Math.min(MAX_DIST' in m.group(1), '写入距离时按上限钳制')
m2 = re.search(r'players\.forEach\(a=>\{ G\.dist\[a\.id\]=\{\}; players\.forEach\(b=>\{ G\.dist\[a\.id\]\[b\.id\] = a===b\?0:1; \}\); \}\);', js)
chk(bool(m2), '初始距离每人每对均为 1')
chk('G.dist[a.id][b.id]=v; G.dist[b.id][a.id]=v;' in js, '距离按“玩家对”存储（两两独立，非共享全局值）')
chk('function distChips' in js, '界面按对展示距离')

print('\n【3】2V2 模式')
chk("let gameMode = '1v1';" in js, '模式变量默认 1v1')
chk("gameMode==='2v2'" in js, '存在 2v2 分支')
chk('allyCount = is2v2 ? 1 : 0' in js, '2v2 生成 1 名 AI 队友')
chk('foeCount  = is2v2 ? 2 : enemyCount' in js, '2v2 固定 2 名敌人')
chk("data-mode=\"2v2\"" in idx, '设置界面有 2V2 按钮')
chk("q.alive && q.team===p.team" in js or 'aliveAlliesOf' in js, '队友判定存在')

print('\n【4】局域网联机 + 9 位房间码 + server')
chk(srv_path.exists() and 'room' in srv, 'server.js 存在且含房间逻辑')
chk("const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'" in srv, '房间码字符集：大写字母+数字')
chk('length:9' in srv.replace(' ',''), '房间码长度 9')
chk("crypto.randomInt(ALPHABET.length)" in srv, '房间码随机生成')
chk('/api/create' in srv and "sub === 'join'" in srv and "sub === 'leave'" in srv, '创建/加入/离开房间接口')
chk("sub === 'ready'" in srv and "sub === 'start'" in srv, '准备/开始接口')
chk("sub === 'action'" in srv and "sub === 'events'" in srv, '动作广播 + 增量拉取接口')
chk('const body = req.method' in srv, 'POST 请求体统一读取（修复过挂起 bug）')
chk((ROOT / 'start-server.cmd').exists(), 'start-server.cmd 一键启动脚本')
chk('/^[A-Z0-9]{9}$/.test(code)' in js, '客户端校验 9 位房间码')
chk('netStartMatch' in js and 'netSeedFromCode' in js, '两端同种子开局（同步用）')
chk("setInterval(tick, 600)" in js, '客户端短轮询同步')

print('\n【5】猜拳获胜 AP 可选 1 或 2（判定除外）')
chk('let apPerWin = 2;' in js, '变量 apPerWin 存在')
chk('data-ap="2"' in idx and 'data-ap="1"' in idx, '设置界面有 1 / 2 AP 两个按钮')
chk("apPerWin=+b.dataset.ap" in js, '按钮绑定到 apPerWin')
chk('ap += apPerWin' in js or 'ap+=apPerWin' in js, '猜拳胜者按 apPerWin 加分')
# 判定不给 AP：doJudgment 内不应出现 ap +=
jd = re.search(r'function doJudgment\(.*?\n\}', js, re.S)
chk(bool(jd) and 'ap +=' not in jd.group(0) and 'ap+=' not in jd.group(0), '判定流程不发放 AP')
chk('target.ap -= 1' in (jd.group(0) if jd else ''), '平局闪避才消耗 1 AP')

print('\n【6】进程升级进度式（小点 + 每回合存盘）')
chk('function progNeed' in js and 'function progProgress' in js, '进度点函数存在')
chk('function addProgPoint' in js, '投入 1 步的入口存在')
chk('p.prog += 1' in js and 'p.progPts -= progNeed(p)' in js, '满点才升级、多余结转')
chk('function progSave' in js and "localStorage.setItem('mcProg'" in js, '进度写入本地存储')
chk('async function endOfRound' in js and 'progSave(q)' in js, '回合结束时保存进度')
chk('function progPointsHtml' in js and 'class="dot' in js, '小点渲染函数')
chk('.progdots .dot' in idx and '.progdots .dot.on' in idx, '小点样式（点亮态）')
chk('progPointsHtml(p)' in js, '玩家面板调用小点渲染')
# 不再是“一次升满”
chk('p.ap-=UPGRADE[next].cost; p.prog=next;' not in js, '已无“一次扣满直接升级”的旧逻辑')

print('\n【7】初始界面可改玩家名称')
chk('id="nameInput"' in idx, '名称输入框')
chk('id="nameSave"' in idx, '保存按钮')
chk('let playerName' in js and 'playerName = v;' in js, '名称写入变量')
chk("localStorage.setItem('mcSettings'" in js or 'saveSettings' in js, '名称随设置持久化')
chk("makePlayer(myName, true" in js, '开局使用自定义名称')

print('\n【8】初始界面（左：开始/设置/规则，右：改名称）+ 规则页')
chk('id="screen-main"' in idx, '主菜单页存在')
chk('id="mStart"' in idx and 'id="mSetting"' in idx and 'id="mRules"' in idx, '左侧 开始/设置/规则 三个入口')
chk('id="nameInput"' in idx and '你的名称' in idx, '右侧更改名称区')
chk('const RULE_PAGES' in js and 'function renderRules' in js, '规则页分页渲染')
chk('id="ruleBody"' in idx and 'id="ruleTabs"' in idx, '规则页容器')
pages = re.findall(r"\{key:'(\w+)',\s*title:'([^']+)'\}", js)
chk(len(pages) >= 6, '规则分页数量', ' / '.join(t for _, t in pages))
chk('function itemRow' in js and '.map(itemRow)' in js and 'it.cost' in js, '规则页按物品逐条介绍（含步数数值）')
chk('基础玩法' in js and '猜拳阶段' in js, '规则页含玩法说明')

print(f'\n──────── 源码级验收：通过 {ok_n} 项，失败 {bad_n} 项 ────────')
print(f'index.html {len(idx)/1024:.0f} KB ｜ server.js {len(srv)/1024:.0f} KB ｜ RULES.md {len(rules)/1024:.0f} KB')
