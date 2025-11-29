
自律型研究エージェントアーキテクチャ機能仕様書：博士級学位論文の自動生成システム (ARAS)


1. 序論と設計哲学


1.1 背景と目的

現代の学術研究において、知識の爆発的な増加は研究者にとって重大な認知負荷となっている。特に博士課程レベルの研究においては、数千に及ぶ先行研究を網羅的に調査し、未踏の研究領域（Research Gap）を特定し、新規性のある仮説を立案し、それを論理的かつ厳密な長編の物語として記述することが求められる。従来の生成AI（Large Language Models: LLM）は、短い要約や断片的な文章作成においては有用性を示してきたが、数万語に及ぶ一貫した論理性と、厳密な出典管理が求められる「博士論文」の執筆においては、コンテキストウィンドウの制限や幻覚（ハルシネーション）の問題により、実用レベルには達していなかった1。
本機能仕様書は、これらの課題を克服し、ユーザーから与えられた「研究テーマ」または「シード論文（既存の論文）」を入力として、Deep Research（深層調査）から執筆、査読、そしてLaTeX形式での原稿出力までを自律的に遂行する**Autonomous Research Agent System (ARAS)**のアーキテクチャを定義するものである。本システムは、単なるテキスト生成ツールではなく、研究プロセスそのものをシミュレートする「エージェント型研究知能（Agentic Research Intelligence: ARI）」として設計される3。

1.2 コアフィロソフィー：エージェント型研究知能 (ARI)

本システムの設計哲学は、人間が論文を書く際の認知的プロセスを、専門化されたAIエージェントの集合体として模倣することにある。人間の研究者が「調査」「構想」「執筆」「推敲」という異なる脳内モードを切り替えるように、本システムもまた、LangGraphを用いた階層的な状態管理によって、異なる役割を持つエージェント（Supervisor-Workerパターン）をオーケストレーションする5。
特に重視するのは以下の2点である：
長期的整合性（Long-term Coherence）の維持：各章を独立して生成しつつも、論文全体としての主張のブレを防ぐため、MemGPTに触発された階層的メモリ管理システムを導入する。これにより、第1章で定義した用語や仮説が、第5章の考察においても矛盾なく参照されることを保証する7。
学術的厳密性（Academic Rigor）の担保：LLMの内部知識に依存せず、常に外部の信頼できる学術データベース（arXiv, Semantic Scholar）を参照し、Scite.ai等の検証ツールを用いて引用の正確性と文脈的適切性を担保する「Retrieval-Augmented Generation (RAG)」を徹底する9。

2. システムアーキテクチャとオーケストレーション戦略

博士論文のような大規模ドキュメントの生成には、単一のエージェントではなく、役割分担されたマルチエージェントシステムが不可欠である。本章では、その全体像と制御フローを定義する。

2.1 LangGraphによる階層的制御フロー

本システムは、循環的かつステートフルなワークフローを構築可能なLangGraphフレームワークを採用する。これにより、直線的な処理（DAG）だけでなく、品質基準を満たすまで執筆と修正を繰り返す「反復ループ」や、必要に応じて前のフェーズ（例：執筆中に調査不足が判明した場合の再調査）に戻る「タイムトラベル」が可能となる5。

2.1.1 Supervisor-Worker パターン

システムの中核には、**Chief Editor Agent（総括編集者）**が配置される。このSupervisorエージェントは、直接的なタスク実行は行わず、論文全体の「Global State（全体状態）」を管理し、下位の専門チーム（Sub-teams）にタスクを委譲する権限を持つ11。

階層レベル
エージェント名
役割と責任
Level 0 (Root)
Chief Editor (Supervisor)
プロジェクト全体の進捗管理、フェーズ移行判定（調査→構成→執筆→査読）、品質ゲートの最終承認。ユーザーとの対話インターフェース。
Level 1 (Team Leads)
Research Lead
調査計画の策定、検索クエリの最適化、情報の網羅性評価。情報の「広さ」と「深さ」を管理する。


Planning Lead
論文構成（目次）の策定、新規性（Novelty）の評価、論理展開の設計。


Drafting Lead
各章の執筆管理、文体（Tone）の統一、コンテキストの注入。章ごとのWriterエージェントを監督。


Review Lead
査読プロセスの管理、引用検証、幻覚検出、倫理チェック。
Level 2 (Workers)
Reference Hunter
API（Tavily, Semantic Scholar）を用いた文献収集とフィルタリング。


Code Executor
Pythonサンドボックス内でのデータ分析、図表作成、コード検証13。


Novelty Checker
提案されたアイデアと既存文献の類似性を判定し、新規性をスコアリングする14。


Scite Verifier
引用の撤回状況や支持/反証の文脈を確認する9。


2.1.2 ステートスキーマと永続化

長時間の実行に耐えうるよう、システムの状態はリレーショナルデータベース（PostgreSQL等）に永続化されるチェックポイントとして管理される。この「Thesis State（論文状態）」オブジェクトは、全エージェントが共有する唯一の真実（Single Source of Truth: SSOT）として機能する。
Thesis Stateの主要構成要素:
Manuscript Object: 論文の階層構造（タイトル、アブストラクト、章、節、本文）を保持するJSONツリー。
Knowledge Graph: 収集された文献データ、それらの引用関係、および抽出された「Facts（事実）」のネットワーク。
Global Context Bank: 論文全体で統一すべき定義、略語、中心仮説、文体ガイドラインを格納した共有メモリ。
Execution Trace: 各エージェントのアクション履歴とエラーログ（デバッグおよび再現性確保のため）。

2.2 外部ツール連携とサンドボックス環境

「博士レベル」のアウトプットを保証するためには、LLMの幻覚を防ぎ、事実に基づいた処理を行う必要がある。そのために、以下の外部環境との連携を仕様に含める。
Dockerized Sandbox: データ分析やグラフ描画、アルゴリズムの検証を行う際、LLMが生成したPythonコードを安全に実行するための隔離環境。これは「AI Scientist」等の先行研究でも採用されている標準的な構成である13。コードの実行結果（標準出力、生成された画像ファイル）は、再びコンテキストとしてエージェントにフィードバックされる。
Standardized API Interfaces: Semantic Scholar, arXiv, Scite.ai等の学術サービスとは、OpenAPI仕様に基づいた厳格なインターフェースで接続し、構造化データ（JSON）として情報を取得する。これにより、不明瞭なテキスト解析による情報の劣化を防ぐ16。

3. フェーズ1：Deep Researchと知識獲得 (Knowledge Acquisition)

優れた論文は、徹底的な先行研究調査（Literature Review）の上に成り立つ。本フェーズでは、ユーザーの入力（テーマやシード論文）を出発点とし、関連する知識空間を網羅的かつ探索的にスキャンするプロセスを定義する。

3.1 入力モードによる分岐処理

本システムは、ユーザーからの入力タイプに応じて初期動作を最適化する。
テーマ入力モード（Theme-based）:
ユーザーが「自律エージェントによる科学的発見」のような抽象的なテーマを与えた場合。
動作: Research Leadエージェントが、そのテーマを構成する主要なキーワード、研究コミュニティ、歴史的背景を特定するための「広範な探索（Breadth-First Exploration）」から開始する12。
シード論文入力モード（Paper-based）:
ユーザーが特定の既存論文（PDFまたはURL）を与え、それを発展させたい場合。
動作: 入力された論文を基準点（Anchor）とし、その論文が引用している過去の研究（Roots）と、その論文を引用している新しい研究（Leaves）を追跡する「引用グラフ探索（Citation Graph Traversal）」を行う。これにより、その論文が位置する研究の文脈を正確に特定する17。

3.2 再帰的研究ツリー (Recursive Research Tree) 手法

従来の単純な検索（クエリを投げて上位10件を要約する）では、博士論文に必要な深さには到達できない。本システムでは、GPT-Researcher等で提唱されている「再帰的研究ツリー」手法を採用し、情報の解像度を段階的に高めていく12。

3.2.1 幅優先探索によるランドスケープ把握

まず、Research Leadは対象トピックを複数のサブトピック（側面）に分解する。例えば「自律エージェント」というテーマであれば、「アーキテクチャ」「記憶管理」「ツール使用」「評価指標」といった観点である。
クエリ生成: 各サブトピックに対して、検索エンジン（Tavily等）向けの最適化されたクエリを生成する。
フィルタリング: 検索結果から、非学術的なソース（ブログ、ニュースサイト等）を除外し、arXiv、大学ドメイン(.edu)、主要なジャーナルサイトのみを候補として残す12。

3.2.2 深さ優先探索による引用追跡

次に、特定された重要文献に対して深掘りを行う。ここで重要なのは、Semantic Scholar APIを活用した「Influential Citation（影響力の高い引用）」の特定である。
Influential Citation Filtering: 単に引用されているだけでなく、その論文の手法や理論が後続の研究に強く影響を与えている場合（Semantic Scholarが提供するinfluentialCitationCountや引用文脈の分類に基づく）、そのリンクを辿ってさらに調査を行う17。これにより、表面的な関連性ではなく、議論の本質的な系譜を抽出する。

3.3 文献の取り込みとベクトル化 (RAG Pipeline)

収集された文献（PDF, HTML）は、執筆時に参照可能な形式に変換する必要がある。
Parsing: DoclingやPyPDFLoaderを用いてPDFを解析し、テキストだけでなく、セクション構造、図表のキャプション、参考文献リストを構造化データとして抽出する19。
Parent-Child Chunking: 文脈を保持するため、単純な固定長チャンクではなく、小さなチャンク（検索用）とそれが属する大きな親チャンク（LLMへの入力用）を紐付ける「Parent-Child」方式を採用する21。
Semantic Embedding: 学術文章に特化した埋め込みモデル（例：specter2やallenai-specter）を使用してベクトル化し、MilvusやChromaDB等のVector Storeに格納する19。この際、メタデータとして「発行年」「被引用数」「著者」を付与し、後の検索で「2020年以降の論文に限定」といったフィルタリングを可能にする23。

4. フェーズ2：構造計画と新規性評価 (Structural Planning)

十分な知識が集まった段階で、論文の骨格（アウトライン）を設計する。博士論文において最も重要なのは「新規性（Novelty）」の主張であるため、このフェーズでは単なる章立てだけでなく、独自性の検証も行う。

4.1 STORM手法による多角的視点の導入

スタンフォード大学の研究に基づく**STORM (Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking)**手法を導入し、一面的なバイアスを排除した包括的なアウトラインを作成する24。
Perspective Discovery (視点の発見): 収集した文献を分析し、トピックを取り巻く異なる立場や競合する理論（例：「計算効率重視派」対「精度重視派」）を特定する。
Simulated Conversation (模擬対話): 「Wiki編集者」と「トピック専門家」というペルソナを持つエージェント同士に対話をさせ、お互いに質問を投げかけることで、トピックの深掘りを行う。この対話ログから、網羅すべき論点を抽出する24。
Outline Synthesis (構成の統合): 対話の結果に基づき、標準的な博士論文の構成（序論、文献レビュー、方法論、実験、結果、考察、結論）にマッピングし、3階層（章・節・項）の詳細な目次（Table of Contents: TOC）を生成する。

4.2 アイデア新規性チェッカー (Idea Novelty Checker)

生成された論文の方向性が、既存研究の焼き直しにならないよう、「新規性評価フレームワーク」を組み込む14。

4.2.1 ファセット分解と検索

Planning Leadが提案する「中心仮説（Central Hypothesis）」を、以下の4つのファセット（側面）に分解する14：
目的 (Purpose): 何を解決しようとしているか。
メカニズム (Mechanism): どのような手法を用いるか。
評価 (Evaluation): どうやって有効性を示すか。
応用 (Application): どのドメインに適用するか。
このファセットに基づいてVector Storeを再検索し、類似する既存論文を抽出する。

4.2.2 比較評価とピボット

LLMを用いて、提案仮説と既存論文を比較する。もし、4つのファセットすべてが既存の単一の論文と一致する場合、それは「新規性なし」と判定される。その場合、Planning Leadは仮説を修正（Pivot）するよう指示される（例：「手法は同じだが、評価指標を新しいものに変える」「別の応用分野に適用する」等）14。これにより、執筆開始前に論文の価値を保証する。

4.3 マスタープランの確定

フェーズ2の出力として、以下の情報を含む「Master Plan」オブジェクトが確定され、Supervisorによってロックされる。以降の執筆フェーズで、この範囲を逸脱する内容は原則として許容されない。

JSON


{
  "thesis_title": "大規模言語モデルを用いた自律的研究エージェントにおける階層的記憶管理",
  "central_hypothesis": "MemGPTを用いたコンテキスト管理は、従来の手法と比較して長編論文の整合性スコアを40%向上させる。",
  "novelty_justification": "LangGraphのSupervisorパターンとMemGPTを組み合わせた初の博士論文生成システムである点。",
  "table_of_contents": [
    {
      "chapter_id": 1,
      "title": "序論",
      "sections": [
        {"id": "1.1", "topic": "研究の背景", "assigned_sources": [1, 26]}
      ]
    }
  ]
}



5. フェーズ3：一貫性のある執筆とコンテキスト管理 (Iterative Drafting)

数万語に及ぶ執筆において最大の課題は、章をまたいだ内容の矛盾や、用語の揺らぎを防ぐことである。本システムでは、MemGPTの概念を応用した高度なコンテキスト管理によりこれを解決する。

5.1 仮想コンテキストOS (Virtual Context Operating System)

各Writerエージェントは、論文全体の全テキストを見ることはできない（トークン制限のため）。代わりに、OSのメモリ管理に似た3層のコンテキスト構造を提供する7。
メモリ階層
名称
内容と機能
Tier 1 (Main Context)
Active Workspace
現在執筆中のセクションのテキスト、直前のセクションの要約、および「Global Thesis Statement」。最も高速かつ頻繁にアクセスされる。
Tier 2 (Working Context)
Chapter Summaries
既に書き終えた他の章の「要約（Summaries）」。Writerが「第2章で述べたように」と参照する場合、この要約層を確認する。
Tier 3 (Archival Storage)
Vector Database
全文献の生データ、実験データの生ログ。Writerが必要に応じて「Recall（検索）」関数を呼び出し、特定の情報をTier 1にロードする。


5.2 逐次的執筆と自己修正ループ

執筆は、目次に沿って章ごとにシーケンシャルに行われるが、各セクション内で以下のマイクロループが回る。
Prompt Construction: Drafting Leadは、そのセクションで書くべき内容（Goal）、使用すべき文献（Sources）、および文体ガイドライン（Style）を含むプロンプトを構築する。
Drafting: Writerエージェントがテキストを生成する。この際、引用は``のようなプレースホルダー形式で埋め込むことが強制される。
Cross-Reference Check: 生成されたテキスト内で「前述したように」等の表現が使われた場合、CritiqueエージェントがTier 2メモリ（過去の要約）を参照し、本当に前述されているか、矛盾していないかを検証する27。
Style Enforcement: 学術論文特有の言い回し（「我々は」の不使用、受動態の適切な使用等）が守られているかをチェックし、違反があれば即座に書き直しを命じる28。

5.3 テクニカルコンテンツの生成

CSや理工系の論文では、数式やコード、図表が必須である。
LaTeX数式: 数式はすべてLaTeX形式（$E=mc^2$）で出力させる。
コードと図表: 「第3章の実験結果をグラフにして」という指示に対し、Code ExecutorエージェントがPython（Matplotlib/Seaborn）を実行して画像を生成し、その画像パスとキャプションをLaTeX原稿に挿入する13。これにより、捏造ではない実際のデータに基づいた図表が保証される。

6. フェーズ4：学術的厳密性・検証・査読 (Verification & Review)

「博士レベル」と見なされるためには、幻覚（Hallucination）が許されず、引用の一つ一つが正確でなければならない。本フェーズは、自動化された「厳しい査読者」として機能する。

6.1 幻覚検出と修正 (Hallucination Detection)

LLMがもっともらしく嘘をつくのを防ぐため、複数の検出レイヤーを設ける10。

6.1.1 ログ確率と自己無撞着性チェック

Seq-Logprob Check: 生成されたテキスト、特に固有名詞や数値、引用部分について、トークン生成時の対数確率（Log Probability）を監視する。確率が低い（自信がない）箇所は、潜在的な幻覚としてフラグを立てる10。
ConFactCheck: 生成された内容に基づいて、逆に質問（Probe Questions）を生成し、同じLLMに答えさせる。本文と回答に矛盾があれば、幻覚の可能性が高いと判断し、再調査をトリガーする30。

6.1.2 引用検証システム (The Scite Layer)

最も重要な機能の一つが、Scite.ai API等を用いた引用の健全性チェックである9。Reviewエージェントは、ドラフト内のすべての引用に対して以下を確認する：
実在確認: DOIが存在し、メタデータ（著者、年、タイトル）が正しいか。
撤回チェック: 引用した論文が撤回（Retracted）されていないか。撤回論文の引用は致命的なミスとなるため、発見時は警告と共に代替論文の提案を求める32。
引用文脈の整合性 (Citation Context): 論文内で「AはBであると主張した」と引用している場合、実際の被引用論文の文脈（SciteのSmart Citations）と照らし合わせ、その主張が「的支持（Supporting）」なのか「反証（Contrasting）」なのかを確認する。誤った文脈での引用（例：批判されている論文を肯定的に引用する）を防ぐ。

6.2 自動査読プロセス (Automated Peer Review)

最終稿に対し、Review Leadエージェントが、実際の大学で使用される「博士論文評価ルーブリック（Rubric）」に基づいて採点を行う33。
評価項目: 研究課題の明確さ、文献レビューの網羅性、方法論の妥当性、結果の解釈、新規性の主張。
フィードバック: 各項目について5段階評価と具体的な修正コメント（例：「第3章の実験設定の記述が不十分で再現性がない」）を生成する。このスコアが規定値（例：4.0/5.0）に達しない場合、SupervisorはDraftingフェーズへの差し戻し（Revision）を指示する。

6.3 最終コンパイルと出力

全てのチェックを通過した後、最終成果物を生成する。
BibTeX生成: 確定した引用リストに基づき、正確なBibTeXファイルを生成する35。
LaTeXコンパイル: 大学指定のテンプレート（クラスファイル）にテキストを流し込み、PDFをビルドする。図表の参照番号（Fig. 1）や式番号の整合性もここで最終確定される。

7. 実装仕様と技術スタック

本システムを構築するための推奨技術スタックとデータモデルを定義する。

7.1 コアフレームワーク

Orchestration: LangGraph (Python)。循環的なグラフ構造、状態の永続化、人間参加型（Human-in-the-loop）の承認フローを実装するために必須である11。
LLM Interface: LangChain。モデルの抽象化を行い、タスクに応じてOpenAI (GPT-4o) や Anthropic (Claude 3.5 Sonnet) を切り替えるために使用。複雑な推論（構成、査読）には「o1」や「Claude 3.5 Sonnet」、単純なタスクには軽量モデルを使い分ける37。
Prompt Optimization: DSPy。プロンプトの手動調整ではなく、最適化アルゴリズムを用いて、タスク（例：引用意図分類）ごとのプロンプト精度を向上させる38。

7.2 データインフラストラクチャ

Vector Database: Milvus または ChromaDB。大量の論文チャンクを高速に検索するために使用。メタデータフィルタリング機能が必須19。
Relational Database: PostgreSQL。論文の構造データ（目次、各節の進捗、修正履歴）およびLangGraphのチェックポイントデータを保存する。

7.3 データモデル定義 (State Schema)

LangGraphで管理される状態オブジェクトの型定義（Python/Pydantic形式）は以下の通りである。

Python


from typing import TypedDict, List, Dict, Optional, Annotated
import operator

class Reference(TypedDict):
    id: str  # S2 Paper ID or DOI
    title: str
    authors: List[str]
    year: int
    abstract: str
    citation_intent: str # 'Support', 'Contrast', 'Background'
    is_influential: bool

class Section(TypedDict):
    id: str # e.g., "1.2.1"
    title: str
    content: str # Markdown text
    summary: str # For working memory
    citations: List[str]
    status: str # 'Planned', 'Drafted', 'InReview', 'Approved'
    feedback: List[str] # Review comments

class ThesisState(TypedDict):
    # Global Inputs
    topic: str
    target_word_count: int
    style_guide: Dict[str, str]
    
    # Research Artifacts
    knowledge_graph: List # 全収集文献
    perspectives: List[str] # STORMで得られた視点
    
    # Structure & Content
    thesis_title: str
    hypothesis: str
    outline: List # フラット化されたセクションリスト
    
    # Execution State
    current_section_index: int
    # 完了したセクションの要約リスト（コンテキストウィンドウ節約用）
    chapter_summaries: Annotated, operator.ior]
    
    # Quality Gates
    novelty_score: float
    hallucination_flags: List[str]
    
    # Human Feedback
    user_approval_status: str



7.4 外部API仕様

Semantic Scholar API (S2AG): 引用グラフ探索用。influentialCitationCountフィールドを活用39。
Tavily Search API: エージェント用に最適化されたWeb検索。
Scite.ai API: 引用の質的検証用（Smart Citations）。
arXiv API: 最新のプレプリント取得用。

8. 詳細ワークフローロジック

以下は、システムのメインループとなる自律スクリプトの疑似コードである。

Python


def main_workflow(topic: str):
    # 初期化
    state = initialize_state(topic)
    
    # --- Phase 1: Deep Research ---
    # SupervisorがResearch Leadに委譲
    research_plan = Supervisor.delegate("Research Lead", state.topic)
    
    # 再帰的調査ループ
    queries = ResearchLead.generate_queries(research_plan)
    raw_docs = ParallelExecution(Tavily.search(q) for q in queries)
    # 学術フィルタリングとグラフ拡張
    academic_docs = filter_academic(raw_docs)
    graph_docs = SemanticScholar.expand_citations(academic_docs) 
    state.vector_store.ingest(graph_docs)
    
    # --- Phase 2: Planning ---
    # STORMモジュールによる多角的視点の獲得
    perspectives = STORM_Module.discover_perspectives(state.vector_store)
    
    # 目次の生成と新規性チェック
    outline_candidate = PlanningLead.generate_toc(perspectives)
    novelty_report = NoveltyChecker.evaluate(outline_candidate.hypothesis, state.vector_store)
    
    if novelty_report.score < THRESHOLD:
        # 新規性不足ならテーマをピボットしてPhase 1へ戻る（Human-in-the-loop推奨）
        state.topic = refine_topic(novelty_report.feedback)
        return trigger_research_phase(state)
        
    state.outline = outline_candidate
    Supervisor.approve("Plan Approved")

    # --- Phase 3: Drafting (Iterative) ---
    for section in state.outline:
        # MemGPTロジック: コンテキストの構築
        # グローバルコンテキスト + 直前のセクションの要約 + 関連文献(RAG)
        context = MemGPT.construct_context(
            global_ctx=state.hypothesis,
            prev_summary=state.chapter_summaries.get(prev_section_id),
            rag_docs=state.vector_store.search(section.topic)
        )
        
        # 執筆実行
        draft = WriterAgent.write(section.prompt, context)
        
        # --- Phase 4: Verification Loop ---
        while True:
            # 査読エージェントによるチェック
            critique = ReviewAgent.critique(draft)
            scite_check = SciteVerifier.check(draft.citations)
            
            if critique.passed and scite_check.passed:
                break # 承認
            else:
                # 修正指示とともにWriterへ戻す
                draft = WriterAgent.revise(draft, critique, scite_check)
        
        # セクション完了処理
        state.manuscript.append(draft)
        # ワーキングメモリ（要約）の更新
        state.chapter_summaries[section.id] = summarize(draft)

    # --- Final Compilation ---
    full_manuscript = compile_latex(state.manuscript)
    return full_manuscript



9. 結論と展望

本仕様書で定義されたアーキテクチャは、既存のLLMツールの限界であった「一貫性」「幻覚」「引用の不正確さ」を、LangGraphによる構造化された制御、MemGPTによる記憶管理、そしてScite.ai等による外部検証を組み合わせることで体系的に解決するものである。
特に、STORM手法による多角的な視点の導入と、Idea Novelty Checkerによる執筆前の価値検証プロセスは、単に「長い文章を書く」だけでなく、「学術的価値のある論文を書く」という博士課程レベルの要求に応えるための重要な差別化要因である。
今後の展望としては、論文執筆だけでなく、提案された実験自体をシミュレーション環境やロボット実験室（Self-Driving Labs）で実行し、その結果をリアルタイムで論文に反映させる「実験と執筆の完全ループ化」が挙げられる3。本システムは、人間の研究者を単純作業から解放し、より高次の概念設計や倫理的判断に集中させるための強力なパートナー（Copilot）となるだろう。

10. コンポーネント詳細仕様 (Deep Dive)

本章では、開発者が実際にコードを記述する際に必要となる、各サブシステムの詳細な挙動とロジックについて解説する。

10.1 Perception System: 探索アルゴリズムの詳細

「目」となるPerception Systemは、単にキーワードマッチングを行うだけでなく、文献の「権威性」と「文脈」を理解する必要がある。

10.1.1 複合スコアリングアルゴリズム

検索された数千の文献から、実際に読むべき（RAGのコンテキストに入れるべき）数十件を選定するために、以下の重み付けスコアを使用する。

$$Score(p) = \alpha \cdot Sim(q, p_{abs}) + \beta \cdot \log(C_{inf}) + \gamma \cdot I(Year)$$
ここで：
$Sim(q, p_{abs})$: ユーザークエリと論文アブストラクトのベクトル類似度（Specter2使用）。意味的な関連性を担保する。
$C_{inf}$: Semantic ScholarのinfluentialCitationCount。単純な被引用数ではなく、他論文に強い影響を与えた「本質的な価値」を評価する39。
$I(Year)$: 経年減衰関数。分野にもよるが、CS系であれば直近3〜5年を高く評価するよう調整する。
$\alpha, \beta, \gamma$: 調整パラメータ（例：State-of-the-Art調査なら $\gamma$ を高く、基礎理論調査なら $\beta$ を高く設定）。

10.2 Reasoning System: 推論と論理構築

「脳」となるReasoning Systemは、論文の論理的整合性を保つ責任を持つ。

10.2.1 Tree-of-Thought (ToT) による考察の深化

特に「考察（Discussion）」章の執筆において、単一の解釈を出力するのではなく、ToT推論を用いる1。
Branching: 実験結果に対して、3つの異なる解釈仮説（例：「手法の優位性によるもの」「データの偏りによる可能性」「ベースラインの弱さ」）を生成する。
Validation: 各仮説に対し、Vector Store内の文献を証拠として突き合わせる。証拠がない、または反証が存在する仮説は枝刈り（Pruning）される。
Synthesis: 生き残った解釈の中で最も論理的に強固なものを採用し、考察の文章を構築する。

10.2.2 新規性のスペクトル評価

新規性は 0 か 1 かではない。システムは以下のスペクトルで判定を行う41。
Combinatorial Novelty (組み合わせ的新規性): 分野Xの手法Aを、分野Yの問題Bに適用する。キーワード共起ネットワークにおいて、XとYの間にエッジが少ない場合に検出される。
Incremental Novelty (漸進的新規性): 既存手法の性能をN%改善する。これは比較実験の結果記述に依存する。
Disruptive Novelty (破壊的新規性): 通説を覆す。これには非常に強い証拠（高い信頼度の実験データと多数の支持文献）が必要となるため、システムは「SciteのContrasting引用」を慎重に分析する。

10.3 Execution System: 執筆と編集の現場

「手」となるExecution Systemは、実際にLaTeXコードや図表を生成する。

10.3.1 引用オブジェクト管理

テキスト生成中、引用は文字列ではなく「オブジェクト」として扱われる。
内部表現: テキスト中には `` のようなマーカーのみを置く。
Latex解決: 最終コンパイル時に、このIDを \cite{Vaswani2017} に変換し、.bibファイルにエントリを自動生成する。
重複排除: 「Vaswani et al. 2017」と「Attention is All You Need」が同一であることをS2AG IDで識別し、参考文献リストの重複を防ぐ18。

10.4 倫理と安全性のガードレール

自律エージェントが暴走しないよう、以下の安全装置を組み込む。
剽窃チェック (Plagiarism Check): 生成されたパラグラフと、Vector Store内の原文とのCosine類似度が0.8を超える場合、剽窃とみなし、Paraphraserエージェントに書き直しを命じる28。
Dual-Use制限: 生物兵器やサイバー攻撃コードなど、危険な知識の生成を防ぐため、Supervisorに安全ガイドラインをハードコードし、危険なトピックが検出された場合はタスクを拒否する43。

11. 実装ガイド：ステップ・バイ・ステップ

開発者が本システムを実装するための具体的な手順を示す。

11.1 環境構築 (Environment Setup)

依存関係の衝突を防ぐため、Poetry または uv を用いた環境管理を推奨する。

Bash


# Core dependencies for Agent Logic
poetry add langchain langgraph langchain-openai pydantic
# Database drivers
poetry add chromadb pymilvus psycopg2-binary
# Scientific & PDF tools
poetry add arxiv semanticscholar docling pypdf
# Search & Web
poetry add tavily-python beautifulsoup4



11.2 State Graphの定義 (Graph Definition)

LangGraphの核心であるノードとエッジの定義例。

Python


from langgraph.graph import StateGraph, END

# グラフの初期化
workflow = StateGraph(ThesisState)

# ノードの登録
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("researcher", research_node)
workflow.add_node("planner", planning_node)
workflow.add_node("writer", writer_node)
workflow.add_node("reviewer", review_node)

# エッジ（遷移ルール）の定義
# Supervisorが次のステップを決定する
workflow.add_conditional_edges(
    "supervisor",
    decide_next_step,
    {
        "research": "researcher",
        "plan": "planner",
        "write": "writer",
        "review": "reviewer",
        "finish": END
    }
)

# 各ワーカーは終了後Supervisorに戻る
workflow.add_edge("researcher", "supervisor")
workflow.add_edge("planner", "supervisor")
workflow.add_edge("writer", "supervisor") # 実際はReviewerへ流す場合もある
workflow.add_edge("reviewer", "supervisor")

app = workflow.compile(checkpointer=postgres_saver)



11.3 エラーハンドリングとリトライ

長時間の自律動作ではAPIエラーが必至である。LangGraphの機能を用い、各ノードにリトライポリシーを設定する。
Rate Limit: Semantic Scholar API等のレート制限（HTTP 429）に対し、指数バックオフ（Exponential Backoff）を実装する。
Context Overflow: LLMがコンテキスト長を超過した場合（エラー発生時）、自動的にTier 2メモリ（要約）の圧縮度を上げて再試行するロジックを組み込む。
この仕様書に基づき実装を進めることで、単なるテキスト生成を超えた、真に「研究」を行う自律エージェントシステムが構築可能となる。
引用文献
Fundamentals of Building Autonomous LLM Agents This paper is based on a seminar technical report from the course Trends in Autonomous Agents: Advances in Architecture and Practice offered at TUM. - arXiv, 11月 29, 2025にアクセス、 https://arxiv.org/html/2510.09244v1
Autonomous Manuscript Creation - Emergent Mind, 11月 29, 2025にアクセス、 https://www.emergentmind.com/topics/autonomous-manuscript-creation
Evaluating Sakana's AI Scientist for Autonomous Research: Wishful Thinking or an Emerging Reality Towards 'Artificial Research Intelligence' (ARI)? - arXiv, 11月 29, 2025にアクセス、 https://arxiv.org/html/2502.14297v3
Evaluating Sakana's AI Scientist: Bold Claims, Mixed Results, and a Promising Future? - arXiv, 11月 29, 2025にアクセス、 https://arxiv.org/pdf/2502.14297
LangGraph - LangChain, 11月 29, 2025にアクセス、 https://www.langchain.com/langgraph
LangGraph Multi-Agent Systems: Production-Grade Orchestration - EffiFlow, 11月 29, 2025にアクセス、 https://jangwook.net/en/blog/en/langgraph-multi-agent
MemGPT with Real-life Example: Bridging the Gap Between AI and OS | DigitalOcean, 11月 29, 2025にアクセス、 https://www.digitalocean.com/community/tutorials/memgpt-llm-infinite-context-understanding
MemGPT: OS Inspired LLMs That Manage Their Own Memory - LanceDB, 11月 29, 2025にアクセス、 https://lancedb.com/blog/memgpt-os-inspired-llms-that-manage-their-own-memory-793d6eed417e/
Scite: AI for Research, 11月 29, 2025にアクセス、 https://scite.ai/
LLM Hallucination Detection and Mitigation: Best Techniques - Deepchecks, 11月 29, 2025にアクセス、 https://www.deepchecks.com/llm-hallucination-detection-and-mitigation-best-techniques/
Building Multi-Agent Systems with LangGraph-Supervisor - DEV Community, 11月 29, 2025にアクセス、 https://dev.to/sreeni5018/building-multi-agent-systems-with-langgraph-supervisor-138i
Blog | GPT Researcher, 11月 29, 2025にアクセス、 https://docs.gptr.dev/blog
How AI Researcher Automates Scientific Research from Design to Paper Writing - 高效码农, 11月 29, 2025にアクセス、 https://www.xugj520.cn/en/archives/ai-researcher-automated-scientific-research.html
Literature-Grounded Novelty Assessment of ... - ACL Anthology, 11月 29, 2025にアクセス、 https://aclanthology.org/2025.sdp-1.9.pdf
How AI Science Agents Transform Research Workflows - Docker, 11月 29, 2025にアクセス、 https://www.docker.com/blog/ai-science-agents-research-workflows/
GPT Researcher - Tavily Docs, 11月 29, 2025にアクセス、 https://docs.tavily.com/examples/open-sources/gpt-researcher
Mastering Research with the Semantic Scholar API: An Insider's Guide - Skywork.ai, 11月 29, 2025にアクセス、 https://skywork.ai/skypage/en/Mastering-Research-with-the-Semantic-Scholar-API-An-Insider's-Guide/1973804064216641536
The Semantic Scholar Open Data Platform - arXiv, 11月 29, 2025にアクセス、 https://arxiv.org/html/2301.10140v2
Implement RAG with LangChain to Explore IBM Quantum Research, 11月 29, 2025にアクセス、 https://www.ibm.com/think/tutorials/rag-langchain-explore-quantum-research-granite
Running the STORM AI Research System with Your Local Documents - Medium, 11月 29, 2025にアクセス、 https://medium.com/data-science/running-the-storm-ai-research-system-with-your-local-documents-e413ea2ae064
A Practical Guide to RAG with Haystack and LangChain - DigitalOcean, 11月 29, 2025にアクセス、 https://www.digitalocean.com/community/tutorials/production-ready-rag-pipelines-haystack-langchain
Hands on LangChain: RAG - Medium, 11月 29, 2025にアクセス、 https://medium.com/@ai-data-drive/hands-on-langchain-rag-dd639d0576f6
LitLLMs, LLMs for Literature Review: Are we there yet? - arXiv, 11月 29, 2025にアクセス、 https://arxiv.org/html/2412.15249v2
stanford-oval/storm: An LLM-powered knowledge curation ... - GitHub, 11月 29, 2025にアクセス、 https://github.com/stanford-oval/storm
teddynote-lab/STORM-Research-Assistant: 🌪️ AI research assistant that generates Wikipedia-quality articles through multi-perspective analysis. Based on Stanford's STORM methodology. - GitHub, 11月 29, 2025にアクセス、 https://github.com/teddynote-lab/STORM-Research-Assistant
[Literature Review] Can LLMs Identify Gaps and Misconceptions in Students' Code Explanations? - Moonlight, 11月 29, 2025にアクセス、 https://www.themoonlight.io/en/review/can-llms-identify-gaps-and-misconceptions-in-students-code-explanations
AI Thesis Writing Tool - AI Dissertation Writer | Paperpal, 11月 29, 2025にアクセス、 https://paperpal.com/paperpal-for-students
Detect hallucinations for RAG-based systems | Artificial Intelligence - AWS, 11月 29, 2025にアクセス、 https://aws.amazon.com/blogs/machine-learning/detect-hallucinations-for-rag-based-systems/
Consistency Is the Key: Detecting Hallucinations in LLM Generated Text By Checking Inconsistencies About Key Facts - arXiv, 11月 29, 2025にアクセス、 https://arxiv.org/html/2511.12236v1
API Documentation - Scite.ai, 11月 29, 2025にアクセス、 https://scite.ai/reports/api-documentation-OVaNJgln
Trinka Citation Checker | Get Automated Citation Analysis, 11月 29, 2025にアクセス、 https://www.trinka.ai/features/citation-checker
Written material rubric (for written part of dissertation, thesis, professional paper, literature review of qualifying examinat, 11月 29, 2025にアクセス、 https://gs.hkbu.edu.hk/f/page/464/RPg-Thesis-Rubric-COMP.doc
PhD Computer Science - Assessment of Graduate Program - SMU, 11月 29, 2025にアクセス、 https://www.smu.edu/-/media/site/lyle/accreditation-rubrics/phd-computer-science-rubric.pdf
sypsyp97/AutoCitation: An LLM agent that helps you find real citations for your content., 11月 29, 2025にアクセス、 https://github.com/sypsyp97/AutoCitation
LangGraph: Hierarchical Agent Teams - Kaggle, 11月 29, 2025にアクセス、 https://www.kaggle.com/code/ksmooi/langgraph-hierarchical-agent-teams
Mastering AI-Powered Research: My Guide to Deep Research, Prompt Engineering, and Multi-Step Workflows : r/ChatGPTPro - Reddit, 11月 29, 2025にアクセス、 https://www.reddit.com/r/ChatGPTPro/comments/1in87ic/mastering_aipowered_research_my_guide_to_deep/
A Large-Scale Dataset and Citation Intent Classification in Turkish with LLMs This work was supported by TÜBİTAK ULAKBİM. - arXiv, 11月 29, 2025にアクセス、 https://arxiv.org/html/2509.21907v1
Semantic Scholar API (Academic Graph) - GitHub, 11月 29, 2025にアクセス、 https://gist.github.com/alexandreteles/c8bc00830e97eefa961e26c49aa666e7
Self-driven Biological Discovery through Automated Hypothesis Generation and Experimental Validation | bioRxiv, 11月 29, 2025にアクセス、 https://www.biorxiv.org/content/10.1101/2025.06.24.661378v1.full-text
(PDF) A review on the novelty measurements of academic papers - ResearchGate, 11月 29, 2025にアクセス、 https://www.researchgate.net/publication/388440814_A_review_on_the_novelty_measurements_of_academic_papers
Novelty in Science. A guide to reviewers | by Michael Black - Medium, 11月 29, 2025にアクセス、 https://medium.com/@black_51980/novelty-in-science-8f1fd1a0a143
STORM - Stanford University, 11月 29, 2025にアクセス、 https://storm.genie.stanford.edu/
