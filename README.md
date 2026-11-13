# 方块猜拳战场 · Minecraft 二创桌游

猜拳夺 AP → 升进程 / 造装备 / 收补给 → 相互战斗。所有角色、物品、进程都是方块味儿的。
不是 Minecraft 本体，是**用猜拳当引擎的 MC 二创对战桌游**：一局几分钟，网页直接玩，能装成 App，也能局域网联机。

- **网页版**：`index.html` 单文件全包（无框架、无构建、离线可玩）
- **手机**：浏览器「添加到主屏幕」或直接装 `dist/` 里的 APK
- **联机**：`node server.js` 起房间服务，9 位房间码进房，6 个座位可换队伍、空位可加人机
- **给 QQ 机器人读**：`GET /api/room/<房间码>/peek` 返回中文战报，贴到群里就能聊

## 玩法速览

| 阶段 | 说明 |
|---|---|
| 猜拳 | 全体存活玩家同时出拳，克制其余所有人者 +1~2 AP；平手重出 |
| 行动 | 每人每回合 1 次免费行动，之后每 1 AP 买一次行动（AP 回合结束清零） |
| 进程 | 空手 → 石(1点) → 铁(3点) → 钻石(3点)，进度按「玩家名」存档 |
| 结束 | 敌方全灭获胜；你（或你的队伍）全灭失败 |

生命 4 点，距离上限、武器/护甲/附魔/建筑/药水/TNT 等细节见游戏内「规则」页。

## 快速开始

### 1. 单机 / 人机（最简单）
双击 `index.html` 就能玩。

### 2. 局域网联机（推荐用这个入口）
```bash
node server.js          # 或双击 start-server.cmd
```
- 本机：`http://127.0.0.1:8787`
- 同局域网的朋友/手机：`http://<你的内网IP>:8787`

进「🌐 局域网联机」→ 创建房间 → 把 **9 位房间码** 发给对方（QQ 里发就行）→ 对方输码加入。

- **点座位换队伍**：下拉选队伍 A/B/C/D，同队是队友、异队是敌人（支持三方、四方混战）
- **空位加人机**：空座位点「＋人机」，每名人机可单独设强度（简单/普通/困难），人数可以不对等
- **房主**：可以加/删人机、踢人、转让房主、点「开始对局」

### 3. 手机
- **装到主屏幕**：手机浏览器打开页面 → 菜单里「📲 安装到桌面」（Chrome/Edge）或 Safari「分享 → 添加到主屏幕」；之后断网也能开
- **APK**：`dist/猜拳战场-1.7.0.apk`，装好后资源全在本地，**联机时**在「服务器地址」里填电脑的 `http://192.168.x.x:8787`

## 给机器人 / 脚本用的接口

```
GET  /api/ping                               服务存活 + 版本
GET  /api/version                            版本号（网页用它做更新提示）
POST /api/create                             {name} → {code, youId, room}
POST /api/room/<码>/join                     {name} → 进空座位
POST /api/room/<码>/team                     {id, slot, team}     换队伍
POST /api/room/<码>/bot                      {id, slot, op:fill|clear|update, team?, diff?}
POST /api/room/<码>/host                     {id, slot}          转让房主
POST /api/room/<码>/kick                     {id, slot}
POST /api/room/<码>/start                    {id}                房主开局
GET  /api/room/<码>/events?id=&since=        增量事件 + 座位 + 局面快照
POST /api/room/<码>/snapshot                 {id, snap}          房主每 0.8s 上报局面
GET  /api/room/<码>/peek                     只读：座位/队伍/局面 + 中文战报 brief
```

`peek` 的 `brief` 直接就是一段人话战报：

```
🏟 房间 9C23WTEVG · 3 队 4 人 · 对局进行中 · 生命 4 / 猜拳获胜 +2 AP
队伍A：房主小明(房主)｜队伍B：史蒂夫(人机·困难)｜队伍C：朋友小红、爱丽克丝(人机·困难)
第 7 回合 · 存活 3/4
[A]房主小明：4血 / 2AP / 石进程 / 石剑；...
最近：第 7 回合 ⏎ 房主小明 用 石剑 命中 朋友小红 -1 血
```

## 目录

```
index.html              整个游戏（HTML+CSS+JS 单文件）
server.js               零依赖联机服务器（静态托管 + 房间 + peek 战报）
sw.js / manifest.*      PWA：离线缓存 + 可安装
version.json            版本号与更新说明（网页据此弹更新窗口）
icon-*.png              应用图标（tools/make_pwa_icons.py 可重生成）
android/                APK 壳（WebView + assets/www），build.sh 一键打包
tools/                  补丁脚本、图标生成、自动化测试
  test-roster.html      队伍编辑 / 人机 浏览器测试
  test-lobby.html       联机座位 / 观战 / 更新窗口 / 手机布局 测试
  test-net-api.mjs      房间接口（座位/队伍/人机/战报）测试
dist/                   构建产物（APK）
```

## 自测

```bash
node server.js 8803 &                                  # 起测试服务
node tools/test-net-api.mjs                            # 房间/座位/人机/战报 接口
# 浏览器打开 http://127.0.0.1:8803/tools/test-lobby.html  （用无头浏览器看 <pre id="results">）
# 浏览器打开 http://127.0.0.1:8803/tools/test-roster.html
```

## 版本与更新

改 `version.json` 的 `version` 就能让所有在线客户端右下角弹「有新版本」窗口（点了会清缓存 + 更新 Service Worker 再重载）。
APK 的版本号在 `android/AndroidManifest.xml`，重新打包时 `build.sh` 会从 `version.json` 同步。

## 已知边界

- 联机目前是**房主执棋 + 其他座位实时观战**（同一局、同一份座位表）。真正的双人同时操作尚未实现。
- Android 壳用系统 WebView 跑同一份网页，不依赖任何第三方库；不含 Gradle 工程。
