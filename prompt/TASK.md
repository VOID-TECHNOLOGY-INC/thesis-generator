# 実装タスク計画（PR単位）

PRごとに小さく進め、TDDとCI通過を必須とする。ブランチ名は例示。

## Phase 1: Foundation
- [x] chore/init-project-structure  
  - pyproject.toml（Poetry/uv）、core依存（langgraph/langchain/pydantic/pytest/ruff/mypy 等）追加  
  - ruff.toml, mypy.ini, .env.example 整備  
  - CI: GitHub Actions で lint + pytest  
  - Tests: env未設定時のエラー、pytestのダミーテスト起動確認
- [x] feature/define-state-schema  
  - `src/state.py` に ThesisState の TypedDict または Pydantic モデル定義（PLAN/SPEC準拠）  
  - topic/target_word_count/style_guide、knowledge_graph/perspectives、outline/manuscript、current_section_index、chapter_summaries(Annotated[Dict[str,str], operator.or_])、vector_store_uri、novelty_score/hallucination_flags、user_approval_status/execution_trace/next_node を含める  
  - Tests: chapter_summariesのリデュース動作、型バリデーションエラー確認

## Phase 2: Tools
- [x] feature/tool-rag-ingest  
  - `src/tools/ingest.py` Docling/PyPDFLoaderでセクション構造抽出、Parent-Childチャンク生成、メタデータ（year/citations/authors）付与  
  - specter系埋め込みでMilvus/Chromaに格納し vector_store_uri を返す `ingest_documents` と `search_sections(query, filters)` を実装  
  - Tests: 親子チャンク対応、年度フィルタの適用確認
- [x] feature/tool-openalex  
  - `src/tools/openalex.py` OpenAlex API（search_papers, get_paper_details）  
  - LangChain @tool 化  
  - Tests: モックでJSONパース、ページネーション取得確認
- [x] feature/tool-docling-parser  
  - `src/tools/pdf_parser.py` Doclingで PDF→Markdown 変換（URL→一時保存→解析）  
  - Grobid/Unstructured等のフォールバックを実装し、Docling失敗時も最低限の本文を確保  
  - Tests: 複雑レイアウトPDFの見出し/表検出、破損URL時のエラー、Docling失敗時にフォールバックが動作すること
- [x] feature/tool-scite-validation  
  - `src/tools/citation_check.py` Scite API で supporting/mentioning/contrasting tallies と信頼スコア判定  
  - カバレッジ外/レート制限時のフォールバック（警告＋手動承認or代替ソース）を実装  
  - Tests: 代表DOIでスコア/警告のデータ駆動テスト、レート制限/Unknown DOI時のフォールバック動作
- [ ] feature/citation-stance-fallback  
  - Sciteをオプション化し、未設定時は OpenAlex/S2/COCI から引用元要旨を取得→LLMでsupporting/contrasting分類するパイプラインを用意  
  - スコア算出ロジックは Scite と同等の指標を維持し、カバレッジなし時は警告＋手動レビュー要で返す  
  - Tests: Sciteなし環境でのLLM分類モックによるスコア計算、OpenAlexレスポンス空時の警告フロー、APIエラー時のフォールバック確認
- [x] feature/tool-e2b-sandbox  
  - `src/tools/code_execution.py` e2b_code_interpreter 統合、コード実行と出力/生成ファイル取得、タイムアウト  
  - Tests: 正常計算、無限ループ/外部アクセス阻止のサンドボックス確認

## Phase 3: Agents
- [ ] feature/agent-planner-novelty  
  - STORM視点から3階層TOC生成、中央仮説を4ファセット（Purpose/Mechanism/Evaluation/Application）でNovelty評価し、類似度高の場合にピボット案を生成  
  - Master Plan（hypothesis/outline/novelty_score）をThesisStateにロック  
  - Tests: ピボット発生のモック検証、TOCに主要章（序論/文献/方法/結果/考察/結論）が含まれるか確認
- [ ] feature/agent-researcher-storm  
  - STORM視点生成、視点別検索、対話シミュレーションで疑問抽出→documents へ格納  
  - Tests: 多様視点生成（重複なし）、documents への視点メタデータ付与
- [ ] feature/agent-validator  
  - Sciteツールで信頼性判定、否定/撤回フラグ付け、Noveltyチェックプロンプト  
  - Sciteカバレッジ外の扱い（警告＋代替チェックorヒューマン承認）を明記  
  - Tests: 混在リスト入力で疑わしい論文がフラグされるか、カバレッジ外ケースでフォールバックが動くか
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
- [ ] chore/runtime-safety-and-secrets  
  - code_execution.py をDocker/E2Bでネットワーク遮断・書き込み制限付きで実行するラッパー化（検索/APIアクセスは別プロセスで実行しコンテナからは禁止）  
  - Secret Manager/Vault連携でAPIキーを取得し、環境変数直読み禁止  
  - PDFアップロードのPIIマスク、保持期間(30日)の自動削除ジョブ  
  - Tests: 外部アクセスを試みるコードが遮断される、Secret未設定時は起動エラー、PIIマスク適用確認

## Phase 5: Delivery & QA
- [ ] feature/user-interface  
  - CLI `src/main.py`（argparse）、ストリーミングUI `src/app.py`（Streamlit/FastAPI + astream_events）、Markdown出力保存  
  - Tests: 実行後に出力ファイル生成・非空を確認
- [ ] chore/e2e-testing-and-eval  
  - 統合テストスイート、LangSmith評価セット、幻覚/引用精度の自動評価スクリプト、性能・レート測定  
  - Tests: 代表トピックでタイムアウトしない、API呼び出し回数がしきい値内、評価スコア計測

## Phase 6: 品質ゲート・運用
- [ ] chore/quality-gates-and-ops  
  - Supervisor/Reviewerに段階的ゲートを実装（警告: Novelty>=0.6、引用対応率>=0.98、Scite失敗は再試行+警告 / ブロック: Novelty>=0.7、引用対応率100%、Scite偽陽性/偽陰性ゼロ）し、違反時に差し戻し  
  - TOC各Sectionにassigned_sourcesを紐付け、引用カバレッジチェックを自動化  
  - ゴールデンセットによるCitation Precision/Recall、Fact-to-Source一致率、スタイル遵守率の回帰テストをCIに組み込み  
  - SLO/モニタリング（1章あたり平均生成時間、ベクトル検索レイテンシ、Scite照会成功率、APIコストプロファイルなど）の収集とアラート設定  
  - Tests: 引用欠落セクションでCI失敗、評価メトリクス閾値下回りでビルド失敗、SLO/コストメトリクス収集のサニティ
