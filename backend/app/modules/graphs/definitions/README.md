# Graph 流程圖生成說明

本目錄包含兩個 LangGraph 定義檔案,均可單獨執行以生成流程圖。

## 檔案說明

### 1. base_graph.py
基礎對話 Graph,不包含 RAG 檢索功能。

**流程**: START → llm_node → END

**執行方式**:
```bash
cd C:\python_project\Metora\backend\app\modules\graphs\definitions
C:\python_project\Metora\.venv\Scripts\python.exe base_graph.py
```

**輸出**: `base_graph.png`

### 2. rag_graph.py
完整的 RAG 對話 Graph,包含意圖判別、查詢重構和檢索功能。

**流程**:
- START → intent_check → 條件分支:
  - 需要 RAG: → query_rewrite → rag_retrieval → llm_final → END
  - 不需要 RAG: → llm_final → END

**執行方式**:
```bash
cd C:\python_project\Metora\backend\app\modules\graphs\definitions
C:\python_project\Metora\.venv\Scripts\python.exe rag_graph.py
```

**輸出**: `rag_graph.png`

**注意**: rag_graph.py 需要初始化完整的系統資源 (資料庫、Redis、AI 模型等),執行時間較長。

## 流程圖特點

### Base Graph
- 簡單直接的對話流程
- 使用最近 5 輪對話作為上下文
- 適合一般聊天對話

### RAG Graph
- **意圖判別節點** (intent_check): 使用 3 輪上下文判斷是否需要檢索
- **查詢重構節點** (query_rewrite): 使用 3 輪上下文進行查詢拆解和重寫
- **RAG 檢索節點** (rag_retrieval): 跨 Collection 並行檢索並重排序
- **最終回應節點** (llm_final): 使用 5 輪上下文生成最終回應
- 條件路由根據意圖判別結果選擇是否進入檢索流程

## 技術細節

- **記憶系統**:
  - 5 輪記憶用於最終 LLM 回應
  - 3 輪記憶用於意圖判別和查詢重構
- **LLM Provider**: 支援 Ollama 等多種 LLM
- **檢索架構**: 向量檢索 + BM25 + RRF 融合 + BGE Reranker
- **流程圖格式**: PNG (使用 Mermaid 引擎生成)

## 依賴要求

生成流程圖需要以下依賴:
- langgraph
- graphviz (系統層級)
- 相關 Python 套件已在虛擬環境中安裝

## 生成的流程圖

執行後會在同目錄下生成:
- `base_graph.png` - 基礎對話流程圖
- `rag_graph.png` - RAG 對話流程圖

可以直接開啟這些 PNG 檔案查看 Graph 的視覺化流程。




 Graph 物件的生命週期

  時機 1：應用啟動時（只執行一次）

  # app/core/resource_manager.py:126
  initialize_graphs(settings, self.llm_provider, retrieval_service)

  # ↓ 調用

  # app/modules/graphs/registry.py:99-127
  def initialize_graphs(settings, llm_provider, retrieval_service):
      # 建立 base_graph（只建立一次）
      base_graph = create_base_graph(settings, llm_provider)
      GraphRegistry.register(
          name="base_graph",
          graph=base_graph,  # ← 存入 class variable
          ...
      )

      # 建立 rag_graph（只建立一次）
      rag_graph = create_rag_graph(settings, llm_provider, retrieval_service)
      GraphRegistry.register(
          name="rag_graph",
          graph=rag_graph,  # ← 存入 class variable
          ...
      )

  存儲位置（單例模式）：

  # app/modules/graphs/registry.py:12-13
  class GraphRegistry:
      _graphs: Dict[str, CompiledStateGraph] = {}  # ← class variable（全局共享）
      _metadata: Dict[str, Dict[str, Any]] = {}

  這是一個類變量（class variable），在整個應用生命週期中只有一份！

  ---
  時機 2：每次對話請求時

  # app/modules/chat/service.py:239
  executor = GraphExecutor(session.graph_type, self.settings)

  # ↓ 初始化 Executor

  # app/modules/graphs/executor.py:14-24
  class GraphExecutor:
      def __init__(self, graph_type: str, settings):
          self.graph_type = graph_type
          self.settings = settings
          self.graph = GraphRegistry.get(graph_type)  # ← 從 Registry 取得已存在的 Graph

  關鍵代碼：
  self.graph = GraphRegistry.get(graph_type)

  GraphRegistry.get() 做了什麼：
  # app/modules/graphs/registry.py:40-55
  @classmethod
  def get(cls, name: str) -> CompiledStateGraph:
      if name not in cls._graphs:
          raise ValueError(f"Graph '{name}' 未註冊")
      return cls._graphs[name]  # ← 返回已存在的 Graph 實例（引用）

  這只是返回引用，不會創建新的 Graph！

  ---
  時機 3：執行 Graph

  # app/modules/graphs/executor.py:174-176
  async for stream_mode, chunk in self.graph.astream(
      state,  # ← 每次執行傳入新的 State
      stream_mode=["updates", "messages"]
  ):

  這裡：
  - self.graph 是共享的 Graph 實例（不變）
  - state 是每次請求新建的（每次不同）

  2.2 完整流程圖

  [應用啟動]
      ↓
  ResourceManager.initialize()
      ↓
  initialize_graphs()
      ├─ create_base_graph() → base_graph 實例（只建立一次）
      ├─ create_rag_graph() → rag_graph 實例（只建立一次）
      └─ GraphRegistry._graphs = {
             "base_graph": <CompiledStateGraph 實例 A>,
             "rag_graph": <CompiledStateGraph 實例 B>
         }

  ================================================================

  [用戶 1 發送訊息]
      ↓
  ChatService.stream_chat()
      ↓
  executor = GraphExecutor("base_graph", settings)
      ├─ self.graph = GraphRegistry.get("base_graph")
      └─ 返回實例 A 的引用（不創建新實例）
      ↓
  executor.stream_execute(state1)  # state1 是新建的
      ↓
  self.graph.astream(state1)  # 用共享的 Graph 實例 A 執行

  ================================================================

  [用戶 2 發送訊息（同時進行）]
      ↓
  ChatService.stream_chat()
      ↓
  executor = GraphExecutor("base_graph", settings)
      ├─ self.graph = GraphRegistry.get("base_graph")
      └─ 返回實例 A 的引用（同一個實例！）
      ↓
  executor.stream_execute(state2)  # state2 是新建的（與 state1 不同）
      ↓
  self.graph.astream(state2)  # 用同一個 Graph 實例 A 執行

  2.3 關鍵區別

  | 項目                 | 生命週期 | 是否共享     | 何時創建        |
  |--------------------|------|----------|-------------|
  | CompiledStateGraph | 應用級別 | ✅ 共享（單例） | 應用啟動時       |
  | GraphExecutor      | 請求級別 | ❌ 每次新建   | 每次對話請求      |
  | State              | 執行級別 | ❌ 每次新建   | 每次 Graph 執行 |

  三、為什麼這樣設計？

  3.1 優勢

  1. 效能優化
  - Graph 編譯是昂貴的操作（構建節點、邊、執行計劃）
  - 只編譯一次，後續直接使用
  - 節省 CPU 和內存

  2. 線程安全
  - LangGraph 的 CompiledStateGraph 是線程安全的
  - 可以同時被多個請求使用
  - 每個請求使用不同的 State，不會互相干擾

  3. 資源管理
  - Graph 內部包含 LLM 連接等資源
  - 共享這些資源，避免重複創建

  3.2 如何保證請求隔離？

  關鍵：每次執行傳入不同的 State

  # 用戶 1 的請求
  state1 = {
      "messages": [用戶1的歷史],
      "user_query": "用戶1的問題",
      ...
  }
  graph.astream(state1)  # ← 獨立的狀態

  # 用戶 2 的請求（同時進行）
  state2 = {
      "messages": [用戶2的歷史],
      "user_query": "用戶2的問題",
      ...
  }
  graph.astream(state2)  # ← 獨立的狀態

  LangGraph 的 astream() 方法：
  - 接收 State 作為參數
  - 創建新的執行上下文
  - 不修改 Graph 本身
  - 返回獨立的執行結果

  這類似於：
  # 函數對象是共享的
  def add(a, b):
      return a + b

  # 但每次調用是獨立的
  result1 = add(1, 2)  # 不會影響
  result2 = add(3, 4)  # 另一個調用

  四、修正後的架構理解

  原來的（錯誤）理解：

  每次對話請求
      ↓
  創建新的 Graph 物件（❌）
      ↓
  執行 Graph
      ↓
  銷毀 Graph 物件

  正確的理解：

  [應用啟動時]
      ↓
  創建 Graph 物件（一次）
      ↓
  存入 GraphRegistry（單例）

  ================================================================

  [每次對話請求]
      ↓
  從 GraphRegistry 取得 Graph 引用（共享）
      ↓
  創建新的 State（請求級別）
      ↓
  用共享的 Graph 執行新的 State
      ↓
  State 執行完成後被丟棄
      ↓
  Graph 繼續存在（供下次使用）

  五、實際驗證

  您可以添加日誌來驗證：

  # app/modules/graphs/registry.py:40-55
  @classmethod
  def get(cls, name: str) -> CompiledStateGraph:
      if name not in cls._graphs:
          raise ValueError(f"Graph '{name}' 未註冊")

      graph = cls._graphs[name]
      print(f"[DEBUG] 返回 Graph 實例 ID: {id(graph)}")  # ← 添加這行
      return graph

  如果多次請求，您會看到：
  [DEBUG] 返回 Graph 實例 ID: 140234567890  # 第一次請求
  [DEBUG] 返回 Graph 實例 ID: 140234567890  # 第二次請求（相同ID！）
  [DEBUG] 返回 Graph 實例 ID: 140234567890  # 第三次請求（相同ID！）

  六、總結

  核心要點

  1. Graph 物件是單例
    - 應用啟動時創建
    - 存儲在 class variable 中
    - 所有請求共享
  2. GraphExecutor 是請求級別
    - 每次請求創建
    - 但它只是持有 Graph 的引用
    - 不創建新的 Graph
  3. State 是執行級別
    - 每次執行創建
    - 請求之間完全隔離
    - 執行完成後丟棄

  與 Stateless/Stateful 的關係

  Stateless 指的是：
  - Graph 執行是無狀態的
  - 不通過 checkpointer 持久化 State
  - 每次執行後 State 被丟棄

  但：
  - Graph 物件本身是有狀態的（持久存在）
  - 只是每次執行的 State 是新的

  這是正確的設計！