# changelog-monitor - Claude Code Documentation

## プロジェクト概要

このプロジェクトは、GitHubリポジトリのCHANGELOG.mdを定期的に監視し、更新があった際にGemini APIで日本語翻訳してLINE Notifyに通知する自動化システムです。

### 動作フロー

1. **15分ごとに実行**（GitHub Actions）
2. **CHANGELOG.md取得** - GitHub Raw Content APIから最新版を取得
3. **変更検出** - スナップショットとハッシュ比較
4. **差分抽出** - 新しく追加された行のみを抽出
5. **日本語翻訳** - Gemini APIで技術文書として翻訳
6. **LINE通知** - 翻訳結果をLINE Notifyで送信
7. **スナップショット更新** - 次回比較用に保存

## 技術スタック

- **Python 3.13** - 最新安定版
- **uv** - 高速なPythonパッケージマネージャー
- **google-genai** - Gemini API公式クライアント
- **requests** - HTTP通信
- **pyyaml** - YAML設定ファイル読み込み
- **GitHub Actions** - 自動実行基盤
- **Dev Container** - 統一された開発環境

## アーキテクチャ

### モジュール構成

```
scripts/
├── fetcher.py       # GitHubからCHANGELOG取得・差分抽出
├── translator.py    # Gemini API翻訳
├── notifier.py      # LINE Notify送信
└── monitor.py       # メインロジック・スナップショット管理
```

### データフロー

```
monitor.py
  │
  ├─→ fetcher.fetch_changelog()
  │     └─→ GitHub Raw Content API
  │
  ├─→ SnapshotManager.load_snapshot()
  │     └─→ snapshots/{owner}_{repo}_CHANGELOG.json
  │
  ├─→ fetcher.extract_diff()
  │     └─→ 行単位の差分検出
  │
  ├─→ translator.translate()
  │     └─→ Gemini 2.0 Flash API
  │
  ├─→ notifier.send()
  │     └─→ LINE Notify API
  │
  └─→ SnapshotManager.save_snapshot()
        └─→ snapshots/{owner}_{repo}_CHANGELOG.json
```

## 主要機能

### 1. CHANGELOG監視

**Fetcherクラス** (`scripts/fetcher.py`)

- `fetch_changelog()`: GitHub Raw Content APIから取得
  - URL: `https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file}`
  - タイムアウト: 10秒
  - エラーハンドリング: 404、タイムアウト、ネットワークエラー

- `extract_diff()`: 差分抽出
  - 行単位比較
  - 先頭から新規行のみ抽出
  - 最大50行まで
  - 初回は全体の先頭50行

### 2. 翻訳処理

**Translatorクラス** (`scripts/translator.py`)

- **モデル**: `gemini-2.0-flash-exp`
- **温度**: 0.3（安定した翻訳）
- **最大トークン数**: 2048

**翻訳ルール:**
- 技術的に正確な翻訳
- バージョン番号は英語のまま（例: v2.0.74）
- 技術用語は英語のまま（API、SDK、CLI等）
- コマンド・関数名・クラス名は英語のまま
- ファイル名・パスは英語のまま
- URLは変更しない
- コードブロックは変更しない
- マークダウン記法を保持
- 箇条書き構造を保持

**エラーハンドリング:**
- レート制限（429）: 3秒待機して1回リトライ
- その他エラー: 原文に "[翻訳失敗]" を付けて返却

### 3. 通知システム

**Notifierクラス** (`scripts/notifier.py`)

- **API**: LINE Notify (`https://notify-api.line.me/api/notify`)
- **タイムアウト**: 10秒

**メッセージフォーマット:**
```
📄 {repo_name} CHANGELOG更新

{translated_text}

詳細: {repo_url}
```

**文字数制限:**
- LINE Notify上限: 1000文字
- 翻訳テキスト部分: 最大800文字
- 超過時: `truncate_message()`で切り詰め
  - 改行位置を優先
  - スペース位置を次点
  - 末尾に "...(続きはリンク先で)" を追加

### 4. スナップショット管理

**SnapshotManagerクラス** (`scripts/monitor.py`)

**ファイル名パターン:**
```
snapshots/{owner}_{repo}_CHANGELOG.json
```

**スナップショット構造:**
```json
{
  "repository": {
    "owner": "anthropics",
    "repo": "claude-code",
    "file": "CHANGELOG.md",
    "branch": "main"
  },
  "content_hash": "sha256のハッシュ値",
  "last_updated": "2025-12-27T15:30:00+00:00",
  "last_checked": "2025-12-27T15:45:00+00:00"
}
```

**主要メソッド:**
- `load_snapshot()`: 既存スナップショット読み込み
- `save_snapshot()`: スナップショット保存
- `calculate_hash()`: SHA256ハッシュ計算
- `update_last_checked()`: チェック日時のみ更新

**変更検出:**
1. 現在のCHANGELOG内容からSHA256ハッシュ計算
2. スナップショットのハッシュと比較
3. 一致: 変更なし（通知なし）
4. 不一致: 変更あり（翻訳・通知・更新）

## 開発ガイド

### ローカル実行

```bash
# Dev Container内で実行
uv run python scripts/monitor.py
```

### テスト実行

```bash
uv run pytest
```

### リント実行

```bash
# チェック
uv run ruff check .

# 自動修正
uv run ruff check --fix .
```

### フォーマット実行

```bash
uv run ruff format .
```

## 設定詳細

### 環境変数

**必須:**
- `GEMINI_API_KEY`: Gemini APIキー
  - 取得: https://aistudio.google.com/app/apikey
- `LINE_NOTIFY_TOKEN`: LINE Notifyトークン
  - 取得: https://notify-bot.line.me/my/

**設定場所:**
- ローカル: `.env`ファイル
- GitHub Actions: Repository Secrets

### 設定ファイル（config/repositories.yml）

**グローバル設定:**
```yaml
translation:
  model: "gemini-2.0-flash-exp"  # Geminiモデル
  max_tokens: 2048                # 最大トークン数
  temperature: 0.3                # 温度パラメータ

notification:
  max_message_length: 800         # 翻訳テキストの最大文字数
```

**リポジトリ設定:**
```yaml
repositories:
  - name: "Claude Code"           # 表示名（日本語可）
    owner: "anthropics"           # GitHubオーナー
    repo: "claude-code"           # リポジトリ名
    file: "CHANGELOG.md"          # 監視ファイル
    branch: "main"                # ブランチ
    enabled: true                 # 有効/無効
```

### 監視対象の追加方法

1. `config/repositories.yml`を開く
2. `repositories`配列に新しいエントリを追加
3. コミット・プッシュ
4. 次回実行から自動的に監視開始

**例:**
```yaml
repositories:
  - name: "Your Project"
    owner: "your-org"
    repo: "your-repo"
    file: "CHANGELOG.md"
    branch: "main"
    enabled: true
```

## トラブルシューティング

### 1. "GEMINI_API_KEY environment variable is required"

**原因:** 環境変数が設定されていない

**解決策:**
- ローカル: `.env`ファイルに`GEMINI_API_KEY=...`を追加
- GitHub Actions: Repository Secretsに`GEMINI_API_KEY`を追加

### 2. "LINE_NOTIFY_TOKEN environment variable is required"

**原因:** 環境変数が設定されていない

**解決策:**
- ローカル: `.env`ファイルに`LINE_NOTIFY_TOKEN=...`を追加
- GitHub Actions: Repository Secretsに`LINE_NOTIFY_TOKEN`を追加

### 3. 通知が届かない

**確認項目:**
1. LINE Notifyトークンが有効か確認
2. トークンが正しくSecretsに設定されているか確認
3. GitHub Actionsのログを確認
4. notifier.pyのログを確認

### 4. 翻訳が失敗する（"[翻訳失敗]"）

**確認項目:**
1. Gemini APIキーが有効か確認
2. API制限に達していないか確認（無料枠: 15 RPM）
3. translator.pyのログを確認
4. Gemini APIのステータスページを確認

### 5. スナップショットがコミットされない

**確認項目:**
1. `snapshots/`ディレクトリが存在するか確認
2. `.gitignore`に`snapshots/`が含まれていないか確認
3. GitHub Actionsの権限設定を確認
4. ワークフローのログを確認

### 6. 変更があるのに通知されない

**確認項目:**
1. `enabled: true`になっているか確認
2. スナップショットのハッシュが正しいか確認
3. ログで差分抽出結果を確認
4. CHANGELOGの更新場所を確認（先頭以外は検出されない）

## コスト試算

### Gemini API（無料枠）
- **制限**: 15 RPM（Requests Per Minute）
- **実行頻度**: 15分に1回 = 1時間に4回 = 1日96回
- **RPM制限**: 15分に1回なので余裕で問題なし
- **月間実行回数**: 約2,880回
- **コスト**: $0（無料枠内）

### LINE Notify
- **制限**: 1時間あたり1000件
- **実行頻度**: 変更時のみ
- **コスト**: $0（完全無料）

### GitHub Actions
- **パブリックリポジトリ**: 無料
- **実行時間**: 1回あたり約30秒〜1分
- **月間実行時間**: 約48〜96時間
- **コスト**: $0（パブリックリポジトリ）

**総コスト: $0**

## よくある質問

### Q: プライベートリポジトリでも使えますか？

A: はい、使えます。ただしGitHub Actionsの無料枠は月2,000分です。超過すると課金されます。

### Q: 監視頻度を変更できますか？

A: はい、`.github/workflows/monitor.yml`のcron式を変更してください。
例: `*/30 * * * *`（30分ごと）

### Q: 複数のLINEグループに通知できますか？

A: 現在は1つのトークンのみサポート。複数通知したい場合は、notifier.pyを拡張して複数トークンに対応する必要があります。

### Q: CHANGELOGの途中の変更は検出されますか？

A: いいえ、現在の実装は先頭からの差分のみ検出します。途中の変更を検出したい場合は、より高度な差分アルゴリズムが必要です。

### Q: 翻訳の品質を調整できますか？

A: はい、`config/repositories.yml`の`temperature`パラメータを調整してください。
- 0.0〜0.5: より安定・正確
- 0.5〜1.0: より創造的・自然

### Q: 他の翻訳APIは使えますか？

A: translator.pyを書き換えれば可能です。例: OpenAI GPT、Claude API、DeepL等
