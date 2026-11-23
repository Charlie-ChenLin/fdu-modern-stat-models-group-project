#!/usr/bin/env python3
"""Fetch the real-world 1991 SIPP 401(k) dataset from the CausalAIBook repository
(Chernozhukov, Hansen, Kallus, Spindler, Syrgkanis) and document provenance.
"""

from __future__ import annotations

import hashlib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_URL = "https://raw.githubusercontent.com/CausalAIBook/MetricsMLNotebooks/main/data/401k.csv"
RAW_CSV = BASE_DIR / "sipp_1991_401k.csv"
PROVENANCE_MD = BASE_DIR / "DATA_PROVENANCE.md"


def main() -> None:
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw_bytes = resp.read()
    RAW_CSV.write_bytes(raw_bytes)
    sha256 = hashlib.sha256(raw_bytes).hexdigest()

    df = pd.read_csv(RAW_CSV)
    assert df.isna().sum().sum() == 0, "Unexpected missing values!"

    core_cols = [
        ("net_tfa", "家庭净金融资产 (美元, 结果变量 Y)"),
        ("e401", "雇主是否提供 401(k) 资格 (0/1, 处置变量 D)"),
        ("p401", "是否实际参与 401(k) 计划 (0/1, 工具变量分析第二阶段内生处置)"),
        ("age", "户主年龄 (岁, 25-64)"),
        ("inc", "家庭年收入 (美元)"),
        ("educ", "受教育年限 (年)"),
        ("fsize", "家庭人口规模 (人)"),
        ("marr", "是否已婚 (0/1)"),
        ("twoearn", "是否双职工家庭 (0/1)"),
        ("db", "是否拥有固定收益养老金 DB Plan (0/1)"),
        ("pira", "是否参与个人退休账户 IRA (0/1)"),
        ("hown", "是否自有住房 (0/1)"),
    ]

    fetched_at = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    lines = [
        "# 数据来源与核查记录（Version 2: 双重机器学习 DML）",
        "",
        f"- **抓取时间**：{fetched_at}",
        f"- **数据下载来源**：`{DATA_URL}`",
        f"- **本地文件与 SHA-256**：`sipp_1991_401k.csv` (`{sha256}`)",
        "- **原始调查出处**：美国人口普查局 1991 年《收入与项目参与调查》（Survey of Income and Program Participation, SIPP），由 Poterba, Venti & Wise (1995)、Abadie (2003)、Chernozhukov & Hansen (2004) 及 Chernozhukov et al. (2018, *The Econometrics Journal*) 标准化用于退休储蓄因果效应研究。",
        f"- **样本维度与完整性**：{df.shape[0]} 户家庭 × {df.shape[1]} 个变量，总缺失值 `{int(df.isna().sum().sum())}`。",
        f"- **处置组与对照组分布**：`e401 = 1`（具备 401(k) 资格）共有 `{int((df['e401']==1).sum())}` 户（`{df['e401'].mean()*100:.2f}%`）；`e401 = 0` 共有 `{int((df['e401']==0).sum())}` 户。",
        f"- **实际参与率**：在具备资格的家庭中，`p401 = 1` 占比 `{df.loc[df['e401']==1, 'p401'].mean()*100:.2f}%`；在无资格家庭中 `p401 = 1` 占比 `{df.loc[df['e401']==0, 'p401'].mean()*100:.2f}%`（单边服从性，适合作为工具变量第一阶段）。",
        "",
        "## 核心变量字典与描述统计",
        "",
        "| 变量名 | 含义说明 | 均值 | 标准差 | 最小值 | 中位数 | 最大值 |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for col, desc in core_cols:
        s = df[col]
        lines.append(
            f"| `{col}` | {desc} | {s.mean():,.2f} | {s.std(ddof=1):,.2f} | "
            f"{s.min():,.1f} | {s.median():,.1f} | {s.max():,.1f} |"
        )
    PROVENANCE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {RAW_CSV.name} ({df.shape}) and {PROVENANCE_MD.name}")


if __name__ == "__main__":
    main()
