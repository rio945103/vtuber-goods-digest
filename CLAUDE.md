# vtuber_goods_digest

複数 VTuber 事務所のストアを巡回し、新着グッズを Discord に通知するツール。Web 管理画面つき(Flask)。

## 動かしかた

- 通知バッチ:`run_daily.bat` 参照(Windows タスクスケジューラで毎日実行、ログは `logs\scheduled.log`)
- 管理画面:`.venv\Scripts\python.exe src\app.py` → http://127.0.0.1:5000/
- 環境変数は `.env` に置き、`src\settings.py` 経由で読む

## 構成のキモ

- `src\{fetchers,parsers,filters,notifiers}\` … 役割ごとに分離。
- `config\members.json` … 監視対象メンバー。`store_type` で取得方法が分岐する:
  - `nijisanji` … HTML スクレイピング
  - `shopify` … Shopify API でメンバー専用ストアから取得
  - `shopify_search` … Shopify 検索 API(Neo-Porte のような複数メンバー共有ストア用)
- 新ストア対応は `fetchers\` と `parsers\` に追加し、`main.py` の `store_type` 分岐に1行足す。

## 触るときの注意

- DB を消すと全商品が新規扱いになり大量通知が飛ぶ。消す前にバックアップ。
- `members.json` の `display_name` は DB の紐付けキー。変えない。
- 新しい事務所(`agency`)を追加するときは `members.json` だけでなく `src\app.py` の `AGENCY_LABELS` も更新する。
- 並列リクエストは入れない(逐次処理でストアへの負荷を抑える方針)。
- スクレイピング失敗は実行ログ末尾の「取得失敗メンバー」セクションに出る。
