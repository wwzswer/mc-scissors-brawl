# QQ 机器人 / MCP 适配层

这个目录放的是「方块猜拳战场」的 MCP server（stdio），让 QQ 机器人直接开桌游玩：

```bash
node mcp/mcp-mc-brawl.js            # 正常跑（MCP stdio）
node mcp/mcp-mc-brawl.js --selftest # 自检：加载游戏 → 开局 → 推若干轮
```

它做的事：用 `vm` + 假 DOM 把仓库根目录的 `index.html` 里那段脚本加载起来，
然后调 `window.MCGame` 的接口来开局、出拳、行动、读日志 —— **规则和网页/App 完全同一份**。

游戏侧为此做了两处配合（否则会 `window.addEventListener is not a function`）：

- 事件注册全部走 `onWindow()` / `onDocument()` 包装，无 DOM 环境下静默跳过
- `checkUpdate()` 先判断 `typeof fetch`，沙箱里不联网就不检查更新

依赖：`@modelcontextprotocol/sdk`、`zod`。实际部署时这些在 `qq-bridge/` 的 node_modules 里。

## 让她坐进网页房间当对手（mc_room_* 四个工具）

不再只是「只读观战」——她可以占一个**真座位**，由房主（网页端）的引擎向她提问、她来回答：

| 工具 | 作用 |
|---|---|
| `mc_room_join(code, name?, serverUrl?)` | 用 9 位房间码占一个座位（会自动进人少的队） |
| `mc_room_wait(timeoutMs?)` | 等房主问：出拳 / 行动清单 / 要不要闪避。超时返回「还没轮到你」 |
| `mc_room_answer(move? / choice?)` | 回出拳（rock/scissors/paper）、回行动（序号或选项 id，`"pass"` 结束行动） |
| `mc_room_board()` | 读局面：每人血量/AP/进程/装备 + 最近一条日志 |

用法：

```
她：mc_room_join(code="ABCD12345")
你：网页端点「开始对局」
她：循环 mc_room_wait → 拿到问题就 mc_room_answer
```

底层就是网页访客端用的那套 `ask/ans` 协议（房主发 `{kind:'ask'}`，她回 `{kind:'ans'}`），
所以**不需要改任何服务端代码**，房主那边把她当成普通的远端真人对待，超时 180 秒会自动跳过。
