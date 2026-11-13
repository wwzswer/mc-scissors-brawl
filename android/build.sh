#!/bin/bash
# =============================================================================
# 方块猜拳战场 · Android APK 构建（不依赖 Gradle，直接用 aapt2 / javac / d8 / apksigner）
#
# 用法：
#   bash build.sh            # 构建 + 签名 + 校验
#   bash build.sh --clean    # 先清理中间产物
#
# 依赖（放在一起即可，路径可用环境变量覆盖）：
#   JAVA_HOME     JDK 17（javac / keytool）
#   SDK           Android SDK 根目录，里面要有：
#                   build-tools/34.0.0/{aapt2,d8,zipalign,apksigner}.exe + lib/
#                   platforms/android-35/android.jar
# 产物：../dist/猜拳战场-<版本>.apk
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

# ---- 路径（可用环境变量覆盖）----
export JAVA_HOME="${JAVA_HOME:-C:/Users/Administrator/AppData/Local/Temp/android-build/jdk-17.0.21+9}"
SDK="${SDK:-C:/Users/Administrator/AppData/Local/Temp/android-build/sdk}"
BT_VERSION="${BT_VERSION:-34.0.0}"
PLATFORM="${PLATFORM:-android-35}"
BT="$SDK/build-tools/$BT_VERSION"
ANDROID_JAR="$SDK/platforms/$PLATFORM/android.jar"
JAVAC="$JAVA_HOME/bin/javac.exe"
KEYTOOL="$JAVA_HOME/bin/keytool.exe"

VERSION="$(node -e "console.log((require('$ROOT/version.json')||{}).version||'0.0.0')" 2>/dev/null || echo 0.0.0)"
VERSION_CODE="$(echo "$VERSION" | awk -F. '{printf "%d%02d%02d", $1,$2,$3}')"
APP_NAME="猜拳战场-$VERSION"
OUT_APK="$ROOT/dist/$APP_NAME.apk"

[ -f "$ANDROID_JAR" ] || { echo "缺少 android.jar：$ANDROID_JAR"; exit 1; }
[ -x "$JAVAC" ] || { echo "缺少 javac：$JAVAC（JAVA_HOME=$JAVA_HOME）"; exit 1; }
for t in aapt2 d8 zipalign apksigner; do
  [ -f "$BT/$t.exe" ] || { echo "缺少 build-tools 工具：$BT/$t.exe"; exit 1; }
done

if [ "${1:-}" = "--clean" ]; then rm -rf "$HERE/build"; fi
rm -rf "$HERE/build"
mkdir -p "$HERE/build"/{res,gen,classes,dex,apk} "$ROOT/dist"

echo "== 1/7 准备资源与网页（assets/www）=="
rm -rf "$HERE/assets/www"
mkdir -p "$HERE/assets/www"
for f in index.html manifest.webmanifest sw.js version.json \
         icon-192.png icon-512.png icon-maskable-512.png apple-touch-icon-180.png; do
  [ -f "$ROOT/$f" ] && cp "$ROOT/$f" "$HERE/assets/www/$f"
done
# App 壳里不需要 Service Worker（资源本来就打包在本地），显式去掉注册也无害，保留即可
echo "   assets: $(ls "$HERE/assets/www" | tr '\n' ' ')"

echo "== 2/7 生成图标 =="
if command -v python >/dev/null 2>&1; then python "$ROOT/tools/make_android_icons.py" "$HERE/res"; else echo "  跳过（没有 python）"; fi

echo "== 3/7 aapt2 compile =="
"$BT/aapt2.exe" compile --dir "$HERE/res" -o "$HERE/build/res/resources.zip"

echo "== 4/7 aapt2 link（含 assets）=="
"$BT/aapt2.exe" link \
  -o "$HERE/build/apk/base.apk" \
  -I "$ANDROID_JAR" \
  --manifest "$HERE/AndroidManifest.xml" \
  -A "$HERE/assets" \
  --java "$HERE/build/gen" \
  --min-sdk-version 21 \
  --target-sdk-version 35 \
  --version-code "$VERSION_CODE" \
  --version-name "$VERSION" \
  --auto-add-overlay \
  "$HERE/build/res/resources.zip"

echo "== 5/7 javac + d8 =="
find "$HERE/build/gen" -name '*.java' > "$HERE/build/sources.txt"
find "$HERE/src" -name '*.java' >> "$HERE/build/sources.txt"
"$JAVAC" -encoding UTF-8 -source 8 -target 8 -nowarn \
  -bootclasspath "$ANDROID_JAR" -classpath "$ANDROID_JAR" \
  -d "$HERE/build/classes" @"$HERE/build/sources.txt" 2>&1 | grep -v "^注:" || true
find "$HERE/build/classes" -name '*.class' > "$HERE/build/classes.txt"
"$BT/d8.exe" --lib "$ANDROID_JAR" --min-api 21 --output "$HERE/build/dex" @"$HERE/build/classes.txt"
(cd "$HERE/build/dex" && zip -q -X "$HERE/build/apk/base.apk" classes.dex)

echo "== 6/7 zipalign + 签名 =="
KS="$HERE/keystore.jks"
if [ ! -f "$KS" ]; then
  "$KEYTOOL" -genkeypair -v -keystore "$KS" -alias mcbrawl -keyalg RSA -keysize 2048 \
    -validity 10000 -storepass mcbrawl -keypass mcbrawl \
    -dname "CN=MC Brawl, OU=Game, O=DSH, L=Local, ST=Local, C=CN" >/dev/null 2>&1
  echo "   已生成签名用 keystore（android/keystore.jks，口令 mcbrawl）"
fi
"$BT/zipalign.exe" -f -p 4 "$HERE/build/apk/base.apk" "$HERE/build/apk/aligned.apk"
"$BT/apksigner.exe" sign --ks "$KS" --ks-pass pass:mcbrawl --key-pass pass:mcbrawl \
  --min-sdk-version 21 --out "$OUT_APK" "$HERE/build/apk/aligned.apk"

echo "== 7/7 校验 =="
"$BT/apksigner.exe" verify -v "$OUT_APK" | head -6
"$BT/aapt2.exe" dump badging "$OUT_APK" | head -5
ls -la "$OUT_APK" | awk '{print "   ->", $5, "bytes", $9}'
echo "完成：$OUT_APK"
