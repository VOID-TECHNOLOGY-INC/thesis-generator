# thesis-generator / ARAS

博士級の学位論文を自律生成する **Autonomous Research Agent System (ARAS)** の仕様概要をまとめたリポジトリ。テーマ入力またはシード論文を起点に、深層調査・構成計画・執筆・査読・LaTeX出力までをマルチエージェントで自動化する。

- **LangGraph Supervisor-Worker**: Chief Editor が Research/Planning/Drafting/Review の各リードとワーカーをオーケストレーション。DBにチェックポイントを永続化し長時間実行を維持。
- **RAGファースト設計**: Tavily/ OpenAlex / arXiv から収集した文献を Docling/PyPDFLoader で構造化し、Specter2 などでベクトル化。ChromaDB/Milvus に格納し、メタデータフィルタで新旧・影響度を制御。
- **STORM × Novelty Checker**: 多視点対話でアウトラインを合成し、Purpose/Mechanism/Evaluation/Application の4ファセット比較で新規性を判定・ピボット。
- **MemGPT型コンテキスト管理**: Active Workspace / Chapter Summaries / Vector Store の3層メモリで長編整合性を維持。セクションごとに Draft → Critique → 修正のループを実施。
- **厳密な査読レイヤ**: ログ確率・自己無撞着チェック、Scite.ai で引用の実在/支持/反証を検証。剽窃チェックと危険トピック検知をガードレールとして実装。

## 環境変数の設定 (.env)
`src/thesis_generator/config.py` は `.env` または環境変数からキーをロードします。ローカルで実行する場合は `.env.example` を複製して値を入れてください。

```bash
cp .env.example .env
# エディタで以下を書き換え:
# OPENAI_API_KEY=sk-...                # https://platform.openai.com/api-keys
# SCITE_API_KEY=...                    # https://api.scite.ai
# OPENALEX_MAILTO=you@example.com      # 任意。負荷配分のための連絡先
# LANGCHAIN_TRACING_V2=false
# LANGCHAIN_ENDPOINT=                  # 例: https://api.smith.langchain.com
# LANGCHAIN_API_KEY=                   # LangSmithのAPIキー
# LANGCHAIN_PROJECT=thesis-generator   # 任意のプロジェクト名
```

一時的にシェルで設定する場合は `export OPENAI_API_KEY=...` のように環境変数をセットしてからコマンドを実行してください。

### LangChain/LangSmith の設定
- トレーシングを使わない場合は `LANGCHAIN_TRACING_V2=false` のままで構いません。
- LangSmith でトレースしたい場合だけ、以下を有効化してください。
  ```bash
  LANGCHAIN_TRACING_V2=true
  LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
  LANGCHAIN_API_KEY=lsv2-...   # LangSmithの「Settings > API Keys」で取得
  LANGCHAIN_PROJECT=thesis-generator
  ```
  上記のままでも動作に影響はなく、設定しなければトレーシング無しで動きます。

## 主要アーキテクチャ
- **フェーズ**: (1) Deep Research (幅優先→引用深掘り) → (2) Structural Planning (STORM + 新規性評価) → (3) Iterative Drafting (RAG + メモリ階層) → (4) Verification & Review → (5) LaTeXコンパイル。
- **エージェント**: Chief Editor / Research Lead / Planning Lead / Drafting Lead / Review Lead と、Reference Hunter・Code Executor・Novelty Checker・Scite Verifier などのワーカー。
- **状態管理 (ThesisState)**: テーマ、スタイルガイド、知識グラフ、視点リスト、アウトライン、進捗インデックス、章要約、novelty_score、hallucination_flags、ユーザー承認状態を保持。セクションは `id/title/content/summary/citations/status/feedback` を持ち、引用は S2 ID or DOI ベースで一元管理。
- **ツール連携**: OpenAlex / Tavily / arXiv / Scite.ai API、PostgreSQL チェックポイント、Docker サンドボックスでの Python 実行と図表生成。

## セットアップ (開発用)
Poetry 例:
```bash
poetry add langchain langgraph langchain-openai pydantic
poetry add chromadb pymilvus psycopg2-binary
poetry add arxiv pyalex docling pypdf
poetry add tavily-python beautifulsoup4
```
uv 派生や他のパッケージマネージャでも同等に追加する。

## 執筆・検証フローの要点
- セクション単位で RAG コンテキストを構築し、引用は `` のようなIDプレースホルダで保持。最終コンパイル時に `\cite{...}` と `.bib` を自動生成。
- Critique がスタイル/整合性/引用妥当性をチェックし、Scite Verifier が実在・支持/反証文脈を検証。問題があれば Drafting に差し戻す。
- 剽窃類似度が高い場合は Paraphraser で再生成。危険トピックは Supervisor が拒否。
- API レート制限やコンテキスト溢れに備え、指数バックオフと要約圧縮によるリトライを実装。

## 今後の実装タスク例
- LangGraph ステートグラフの具現化と Postgres チェックポインタ統合
- Vector Store ingest パイプラインと Parent-Child チャンク化の実装
- Novelty Checker（4ファセット比較）のスコアリングロジック実装
- Scite/Trinka 互換の引用検証モジュール実装
- Docker サンドボックスでの Code Executor と LaTeX ビルドパイプライン
