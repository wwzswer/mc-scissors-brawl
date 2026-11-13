# adb-install-apk.ps1 —— 用无线调试/USB 装 APK，并抓安装失败的真实原因
#
# 用法（三种）：
#   1) USB 直接插上（已开 USB 调试）：
#        powershell -ExecutionPolicy Bypass -File tools/adb-install-apk.ps1
#   2) 已经配对过，只要连一下无线调试（手机「无线调试」页面显示的 IP:端口）：
#        powershell -ExecutionPolicy Bypass -File tools/adb-install-apk.ps1 -Connect 192.168.1.5:37041
#   3) 第一次配对（手机「使用配对码配对设备」弹窗里的 IP:端口 + 6 位码）：
#        powershell -ExecutionPolicy Bypass -File tools/adb-install-apk.ps1 -Pair 192.168.1.5:37123 -Code 123456 -Connect 192.168.1.5:37041
#
# 产物：/tmp 风格的控制台输出 + 失败时把关键日志打到屏幕上
param(
    [string]$Apk = "",
    [string]$Connect = "",
    [string]$Pair = "",
    [string]$Code = ""
)

$ErrorActionPreference = "Continue"
$OutputEncoding = [System.Text.Encoding]::UTF8
$ADB = "C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
if (-not (Test-Path $ADB)) { Write-Host "找不到 adb.exe: $ADB" -ForegroundColor Red; exit 1 }

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $Apk) {
    $Apk = Get-ChildItem (Join-Path $root "dist") -Filter "猜拳战场-*.apk" -ErrorAction SilentlyContinue |
           Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $Apk -or -not (Test-Path $Apk)) { Write-Host "找不到 APK，用 -Apk 指定" -ForegroundColor Red; exit 1 }
Write-Host "APK: $Apk" -ForegroundColor Cyan

function Step($m) { Write-Host ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) -ForegroundColor Cyan }

# ---- 1. 配对 / 连接 ----
if ($Pair -and $Code) {
    Step "配对 $Pair（码 $Code）"
    & $ADB pair $Pair $Code
}
if ($Connect) {
    Step "连接 $Connect"
    & $ADB connect $Connect
}

Step "当前设备"
& $ADB devices -l

$serial = $null
foreach ($l in (& $ADB devices)) {
    if ($l -match '^(\S+)\s+device$') { $serial = $matches[1]; break }
}
if (-not $serial) {
    Write-Host "没有在线设备：请确认 USB 调试已开，或先 -Pair/-Connect" -ForegroundColor Yellow
    exit 2
}
Write-Host "设备: $serial" -ForegroundColor Green

# ---- 2. 设备信息（判断是不是 vivo/iQOO 那套校验） ----
Step "设备信息"
& $ADB -s $serial shell getprop ro.product.brand
& $ADB -s $serial shell getprop ro.product.model
& $ADB -s $serial shell getprop ro.build.version.release
& $ADB -s $serial shell getprop ro.build.version.sdk
Step "可能的厂商安装校验相关包"
& $ADB -s $serial shell pm list packages 2>$null | Select-String -Pattern "vivo|iqoo|bbk|abroad|installer" | Select-Object -First 20

# ---- 3. 清日志 → 安装 → 抓日志 ----
Step "清空 logcat"
& $ADB -s $serial logcat -c

Step "安装 APK"
$out = & $ADB -s $serial install -r -d "$Apk" 2>&1
$out | ForEach-Object { Write-Host "  $_" }

Start-Sleep -Milliseconds 800
Step "安装相关日志（失败原因通常在这里）"
$log = & $ADB -s $serial logcat -d -v brief 2>$null
$log | Select-String -Pattern "PackageManager|PackageInstaller|installd|vivo|bbk|INSTALL_FAILED|INSTALL_|com\.dsh\.mcbrawl|verify|signature" |
    Select-Object -Last 60 | ForEach-Object { Write-Host "  $_" }

if ($out -match "Success") {
    Write-Host ""
    Write-Host "安装成功，直接启动：" -ForegroundColor Green
    & $ADB -s $serial shell monkey -p com.dsh.mcbrawl -c android.intent.category.LAUNCHER 1 | Out-Null
    Start-Sleep -Seconds 2
    Step "启动后的崩溃日志（如果有）"
    (& $ADB -s $serial logcat -d -v brief 2>$null) | Select-String -Pattern "AndroidRuntime|FATAL|mcbrawl" |
        Select-Object -Last 30 | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host ""
    Write-Host "安装失败。把上面 'install' 那一行 + 日志里 INSTALL_FAILED_* / vivo 相关几行发出来即可定位。" -ForegroundColor Yellow
}
