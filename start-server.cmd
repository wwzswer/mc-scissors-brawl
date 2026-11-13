@echo off
chcp 65001 >nul
title 方块猜拳战场 · 局域网联机服务
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo   [错误] 没有找到 Node.js。
  echo   本游戏的联机服务需要 Node.js 18 或更高版本。
  echo   安装后重新双击本文件即可。
  echo.
  pause
  exit /b 1
)
echo.
echo   正在启动联机服务，稍后会自动打开浏览器…
echo   ^(这个黑窗口不要关，关掉联机就断了^)
echo.

node server.js %*
echo.
echo   服务已停止。
pause
