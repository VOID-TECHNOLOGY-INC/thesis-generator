
自律型学術研究エージェントシステム実装計画書：LangGraphとマルチモーダル検証ツールの統合による次世代研究支援基盤


1. 序論：プロジェクトの背景とアーキテクチャ哲学

本ドキュメントは、現代の学術研究プロセスが抱える情報の断片化と検証コストの増大という課題に対し、LangGraphを用いた自律型マルチエージェントシステム（Multi-Agent System: MAS）による技術的解決策を提示し、その詳細な実装計画を定義するものである。本計画の核心は、スタンフォード大学が提唱する**STORM（Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking）**の概念を拡張し、Semantic Scholarによる広範な知識グラフ探索と、Scite.aiによる「スマート引用（Smart Citations）」を用いた厳格な事実検証（Fact-Checking）を統合することにある。
我々が目指すシステムは、単にテキストを生成するだけのLLM（Large Language Model）ラッパーではない。それは、研究者が行う「仮説立案」「文献調査」「批判的検証」「執筆」という一連の認知プロセスを、専門化されたエージェント群に委譲し、それらを中央の監督者（Supervisor）がオーケストレーションすることで、人間が検証可能な信頼性の高い学術レポートを自律的に生成する基盤である。
本実装計画書は、ソフトウェアエンジニアリングのベストプラクティスに基づき、テスト駆動開発（TDD: Test-Driven Development）を開発プロセスの根幹に据える。すべての機能実装は、まず失敗するテストケースの作成から始まり、そのテストを通過させるためのコード記述、そしてリファクタリングという厳格なサイクルを経て行われる。また、各機能は粒度の細かいPull Request（PR）単位に分割され、それぞれに対して独立したFeatureブランチを作成することで、並行開発におけるコンフリクトを最小限に抑えつつ、コード品質を維持する戦略を採用する。

1.1 アーキテクチャの選定：なぜLangGraph Supervisorパターンなのか

本システムの中核には、LangChainエコシステム上に構築されたグラフベースのオーケストレーションフレームワークであるLangGraphを採用する。従来の直線的なチェーン（Chain）構造ではなく、循環可能なグラフ構造を選択する理由は、学術研究というタスクの非線形性にある。研究プロセスは、調査結果に基づいて新たな疑問が生まれ、再度調査に戻るという試行錯誤の連続である。LangGraphの状態管理（State Management）と条件付きエッジ（Conditional Edges）は、この動的なワークフローをモデル化するのに最適である。
特に、本計画ではSupervisor（監督者）アーキテクチャを採用する。これは、ユーザーからの複雑な要求を単一のエージェントで処理するのではなく、中央のSupervisorノードが現在の状態（Global State）を分析し、調査（Researcher）、検証（Validator）、執筆（Writer）といった特定の役割を持つワーカーエージェントにタスクを動的にルーティングする設計パターンである。これにより、各エージェントの責務（Separation of Concerns）が明確化され、個別の最適化やツールの差し替えが容易になる拡張性の高いシステムが実現する。
コンポーネント
選定技術
選定理由と役割
Orchestration
LangGraph
循環フロー、永続化（Checkpointing）、Human-in-the-loopのネイティブサポートにより、複雑な自律エージェントの制御を実現する。
Literature Search
Semantic Scholar API
2億本以上の論文データベースへのグラフアクセスを提供。引用・被引用関係のトラバース（Graph Traversal）により、関連研究の深掘りが可能。
Validation
Scite.ai API
引用文脈（支持/否定/言及）の分類データを提供。LLMの幻覚（Hallucination）を抑制し、生成された主張の裏付けを行うための唯一無二の検証ソース。
Document Parsing
Docling (IBM)
PDF文書のレイアウト解析と構造化データ抽出に特化。図表や数式の文脈を保持したままテキスト化し、RAG（Retrieval-Augmented Generation）の精度を向上させる。
Code Execution
E2B Sandbox
安全な隔離環境でのコード実行を提供。データ分析やグラフ描画など、LLM単体では不可能な計算タスクを補完する。
Testing
Pytest & LangSmith
TDDの中核となるテストフレームワークと、エージェントの実行トレース・評価基盤。非決定的なLLMの挙動を観測可能にする。


2. 開発プロセス規定：TDDとブランチ戦略

本プロジェクトにおける開発は、単なる機能の実装ではなく、「信頼性の構築」プロセスであると定義する。したがって、以下の開発規定を全開発者が遵守するものとする。

2.1 テスト駆動開発（TDD）の義務化

TDDは、本プロジェクトにおいて推奨事項ではなく義務である。特に、外部APIや非決定的なLLMを扱う本システムにおいて、コードの堅牢性を担保する唯一の手段は、実行可能な仕様書としてのテストコードである。
開発サイクルは以下の厳格な手順（Red-Green-Refactor）に従う：
Red (Test First): 実装しようとする機能の要件を満たすテストコードを記述する。この時点では実装が存在しないため、テストは必ず失敗する。このフェーズでは、インターフェース設計（関数名、引数、戻り値）を確定させることにもなる。
Green (Make it Pass): テストを通過させるための最小限の実装を行う。この段階では、コードの美しさよりも動作の正確性を優先する。
Refactor: 重複の排除、可読性の向上、設計の改善を行う。この際、既存のテストがすべて通過し続けることを確認する。

2.2 ブランチ運用とPR管理

Gitを用いたバージョン管理においては、メインブランチ（main または develop）の安定性を最優先する。
Feature Branch Workflow: すべてのタスクは、JiraやGitHub Issues等のチケットIDをプレフィックスに持つ新しいブランチ（例: feature/PROJ-101-implement-scholar-tool）で作業を行う。直接メインブランチへコミットすることは禁止とする。
Pull Request (PR) Granularity: 1つのPRは単一の論理的な変更単位に留める。巨大なPRはレビューの質を低下させるため、機能が複雑な場合は、さらに小さなサブタスクに分割し、それぞれに対してブランチを作成する。
Review Criteria: PRのマージ条件として、CI（Continuous Integration）による自動テストの通過を必須とする。また、カバレッジレポートを確認し、主要なロジックに対するテストカバレッジが低下していないことを確認する。

3. 実装フェーズ詳細計画

本システムの実装は、基盤構築から始まり、ツール実装、エージェントロジック、そして全体統合へと進む5つのフェーズで構成される。各フェーズは具体的なPR単位のタスクに分解されており、それぞれのタスクにおいて実装すべき機能と、TDDで記述すべきテスト内容が定義されている。

Phase 1: プロジェクト基盤と型定義（Foundation & Type System）

このフェーズでは、堅牢なアプリケーションの土台を築く。Pythonの動的型付けに起因するバグを防ぐため、Pydanticを用いた厳格な型定義と、静的解析ツールの導入を行う。

開発環境の初期化とCIパイプラインの構築

目的: 開発チーム全体で統一されたコード品質基準を強制し、TDDを実践するための自動テスト基盤を確立する。
実装タスク:
依存関係管理: pyproject.toml (Poetryまたはuv推奨) を作成し、langgraph, langchain, pydantic, pytest, ruff, mypy などのコアライブラリを定義する。
静的解析設定: ruff.toml および mypy.ini を設定し、厳格なLintルール（未使用インポートの禁止、型ヒントの強制など）を適用する。
CI構成: GitHub Actionsのワークフロー定義ファイルを作成し、PR作成時に自動的にLintチェックと単体テストが実行されるようにする。
環境変数管理: .env.example を作成し、OPENAI_API_KEY, SEMANTIC_SCHOLAR_API_KEY, SCITE_API_KEY 等の機密情報の取り扱いを標準化する。
TDD / テスト内容:
Environment Test: 必要な環境変数がロードされない場合に、アプリケーションが適切なエラーメッセージを出して終了することを確認するテスト。
Sanity Check: 単純な計算（1+1=2）を行うダミーテストを配置し、CI上でpytestが正しく起動・報告することを確認する。
ブランチ名: chore/init-project-structure

共有状態（Global State）スキーマの設計

目的: エージェント間で共有されるコンテキストデータの構造を定義する。LangGraphにおいてStateはエージェントの「記憶」そのものであり、この設計がシステムの表現力を決定する。
実装タスク:
src/state.py の作成。
ResearchState クラスの定義（TypedDict または Pydantic モデルを使用）。以下のフィールドを含める必要がある：
messages: エージェント間の会話履歴（LangChainの BaseMessage リスト）。operator.add リデューサーを使用して履歴を蓄積する設計とする。
research_topics: 調査すべきトピックのリスト。STORMにおける「視点（Perspectives）」を管理する。
documents: 収集・解析された文献データのリスト。
citation_stats: 引用分析結果（支持/否定の数など）。
draft_sections: 執筆中のセクションごとのテキストデータ。
next_node: 次に遷移すべきノード名（Supervisorによるルーティング結果）。
TDD / テスト内容:
State Reducer Test: messages フィールドに新しいメッセージを追加した際、古い履歴が上書きされずに正しく結合（Append）されるかを確認するテスト。
Schema Validation Test: 不正なデータ型（例: documents に文字列を入れるなど）をStateに代入しようとした際に、型チェックエラーが発生することを確認するテスト。
ブランチ名: feature/define-state-schema

Phase 2: ツールレイヤーの実装（The Senses）

エージェントが外界と接触するための「感覚器官」となるツール群を実装する。ここでは外部APIとの通信が発生するため、テストにおけるモック戦略が重要となる。

Semantic Scholar API ラッパーの実装

目的: 学術文献の検索および詳細情報の取得機能を提供する。グラフAPIを活用し、単純なキーワード検索だけでなく、引用ネットワークを辿れるようにする。
実装タスク:
src/tools/scholar.py の作成。
SemanticScholarAPI クラスの実装。
search_papers(query, year_range, limit): /graph/v1/paper/search エンドポイントを使用。
get_paper_details(paper_id): タイトル、アブストラクト、著者、引用数、被引用数（citationCount, influentialCitationCount）を取得。
レート制限（HTTP 429）に対する指数バックオフ（Exponential Backoff）リトライロジックの実装。
LangChainの @tool デコレータを用いたツール化。
TDD / テスト内容:
Mock Integration Test: vcrpy または pytest-mock を使用し、APIからのJSONレスポンスをファイルとして保存（カセット化）する。これにより、実際のAPIを叩かずに、パースロジック（JSONからPydanticオブジェクトへの変換）が正しく動作することを保証する。
Pagination Test: 検索結果が多数ある場合、ページネーション処理が正しく動作し、指定された件数分のデータを取得できるか確認する。
ブランチ名: feature/tool-semantic-scholar

Docling PDF解析ツールの実装

目的: 論文PDFから、LLMが理解しやすい形式（Markdown等）でテキストを抽出する。特に、表（Table）構造の維持に注力する。
実装タスク:
src/tools/pdf_parser.py の作成。
IBM docling ライブラリの統合。
parse_pdf_from_url(url: str) 関数の実装。
指定されたURLからPDFをダウンロード（一時ファイルまたはメモリ上）。
DocumentConverter を使用して解析を実行。
結果をMarkdown形式で出力し、特に表データがMarkdownテーブルとして正しく表現されているかを確認する処理を含める。
TDD / テスト内容:
Layout Preservation Test: 既知の複雑なレイアウト（2段組み、図表混在）を持つサンプルPDFを用意し、変換後のMarkdownに特定の見出しや表のセルデータが含まれているかを検証する。
Error Handling Test: 破損したPDFやアクセスできないURLを与えた際に、システム全体をクラッシュさせず、適切なエラーメッセージを返すか確認する。
ブランチ名: feature/tool-docling-parser

Scite.ai 引用検証ツールの実装

目的: 論文の信頼性を定量的に評価するための「スマート引用」データを取得する。
実装タスク:
src/tools/citation_check.py の作成。
check_paper_validity(doi: str) 関数の実装。
Scite APIのエンドポイント（/tallies 等）を使用し、指定されたDOIに対する supporting, mentioning, contrasting の引用数を取得する。
検証ロジック: contrasting（否定的な引用）の数が閾値を超えた場合、または supporting が著しく少ない場合、「要検証」フラグを付与するロジックを実装する。
TDD / テスト内容:
Data Driven Test: 肯定的な評価が確立している論文（例: DNA構造）と、後に撤回されたり議論を呼んだ論文（例: 常温核融合関連）のDOIをテストケースとして用意し、ツールがそれぞれ適切な「信頼性スコア」または「警告」を返すか検証する。
ブランチ名: feature/tool-scite-validation

E2B Code Interpreterの実装

目的: LLMが苦手とする正確な計算やデータ可視化を、安全なサンドボックス環境で行う。
実装タスク:
src/tools/code_execution.py の作成。
e2b_code_interpreter SDKの統合。
execute_python(code: str, context_files: list) ツールの実装。
必要なデータ（CSV等）をサンドボックスへアップロード。
エージェントが生成したPythonコードを実行。
標準出力（stdout/stderr）および生成された画像ファイル（PNG/PDF）を取得し、エージェントへのレスポンスとして整形する。
TDD / テスト内容:
Sandbox Isolation Test: 単純な計算（print(1+1)）の実行テストに加え、外部ネットワークへの不正なアクセスや、無限ループするコードを与えた際に、タイムアウトや制限が正しく機能するかを確認する。
ブランチ名: feature/tool-e2b-sandbox

Phase 3: エージェントノードの実装（The Brains）

ツールを利用して自律的に思考・行動するエージェントロジックを実装する。各エージェントはLangGraphの「ノード」として機能し、Stateを受け取ってStateを返す関数となる。

Research Agent（STORM型探索ロジック）の実装

目的: 単一のクエリではなく、多角的な視点からリサーチを行うSTORMのコアロジックを実装する。
実装タスク:
src/agents/researcher.py の作成。
Perspective Generation: ユーザーのトピックに対し、「経済的視点」「技術的課題」「歴史的背景」など、調査すべき複数の切り口（Perspectives）をLLMに生成させるプロンプトの実装。
Iterative Search: 各視点に基づき、Semantic Scholarツールを用いて検索を実行し、得られたアブストラクトを要約してStateの documents に追加するループ処理。
Conversation Simulation: 仮想的な「専門家」と「インタビュアー」の対話をシミュレートし、深掘りすべき質問を生成するSTORM特有の機能の実装。
TDD / テスト内容:
Prompt Logic Test: トピックを入力した際、LLMが重複のない多様な視点（例: 3つ以上）を生成するか確認する。
State Update Test: 検索実行後、State内のドキュメントリストが増加しており、かつ各ドキュメントに「どの視点に基づいた検索結果か」というメタデータが付与されているか検証する。
ブランチ名: feature/agent-researcher-storm

Validator Agent（新規性・信頼性評価）の実装

目的: 収集された情報の質を担保する。Sciteツールを活用し、引用分析に基づくフィルタリングを行う。
実装タスク:
src/agents/validator.py の作成。
Research Agentが収集した候補論文リストに対し、Sciteツールを一括（または並列）実行する。
Novelty Check: ユーザーの主張や仮説が、既存の論文ですでに否定されていないか、あるいは既知の事実ではないかを判定するプロンプトエンジニアリング。
信頼性の低いソース（撤回論文や否定引用多数）を除外リストに移動し、Writerエージェントが使用しないようにマークする処理。
TDD / テスト内容:
Filtering Logic Test: 混合リスト（信頼できる論文 + 疑わしい論文）を入力とし、エージェントの処理後に「疑わしい論文」が適切にフラグ付けされているかを確認する。
ブランチ名: feature/agent-validator

Writer Agent（ドラフト作成と引用付与）の実装

目的: 検証済み情報に基づき、構造化されたレポートを執筆する。
実装タスク:
src/agents/writer.py の作成。
Outline Generation: 収集された情報に基づき、レポートの目次（構成案）を作成するステップ。
Section Writing: 各セクションを執筆する際、documents Stateにある論文ID（例: ``）を明示的に参照することを強制するシステムプロンプト。
Revision Loop: 生成されたテキストが長すぎる場合や、引用が不足している場合に、自己修正を行うループ処理。
TDD / テスト内容:
Citation Compliance Test: 生成されたテキストを正規表現でスキャンし、段落ごとに少なくとも1つの引用マーカーが含まれているかを検証する。引用がない段落が生成された場合、テストは失敗とする。
ブランチ名: feature/agent-writer

Phase 4: オーケストレーションとグラフ構築（The Nervous System）


Supervisor Router（構造化出力）の実装

目的: 状況に応じて適切なエージェントを呼び出す、システムの「司令塔」を実装する。
実装タスク:
src/graph/supervisor.py の作成。
Routing Schema: Pydanticを用いて、Supervisorの決定を構造化データとして定義する。
Python
class RouteResponse(BaseModel):
    next_agent: Literal
    reasoning: str = Field(description="Why this agent was chosen")


Decision Logic: 現在のState（調査の進捗度、情報の充足度）をプロンプトに含め、with_structured_output メソッドを用いてLLMに次のアクションを決定させる。
TDD / テスト内容:
Scenario Based Routing Test:
ケースA: 「情報がまだ何もない」状態 → 期待値: Researcher
ケースB: 「ドラフトはあるが検証されていない」状態 → 期待値: Validator
ケースC: 「ドラフト完成済み」状態 → 期待値: FINISH
これらのシナリオをシミュレートし、Routerが正しい判断を下すか検証する。
ブランチ名: feature/graph-supervisor-router

LangGraphの構築とコンパイル

目的: ノードとエッジを結合し、実行可能なアプリケーションとしてグラフを構築する。
実装タスク:
src/graph/builder.py の作成。
StateGraph インスタンスの作成。
各ノード（Supervisor, Researcher, Validator, Writer, Analyst）の登録。
Conditional Edges: Supervisorノードからの出力を分岐条件として、各ワーカーノードへ接続するエッジを定義する。
Checkpointing: SqliteSaver 等を用いて、グラフの実行状態を永続化する設定を行う（これにより、途中で停止しても再開可能にする）。
TDD / テスト内容:
Graph Integrity Test: コンパイルされたグラフオブジェクトを検査し、孤立したノード（到達不能なノード）や、出口のない無限ループ構造が存在しないかを確認する静的検査テスト。
End-to-End Smoke Test: モックされたツールを使用し、スタートから終了（FINISH）までエラーなく遷移することを確認する実行テスト。
ブランチ名: feature/construct-main-graph

Phase 5: インターフェースと品質保証（Delivery）


CLIおよびストリーミングUIの実装

目的: ユーザーがシステムを操作し、エージェントの思考過程を可視化するためのインターフェース。
実装タスク:
src/main.py（CLIエントリーポイント）の実装。argparse を用いてトピックやオプションを受け取る。
src/app.py（StreamlitまたはFastAPI）。LangChainの astream_events APIを利用し、エージェントが現在何をしているか（「論文検索中...」「執筆中...」）をリアルタイムで表示する。
最終成果物をMarkdownファイルとして保存する機能。
TDD / テスト内容:
Output File Test: アプリケーション実行後、指定されたパスにレポートファイルが生成され、かつ空ファイルでないことを確認する。
ブランチ名: feature/user-interface

総合テストと評価（E2E & Eval）

目的: システム全体の振る舞いを検証する。
実装タスク:
統合テストスイートの作成。
LangSmithを用いた評価セットの定義（入力トピックと理想的な回答のペア）。
幻覚（Hallucination）の有無や、引用の正確性を自動評価するスクリプトの作成。
TDD / テスト内容:
Performance Test: 典型的なリクエスト（例: 「量子コンピュータの最新動向」）に対し、タイムアウトせずに完了するか、APIコール数が予算（レート制限）内に収まっているかを計測する。
ブランチ名: chore/e2e-testing-and-eval

4. リスク管理と技術的課題への対策

本システムの開発において想定されるリスクと、それに対する技術的な緩和策を以下に定義する。

4.1 APIレート制限とコスト管理

課題: Semantic ScholarやSciteのAPIは、短時間に大量のリクエストを送るとブロックされる可能性がある。また、LLMのトークンコストも無視できない。
対策:
キャッシュ層の導入: 一度取得した論文データや引用情報は、ローカルデータベース（SQLite）またはRedisにキャッシュし、同一クエリに対する再リクエストを防ぐ。
バッチ処理: Scite APIなどは複数のDOIを一度にリクエストできるエンドポイントを持っている場合があるため、可能な限りバッチリクエストを実装する。

4.2 幻覚（Hallucination）のリスク

課題: LLMが存在しない論文を捏造したり、引用文脈を誤って解釈する可能性がある。
対策:
Groundingの強制: Writerエージェントには、「State内の documents リストに存在する論文ID以外は引用してはならない」という制約を課す。
Sciteによる二重チェック: 最終ドラフトに含まれるすべての引用に対し、最後に再度Scite APIで存在確認を行う工程をValidatorに追加する。

4.3 無限ループとエージェントの暴走

課題: Supervisorが「情報不足」と判断し続け、ResearcherとSupervisorの間で無限ループが発生する恐れがある。
対策:
Recursion Limit: LangGraphの recursion_limit 設定を利用し、最大ステップ数を制限する。
Budgeting: SupervisorのStateに「検索回数カウンター」を持たせ、規定回数（例: 5回）を超えたら強制的に執筆フェーズへ移行するロジックを組み込む。

5. 結論

本実装計画は、LangGraphの強力なオーケストレーション能力と、Semantic ScholarおよびScite.aiという信頼性の高い学術データソースを融合させることで、次世代の研究支援ツールを実現するための青写真である。
TDDの義務化とPRベースの厳格なワークフローは、開発初期の速度を若干低下させるかもしれないが、システムの複雑性が増すにつれて、その真価を発揮する。バグの早期発見、仕様の明確化、そして何より「動くことが保証されたコード」の積み重ねが、最終的なプロジェクトの成功を約束するものである。
開発チームは、直ちに chore/init-project-structure ブランチを作成し、本計画に基づいた実装を開始されたい。
