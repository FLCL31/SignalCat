# TODO.md: AI Hybrid Signal Engine MVP Plan

## 1. 项目理解

当前目录文档描述的是一个面向 **Bitget AI Hackathon S1 - Track 3 / Stock AI Trading** 的项目：

- 项目名称暂定：`AI-Hybrid-Signal-Engine`
- 核心目标：把 `LIST.md` 中的 TradingView AI 美股产业链静态股票池，转化成一个可运行、可验证的动态交易信号系统。
- 当前股票池：`LIST.md` 已确认为 **211 只股票 / 24 个分类**。
- 核心方法：结合价格/技术指标、动量、行业内龙头分数、宏观/情绪因子，以及 DeepSeek LLM 推理，生成排名、交易理由和 paper trading 记录。
- 最终交付：公开 Dashboard、GitHub 仓库、模拟交易日志、README/Thesis、2-3 分钟 Demo 视频、X 帖子和 Google Form 提交。

MVP 的关键原则：

- 默认只做 **Paper Trading**，不触碰真实资金。
- 后续使用 Bitget API 作为默认行情数据源；`yfinance` fallback 默认关闭。
- 前端优先使用 **Gradio**，方便快速部署到 Hugging Face Spaces / Railway / Render。
- 日志必须可复现，至少生成 `SQLite + CSV` 两种格式。

## 2. MVP 交付范围

必须完成：

- [ ] 解析 `LIST.md`，提取 `category`、`ticker`、`exchange`。
- [ ] 生成可运行的股票 universe，先支持 10-20 只 MVP 测试池，再支持全量 211 只。
- [ ] 获取历史行情数据，默认使用 Bitget 数据源。
- [ ] 计算基础因子：
  - [ ] 技术指标：RSI、均线趋势、成交量变化。
  - [ ] 动量因子：近 5/20 日收益、波动率调整收益。
  - [ ] 分类龙头因子：同分类内相对强弱排名。
  - [ ] 宏观/情绪因子：MVP 可先用手动输入或默认值，后续接 Agent Hub / 新闻源。
- [ ] 归一化因子并计算综合分数。
- [ ] 调用 DeepSeek 生成最终 Top N 排名和简短理由。
- [ ] 在无 DeepSeek Key 时提供 deterministic fallback，保证 Demo 可运行。
- [ ] 实现 paper trading：
  - [ ] 初始资金默认 `10000 USDT`。
  - [ ] 每次买入 Top 3-5。
  - [ ] 单票仓位上限默认 20%。
  - [ ] 支持止损参数，默认 -5%。
  - [ ] 支持历史回测模式。
- [ ] 写入交易日志：
  - [ ] `data/trades.db`
  - [ ] `logs/trades.csv`
- [ ] 实现 Gradio Dashboard：
  - [ ] 当前排名表格。
  - [ ] 因子贡献图。
  - [ ] Paper trading PnL 曲线。
  - [ ] 最近交易日志表。
  - [ ] CSV 下载按钮。
- [ ] 写 README：
  - [ ] Thesis。
  - [ ] 架构说明。
  - [ ] 本地运行说明。
  - [ ] 环境变量说明。
  - [ ] Dashboard 截图。
  - [ ] 示例交易日志说明。

暂不做：

- [ ] 真实下单。
- [ ] 高频 websocket。
- [ ] 复杂事件驱动回测引擎。
- [ ] 移动端适配专项优化。
- [ ] 大规模新闻抓取和全自动舆情系统。

## 3. 推荐目录结构

建议后续 coding 时创建以下结构：

```text
.
├── DESIGN.md
├── LIST.md
├── TODO.md
├── README.md
├── .env.example
├── requirements.txt
├── main.py
├── config/
│   └── config.example.yaml
├── data/
│   ├── universe.csv
│   ├── prices/
│   └── trades.db
├── logs/
│   └── trades.csv
├── factors/
│   ├── technical.py
│   ├── momentum.py
│   ├── category_leader.py
│   └── macro_sentiment.py
├── llm/
│   └── deepseek_fusion.py
├── trading/
│   ├── paper_trader.py
│   └── logger.py
├── dashboard/
│   └── app.py
├── utils/
│   ├── data_loader.py
│   ├── market_data.py
│   └── scoring.py
├── tests/
│   ├── test_data_loader.py
│   ├── test_factors.py
│   └── test_paper_trader.py
└── submission/
    ├── SUBMISSION.md
    └── demo_script.md
```

## 4. 实施顺序

### Phase 0: 项目初始化

- [ ] 创建 Python 项目基础结构。
- [ ] 添加 `.gitignore`，确保 `.env`、数据库、缓存、私钥不会提交。
- [ ] 添加 `.env.example`，只写变量名，不写真实 key。
- [ ] 添加 `requirements.txt`。
- [ ] 添加 `config/config.example.yaml`，放默认参数。

验收标准：

- [ ] `python -m pytest` 能启动测试框架。
- [ ] `python main.py --help` 或等价命令可运行。

### Phase 1: Universe 解析

- [ ] 读取根目录 `LIST.md`。
- [ ] 解析制表符分隔内容。
- [ ] 输出标准字段：`index`、`category`、`ticker`、`exchange`。
- [ ] 统计分类数、ticker 数，并在控制台输出。
- [ ] 生成 `data/universe.csv`。

验收标准：

- [ ] 能正确识别 211 个 ticker。
- [ ] 能正确识别 24 个分类。
- [ ] 控制台输出并确认股票池为 211 个 ticker / 24 个分类。

### Phase 2: 行情数据层

- [ ] 实现 `utils/market_data.py`。
- [ ] 默认使用 Bitget API 获取行情数据。
- [ ] 从 Bitget spot symbols 构建 ticker 映射，优先尝试 `{TICKER}ONUSDT`，例如 `NVDA -> NVDAONUSDT`。
- [ ] 缓存价格数据到 `data/prices/`。
- [ ] 对 Bitget 不支持的 ticker 给出清晰错误；仅在 `YFINANCE_FALLBACK=true` 时才使用 yfinance。

验收标准：

- [ ] 可对 10-20 个代表性 ticker 拉取 6-12 个月日线数据。
- [ ] 能从 Bitget 获取至少 `NVDAONUSDT` 这类股票 token 的 ticker/历史 K 线。
- [ ] 网络失败时使用缓存或给出清晰错误。

### Phase 3: 因子计算

- [ ] 实现技术因子。
- [ ] 实现动量因子。
- [ ] 实现分类龙头因子。
- [ ] 实现宏观/情绪占位因子。
- [ ] 对所有因子做 0-100 归一化。
- [ ] 输出每只股票的总分和因子贡献。

验收标准：

- [ ] 能生成 Top N 排名。
- [ ] 每个排名包含可展示的因子贡献。

### Phase 4: DeepSeek 融合

- [ ] 通过 OpenAI-compatible client 调用 DeepSeek。
- [ ] Prompt 输出严格 JSON。
- [ ] 加 JSON 解析和错误 fallback。
- [ ] 限制一次传入的股票数量，避免 token 过大。

验收标准：

- [ ] 有 key 时，排名包含 LLM 生成理由。
- [ ] 无 key 时，Dashboard 仍可用 fallback 理由运行。

### Phase 5: Paper Trading 和日志

- [ ] 实现资金、持仓、买入、卖出、止损。
- [ ] 支持最新信号执行一次。
- [ ] 支持历史回测模式。
- [ ] 每笔交易写入 SQLite。
- [ ] 导出 CSV。

验收标准：

- [ ] `logs/trades.csv` 至少有 10-20 条示例交易。
- [ ] Dashboard 能展示交易明细和 PnL 曲线。

### Phase 6: Dashboard

- [ ] 使用 Gradio 构建页面。
- [ ] 增加运行按钮和参数输入。
- [ ] 展示排名、理由、因子贡献、PnL、交易日志。
- [ ] 提供 CSV 下载。

验收标准：

- [ ] `python dashboard/app.py` 本地可运行。
- [ ] 页面截图可用于 README。

### Phase 7: 文档、部署和提交

- [ ] 完成 README。
- [ ] 部署 Dashboard。
- [ ] 录制 2-3 分钟 Demo 视频。
- [ ] 发布 X 帖子，包含项目链接、视频、`#BitgetHackathon`、`@Bitget_AI`。
- [ ] 填写 Google Form。
- [ ] 在 `submission/SUBMISSION.md` 记录最终提交链接。

验收标准：

- [ ] GitHub 仓库公开。
- [ ] Dashboard 链接公开可访问。
- [ ] X 帖链接已记录。
- [ ] Google Form 已提交。

## 5. 风险和取舍

- 股票池数量已统一为 211，只要 README、Dashboard 和提交文案保持同一口径。
- Bitget 数据接入已通过基础认证测试；实现时仍需处理具体 symbol 映射、接口限频和不支持 ticker 的跳过逻辑。
- DeepSeek 输出 JSON 可能不稳定：必须有 schema 校验和 fallback。
- 全量 211 只股票可能慢：Dashboard 默认先展示 Top 20，后台可支持全量计算。
- 宏观/情绪因子可能变成时间黑洞：MVP 先保留轻量实现，不让它阻塞交易日志和 Dashboard。

## 6. 你需要准备什么

### 必须准备

- [ ] DeepSeek API Key。
  - 本地存放位置：项目根目录 `.env`
  - 部署存放位置：Railway / Render / Hugging Face Spaces 的 Secrets 或 Environment Variables
- [ ] Bitget API Key / Secret / Passphrase 已准备，后续代码优先使用 Bitget。
- [ ] 所有提交文案统一写为 211 只股票。
- [ ] GitHub 空仓库。
  - 仓库地址记录到 `submission/SUBMISSION.md`。
- [ ] 部署平台账号。
  - 推荐 Hugging Face Spaces，其次 Railway / Render。
  - 部署后的 Dashboard URL 记录到 `submission/SUBMISSION.md`。
- [ ] X 账号。
  - Demo 视频和 X 帖链接记录到 `submission/SUBMISSION.md`。

### 推荐准备

- [ ] DeepSeek 模型选择。
  - 推荐先用 `deepseek-chat`，成本和速度更适合 MVP。
  - 如需更强推理再切到 `deepseek-reasoner`。
- [ ] Demo 录屏工具。
  - 录屏文件建议放在 `submission/`，文件名如 `demo-video-notes.md` 记录视频脚本和发布链接。
- [ ] 项目截图。
  - 截图建议放在 `assets/` 或 `submission/`。
- [ ] 提交文案。
  - 项目描述、Thesis、运行说明统一写入 `README.md`。
  - Google Form 最终字段和链接备份到 `submission/SUBMISSION.md`。

### `.env` 建议格式

真实 `.env` 不要提交到 GitHub。后续只提交 `.env.example`。

```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

DATA_SOURCE=bitget
YFINANCE_FALLBACK=false
INITIAL_CASH=10000
TOP_N=5
MAX_POSITION_PCT=0.20
STOP_LOSS_PCT=-0.05

# Bitget credentials. Primary data source while DATA_SOURCE=bitget.
BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSPHRASE=
BITGET_BASE_URL=https://api.bitget.com
BITGET_ENABLED=true
BITGET_STOCK_SYMBOL_SUFFIX=ONUSDT
```

## 7. 立即下一步

- [ ] 按 `Bitget 默认数据源` 的路线先做 MVP。
- [ ] 准备 `.env` 中的 DeepSeek key。
- [ ] 开始编码 Phase 0-1。
