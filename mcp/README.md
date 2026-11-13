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
