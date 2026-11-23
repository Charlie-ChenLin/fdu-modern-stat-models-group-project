# 数据来源与核查记录（Version 1: 高斯图模型与跨资产风险网络）

- **抓取时间**：2026-11-24 01:03:27 CST
- **原始数据源**：Yahoo Finance Chart v8 API (`https://query1.finance.yahoo.com/v8/finance/chart/<TICKER>?period1=1577836800&period2=1767225600&interval=1d`)
- **价格口径**：日频分红与拆股复权收盘价（`indicators.adjclose`）
- **对齐后交易日区间**：`2020-01-02` 至 `2025-12-31`（价格表 1508 行，日对数收益率表 1507 行）
- **缺失值核查**：价格表缺失 `0`，收益率表缺失 `0`
- **收益率定义**：$r_{t,j} = \ln(P_{t,j} / P_{t-1,j})$（自然对数日收益率，无前瞻泄露）

## 15 支 ETF 资产清单与描述统计（2020–2025 日对数收益率）

| 代码 | 英文全称 | 中文名称 | 资产类别 | 样本数 | 日均值(%) | 日标准差(%) | 年化波动率(%) | 最小值(%) | 最大值(%) |
| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| XLK | Technology Select Sector SPDR | 科技 | 股票-成长 | 1507 | 0.0781 | 1.758 | 27.90 | -14.87 | 12.60 |
| XLF | Financial Select Sector SPDR | 金融 | 股票-周期 | 1507 | 0.0450 | 1.598 | 25.36 | -14.74 | 12.36 |
| XLV | Health Care Select Sector SPDR | 医疗健康 | 股票-防御 | 1507 | 0.0340 | 1.146 | 18.19 | -10.38 | 7.42 |
| XLY | Consumer Discretionary Select Sector SPDR | 可选消费 | 股票-周期 | 1507 | 0.0454 | 1.628 | 25.85 | -13.55 | 10.34 |
| XLP | Consumer Staples Select Sector SPDR | 必选消费 | 股票-防御 | 1507 | 0.0250 | 1.038 | 16.47 | -9.87 | 8.17 |
| XLE | Energy Select Sector SPDR | 能源 | 股票-资源 | 1507 | 0.0427 | 2.205 | 35.00 | -22.49 | 14.87 |
| XLI | Industrial Select Sector SPDR | 工业 | 股票-周期 | 1507 | 0.0479 | 1.423 | 22.59 | -12.04 | 11.91 |
| XLB | Materials Select Sector SPDR | 原材料 | 股票-资源 | 1507 | 0.0347 | 1.473 | 23.39 | -11.66 | 11.12 |
| XLU | Utilities Select Sector SPDR | 公用事业 | 股票-防御 | 1507 | 0.0318 | 1.403 | 22.27 | -12.06 | 12.04 |
| XLRE | Real Estate Select Sector SPDR | 房地产 | 股票-利率敏感 | 1507 | 0.0170 | 1.515 | 24.05 | -17.44 | 8.42 |
| XLC | Communication Services Select Sector SPDR | 通信服务 | 股票-成长 | 1507 | 0.0552 | 1.481 | 23.50 | -11.97 | 8.61 |
| TLT | iShares 20+ Year Treasury Bond ETF | 长端美债(20Y+) | 利率债 | 1507 | -0.0186 | 1.077 | 17.10 | -6.90 | 7.25 |
| IEF | iShares 7-10 Year Treasury Bond ETF | 中端美债(7-10Y) | 利率债 | 1507 | -0.0000 | 0.480 | 7.62 | -2.54 | 2.61 |
| HYG | iShares iBoxx $ High Yield Corporate Bond ETF | 高收益信用债 | 信用债 | 1507 | 0.0152 | 0.622 | 9.87 | -5.65 | 6.34 |
| GLD | SPDR Gold Shares | 黄金 | 大宗商品 | 1507 | 0.0672 | 1.031 | 16.37 | -6.64 | 4.74 |
