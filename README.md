# vtuber_goods_digest

複数 VTuber 事務所のグッズストアを定期巡回し、新着商品を Discord に通知するツール。Flask 製の Web 管理画面も付属。

## 機能

- 複数事務所・複数ストア形式に対応した商品取得
- 新着 / 再販 / 発売まもなく のタグ付き Discord 通知
- 重複通知防止（SQLite で通知済みフラグを管理）
- 永久販売品・システム障害通知などの自動除外フィルター
- ブラウザで見られる商品一覧管理画面（事務所・メンバー・ステータスで絞り込み）

## 動作環境

- Python 3.11 以上
- Windows（タスクスケジューラ前提）

## セットアップ

```bash
# 仮想環境を作成して有効化
python -m venv .venv
.venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt
pip install flask   # requirements.txt 未収録のため別途インストール
```

## 設定

### 環境変数 (`.env`)

プロジェクトルートに `.env` を作成する。

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
DATABASE_PATH=data/app.db   # 省略可、デフォルト値
```

### 監視対象メンバー (`config/members.json`)

```jsonc
[
  {
    "display_name": "elira-pendora",          // DB の紐付けキー。後から変更しない
    "keywords": ["エリラ", "Elira Pendora"],
    "store_url": "https://shop.nijisanji.jp/s/niji/page/elira-pendora",
    "store_type": "nijisanji",                // 取得方式（後述）
    "agency": "nijisanji"
  }
]
```

#### `store_type` の種類

| 値 | 説明 |
|---|---|
| `nijisanji` | にじさんじ公式ストアの HTML スクレイピング |
| `shopify` | Shopify の `/products.json` API（メンバー専用ストア用） |
| `shopify_search` | Shopify の検索 API（Neo-Porte など複数メンバー共有ストア用） |

`shopify_search` を使う場合は `search_query` フィールドも追加する。

## 実行方法

### 通知バッチ（手動 or タスクスケジューラ）

```bash
.venv\Scripts\python.exe src\main.py
```

`run_daily.bat` を Windows タスクスケジューラに登録すると毎日自動実行できる。ログは `logs\scheduled.log` に追記される。

### 管理画面

```bash
start_app.bat
# または
.venv\Scripts\python.exe src\app.py
```

ブラウザで http://127.0.0.1:5000/ を開く。

## 管理画面の操作

- **事務所タブ**: にじさんじ / ぶいすぽ / ホロライブ / Neo-Porte で絞り込み
- **メンバーチップ**: 特定メンバーのみ表示
- **ステータスチップ**: 発売中 / 発売予定 で絞り込み
- 商品タイトルはストアへのリンクになっている

## Discord 通知の形式

```
【VTuberグッズ新着ダイジェスト】

■ elira-pendora
・[発売開始 / NEW / グッズ] アクリルスタンド エリラ・ペンドラ
  https://shop.nijisanji.jp/...
```

## プロジェクト構成

```
src/
├── main.py          # 通知バッチのエントリポイント
├── app.py           # Flask 管理画面
├── db.py            # SQLite 操作
├── models.py        # データモデル
├── settings.py      # 環境変数読み込み
├── fetchers/        # ストア別 HTTP 取得
├── parsers/         # ストア別 HTML/JSON パース
├── filters/         # 除外フィルター・ラベル生成
├── notifiers/       # Discord 送信
└── templates/       # Jinja2 HTML テンプレート
config/
└── members.json     # 監視対象メンバー設定
data/
└── app.db           # SQLite データベース（.gitignore 済み）
logs/
└── scheduled.log    # 実行ログ（.gitignore 済み）
```

## 新しいストア・メンバーの追加手順

1. `config/members.json` にエントリを追加する
2. 既存の `store_type` で対応できない場合は `src/fetchers/` と `src/parsers/` に新しいモジュールを追加し、`src/main.py` の `store_type` 分岐に1行足す
3. 新しい事務所を追加する場合は `src/app.py` の `AGENCY_LABELS` も更新する

## 注意事項

- **DB を削除すると全商品が新規扱いになり大量通知が飛ぶ。** 削除前は必ずバックアップを取る。
- `display_name` は DB の紐付けキーなので、追加後は変更しない。
- 並列リクエストは使用しない（ストアへの負荷軽減のため逐次処理）。
- スクレイピング失敗メンバーは実行ログ末尾の「取得失敗メンバー」に出力される。
