# DESIGN.md: SignalCat for AI US Stock Universe (Bitget AI Hackathon S1 - Track 3)

## 项目概述与核心 Thesis

**项目名称**：SignalCat

**所属赛道**：Stock AI Trading 主赛道（Track 3）

**核心 Thesis（必须在项目描述中突出）**：
你的 TradingView 美股 AI 股票列表（共 211 只股票，覆盖 24 个 AI 产业链分类）是一个优质的静态股票池，但缺乏实时多因子动态融合能力。本项目将该列表作为固定 Universe，结合 Bitget API 行情数据、宏观/情绪输入、DeepSeek LLM 推理能力，构建一个**多因子混合信号系统**。系统每日/周期性生成动态排名与交易信号，并通过完整的 paper trading 执行 + 日志记录进行可验证验证，从而将静态列表转化为可执行的、带风险控制的交易信号，解决美股 AI 产业链交易中“信息过载 + 信号单一”的核心痛点。Bitget 不支持的 ticker 默认跳过；仅在显式启用时才使用 `yfinance` fallback。

**项目价值**：
- 直接利用你已有的高质量 TradingView AI 列表（211 只股票）。
- 首版优先利用 Bitget API + DeepSeek API 快速跑通，不默认使用 yfinance。
- 提供清晰、可验证的 paper trading 记录，完美匹配赛道三要求。
- 强调“动态融合 > 静态列表”，Thesis 扎实且有实际意义。

---

## 项目目标与 MVP 范围（严格控制在 24 小时内可完成）

**最终交付目标**：
1. 一个可公开访问的 **Dashboard**（展示排名、因子贡献、paper trading PnL 和日志）。
2. 完整的 **paper trading 执行日志**（CSV + SQLite，可复现）。
3. 公开 **GitHub 仓库**（含完整代码、README、日志示例）。
4. 清晰的 **Thesis** 和项目描述。
5. X 平台 **Demo 视频**（2-3 分钟）。

**MVP 严格范围**（不要做超出部分）：
- 股票池：使用你提供的 211 只股票（24 个分类）。
- 因子数量：5-6 个（TradingView 原始信号 + 技术指标 + 宏观 + 情绪 + 动量 + **各细分类别龙头战法**）。
- 数据更新频率：每小时或每日运行一次（MVP 用脚本手动触发）。
- 交易执行：支持两种模式：
  - **实时 Paper Trading**：纯模拟执行（**不需要账户里有真实资金**）。
  - **历史回测模式**：支持从过去任意时间点开始回放测试（**强烈推荐**，可生成历史绩效报告，用于提交材料证明策略有效性）。
- 前端：**Gradio** Dashboard（内存占用低，适合 4GB 开发机；比 Streamlit 更轻量）。备选：FastAPI + 简单 HTML/JS（极致轻量）。
- 不做：复杂回测引擎、实时 websocket、大量因子、链上深度集成、移动端。

**新增因子说明 - “各细分类别龙头战法”**：
利用 LIST.md 中 24 个细分类别（L0电网输配、L2算力芯片、L4-AI应用与AGENT 等），在每个分类内部计算“龙头战法”分数：
- 识别分类内相对强势股票（价格动量、成交量领导力、相对强弱）。
- 计算该股票在分类内的排名/领导力得分。
- 作为独立因子加入混合打分，强化“产业链细分龙头”逻辑，使系统更贴合你的 24 分类结构。

**成功标准**：
- Dashboard 可公开访问并展示实时排名 + 交易日志。
- GitHub 包含可运行代码 + 完整交易日志示例。
- 提交材料完整，Thesis 清晰。

---

## 交付物清单（Deliverables）

1. **公开 GitHub 仓库**
   - 完整代码 + README（含 Thesis、运行说明、截图、日志示例）。
   - `LIST.md`（直接使用你提供的 Markdown 文件）。
   - `logs/trades.csv`（示例交易日志）。

2. **可公开访问的 Dashboard**
   - 部署在 Railway / Render / Hugging Face Spaces（Gradio 原生支持，内存友好）。
   - 页面包含：当前排名表格（带 DeepSeek 理由）、因子贡献可视化、累计 PnL 曲线、交易明细表。

3. **Paper Trading 日志**
   - SQLite 数据库（`trades.db`） + 导出 CSV。
   - 每笔记录包含：timestamp, ticker, direction, price, quantity, balance_change, reason（来自 DeepSeek）。

4. **Demo 视频**
   - 2-3 分钟 X 帖子视频（展示 Dashboard 操作 + 运行一次完整流程 + Thesis 说明）。

5. **项目描述文本**
   - 用于 Google Form 提交（Thesis 部分重点突出）。

---

## 你需要准备的东西（User Preparation）

在让 AI 开始 coding 前，请准备以下内容：

1. **TradingView 列表数据**（已提供）：
   - Markdown 文件：同目录下的 `LIST.md`
   - 包含 211 只股票，24 个分类（L0 电网/数据中心 → L4 AI 应用与网络安全）。
   - **格式建议**：使用 Markdown 表格或列表，包含 `分类`、`代码`、`交易所` 等字段（AI 会自动解析）。
   - AI coding 时会直接读取 `LIST.md` 作为 Universe，无需额外转换。

2. **API Keys**（必须提前申请/获取）：
   - **DeepSeek API Key**：使用你自己的 DeepSeek API Key（模型推荐 deepseek-chat 或 deepseek-reasoner）。hackathon 提供的 Qwen credits 可作为备选，但优先使用 DeepSeek。
   - **Bitget API Key / Secret / Passphrase**：用于 Bitget 行情数据接入。首版仍只做 paper trading，不触碰真实资金。

3. **开发环境**：
   - Python 3.10+
   - 推荐 IDE：Cursor / VS Code（让 AI 直接在 Cursor 中 coding）。
   - 依赖：`gradio`, `pandas`, `sqlite3`, `requests`, `openai`（DeepSeek 兼容 OpenAI 接口）, `plotly`（可视化）。

4. **部署准备**：
   - Railway / Render / Hugging Face Spaces 账号（Gradio 部署最友好，内存占用低）。
   - GitHub 仓库（提前创建空仓库）。

5. **时间规划**（极度紧急，截止 6 月 25 日 24:00 UTC+8）：
   - 现在开始 coding → 明天白天完成核心功能 → 晚上部署 + 视频 + 提交。

---

## 技术架构

**整体流程**：
```
TradingView 列表 (LIST.md)
        ↓
因子计算模块（技术 + 宏观 + 情绪 + 动量）
        ↓
DeepSeek LLM 融合 → JSON 排名 + 理由
        ↓
Paper Trading 执行 + SQLite 日志
        ↓
Gradio Dashboard（可视化 + PnL）
        ↓
公开部署 + GitHub + X 视频
```

**推荐技术栈**：
- **后端**：Python + Pandas + SQLite
- **LLM**：DeepSeek（通过 openai 兼容接口，模型 deepseek-chat）
- **Agent Hub 集成**：首版可用手动/默认宏观情绪输入，后续再接 Bitget Agent Hub skills（macro, sentiment 等）
- **前端**：Gradio（轻量，适合 4GB 内存；部署简单）
- **数据**：Bitget API 默认数据源；yfinance fallback 默认关闭
- **部署**：Streamlit Cloud / Railway

---

## 推荐项目文件结构

```
ai-hybrid-signal-engine/
├── data/
│   ├── LIST.md                    # 你提供的股票列表（Markdown 格式，211只 + 24分类）
│   └── trades.db                  # SQLite 交易日志
├── factors/
│   ├── technical.py               # 技术指标计算（RSI, MACD 等）
│   ├── macro_sentiment.py         # 首版手动/默认宏观情绪输入，后续可接 Agent Hub
│   └── momentum.py                # 动量/波动率因子
├── llm/
│   └── deepseek_fusion.py         # DeepSeek Prompt + JSON 解析
├── trading/
│   ├── paper_trader.py            # Paper trading 模拟器 + 风控
│   └── logger.py                  # 日志记录模块
├── dashboard/
│   └── app.py                     # Gradio 主页面
├── utils/
│   ├── data_loader.py             # 解析 LIST.md（提取 ticker + 分类）
│   └── market_data.py             # Bitget 行情源封装，yfinance fallback 默认关闭
├── main.py                        # 主运行脚本（每日触发）
├── requirements.txt
├── README.md                      # 完整项目说明 + Thesis
└── DESIGN.md                      # 本文档
```

---

## 详细实现指导（供 AI Coding 使用）

### 1. 数据层（优先完成）
- 直接解析 `LIST.md`（Markdown 格式，AI 自动提取 ticker、分类、交易所等信息作为 Universe）。
- 选定 10-20 只代表性股票作为 MVP 测试池（全 211 只太多了）。
- 获取价格数据：优先使用 Bitget API；如 Bitget symbol 映射或接口异常，默认跳过该 ticker。
- Bitget 股票 token symbol 映射：先读取 spot symbols，优先尝试 `{TICKER}ONUSDT`（例如 `NVDA -> NVDAONUSDT`），找不到时记录错误。

### 2. 因子计算（4-5 个因子）
推荐因子：
- **TradingView 原始信号**：从列表分类或手动打分。
- **技术指标**：RSI(14), MACD, 成交量变化（用 pandas_ta 或简单计算）。
- **宏观因子**：首版用手动/默认输入，后续可通过 Agent Hub macro skill 获取。
- **情绪因子**：首版用手动/默认输入，后续可通过 Agent Hub sentiment skill + 简单新闻获取。
- **动量因子**：过去 N 日涨跌幅 + 波动率。

### 3. DeepSeek 融合（核心亮点）
使用以下 Prompt 模板（AI coding 时直接实现）：

```python
prompt = f"""
你是一个专业的美股 AI 产业链量化分析师。

股票池（来自 TradingView AI 关注列表，共 {len(tickers)} 只，覆盖电网、数据中心、半导体、算力、存储、光模块、AI 应用、网络安全等 24 个分类）：
{ticker_list_str}

当前宏观环境：{macro_data}
情绪数据：{sentiment_data}
各股票最新技术指标：
{technical_data_str}

请综合以上信息，对每只股票进行 0-100 分打分，并输出前 5 名推荐 + 每只股票的简短理由（50 字内）。
输出必须是严格的 JSON 格式：
{{
  "rankings": [
    {{"ticker": "NVDA", "score": 92, "reason": "算力需求持续爆发 + 技术超买但动量强劲"}},
    ...
  ],
  "overall_thesis": "当前 AI 产业链处于..."
}}
"""
```

解析 JSON 后得到排名和理由。

### 4. Paper Trading + 日志（重要说明）
- **完全模拟（Paper Trading）**：**不需要账户里真的有钱**。所有交易都是在内存/数据库中模拟执行，不会触碰真实资金或真实账户。完美符合 hackathon “无需真实资金” 的要求。
- **支持历史回测**：系统可以从**过去任意时间点**开始回放历史数据，进行 walk-forward 或简单历史模拟测试（例如从 2025 年某月开始 replay 每天的信号并执行交易）。这能生成更丰富的可验证交易记录，大幅提升提交材料的说服力。
- 初始资金：10,000 USDT（模拟）
- 规则示例：每天买入 Top 3-5，持有 1-3 天，单笔仓位 ≤ 20%，止损 -5%。
- 每笔交易记录完整字段 + DeepSeek 生成的 reason（timestamp, ticker, direction, price, quantity, balance_change, reason）。

### 5. Dashboard 页面设计（Gradio - 推荐轻量方案）
推荐页面布局：
- **Sidebar**：运行按钮 + 参数设置（初始资金、持仓数量）
- **主页面**：
  - 当前 Top 排名表格（含分数 + DeepSeek 理由）
  - 因子贡献雷达图 / 柱状图
  - 累计 PnL 曲线（plotly）
  - 最近交易明细表
  - 完整日志下载按钮（CSV）

---

## 部署与运行指令

```bash
# 本地运行（Gradio）
pip install -r requirements.txt
python dashboard/app.py

# 部署推荐
# Railway / Render / Hugging Face Spaces（Gradio 原生支持）
```

---

## 提交材料准备 checklist（必须在 6 月 25 日 24:00 前完成）

- [ ] GitHub 仓库公开 + README 完善（含 Thesis）
- [ ] Dashboard 上线并可公开访问
- [ ] `logs/trades.csv` 包含至少 10-20 笔模拟交易记录
- [ ] X 帖子发布（#BitgetHackathon @Bitget_AI + 视频 + 链接）
- [ ] Google Form 提交（https://forms.gle/CEGB6fRtuobD3bCj8）
  - 填写项目描述（Thesis 部分重点写）
  - 上传/填写所有链接
  - 附上 X 帖子链接（争 Community Impact Award）

---

## 时间规划建议（现在是 6 月 25 日 00:00，极度紧急）

- **现在 - 凌晨 4:00**：数据层 + 基础框架 + 解析 LIST.md 准备
- **明天上午**：因子计算 + DeepSeek Prompt 实现 + 融合模块
- **明天下午**：Paper trading + 日志 + Dashboard 核心页面
- **明天晚上 18:00 前**：部署 + 测试 + 录制 Demo 视频
- **明天晚上 20:00-24:00**：完善 README + 发 X 帖 + 提交 Google Form

**立即行动建议**：
1. 把这个 DESIGN.md 复制给 Cursor / Claude / GPT-4o 等 AI coding 工具。
2. 提供 `LIST.md` 文件，让 AI 直接解析（无需转换）。
3. 先让 AI 搭建基础框架（`main.py` + Gradio 空页面）。

---

**本 DESIGN.md 已包含完整项目蓝图、代码结构、Prompt 示例、交付物要求和时间规划**，可直接复制给 AI 进行端到端开发。

如需进一步细化（例如具体代码模板、完整 Prompt 最终版、Streamlit 页面详细代码），请随时告诉我，我可以继续补充！ 

现在时间非常紧，**立刻开始 coding**，我们目标是明天晚上前完成全部提交材料。加油！
