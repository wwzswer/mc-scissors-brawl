# =============================================================================
# 把本地仓库推到 GitHub（token 只在内存里用一次，不写进任何文件）
#
# 用法：在仓库根目录执行
#   powershell -ExecutionPolicy Bypass -File tools/push-github.ps1
#   powershell -ExecutionPolicy Bypass -File tools/push-github.ps1 -Repo mc-scissors-brawl -User wwzswer
#
# 说明：
#   · 令牌要从 https://github.com/settings/tokens 生成（classic 勾 repo 即可）
#   · 仓库不存在会先用 API 建一个 public 仓库
#   · 本机 git 的 schannel 证书吊销检查是坏的，必须带 http.sslVerify=false 才能连 GitHub
# =============================================================================
param(
    [string]$Repo = "mc-scissors-brawl",
    [string]$User = "wwzswer",
    [string]$Branch = "main",
    [string]$Description = "方块猜拳战场 · Minecraft 二创猜拳桌游（网页 / PWA / 局域网联机 / Android APK）"
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$secure = Read-Host "粘贴 GitHub Personal Access Token（输入内容不会显示，也不会写进文件）" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$token = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

if ([string]::IsNullOrWhiteSpace($token)) { Write-Host "没有输入 token，退出。" -ForegroundColor Yellow; exit 1 }

$headers = @{ Authorization = "token $token"; "User-Agent" = "mc-brawl-push" }

Write-Host "→ 检查仓库 $User/$Repo 是否存在…"
$exists = $true
try {
    Invoke-RestMethod -Method Get -Uri "https://api.github.com/repos/$User/$Repo" -Headers $headers | Out-Null
    Write-Host "  已存在。" -ForegroundColor Green
} catch {
    $exists = $false
    Write-Host "  不存在，尝试创建…" -ForegroundColor Yellow
}

if (-not $exists) {
    $body = @{ name = $Repo; private = $false; description = $Description; has_issues = $true; has_wiki = $false } | ConvertTo-Json
    try {
        Invoke-RestMethod -Method Post -Uri "https://api.github.com/user/repos" -Headers $headers -ContentType "application/json" -Body $body | Out-Null
        Write-Host "  已创建 https://github.com/$User/$Repo" -ForegroundColor Green
    } catch {
        Write-Host "  创建失败（token 可能没有 repo 权限）：$($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Push-Location $here
try {
    git -c http.sslVerify=false push "https://${User}:${token}@github.com/$User/$Repo.git" "${Branch}:${Branch}"
    if ($LASTEXITCODE -ne 0) { Write-Host "推送失败，看上面的 git 报错。" -ForegroundColor Red; exit 1 }
    Write-Host ""
    Write-Host "推送完成：https://github.com/$User/$Repo" -ForegroundColor Green
} finally {
    Pop-Location
}
