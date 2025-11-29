# 実装タスク計画（PR単位）

PRごとに小さく進め、TDDとCI通過を必須とする。ブランチ名は例示。

## Phase 1: Foundation
- [ ] chore/init-project-structure  
  - pyproject.toml（Poetry/uv）、core依存（langgraph/langchain/pydantic/pytest/ruff/mypy 等）追加  
  - ruff.toml, mypy.ini, .env.example 整備  
  - CI: GitHub Actions で lint + pytest  
  - Tests: env未設定時のエラー、pytestのダミーテスト起動確認
- [ ] feature/define-state-schema  
  - `src/state.py` に Thesis/Research State の TypedDict または Pydantic モデル定義  
  - メッセージリデューサー（append）、構造フィールド（research_topics/documents/citation_stats/draft_sections/next_node 等）  
  - Tests: メッセージ追記のリデュース動作、型バリデーションエラー確認

## Phase 2: Tools
- [ ] feature/tool-semantic-scholar  
  - `src/tools/scholar.py` SemanticScholarAPI（search_papers, get_paper_details, 429リトライ）  
  - LangChain @tool 化  
  - Tests: VCR/モックでJSONパース、ページネーション取得確認
- [ ] feature/tool-docling-parser  
  - `src/tools/pdf_parser.py` Doclingで PDF→Markdown 変換（URL→一時保存→解析）  
  - Tests: 複雑レイアウトPDFの見出し/表検出、破損URL時のエラー
- [ ] feature/tool-scite-validation  
  - `src/tools/citation_check.py` Scite API で supporting/mentioning/contrasting tallies と信頼スコア判定  
  - Tests: 代表DOIでスコア/警告のデータ駆動テスト
- [ ] feature/tool-e2b-sandbox  
  - `src/tools/code_execution.py` e2b_code_interpreter 統合、コード実行と出力/生成ファイル取得、タイムアウト  
  - Tests: 正常計算、無限ループ/外部アクセス阻止のサンドボックス確認

## Phase 3: Agents
- [ ] feature/agent-researcher-storm  
  - STORM視点生成、視点別検索、対話シミュレーションで疑問抽出→documents へ格納  
  - Tests: 多様視点生成（重複なし）、documents への視点メタデータ付与
- [ ] feature/agent-validator  
  - Sciteツールで信頼性判定、否定/撤回フラグ付け、Noveltyチェックプロンプト  
  - Tests: 混在リスト入力で疑わしい論文がフラグされるか
- [ ] feature/agent-writer  
  - アウトライン生成、セクション執筆、引用ID `` 強制、自己修正ループ  
  - Tests: 段落ごとに引用マーカー存在確認、長文分割/修正動作

## Phase 4: Orchestration
- [ ] feature/graph-supervisor-router  
  - `src/graph/supervisor.py` RouteResponse（structured output）、Stateに応じた次ノード決定  
  - Tests: 状況別ルーティング（情報なし→Researcher、未検証ドラフト→Validator、完了→FINISH）
- [ ] feature/construct-main-graph  
  - `src/graph/builder.py` StateGraph構築、各ノード登録、条件付きエッジ、checkpoint設定  
  - Tests: グラフ静的検査（孤立/無限ループなし）、モックツールでENDまでのスモーク

## Phase 5: Delivery & QA
- [ ] feature/user-interface  
  - CLI `src/main.py`（argparse）、ストリーミングUI `src/app.py`（Streamlit/FastAPI + astream_events）、Markdown出力保存  
  - Tests: 実行後に出力ファイル生成・非空を確認
- [ ] chore/e2e-testing-and-eval  
  - 統合テストスイート、LangSmith評価セット、幻覚/引用精度の自動評価スクリプト、性能・レート測定  
  - Tests: 代表トピックでタイムアウトしない、API呼び出し回数がしきい値内、評価スコア計測
