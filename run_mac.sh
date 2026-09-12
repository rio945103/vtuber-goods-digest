#!/bin/bash
# vtuber_goods_digest の MacBook 定期実行スクリプト（launchd から毎日 06:00 JST に起動する前提）
#
# 実行内容: python src/main.py で新着グッズを取得し Discord Webhook へ通知する。
# cc-knowledge への書き込みは一切行わない（独立したツール）。
#
# 前提: .venv は Mac 上で作り直すこと（Windows venv は使い回せない）。
#       flask は requirements.txt に含まれていない（README にも明記）。
#       通知バッチ(main.py)は flask を使わないため、バッチ専用運用なら不要。
#       管理画面(src/app.py, port 5000)も使う場合のみ `pip install flask` を追加する。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p logs
LOG_FILE="logs/scheduled_$(TZ='Asia/Tokyo' date '+%Y%m%d_%H%M').log"

{
    echo "=== vtuber-goods-digest start: $(TZ='Asia/Tokyo' date '+%Y-%m-%d %H:%M:%S JST') ==="
    .venv/bin/python src/main.py
    EXIT=$?
    echo "=== vtuber-goods-digest end: $(TZ='Asia/Tokyo' date '+%Y-%m-%d %H:%M:%S JST') (exit=$EXIT) ==="
} >> "$LOG_FILE" 2>&1

exit $EXIT
