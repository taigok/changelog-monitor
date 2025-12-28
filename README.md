# changelog-monitor

GitHub CHANGELOG監視・翻訳・Discord通知システム

GitHubリポジトリのCHANGELOG.mdを自動監視し、更新があったらGemini APIで日本語翻訳してDiscordに通知します。

## Features

- GitHub CHANGELOG.mdの自動監視（15分間隔）
- Gemini 2.0 Flash による高品質な日本語翻訳
- 技術用語の適切な保持（バージョン番号、API名、コマンド等）
- Discord Webhookによる即時通知
- Dev Container対応の開発環境
- 完全無料（無料APIの範囲内）

## Setup

### 1. API Key取得

#### Gemini API Key

1. [Google AI Studio](https://aistudio.google.com/app/api-keys) にアクセス
2. Googleアカウントでログイン
3. "Create API Key" をクリック
4. 既存のGCPプロジェクトを選択または新規作成
5. APIキーをコピー

**無料枠:** 15 RPM（15分間隔の実行なら十分）

#### Discord Webhook URL

1. Discordサーバーで通知を受け取りたいチャンネルを選択
2. チャンネル設定（歯車アイコン）→「連携サービス」を開く
3. 「ウェブフック」タブを選択
4. 「新しいウェブフック」をクリック
5. ウェブフック名を入力（例: "CHANGELOG Monitor"）
6. 「ウェブフックURLをコピー」をクリック

### 2. ローカル開発環境（Dev Container）

1. このリポジトリをクローン:
   ```bash
   git clone https://github.com/yourusername/changelog-monitor.git
   cd changelog-monitor
   ```

2. VS Codeで開く:
   ```bash
   code .
   ```

3. Dev Containerで再起動:
   - コマンドパレット（Cmd/Ctrl+Shift+P）を開く
   - "Dev Containers: Reopen in Container" を選択

4. `.env`ファイルを編集:
   ```bash
   # .envは自動作成されます
   # APIキーを設定してください
   ```

   `.env`:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
   ```

### 3. GitHub Actions設定

#### リポジトリをパブリックに設定

GitHub Actionsの無料枠を利用するため、リポジトリはパブリックにしてください。

#### Secretsを設定

1. GitHubリポジトリページで "Settings" を開く
2. 左サイドバーから "Secrets and variables" → "Actions" を選択
3. "New repository secret" をクリック
4. 以下のSecretsを追加:
   - `GEMINI_API_KEY`: 取得したGemini APIキー
   - `DISCORD_WEBHOOK_URL`: 取得したDiscord Webhook URL

## Configuration

### 監視対象の追加

`config/repositories.yml` を編集して、監視したいリポジトリを追加します:

```yaml
repositories:
  - name: "Claude Code"
    owner: "anthropics"
    repo: "claude-code"
    file: "CHANGELOG.md"
    branch: "main"
    enabled: true
```

**フィールド説明:**
- `name`: 表示名（LINE通知に表示される、日本語可）
- `owner`: GitHubオーナー名
- `repo`: リポジトリ名
- `file`: 監視するファイル（通常は `CHANGELOG.md`）
- `branch`: ブランチ名（デフォルト: `main`）
- `enabled`: 有効/無効（`false`で一時的に無効化可能）

### 複数リポジトリの監視

複数のリポジトリを監視する場合は、配列に追加してください:

```yaml
repositories:
  - name: "Claude Code"
    owner: "anthropics"
    repo: "claude-code"
    file: "CHANGELOG.md"
    branch: "main"
    enabled: true

  - name: "Anthropic SDK Python"
    owner: "anthropics"
    repo: "anthropic-sdk-python"
    file: "CHANGELOG.md"
    branch: "main"
    enabled: true
```

## Usage

### ローカル実行

```bash
# Dev Container内で
uv run python scripts/monitor.py
```

### 手動実行（GitHub Actions）

1. GitHubリポジトリページで "Actions" タブを開く
2. "CHANGELOG Monitor" ワークフローを選択
3. "Run workflow" をクリック

### 自動実行

設定後、15分ごとに自動実行されます。スナップショットは自動的にコミット・プッシュされます。

## Discord通知の例

```
📄 **Claude Code CHANGELOG更新**

【v2.0.75】
- LSP（Language Server Protocol）ツールを追加し、定義へのジャンプ、参照の検索、ホバードキュメントなどのコードインテリジェンス機能を実装
- Kitty、Alacritty、Zed、Warpターミナル用の /terminal-setup サポートを追加
...

**詳細:** https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
```

## Development

### テスト実行

```bash
uv run pytest
```

### リント実行

```bash
uv run ruff check .
```

### フォーマット実行

```bash
uv run ruff format .
```

## Cost

すべて無料枠内で動作します:

- **Gemini API**: 無料（15 RPM制限、15分間隔なら問題なし）
- **Discord Webhook**: 完全無料
- **GitHub Actions**: パブリックリポジトリは無料

## License

MIT

## Contributing

Pull requestsを歓迎します！

## Troubleshooting

### "GEMINI_API_KEY environment variable is required"

`.env`ファイルに`GEMINI_API_KEY`が設定されていることを確認してください。

### "DISCORD_WEBHOOK_URL environment variable is required"

`.env`ファイルに`DISCORD_WEBHOOK_URL`が設定されていることを確認してください。

### 通知が届かない

1. Discord Webhook URLが正しいか確認
2. Webhook URLが無効化されていないか確認
3. GitHub Secretsが正しく設定されているか確認
4. GitHub Actionsのログを確認

### 翻訳が失敗する

1. Gemini APIキーが正しいか確認
2. API制限に達していないか確認（無料枠: 15 RPM）
3. ログを確認してエラー内容を特定
