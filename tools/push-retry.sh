#!/bin/bash
# 分段 + 重试推送：这台机器到 GitHub 的链路不稳，整包推容易断
cd "D:/Documents/deepseek-harness/default-workspace/mc-scissors-brawl" || exit 1
: "${GH_TOKEN:?需要 GH_TOKEN}"
URL="https://wwzswer:${GH_TOKEN}@github.com/wwzswer/mc-scissors-brawl.git"

try_push() {   # $1 = 要推到的 refspec
  local ref="$1" i
  for i in 1 2 3 4 5; do
    echo "  [try $i] push $ref"
    if timeout 150 git -c http.sslVerify=false -c http.postBuffer=1048576 -c http.version=HTTP/1.1 \
         -c http.lowSpeedLimit=0 -c http.lowSpeedTime=999999 -c credential.helper= \
         push "$URL" "$ref" >>/tmp/push.log 2>&1; then
      echo "  OK $ref"
      return 0
    fi
    sleep 2
  done
  echo "  FAIL $ref"
  return 1
}

: > /tmp/push.log
HEAD_SHA=$(git rev-parse HEAD)
PARENT=$(git rev-parse HEAD~1)

# 先推父提交，再推 HEAD（每次包小一点）
try_push "$PARENT:refs/heads/main" || true
try_push "$HEAD_SHA:refs/heads/main" || true
git -c http.sslVerify=false -c credential.helper= fetch "$URL" main -q 2>/dev/null
echo "--- 远端 main: $(git rev-parse --short FETCH_HEAD 2>/dev/null)"
echo "--- 本地 HEAD: $(git rev-parse --short HEAD)"
