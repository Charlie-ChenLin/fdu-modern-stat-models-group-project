#!/usr/bin/env python3
"""Fetch real daily adjusted close prices for 15 US sector & cross-asset ETFs (2020-2025)
from Yahoo Finance Chart v8 API and compute aligned daily log returns.
"""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PRICES_CSV = BASE_DIR / "us_etf_prices_2020_2025.csv"
RETURNS_CSV = BASE_DIR / "us_etf_log_returns_2020_2025.csv"
PROVENANCE_MD = BASE_DIR / "DATA_PROVENANCE.md"

# 2020-01-01 00:00:00 UTC to 2026-01-01 00:00:00 UTC
PERIOD1 = 1577836800
PERIOD2 = 1767225600

ASSETS = [
    ("XLK", "Technology Select Sector SPDR", "科技", "股票-成长"),
    ("XLF", "Financial Select Sector SPDR", "金融", "股票-周期"),
    ("XLV", "Health Care Select Sector SPDR", "医疗健康", "股票-防御"),
    ("XLY", "Consumer Discretionary Select Sector SPDR", "可选消费", "股票-周期"),
    ("XLP", "Consumer Staples Select Sector SPDR", "必选消费", "股票-防御"),
    ("XLE", "Energy Select Sector SPDR", "能源", "股票-资源"),
    ("XLI", "Industrial Select Sector SPDR", "工业", "股票-周期"),
    ("XLB", "Materials Select Sector SPDR", "原材料", "股票-资源"),
    ("XLU", "Utilities Select Sector SPDR", "公用事业", "股票-防御"),
    ("XLRE", "Real Estate Select Sector SPDR", "房地产", "股票-利率敏感"),
    ("XLC", "Communication Services Select Sector SPDR", "通信服务", "股票-成长"),
    ("TLT", "iShares 20+ Year Treasury Bond ETF", "长端美债(20Y+)", "利率债"),
    ("IEF", "iShares 7-10 Year Treasury Bond ETF", "中端美债(7-10Y)", "利率债"),
    ("HYG", "iShares iBoxx $ High Yield Corporate Bond ETF", "高收益信用债", "信用债"),
    ("GLD", "SPDR Gold Shares", "黄金", "大宗商品"),
]


def fetch_ticker(symbol: str, retries: int = 3) -> pd.Series:
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?period1={PERIOD1}&period2={PERIOD2}&interval=1d"
    )
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            result = payload["chart"]["result"][0]
            ts = result["timestamp"]
            adj = result["indicators"]["adjclose"][0]["adjclose"]
            dates = pd.to_datetime(ts, unit="s", utc=True).tz_convert("America/New_York").date
            s = pd.Series(adj, index=pd.Index(dates, name="date"), name=symbol, dtype="float64")
            s = s[~s.index.duplicated(keep="last")].dropna()
            return s
        except Exception as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {symbol}: {last_err}")


def main() -> None:
    series_list = []
    for symbol, _, _, _ in ASSETS:
        s = fetch_ticker(symbol)
        series_list.append(s)
        print(f"Fetched {symbol}: {len(s)} rows ({s.index.min()} to {s.index.max()})")

    prices = pd.concat(series_list, axis=1, join="inner").sort_index()
    prices = prices.loc[(prices.index >= datetime(2020, 1, 1).date()) & (prices.index <= datetime(2025, 12, 31).date())]
    assert prices.isna().sum().sum() == 0, "Unexpected missing values in aligned prices!"
    assert (prices > 0).all().all(), "Non-positive prices found!"

    returns = np.log(prices / prices.shift(1)).dropna()
    assert returns.isna().sum().sum() == 0

    prices.to_csv(PRICES_CSV)
    returns.to_csv(RETURNS_CSV)

    fetched_at = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    lines = [
        "# 数据来源与核查记录（Version 1: 高斯图模型与跨资产风险网络）",
        "",
        f"- **抓取时间**：{fetched_at}",
        "- **原始数据源**：Yahoo Finance Chart v8 API (`https://query1.finance.yahoo.com/v8/finance/chart/<TICKER>?period1=1577836800&period2=1767225600&interval=1d`)",
        "- **价格口径**：日频分红与拆股复权收盘价（`indicators.adjclose`）",
        f"- **对齐后交易日区间**：`{prices.index.min()}` 至 `{prices.index.max()}`（价格表 {len(prices)} 行，日对数收益率表 {len(returns)} 行）",
        f"- **缺失值核查**：价格表缺失 `{int(prices.isna().sum().sum())}`，收益率表缺失 `{int(returns.isna().sum().sum())}`",
        "- **收益率定义**：$r_{t,j} = \\ln(P_{t,j} / P_{t-1,j})$（自然对数日收益率，无前瞻泄露）",
        "",
        "## 15 支 ETF 资产清单与描述统计（2020–2025 日对数收益率）",
        "",
        "| 代码 | 英文全称 | 中文名称 | 资产类别 | 样本数 | 日均值(%) | 日标准差(%) | 年化波动率(%) | 最小值(%) | 最大值(%) |",
        "| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for symbol, eng_name, cn_name, cat in ASSETS:
        r = returns[symbol]
        ann_vol = r.std(ddof=1) * np.sqrt(252) * 100
        lines.append(
            f"| {symbol} | {eng_name} | {cn_name} | {cat} | {len(r)} | "
            f"{r.mean()*100:.4f} | {r.std(ddof=1)*100:.3f} | {ann_vol:.2f} | "
            f"{r.min()*100:.2f} | {r.max()*100:.2f} |"
        )
    PROVENANCE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {PRICES_CSV.name} ({prices.shape}), {RETURNS_CSV.name} ({returns.shape}), and {PROVENANCE_MD.name}")


if __name__ == "__main__":
    main()
