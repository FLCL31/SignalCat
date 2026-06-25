# SignalCat — AI 美股信号引擎

SignalCat 是一个面向 **Bitget AI 黑客松（Track 3：AI 股票交易）** 的多因子 AI 股票信号引擎。它把一个包含 211 只美股 AI 产业链股票的静态自选列表，转化成每日动态排名、DeepSeek AI 推理分析和可复现的模拟交易记录。

> ⚠️ 本项目仅做模拟交易（Paper Trading），不会执行真实订单，也不需要真实账户资金。

## 解决什么问题？

做 AI 股票交易的人往往面对一份长长的自选列表，**真正难的不是找到股票，而是决定今天该关注哪几只**。SignalCat 就是解决这个问题的：

1. 读取你整理好的 211 只 AI 产业链股票（覆盖 24 个细分赛道）
2. 自动匹配 Bitget 平台支持的股票代币对
3. 拉取 Bitget 日线行情数据
4. 用技术面、动量、波动率、赛道龙头等多因子给每只股票打分
5. 让 DeepSeek 为排名靠前的信号生成通俗易懂的投资逻辑
6. 用可配置的参数跑一遍模拟交易回测，输出完整日志
7. 在 Gradio 面板里把排名、收益、交易记录可视化展示

这样一份静态股票列表就变成了**可执行、可验证、带风险控制**的交易信号系统。

## 核心功能

- **211 只 AI 股票池**：从 `LIST.md` 自动解析，涵盖 24 个 AI 产业链分类（从电网输配、算力芯片到大模型应用）
- **Bitget 原生数据源**：将美股代码映射为 Bitget 现货交易对（如 `NVDA → NVDAONUSDT`），不支持的自动跳过
- **无静默降级**：默认关闭 yfinance 回退（`YFINANCE_FALLBACK=false`），排名结果严格基于 Bitget 数据，确保数据源清晰可追溯
- **交易对覆盖检查**：`python3 main.py check-symbols` 一键检查 Bitget 支持哪些股票
- **多因子混合打分**：
  - 技术因子：RSI、均线趋势、成交量变化
  - 动量因子：5 日 / 20 日涨幅、波动率调整收益
  - 赛道龙头因子：同分类内相对强弱排名
  - 宏观/情绪因子：MVP 阶段预留中性占位，可后续接入
- **DeepSeek AI 解读**：配置 `DEEPSEEK_API_KEY` 后，自动生成 Top 信号的简洁投资逻辑和整体市场研判
- **不依赖 LLM 也能跑**：未配置 DeepSeek 时自动降级为纯因子排名，管道可正常运行
- **模拟交易引擎**：
  - 初始资金可配（默认 10,000 USDT）
  - 支持 Top-N 选股、单票仓位上限、止损线
  - 每日调仓、手续费（默认 10 bps）、滑点（默认 5 bps）
  - 支持历史回测（3 个月 / 6 个月预设）
- **审计级日志**：每次运行输出排名表、净值曲线、绩效摘要、跳过的股票错误日志、SQLite 交易记录、CSV 交易记录和完整的 Markdown 回测报告
- **Gradio 可视面板**：交互式界面，可直接运行管道、查看排名、因子贡献、模拟盈亏、交易明细和数据覆盖情况
- **部署即用**：提供 `app.py`、`Procfile`、`render.yaml`，可一键部署到 Hugging Face Spaces / Render / Railway

## 项目架构

```
LIST.md（211只AI股票自选列表）
  → utils/data_loader.py     → 解析股票池
  → utils/market_data.py     → Bitget 行情拉取 & 代码映射
  → factors/                 → 多因子计算
  → utils/scoring.py         → 归一化 + 综合打分
  → llm/deepseek_fusion.py   → DeepSeek AI 解读
  → trading/paper_trader.py  → 模拟交易回测
  → trading/logger.py        → SQLite + CSV 日志
  → dashboard/app.py         → Gradio 可视化面板
```

### 核心模块

| 模块 | 说明 |
|------|------|
| `main.py` | CLI 入口，端到端管道编排 |
| `utils/market_data.py` | Bitget 行情客户端，交易对映射，K 线下载与缓存 |
| `factors/` | 技术面、动量、宏观占位、赛道龙头等多因子计算 |
| `llm/deepseek_fusion.py` | OpenAI 兼容格式调用 DeepSeek，含 JSON 解析容错 |
| `trading/paper_trader.py` | 模拟回测引擎：调仓、止损、手续费、滑点、绩效指标 |
| `dashboard/app.py` | Gradio 可视面板 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件填入你的密钥（本地使用，**不要提交到 Git**）：

```bash
# DeepSeek AI 配置（可选，但推荐）
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 数据源 & 模拟交易参数
DATA_SOURCE=bitget
YFINANCE_FALLBACK=false
# 初始资金 (USDT)
INITIAL_CASH=10000
# 每次持仓 Top N 只
TOP_N=5
# 单票最大仓位 20%
MAX_POSITION_PCT=0.20
# 止损线 -5%
STOP_LOSS_PCT=-0.05
# 手续费 10 bps
FEE_BPS=10
# 滑点 5 bps
SLIPPAGE_BPS=5

# Bitget API（公开行情接口无需填，留空即可）
BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSPHRASE=
BITGET_BASE_URL=https://api.bitget.com
BITGET_ENABLED=true
BITGET_STOCK_SYMBOL_SUFFIX=ONUSDT
```

> Bitget 公开行情接口无需 API Key。密钥字段保留用于后续认证接口扩展。

### 3. 解析股票池

```bash
python3 main.py parse-universe
```

### 4. 检查 Bitget 交易对覆盖

```bash
python3 main.py check-symbols
```

### 5. 运行信号 + 模拟交易

```bash
# 基础运行：24 只股票，120 天历史数据，30 天回测
python3 main.py run --limit 24 --history-days 120 --backtest-days 30

# 3 个月回测预设
python3 main.py run --limit 24 --preset 3m

# 6 个月回测预设
python3 main.py run --limit 24 --preset 6m

# 不使用 DeepSeek（纯因子打分）
python3 main.py run --limit 24 --no-llm
```

### 6. 启动可视面板

```bash
python3 app.py
# 浏览器打开 → http://127.0.0.1:7860
```

面板包含三个标签页：
- **Overview（总览）**：排名表格 + 因子贡献图表
- **Trading（交易）**：模拟盈亏曲线、绩效指标、近期交易、CSV 下载
- **Coverage（覆盖）**：被跳过的股票和数据错误

临时公开分享：

```bash
GRADIO_SHARE=true python3 app.py
```

如需稳定的公开地址，建议部署到 Hugging Face Spaces、Render 或 Railway，在平台密钥管理里填入 `.env` 配置。

## 运行测试

```bash
python3 -m pytest -q
python3 -m compileall main.py utils trading dashboard app.py tests
```

## Paper Trading 产物

每次运行 `python3 main.py run ...` 后，会刷新以下可审计产物，评委可以直接打开检查：

| 文件 | 内容 |
|------|------|
| `data/latest_rankings.csv` | 最新股票排名、Bitget 交易对、因子分数和信号理由 |
| `data/equity_curve.csv` | 模拟交易净值曲线 |
| `data/performance_summary.csv` | 收益率、最大回撤、Sharpe、交易次数、手续费和滑点 |
| `data/data_errors.csv` | Bitget 不支持或行情失败的股票列表 |
| `logs/trades.csv` | 每笔模拟交易记录，包含时间、方向、价格、数量、手续费和理由 |
| `submission/backtest_report.md` | 面向提交材料的 Markdown 回测摘要 |

## 当前回测验证结果

最新提交的示例回测（5 只候选股票，60 天历史数据，14 天回测，不调用 DeepSeek）：

```
python3 main.py run --limit 5 --history-days 60 --backtest-days 14 --no-llm
```

产出数据：

| 指标 | 数值 |
|------|------|
| 模拟交易笔数 | 11 笔 |
| 最终净值 | 10,161.85 USDT（初始 10,000） |
| 总收益率 | +1.62% |
| 最大回撤 | -9.79% |
| Sharpe 比率 | 0.60 |
| 手续费/滑点 | 10 bps / 5 bps |

> ⚠️ 以上为模拟交易示例数据，不代表任何投资建议，也不保证未来收益。

## 黑客松交付状态

- ✅ Bitget 为默认行情数据源
- ✅ AI 辅助的多因子股票信号流程
- ✅ 含手续费、滑点、净值曲线的模拟交易回测
- ✅ Gradio 可视面板 + CLI 可复现命令
- ✅ 供评委检查的示例输出

待完成的外部提交项：
- [ ] 将 Gradio 面板部署到公开 URL
- [ ] 录制 2-3 分钟 Demo 视频
- [ ] 发布 X 平台帖子
- [ ] 填写官方提交表单
- [ ] 在 `submission/SUBMISSION.md` 补充最终链接

## 局限性

- 本项目不是真实资金交易机器人
- Bitget 不支持的股票交易对默认跳过
- 宏观和情绪因子在 MVP 阶段为中性占位
- 回测为轻量级每日调仓模拟，非机构级事件驱动引擎
- 结果高度依赖 Bitget 交易对覆盖和历史 K 线数据

## 仓库地址

```text
https://github.com/FLCL31/SignalCat
```
