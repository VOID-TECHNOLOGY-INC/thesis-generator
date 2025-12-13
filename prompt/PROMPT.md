# タスク実行プロンプト

このリポジトリでPR/タスクを進める際の実行手順。`prompt/TASK.md` を単一の出発点にし、`prompt/PLAN.md` と `prompt/SPEC.md` で背景・仕様を確認する。

## 実装フロー

### 1. ブランチ
- `main` から作業を開始し、`feature/<task>-<slug>` 形式でブランチを切る  
  例: `feature/agent-writer-fixes`

### 2. 環境準備
- `.env.example` を `.env` にコピーし、APIキーを設定（OpenAI/Scite/OPENALEX_MAILTO など）  
- `poetry install` で依存を入れる（必要なら `poetry shell`）

### 3. TDD（Red → Green → Refactor）
- まず失敗するテストを書く。外部API（OpenAI/OpenAlex/Scite/E2B）はモックすること
- 最小実装でテストを通し、その後リファクタリング

### 4. コマンドガイド
```bash
poetry run ruff check          # Lint
poetry run mypy src tests      # 型チェック
poetry run pytest              # ユニット/統合/E2E/評価テストすべて
# 長いスイートを分けたい場合の例:
poetry run pytest tests/test_e2e_eval.py
```
- 変更範囲に応じて関連テストを優先し、最終的に `pytest` 全体を通す

### 5. ドキュメント更新
- 仕様や完了状況の変更があれば `prompt/TASK.md` を最新化する
- 新しいインターフェースや挙動変更があれば README やコメントも同期する

### 6. コミット & PR
- コミットメッセージ: `<type>(<scope>): <description>`（例: `fix(graph): handle empty outline`）  
  type は `feat|fix|test|docs|refactor|chore` を使用
- 粒度は小さく、main に直接コミットしない
- PRを作成し、テンプレートに沿ってタスク/テスト結果を記載

### 7. チェックリスト
- [ ] ブランチを `main` から作成した
- [ ] テストを先に書いた（TDD）
- [ ] 関連テストと `poetry run pytest` がパス
- [ ] `poetry run ruff check` / `poetry run mypy src tests` がパス
- [ ] `prompt/TASK.md` などドキュメントを更新した
- [ ] コミットメッセージ形式を遵守した
- [ ] PRを作成し、CIが通過

## 注意事項
- 既存テストを壊さないこと。非決定的な部分はモックで固定する
- 秘匿情報をログ/差分に含めない
- Windows対応はスタブで良いが、macOS/Linux で確実に動くことを優先する
