# セットアップ手順

## 重要: GitHub Actions ワークフローファイルの追加

GitHub のセキュリティ制限により、ワークフローファイルは自動的にプッシュできませんでした。
以下の手順で手動で追加してください。

### 手順

1. **GitHubリポジトリにアクセス**
   - ブラウザで https://github.com/taigok/changelog-monitor を開く

2. **ワークフローファイルを追加**
   - "Add file" → "Create new file" をクリック
   - ファイル名に `.github/workflows/monitor.yml` と入力
   - 以下の内容をコピー&ペースト:

```yaml
name: CHANGELOG Monitor

on:
  # Run every 15 minutes
  schedule:
    - cron: '*/15 * * * *'

  # Allow manual triggering
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - name: Setup Python
        run: uv python install 3.13

      - name: Install dependencies
        run: uv sync

      - name: Run monitor script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          LINE_NOTIFY_TOKEN: ${{ secrets.LINE_NOTIFY_TOKEN }}
        run: uv run python scripts/monitor.py

      - name: Commit and push snapshots
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add snapshots/

          # Only commit if there are changes
          if ! git diff --staged --quiet; then
            git commit -m "chore: update snapshots [skip ci]"
            git push
          else
            echo "No snapshot changes to commit"
          fi
```

3. **コミット**
   - コミットメッセージ: `chore: add GitHub Actions workflow`
   - "Commit new file" をクリック

4. **Secretsを設定**（まだの場合）
   - Settings → Secrets and variables → Actions
   - "New repository secret" をクリック
   - 以下の2つのSecretsを追加:
     - `GEMINI_API_KEY`: Gemini APIキー
     - `LINE_NOTIFY_TOKEN`: LINE Notifyトークン

5. **監視対象を設定**
   - `config/repositories.yml` を編集
   - コメントアウトされた例を参考に、監視したいリポジトリを追加

6. **動作確認**
   - Actions タブを開く
   - "CHANGELOG Monitor" を選択
   - "Run workflow" をクリックして手動実行
   - ログを確認

## 次のステップ

1. `.env`ファイルにAPIキーを設定（ローカル開発用）
2. `config/repositories.yml`に監視対象を追加
3. ローカルでテスト実行: `uv run python scripts/monitor.py`
4. 問題なければ、15分ごとの自動実行が開始されます

詳細は README.md を参照してください。
