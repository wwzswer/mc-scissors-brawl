#!/bin/bash
# =============================================================================
# 方块猜拳战场 · Android APK 构建（不依赖 Gradle，直接用 aapt2 / javac / d8 / apksigner）
#
# 用法：
#   bash build.sh            # 构建 + 签名 + 校验
#
# 需要（路径都可用环境变量覆盖）：
#   JAVA_HOME  JDK 17（javac / keytool / java）
#   SDK        Android SDK 根目录，内含：
#                build-tools/34.0.0/{aapt2.exe,zipalign.exe,lib/d8.jar,lib/apksigner.jar}
#                platforms/android-35/android.jar
# 产物：../dist/猜拳战场-<版本>.apk
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

export JAVA_HOME="${JAVA_HOME:-C:/Users/Administrator/AppData/Local/Temp/android-build/jdk-17.0.21+9}"
SDK="${SDK:-C:/Users/Administrator/AppData/Local/Temp/android-build/sdk}"
BT_VERSION="${BT_VERSION:-34.0.0}"
PLATFORM="${PLATFORM:-android-35}"
BT="$SDK/build-tools/$BT_VERSION"
ANDROID_JAR="$SDK/platforms/$PLATFORM/android.jar"
JAVA="$JAVA_HOME/bin/java.exe"
JAVAC="$JAVA_HOME/bin/javac.exe"
KEYTOOL="$JAVA_HOME/bin/keytool.exe"

VERSION="$(cd "$ROOT" && node -e "try{console.log(require('./version.json').version)}catch(e){console.log('0.0.0')}" 2>/dev/null || echo 0.0.0)"
VERSION_CODE="$(echo "$VERSION" | awk -F. '{printf "%d%02d%02d", $1,$2,$3}')"
APP_NAME="猜拳战场-$VERSION"
OUT_APK="$ROOT/dist/$APP_NAME.apk"

[ -f "$ANDROID_JAR" ] || { echo "缺少 android.jar：$ANDROID_JAR"; exit 1; }
[ -x "$JAVAC" ] || { echo "缺少 javac：$JAVAC"; exit 1; }
[ -f "$BT/aapt2.exe" ] || { echo "缺少 aapt2：$BT/aapt2.exe"; exit 1; }
[ -f "$BT/zipalign.exe" ] || { echo "缺少 zipalign：$BT/zipalign.exe"; exit 1; }
[ -f "$BT/lib/d8.jar" ] || { echo "缺少 d8.jar：$BT/lib/d8.jar"; exit 1; }

rm -rf "$HERE/build"
mkdir -p "$HERE/build"/{res,gen,classes,dex,apk} "$ROOT/dist"

echo "== 1/7 版本 $VERSION（versionCode $VERSION_CODE）=="
echo "== 打包网页资源到 assets/www =="
rm -rf "$HERE/assets/www"
mkdir -p "$HERE/assets/www"
for f in index.html manifest.webmanifest sw.js version.json \
         icon-192.png icon-512.png icon-maskable-512.png apple-touch-icon-180.png; do
  [ -f "$ROOT/$f" ] && cp "$ROOT/$f" "$HERE/assets/www/$f"
done
# 注意：不要打包 ../assets（那是素材原图，网页里已内联成 data URI），
# 而且其中含中文路径，aapt2 的 -A 处理不了中文文件名。
echo "   $(find "$HERE/assets/www" -type f | wc -l) 个文件"

echo "== 2/7 生成图标 =="
python "$ROOT/tools/make_android_icons.py" "$HERE/res" 2>&1 | sed 's/^/   /'

echo "== 3/7 aapt2 compile =="
"$BT/aapt2.exe" compile --dir "$HERE/res" -o "$HERE/build/res/resources.zip" || {
  echo "（res 为空则跳过，直接用空资源包）"; }

echo "== 4/7 aapt2 link（含 assets）=="
LINK_ARGS=(-o "$HERE/build/apk/base.apk" -I "$ANDROID_JAR"
  --manifest "$HERE/AndroidManifest.xml" -A "$HERE/assets"
  --java "$HERE/build/gen" --min-sdk-version 24 --target-sdk-version 35
  --version-code "$VERSION_CODE" --version-name "$VERSION" --auto-add-overlay)
if [ -f "$HERE/build/res/resources.zip" ]; then
  "$BT/aapt2.exe" link "${LINK_ARGS[@]}" "$HERE/build/res/resources.zip"
else
  echo "   !! 没有资源包，图标可能缺失"
  "$BT/aapt2.exe" link "${LINK_ARGS[@]}"
fi

echo "== 5/7 javac + d8 =="
# 注意：javac / d8 用相对路径（在 $HERE 里执行），避免 git-bash 的 /d/... 路径被当成 Windows 绝对路径
( cd "$HERE" && find build/gen src -name '*.java' > build/sources.txt )
( cd "$HERE" && "$JAVAC" -encoding UTF-8 -source 8 -target 8 -nowarn -Xlint:-options     -bootclasspath "$ANDROID_JAR" -classpath "$ANDROID_JAR"     -d build/classes @build/sources.txt )
( cd "$HERE" && find build/classes -name '*.class' > build/classes.txt )
( cd "$HERE" && "$JAVA" -cp "$BT/lib/d8.jar" com.android.tools.r8.D8     --lib "$ANDROID_JAR" --min-api 21 --output build/dex @build/classes.txt )
# 这台机器没有 zip 命令：用 python 解包 + 放入 classes.dex + 重新打包成干净的 zip
python "$ROOT/tools/apk_repack.py" "$HERE/build/apk/base.apk" "$HERE/build/dex/classes.dex"

echo "== 6/7 zipalign + 签名 =="
KS="$HERE/keystore.jks"
if [ ! -f "$KS" ]; then
  "$KEYTOOL" -genkeypair -keystore "$KS" -alias mcbrawl -keyalg RSA -keysize 2048 \
    -validity 10000 -storepass mcbrawl -keypass mcbrawl \
    -dname "CN=MC Brawl, OU=Game, O=DSH, L=Local, ST=Local, C=CN" >/dev/null 2>&1
  echo "   已生成 keystore（android/keystore.jks，口令 mcbrawl）"
fi
"$BT/zipalign.exe" -f -p 4 "$HERE/build/apk/base.apk" "$HERE/build/apk/aligned.apk"
"$JAVA" -jar "$BT/lib/apksigner.jar" sign --ks "$KS" --ks-pass pass:mcbrawl \
  --key-pass pass:mcbrawl --min-sdk-version 21 --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true --v4-signing-enabled true --out "$OUT_APK" "$HERE/build/apk/aligned.apk"

echo "== 7/7 校验 =="
"$JAVA" -jar "$BT/lib/apksigner.jar" verify -v "$OUT_APK" | head -5
"$BT/aapt2.exe" dump badging "$OUT_APK" | head -4
ls -la "$OUT_APK" | awk '{print "   ->", $5, "bytes", $9}'
echo "完成：$OUT_APK"
