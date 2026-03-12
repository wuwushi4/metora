# 法規 JSON 的 references 欄位回填指南

## 📋 目錄

1. [references 欄位結構說明](#references-欄位結構說明)
2. [填寫步驟](#填寫步驟)
3. [範例說明](#範例說明)
4. [常見問題](#常見問題)

---

## references 欄位結構說明

每個條文的 `references` 欄位是一個物件，包含以下四個子欄位：

```json
{
  "raw_text": [],      // 原始引用文字（如 "前條", "第2條"）
  "resolved": [],      // 解析後的絕對條號（如 ["2", "8"]）
  "forward_refs": [],  // 向前引用（本條引用的其他條文）
  "backward_refs": []  // 向後引用（引用本條的其他條文）
}
```

### 欄位說明

| 欄位 | 說明 | 範例 |
|------|------|------|
| `raw_text` | 原始引用文字，保留在條文中的原始表述 | `["前條", "第2條", "第5條至第10條"]` |
| `resolved` | 解析後的絕對條號，統一轉換為數字字串 | `["1", "2", "5", "6", "7", "8", "9", "10"]` |
| `forward_refs` | 本條引用的其他條文（向前指） | `["2", "5"]` |
| `backward_refs` | 其他條文引用本條（向後指） | `["25", "30"]` |

### 關係說明

```
第6條 ──forward_refs──→ 第2條
第6條 ←─backward_refs── 第25條
```

- **forward_refs**：表示"第6條引用了第2條"
- **backward_refs**：表示"第25條引用了第6條"

---

## 填寫步驟

### Step 1：識別條文中的引用

在條文內容中搜尋以下模式：
- `第X條`
- `前條`
- `第X條至第Y條`
- `第X條、第Y條及第Z條`

### Step 2：填寫 forward_refs

對於當前條文，記錄它引用的其他條文。

**範例**：
```
第25條：「違反第6條、第10條規定者，處罰金...」
```

第25條的 `forward_refs` 應填寫：`["6", "10"]`

### Step 3：同步更新 backward_refs

當你填寫某條文的 `forward_refs` 後，需要同步更新被引用條文的 `backward_refs`。

**範例**：
- 第25條 → forward_refs: `["6", "10"]`
- 第6條 → backward_refs 新增: `"25"`
- 第10條 → backward_refs 新增: `"25"`

### Step 4：填寫 raw_text 和 resolved

- `raw_text`：保留條文中的原始文字
- `resolved`：統一轉換為條號（數字字串）

---

## 範例說明

### 範例 1：單筆引用

#### 情境
假設第25條內容為：
```
違反第6條規定者，處新臺幣一萬五千元以上七萬五千元以下罰鍰。
```

#### 填寫結果

**第25條的 references**：
```json
{
  "article_num": "25",
  "article_display": "第25條",
  "content": "違反第6條規定者，處新臺幣一萬五千元以上七萬五千元以下罰鍰。",
  "items": [],
  "references": {
    "raw_text": ["第6條"],
    "resolved": ["6"],
    "forward_refs": ["6"],
    "backward_refs": []
  },
  "note": null,
  "scenarios": []
}
```

**第6條的 references（需同步更新）**：
```json
{
  "article_num": "6",
  "article_display": "第6條",
  "content": "任何人不得騷擾、虐待或傷害動物。",
  "items": [],
  "references": {
    "raw_text": [],
    "resolved": [],
    "forward_refs": [],
    "backward_refs": ["25"]  // 新增 "25"
  },
  "note": null,
  "scenarios": [
    "有人用棍子、石頭等物品毆打路邊的流浪貓狗",
    "看到有人踢打、拖行、摔打寵物或動物"
  ]
}
```

---

### 範例 2：多筆引用

#### 情境
假設第30條內容為：
```
違反第6條、第10條或第11條規定者，處罰金...
```

#### 填寫結果

**第30條的 references**：
```json
{
  "article_num": "30",
  "article_display": "第30條",
  "content": "違反第6條、第10條或第11條規定者，處罰金...",
  "items": [],
  "references": {
    "raw_text": ["第6條", "第10條", "第11條"],
    "resolved": ["6", "10", "11"],
    "forward_refs": ["6", "10", "11"],
    "backward_refs": []
  },
  "note": null,
  "scenarios": []
}
```

**第6條的 references（需同步更新）**：
```json
{
  "backward_refs": ["25", "30"]  // 新增 "30"
}
```

**第10條的 references（需同步更新）**：
```json
{
  "backward_refs": ["30"]  // 新增 "30"
}
```

**第11條的 references（需同步更新）**：
```json
{
  "backward_refs": ["30"]  // 新增 "30"
}
```

---

### 範例 3：連續條文引用

#### 情境
假設第15條內容為：
```
依第5條至第8條規定...
```

#### 填寫結果

**第15條的 references**：
```json
{
  "article_num": "15",
  "article_display": "第15條",
  "content": "依第5條至第8條規定...",
  "items": [],
  "references": {
    "raw_text": ["第5條至第8條"],
    "resolved": ["5", "6", "7", "8"],
    "forward_refs": ["5", "6", "7", "8"],
    "backward_refs": []
  },
  "note": null,
  "scenarios": []
}
```

**第5、6、7、8條都需要同步更新**：
```json
{
  "backward_refs": ["15"]  // 分別新增 "15"
}
```

---

### 範例 4：使用「前條」

#### 情境
假設第7條內容為：
```
前條所稱之動物，應符合...
```
（假設前條為第6條）

#### 填寫結果

**第7條的 references**：
```json
{
  "article_num": "7",
  "article_display": "第7條",
  "content": "前條所稱之動物，應符合...",
  "items": [],
  "references": {
    "raw_text": ["前條"],
    "resolved": ["6"],
    "forward_refs": ["6"],
    "backward_refs": []
  },
  "note": null,
  "scenarios": []
}
```

**第6條的 references（需同步更新）**：
```json
{
  "backward_refs": ["7", "25", "30"]  // 新增 "7"
}
```

---

## 常見問題

### Q1：如果條文沒有引用任何其他條文，如何填寫？

**答**：填寫 `null` 或空物件皆可。

```json
// 方式 1：null
"references": null

// 方式 2：空物件（系統會自動補全）
"references": {
  "raw_text": [],
  "resolved": [],
  "forward_refs": [],
  "backward_refs": []
}
```

---

### Q2：如果條文只被其他條文引用（只有 backward_refs），其他欄位如何填寫？

**答**：其他欄位填空陣列。

```json
"references": {
  "raw_text": [],
  "resolved": [],
  "forward_refs": [],
  "backward_refs": ["25", "30"]
}
```

---

### Q3：如何快速找到所有引用關係？

**答**：使用文字編輯器的搜尋功能：

1. 搜尋 `"第X條"`（X 為當前條號）
2. 在搜尋結果中找到所有引用該條文的地方
3. 記錄這些條文的條號，填入 `backward_refs`

**範例**：
- 搜尋 `"第6條"`
- 找到第25條、第30條內容中都提到"第6條"
- 在第6條的 `backward_refs` 填入 `["25", "30"]`

---

### Q4：條號為 "2-1"、"6-1" 這種，如何填寫？

**答**：保持原樣填寫。

```json
"forward_refs": ["2-1", "6", "6-1"]
```

---

### Q5：如何驗證填寫是否正確？

**答**：檢查以下原則：

1. **雙向對應**：如果 A 的 `forward_refs` 包含 B，則 B 的 `backward_refs` 必須包含 A
2. **數量一致**：`resolved` 的數量應等於 `raw_text` 中展開後的條號數量
3. **無重複**：同一個條號不應在 `forward_refs` 或 `backward_refs` 中重複出現

---

## 自動化工具建議

對於大型法規文件，建議編寫腳本來協助填寫：

1. **解析條文內容**：使用正則表達式找出所有 "第X條" 模式
2. **構建引用圖**：自動建立 forward_refs
3. **反向更新**：自動計算 backward_refs
4. **驗證一致性**：檢查雙向引用是否對應

範例腳本位置：`backend/scripts/preprocessors/build_references.py`（待實作）

---

## 動物保護法第6條完整範例

```json
{
  "article_num": "6",
  "article_display": "第6條",
  "content": "任何人不得騷擾、虐待或傷害動物。",
  "items": [],
  "references": {
    "raw_text": [],
    "resolved": [],
    "forward_refs": [],
    "backward_refs": ["25", "27", "30"]
  },
  "note": null,
  "scenarios": [
    "有人用棍子、石頭等物品毆打路邊的流浪貓狗",
    "看到有人踢打、拖行、摔打寵物或動物",
    "發現有人用刀具、電擊棒等工具傷害動物",
    "目擊有人虐待動物，如燙傷、刺傷、長期挨餓",
    "有人故意追逐、驚嚇動物，造成動物受傷或痛苦",
    "用車輛故意輾壓、撞擊動物"
  ]
}
```

---

## 檢查清單

填寫完成後，請檢查：

- [ ] 所有引用其他條文的條文都填寫了 `forward_refs`
- [ ] 所有被引用的條文都更新了 `backward_refs`
- [ ] `raw_text` 保留了原始文字表述
- [ ] `resolved` 正確展開了所有條號
- [ ] 沒有重複的條號
- [ ] 雙向引用關係對應正確

---

**更新時間**：2025-01-10
**適用範圍**：所有法規 JSON 文件
