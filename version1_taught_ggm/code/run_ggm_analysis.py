#!/usr/bin/env python3
"""Version 1 (Course-Taught Method): Gaussian Graphical Models (GGM) & Graphical Lasso
Applied to 15 US Sector & Cross-Asset ETFs (2020-2025).

Implements both Lecture 5 algorithms directly:
  - Algorithm 1 (Lecture 5.3.3-5.3.4 / ESL Alg 17.1): Constrained Gaussian MLE for known graph structure E
  - Algorithm 2 (Lecture 5.3.5-5.3.6 / ESL Alg 17.2): Graphical Lasso L1-penalized precision matrix estimation
Plus EBIC model selection, network topology diagnostics, regime shift comparison,
and strictly out-of-sample Global Minimum Variance Portfolio (GMVP) risk control backtest.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.covariance import GraphicalLasso, LedoitWolf
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import KFold

# Configure Chinese font + math minus rendering cleanly on macOS
plt.rcParams["font.sans-serif"] = ["Hiragino Sans GB", "Arial Unicode MS", "Heiti TC", "DejaVu Sans"]
plt.rcParams["mathtext.fontset"] = "dejavusans"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 300

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT_DIR / "data" / "us_etf_log_returns_2020_2025.csv"
OUT_DIR = ROOT_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"

ASSET_META = {
    "XLK": {"cn": "科技", "cat": "股票-成长", "color": "#1F4E79"},
    "XLC": {"cn": "通信", "cat": "股票-成长", "color": "#1F4E79"},
    "XLF": {"cn": "金融", "cat": "股票-周期", "color": "#2E75B6"},
    "XLY": {"cn": "可选消费", "cat": "股票-周期", "color": "#2E75B6"},
    "XLI": {"cn": "工业", "cat": "股票-周期", "color": "#2E75B6"},
    "XLE": {"cn": "能源", "cat": "股票-资源", "color": "#C55A11"},
    "XLB": {"cn": "原材料", "cat": "股票-资源", "color": "#C55A11"},
    "XLV": {"cn": "医疗", "cat": "股票-防御", "color": "#548235"},
    "XLP": {"cn": "必选消费", "cat": "股票-防御", "color": "#548235"},
    "XLU": {"cn": "公用事业", "cat": "股票-防御", "color": "#548235"},
    "XLRE": {"cn": "房地产", "cat": "股票-利率敏感", "color": "#7030A0"},
    "TLT": {"cn": "长端美债", "cat": "利率债", "color": "#BF9000"},
    "IEF": {"cn": "中端美债", "cat": "利率债", "color": "#BF9000"},
    "HYG": {"cn": "高收益债", "cat": "信用债", "color": "#A61C00"},
    "GLD": {"cn": "黄金", "cat": "大宗商品", "color": "#7F6000"},
}


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TAB_DIR.mkdir(parents=True, exist_ok=True)


def fit_single_glasso(Z: np.ndarray, alpha: float) -> GraphicalLasso:
    """Fit GraphicalLasso with coordinate descent (Lecture 5.3.6 Algorithm 2)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        gl = GraphicalLasso(alpha=float(alpha), mode="cd", max_iter=600, tol=1e-3, enet_tol=1e-4, assume_centered=True)
        gl.fit(Z)
        return gl


def constrained_gaussian_mle(S: np.ndarray, adj: np.ndarray, tol: float = 1e-9, max_iter: int = 800) -> Tuple[np.ndarray, np.ndarray]:
    """Lecture 5.3.4 Algorithm 1 (ESL Algorithm 17.1):
    Modified regression algorithm for Gaussian graphical model MLE with known edge set E.
    Ensures W_jk = S_jk for (j,k) in E or j=k, and Theta_jk = 0 for (j,k) not in E.
    """
    p = S.shape[0]
    W = S.copy().astype(float)
    eig_min = np.linalg.eigvalsh(W).min()
    if eig_min < 1e-8:
        W += np.eye(p) * (1e-6 - eig_min)

    adj_bool = (adj.astype(bool)).copy()
    np.fill_diagonal(adj_bool, False)

    betas = np.zeros((p, p - 1), dtype=float)
    for _ in range(max_iter):
        W_prev = W.copy()
        for j in range(p):
            idx = [k for k in range(p) if k != j]
            W11 = W[np.ix_(idx, idx)]
            s12 = S[idx, j]
            nbr_mask = adj_bool[j, idx]
            beta = np.zeros(p - 1, dtype=float)
            if np.any(nbr_mask):
                W11_sub = W11[np.ix_(nbr_mask, nbr_mask)]
                s12_sub = s12[nbr_mask]
                beta_sub = np.linalg.solve(W11_sub, s12_sub)
                beta[nbr_mask] = beta_sub
            betas[j] = beta
            w12 = W11 @ beta
            W[idx, j] = w12
            W[j, idx] = w12
        if np.max(np.abs(W - W_prev)) < tol:
            break

    Theta = np.zeros((p, p), dtype=float)
    for j in range(p):
        idx = [k for k in range(p) if k != j]
        w12 = W[idx, j]
        beta = betas[j]
        denom = max(W[j, j] - float(w12 @ beta), 1e-12)
        theta_jj = 1.0 / denom
        Theta[j, j] = theta_jj
        Theta[idx, j] = -beta * theta_jj
    Theta = 0.5 * (Theta + Theta.T)
    support = adj_bool.copy()
    np.fill_diagonal(support, True)
    Theta[~support] = 0.0
    return W, Theta


def precision_to_partial_corr(Theta: np.ndarray) -> np.ndarray:
    d = np.sqrt(np.diag(Theta))
    pcorr = -Theta / np.outer(d, d)
    np.fill_diagonal(pcorr, 1.0)
    return pcorr


def gaussian_nll_per_sample(S_eval: np.ndarray, Theta: np.ndarray) -> float:
    p = S_eval.shape[0]
    sign, logdet = np.linalg.slogdet(Theta)
    if sign <= 0:
        return float("inf")
    return 0.5 * (p * np.log(2.0 * np.pi) - logdet + float(np.trace(S_eval @ Theta)))


def compute_ebic(S_train: np.ndarray, Theta: np.ndarray, n: int, n_edges: int, gamma: float = 0.5) -> Tuple[float, float]:
    p = S_train.shape[0]
    sign, logdet = np.linalg.slogdet(Theta)
    if sign <= 0:
        return float("inf"), float("inf")
    neg2ll = -n * (logdet - float(np.trace(S_train @ Theta)))
    bic = neg2ll + n_edges * np.log(n)
    ebic = bic + 4.0 * n_edges * gamma * np.log(p)
    return float(bic), float(ebic)


def fit_glasso_with_ebic(Z_train: np.ndarray, Z_test: np.ndarray | None = None, gamma: float = 0.5) -> Dict:
    n, p = Z_train.shape
    S_train = np.cov(Z_train.T, bias=True)
    S_test = np.cov(Z_test.T, bias=True) if Z_test is not None else None

    # Full regularization grid from dense to ultra-sparse (<15 edges)
    alphas = np.geomspace(0.03, 0.85, 32)
    path_records = []
    best_ebic = float("inf")
    best_obj = None

    kf = KFold(n_splits=5, shuffle=False)

    for alpha in alphas:
        gl = fit_single_glasso(Z_train, float(alpha))
        Theta_gl = gl.precision_.copy()
        adj = (np.abs(Theta_gl) > 1e-5).astype(int)
        np.fill_diagonal(adj, 0)
        n_edges = int(np.sum(np.triu(adj, 1)))

        _, Theta_refit = constrained_gaussian_mle(S_train, adj)
        bic, ebic = compute_ebic(S_train, Theta_refit, n=n, n_edges=n_edges, gamma=gamma)
        nll_gl_test = gaussian_nll_per_sample(S_test, Theta_gl) if S_test is not None else np.nan
        nll_refit_test = gaussian_nll_per_sample(S_test, Theta_refit) if S_test is not None else np.nan

        cv_nlls = []
        for tr_idx, va_idx in kf.split(Z_train):
            gl_cv = fit_single_glasso(Z_train[tr_idx], float(alpha))
            S_va = np.cov(Z_train[va_idx].T, bias=True)
            cv_nlls.append(gaussian_nll_per_sample(S_va, gl_cv.precision_))
        cv_nll = float(np.mean(cv_nlls))

        pcorr_gl = precision_to_partial_corr(Theta_gl)
        pcorr_refit = precision_to_partial_corr(Theta_refit)

        rec = {
            "alpha": float(alpha),
            "n_edges": n_edges,
            "sparsity": 1.0 - n_edges / (p * (p - 1) / 2),
            "bic": bic,
            "ebic": ebic,
            "cv_nll": cv_nll,
            "test_nll_glasso": float(nll_gl_test),
            "test_nll_refit": float(nll_refit_test),
        }
        path_records.append(rec)

        if ebic < best_ebic:
            best_ebic = ebic
            best_obj = {
                **rec,
                "Theta_gl": Theta_gl,
                "Theta_refit": Theta_refit,
                "adj": adj,
                "pcorr_gl": pcorr_gl,
                "pcorr_refit": pcorr_refit,
            }

    assert best_obj is not None
    return {"best": best_obj, "path": path_records, "S_train": S_train, "S_test": S_test}


def gmvp_weights(Theta: np.ndarray) -> np.ndarray:
    ones = np.ones(Theta.shape[0])
    w = Theta @ ones
    return w / float(ones @ w)


def portfolio_metrics(port_ret: pd.Series, weights_history: np.ndarray | None = None) -> Dict[str, float]:
    ann_ret = float(port_ret.mean() * 252.0)
    ann_vol = float(port_ret.std(ddof=1) * np.sqrt(252.0))
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0.0
    cum = np.exp(port_ret.cumsum())
    running_max = cum.cummax()
    dd = cum / running_max - 1.0
    max_dd = float(dd.min())
    total_ret = float(cum.iloc[-1] - 1.0)
    l1_lev = float(np.mean(np.sum(np.abs(weights_history), axis=1))) if weights_history is not None else 1.0
    return {
        "ann_ret_pct": ann_ret * 100.0,
        "ann_vol_pct": ann_vol * 100.0,
        "sharpe_rf0": sharpe,
        "max_dd_pct": max_dd * 100.0,
        "total_ret_pct": total_ret * 100.0,
        "avg_l1_leverage": l1_lev,
    }


def block_bootstrap_vol_test(r1: np.ndarray, r2: np.ndarray, block_len: int = 10, n_boot: int = 2000, seed: int = 42) -> Dict[str, float]:
    """Circular block bootstrap for OOS annualized volatility difference: vol(r1) - vol(r2)."""
    rng = np.random.default_rng(seed)
    n = len(r1)
    n_blocks = int(np.ceil(n / block_len))
    obs_diff = (np.std(r1, ddof=1) - np.std(r2, ddof=1)) * np.sqrt(252.0) * 100.0
    diffs = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        idx = np.concatenate([(np.arange(s, s + block_len) % n) for s in starts])[:n]
        diffs[b] = (np.std(r1[idx], ddof=1) - np.std(r2[idx], ddof=1)) * np.sqrt(252.0) * 100.0
    ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])
    p_val = 2.0 * min(float(np.mean(diffs <= 0.0)), float(np.mean(diffs >= 0.0)))
    return {
        "vol_diff_pct": float(obs_diff),
        "ci95_low_pct": float(ci_low),
        "ci95_high_pct": float(ci_high),
        "p_value": float(min(p_val, 1.0)),
    }


def run_rolling_gmvp_backtest(returns: pd.DataFrame, test_start: str, alpha_fixed: float, window: int = 252, rebal_every: int = 21) -> Tuple[pd.DataFrame, Dict]:
    """Strictly causal rolling 252-day estimation (rebalanced every 21 trading days) over the test period."""
    cols = list(returns.columns)
    p = len(cols)
    test_idx = returns.index >= test_start
    test_positions = np.where(test_idx)[0]
    first_pos = int(test_positions[0])

    strategies = ["等权组合 (1/N)", "样本协方差 MLE", "Graphical Lasso", "GGM 两步精估 (Alg1)", "Ledoit-Wolf 收缩"]
    strat_rets = {s: [] for s in strategies}
    strat_weights = {s: [] for s in strategies}
    dates = []

    current_w = {s: np.ones(p) / p for s in strategies}

    for pos in range(first_pos, len(returns)):
        if (pos - first_pos) % rebal_every == 0:
            hist = returns.iloc[pos - window:pos].values
            mu_h = hist.mean(axis=0)
            sd_h = hist.std(axis=0, ddof=0)
            Z_h = (hist - mu_h) / sd_h
            S_h = np.cov(hist.T, bias=True)
            D_inv = np.diag(1.0 / sd_h)

            current_w["等权组合 (1/N)"] = np.ones(p) / p
            current_w["样本协方差 MLE"] = gmvp_weights(np.linalg.inv(S_h))

            gl = fit_single_glasso(Z_h, alpha_fixed)
            Theta_gl_ret = D_inv @ gl.precision_ @ D_inv
            current_w["Graphical Lasso"] = gmvp_weights(Theta_gl_ret)

            adj = (np.abs(gl.precision_) > 1e-5).astype(int)
            np.fill_diagonal(adj, 0)
            S_Z_h = np.cov(Z_h.T, bias=True)
            _, Theta_refit_Z = constrained_gaussian_mle(S_Z_h, adj)
            Theta_refit_ret = D_inv @ Theta_refit_Z @ D_inv
            current_w["GGM 两步精估 (Alg1)"] = gmvp_weights(Theta_refit_ret)

            lw = LedoitWolf(assume_centered=False).fit(hist)
            current_w["Ledoit-Wolf 收缩"] = gmvp_weights(np.linalg.inv(lw.covariance_))

        r_today = returns.iloc[pos].values
        dates.append(returns.index[pos])
        for s in strategies:
            strat_rets[s].append(float(current_w[s] @ r_today))
            strat_weights[s].append(current_w[s].copy())

    ret_df = pd.DataFrame(strat_rets, index=pd.Index(dates, name="date"))
    metrics = {s: portfolio_metrics(ret_df[s], np.array(strat_weights[s])) for s in strategies}
    return ret_df, metrics


# ---------------- Plotting Functions ---------------- #

def plot_fig1_heatmaps(corr: np.ndarray, pcorr: np.ndarray, cols: List[str]) -> None:
    y_labels = [f"{c} ({ASSET_META[c]['cn']})" for c in cols]
    x_labels = [f"{c} {ASSET_META[c]['cn']}" for c in cols]
    fig, axes = plt.subplots(1, 2, figsize=(16.0, 6.8))

    for ax, mat, title in [
        (axes[0], corr, "(a) 样本皮尔逊相关矩阵 $R$（受大盘共同因子主导，高度密集）"),
        (axes[1], pcorr, "(b) GGM 稀疏偏相关矩阵 $\\hat{\\rho}_{jk|-jk}$（剥离共同因子后的直接关联）"),
    ]:
        im = ax.imshow(mat, cmap="RdBu_r", vmin=-1.0, vmax=1.0)
        ax.set_xticks(range(len(cols)))
        ax.set_yticks(range(len(cols)))
        ax.set_xticklabels(x_labels, rotation=48, ha="right", fontsize=8.4)
        ax.set_yticklabels(y_labels, fontsize=8.4)
        ax.set_title(title, fontsize=11.3, fontweight="bold", pad=10)
        for i in range(len(cols)):
            for j in range(len(cols)):
                val = mat[i, j]
                if i == j or abs(val) >= 0.08:
                    txt_color = "white" if abs(val) > 0.55 else "#111111"
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=6.9, color=txt_color)

    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.86, pad=0.02)
    cbar.set_label("相关系数 / 偏相关系数", fontsize=10)
    fig.suptitle("图1：传统相关矩阵 vs. 高斯图模型偏相关矩阵（训练集 2020–2023）", fontsize=13.5, fontweight="bold", y=0.98)
    fig.savefig(FIG_DIR / "fig1_corr_vs_pcorr_heatmaps.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig2_network(pcorr: np.ndarray, cols: List[str], node_df: pd.DataFrame) -> None:
    G = nx.Graph()
    for c in cols:
        G.add_node(c)
    p = len(cols)
    for i in range(p):
        for j in range(i + 1, p):
            w = pcorr[i, j]
            if abs(w) > 1e-5:
                G.add_edge(cols[i], cols[j], weight=float(w), abs_w=float(abs(w)))

    pos = nx.spring_layout(G, weight="abs_w", seed=42, k=1.55, iterations=140)
    fig, ax = plt.subplots(figsize=(12.2, 8.5))

    strength_map = dict(zip(node_df["asset"], node_df["strength"]))
    node_colors = [ASSET_META[c]["color"] for c in G.nodes()]
    node_sizes = [1050 + 1100 * (strength_map[c] / max(strength_map.values())) for c in G.nodes()]

    # Layered edge rendering: weak edges subtle, backbone edges (|pcorr| >= 0.12) prominent
    weak_edges = [(u, v) for u, v, d in G.edges(data=True) if d["abs_w"] < 0.12]
    strong_pos = [(u, v) for u, v, d in G.edges(data=True) if d["abs_w"] >= 0.12 and d["weight"] > 0]
    strong_neg = [(u, v) for u, v, d in G.edges(data=True) if d["abs_w"] >= 0.12 and d["weight"] < 0]

    nx.draw_networkx_edges(G, pos, edgelist=weak_edges, width=0.9, edge_color="#94A3B8", alpha=0.20, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=strong_pos, width=[1.5 + 8.5 * G[u][v]["abs_w"] for u, v in strong_pos], edge_color="#1F4E79", alpha=0.78, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=strong_neg, width=[1.5 + 8.5 * G[u][v]["abs_w"] for u, v in strong_neg], edge_color="#C00000", style="dashed", alpha=0.88, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, edgecolors="white", linewidths=2.2, ax=ax)

    for node, (x, y) in pos.items():
        ax.text(
            x, y, f"{node}\n{ASSET_META[node]['cn']}",
            ha="center", va="center", fontsize=8.2, fontweight="bold", color="white"
        )

    edge_labels = {
        (u, v): f"{d['weight']:+.2f}"
        for u, v, d in G.edges(data=True) if d["abs_w"] >= 0.19
    }
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, font_size=7.8, font_color="#111827",
        bbox=dict(alpha=0.80, fc="white", ec="none", pad=0.5), ax=ax
    )

    legend_handles = [
        Line2D([0], [0], color="#1F4E79", lw=2.6, label="核心正偏相关 (|ρ|≥0.12)"),
        Line2D([0], [0], color="#C00000", lw=2.6, linestyle="--", label="核心负偏相关 (|ρ|≥0.12)"),
        Line2D([0], [0], color="#94A3B8", lw=1.2, alpha=0.5, label="次级弱边 (|ρ|<0.12)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#1F4E79", markersize=9, label="成长科技"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2E75B6", markersize=9, label="周期板块"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#548235", markersize=9, label="防御板块"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#C55A11", markersize=9, label="资源板块"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#BF9000", markersize=9, label="利率美债"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#A61C00", markersize=9, label="信用债 (HYG)"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", frameon=True, fontsize=8.4, ncol=2)
    n_strong = len(strong_pos) + len(strong_neg)
    ax.set_title(
        f"图2：15 支 ETF 高斯图模型条件独立风险网络（总计 {G.number_of_edges()} 条边，高亮 {n_strong} 条核心骨架边）",
        fontsize=12.6, fontweight="bold", pad=12
    )
    ax.axis("off")
    fig.savefig(FIG_DIR / "fig2_glasso_network_graph.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig3_path(path_df: pd.DataFrame, best_alpha: float) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.8, 5.2))
    ticks = [0.02, 0.04, 0.08, 0.15, 0.30, 0.60]

    ax1 = axes[0]
    ax1.plot(path_df["alpha"], path_df["n_edges"], marker="o", ms=4, color="#1F4E79", lw=2.2, label="保留边数 |E|")
    ax1.axvline(best_alpha, color="#C00000", ls="--", lw=1.6, label=f"EBIC 最优 α={best_alpha:.3f}")
    ax1.set_xscale("log")
    ax1.set_xticks(ticks)
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}"))
    ax1.set_xlabel("惩罚参数 α（对数刻度）", fontsize=10.5)
    ax1.set_ylabel("网络边数 |E|（满分 105 条）", fontsize=10.5)
    ax1.set_title("(a) 稀疏度随惩罚强度 α 的正则化路径", fontsize=11.5, fontweight="bold")
    ax1.grid(alpha=0.25)
    ax1.legend(fontsize=9)

    ax2 = axes[1]
    ax2.plot(path_df["alpha"], path_df["ebic"], marker="s", ms=4, color="#C55A11", lw=2.2, label="EBIC (γ=0.5, Refit MLE)")
    ax2.plot(path_df["alpha"], path_df["bic"], marker="^", ms=4, color="#2E75B6", lw=1.8, alpha=0.85, label="BIC (γ=0, Refit MLE)")
    ax2.axvline(best_alpha, color="#C00000", ls="--", lw=1.6, label=f"最优 α={best_alpha:.3f}")
    ax2.set_xscale("log")
    ax2.set_xticks(ticks)
    ax2.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}"))
    ax2.set_xlabel("惩罚参数 α（对数刻度）", fontsize=10.5)
    ax2.set_ylabel("信息准则值（越低越好）", fontsize=10.5)
    ax2.set_title("(b) BIC 与 EBIC 模型选择准则曲线", fontsize=11.5, fontweight="bold")
    ax2.grid(alpha=0.25)
    ax2.legend(fontsize=9)

    fig.suptitle("图3：Graphical Lasso 正则化路径与 EBIC 模型选择", fontsize=13.5, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig3_regularization_path_ebic.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig4_regimes(pcorr_r1: np.ndarray, pcorr_r2: np.ndarray, cols: List[str], jaccard: float) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15.0, 6.8))
    G_ref = nx.Graph()
    for c in cols:
        G_ref.add_node(c)
    pos = nx.circular_layout(G_ref)

    titles = [
        "(a) 冲击期 2020–2022（疫情暴跌 + 激进加息）",
        "(b) 新周期 2023–2025（AI 行情 + 高利率平台）",
    ]
    for ax, mat, title in zip(axes, [pcorr_r1, pcorr_r2], titles):
        G = nx.Graph()
        for c in cols:
            G.add_node(c)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                if abs(mat[i, j]) > 1e-5:
                    G.add_edge(cols[i], cols[j], weight=float(mat[i, j]), abs_w=float(abs(mat[i, j])))

        weak_e = [(u, v) for u, v, d in G.edges(data=True) if d["abs_w"] < 0.12]
        pos_e = [(u, v) for u, v, d in G.edges(data=True) if d["abs_w"] >= 0.12 and d["weight"] > 0]
        neg_e = [(u, v) for u, v, d in G.edges(data=True) if d["abs_w"] >= 0.12 and d["weight"] < 0]
        nx.draw_networkx_edges(G, pos, edgelist=weak_e, width=0.8, edge_color="#CBD5E1", alpha=0.28, ax=ax)
        nx.draw_networkx_edges(G, pos, edgelist=pos_e, width=[1.4 + 8.0 * G[u][v]["abs_w"] for u, v in pos_e], edge_color="#1F4E79", alpha=0.76, ax=ax)
        nx.draw_networkx_edges(G, pos, edgelist=neg_e, width=[1.4 + 8.0 * G[u][v]["abs_w"] for u, v in neg_e], edge_color="#C00000", style="dashed", alpha=0.86, ax=ax)
        nx.draw_networkx_nodes(G, pos, node_color=[ASSET_META[c]["color"] for c in G.nodes()], node_size=1280, edgecolors="white", linewidths=2.0, ax=ax)
        for node, (x, y) in pos.items():
            ax.text(x, y, f"{node}\n{ASSET_META[node]['cn']}", ha="center", va="center", fontsize=7.6, fontweight="bold", color="white")
        ax.set_title(f"{title}\n总边数: {G.number_of_edges()} 条（高亮 |ρ|≥0.12: {len(pos_e)+len(neg_e)} 条）", fontsize=10.8, fontweight="bold")
        ax.set_xlim(-1.22, 1.22)
        ax.set_ylim(-1.22, 1.22)
        ax.axis("off")

    fig.suptitle(f"图4：跨市场时期 GGM 结构演化对照（两阶段边重合度 Jaccard = {jaccard:.3f}）", fontsize=13.5, fontweight="bold", y=0.98)
    fig.savefig(FIG_DIR / "fig4_regime_comparison_networks.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig5_oos_backtest(roll_rets: pd.DataFrame, roll_metrics: Dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14.6, 5.5))

    colors = {
        "等权组合 (1/N)": "#7F7F7F",
        "样本协方差 MLE": "#C00000",
        "Graphical Lasso": "#2E75B6",
        "GGM 两步精估 (Alg1)": "#1F4E79",
        "Ledoit-Wolf 收缩": "#548235",
    }

    ax1 = axes[0]
    cum_df = np.exp(roll_rets.cumsum())
    dt_idx = pd.to_datetime(cum_df.index)
    for col in roll_rets.columns:
        lw = 2.4 if "GGM" in col or "Graphical" in col else 1.7
        ls = "--" if col == "样本协方差 MLE" else "-"
        ax1.plot(dt_idx, cum_df[col], label=col, color=colors[col], lw=lw, ls=ls)
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.tick_params(axis="x", rotation=22)
    ax1.set_title("(a) 2024–2025 样本外滚动 GMVP 累计净值曲线", fontsize=11.5, fontweight="bold")
    ax1.set_ylabel("净值（初始 = 1.0）", fontsize=10)
    ax1.grid(alpha=0.25)
    ax1.legend(fontsize=8.5, loc="upper left")

    ax2 = axes[1]
    names = list(roll_metrics.keys())
    vols = [roll_metrics[n]["ann_vol_pct"] for n in names]
    sharpes = [roll_metrics[n]["sharpe_rf0"] for n in names]
    x = np.arange(len(names))
    bars = ax2.bar(x, vols, color=[colors[n] for n in names], width=0.56, alpha=0.9)
    for bar, v, sh in zip(bars, vols, sharpes):
        ax2.text(bar.get_x() + bar.get_width() / 2, v + 0.18, f"{v:.2f}%\n(SR {sh:.2f})", ha="center", va="bottom", fontsize=8.4)
    ax2.set_xticks(x)
    ax2.set_xticklabels(["等权\n1/N", "样本协方差\nMLE", "Graphical\nLasso", "GGM 两步\n(Alg1)", "Ledoit-\nWolf"], fontsize=9)
    ax2.set_ylabel("样本外年化波动率 (%)", fontsize=10)
    ax2.set_ylim(0, max(vols) * 1.25)
    ax2.set_title("(b) 样本外年化波动率与夏普比率对照（目标：最小化波动）", fontsize=11.5, fontweight="bold")
    ax2.grid(axis="y", alpha=0.25)

    fig.suptitle("图5：严格样本外（2024–2025）滚动最小方差组合风控实证", fontsize=13.5, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig5_oos_gmvp_backtest.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig6_centrality_weights(node_df: pd.DataFrame, weights_dict: Dict[str, np.ndarray], cols: List[str]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14.6, 5.6))

    ax1 = axes[0]
    nd = node_df.sort_values("strength", ascending=True)
    y = np.arange(len(nd))
    bar_colors = [ASSET_META[a]["color"] for a in nd["asset"]]
    ax1.barh(y, nd["strength"], color=bar_colors, alpha=0.9)
    ax1.set_yticks(y)
    ax1.set_yticklabels([f"{a} ({ASSET_META[a]['cn']})" for a in nd["asset"]], fontsize=9)
    for idx, (st, deg) in enumerate(zip(nd["strength"], nd["degree"])):
        ax1.text(st + 0.02, idx, f"{st:.2f} (度={deg})", va="center", fontsize=8)
    ax1.set_xlim(0, nd["strength"].max() * 1.30)
    ax1.set_xlabel(r"加权中心度 $\mathrm{Strength}_j = \sum_{k \neq j} |\hat{\rho}_{jk|-jk}|$", fontsize=10)
    ax1.set_title("(a) 网络风险枢纽节点排序（强度与度数）", fontsize=11.5, fontweight="bold")
    ax1.grid(axis="x", alpha=0.25)

    ax2 = axes[1]
    x = np.arange(len(cols))
    width = 0.27
    ax2.bar(x - width, weights_dict["样本协方差 MLE"] * 100, width, label="样本协方差 MLE", color="#C00000", alpha=0.8)
    ax2.bar(x, weights_dict["Graphical Lasso"] * 100, width, label="Graphical Lasso", color="#2E75B6", alpha=0.88)
    ax2.bar(x + width, weights_dict["GGM 两步精估 (Alg1)"] * 100, width, label="GGM 两步精估 (Alg1)", color="#1F4E79", alpha=0.95)
    ax2.axhline(0, color="black", lw=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(cols, rotation=45, ha="right", fontsize=8.8)
    ax2.set_ylabel("组合配置权重 (%)", fontsize=10)
    ax2.set_title("(b) 训练集估计的 GMVP 资产权重对比（稀疏正则缓解极端头寸）", fontsize=11.5, fontweight="bold")
    ax2.legend(fontsize=8.5)
    ax2.grid(axis="y", alpha=0.25)

    fig.suptitle("图6：网络节点拓扑重要度与组合权重稳定性分析", fontsize=13.5, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig6_centrality_and_weights.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ensure_dirs()
    returns = pd.read_csv(DATA_CSV, index_col="date")
    cols = list(returns.columns)
    p = len(cols)

    train_df = returns.loc[returns.index <= "2023-12-31"]
    test_df = returns.loc[returns.index >= "2024-01-01"]

    mu_tr = train_df.mean(axis=0).values
    sd_tr = train_df.std(axis=0, ddof=0).values
    Z_train = (train_df.values - mu_tr) / sd_tr
    Z_test = (test_df.values - mu_tr) / sd_tr

    fit_res = fit_glasso_with_ebic(Z_train, Z_test, gamma=0.5)
    best = fit_res["best"]
    path_df = pd.DataFrame(fit_res["path"])
    path_df.to_csv(TAB_DIR / "glasso_regularization_path.csv", index=False)

    W_refit, Theta_refit_check = constrained_gaussian_mle(fit_res["S_train"], best["adj"])
    support_mask = best["adj"].astype(bool).copy()
    np.fill_diagonal(support_mask, True)
    alg1_primal_err = float(np.max(np.abs((W_refit - fit_res["S_train"])[support_mask])))
    alg1_zero_err = float(np.max(np.abs(Theta_refit_check[~support_mask])))

    S_train_Z = fit_res["S_train"]
    S_test_Z = fit_res["S_test"]
    Theta_mle_Z = np.linalg.inv(S_train_Z)
    lw_Z = LedoitWolf(assume_centered=True).fit(Z_train)
    Theta_lw_Z = np.linalg.inv(lw_Z.covariance_)

    nll_comparison = {
        "Sample_MLE_test_NLL": gaussian_nll_per_sample(S_test_Z, Theta_mle_Z),
        "LedoitWolf_test_NLL": gaussian_nll_per_sample(S_test_Z, Theta_lw_Z),
        "GLasso_EBIC_test_NLL": best["test_nll_glasso"],
        "GGM_Alg1_Refit_test_NLL": best["test_nll_refit"],
    }

    pcorr_refit = best["pcorr_refit"]
    pcorr_gl = best["pcorr_gl"]
    corr_train = np.corrcoef(train_df.values.T)
    edges = []
    G_net = nx.Graph()
    for c in cols:
        G_net.add_node(c)
    for i in range(p):
        for j in range(i + 1, p):
            if best["adj"][i, j] == 1:
                G_net.add_edge(cols[i], cols[j], abs_w=abs(float(pcorr_refit[i, j])))
                edges.append({
                    "u": cols[i],
                    "u_cn": ASSET_META[cols[i]]["cn"],
                    "v": cols[j],
                    "v_cn": ASSET_META[cols[j]]["cn"],
                    "pcorr_refit": float(pcorr_refit[i, j]),
                    "pcorr_glasso": float(pcorr_gl[i, j]),
                    "pearson_corr": float(corr_train[i, j]),
                    "abs_pcorr": abs(float(pcorr_refit[i, j])),
                })
    edge_df = pd.DataFrame(edges).sort_values("abs_pcorr", ascending=False)
    edge_df.to_csv(TAB_DIR / "ggm_edges_ranked.csv", index=False)

    betw = nx.betweenness_centrality(G_net, weight=lambda u, v, d: 1.0 / max(d["abs_w"], 1e-4))
    node_rows = []
    for i, c in enumerate(cols):
        deg = int(np.sum(best["adj"][i]))
        strength = float(np.sum(np.abs(pcorr_refit[i, :] * best["adj"][i, :])))
        node_rows.append({
            "asset": c,
            "cn": ASSET_META[c]["cn"],
            "category": ASSET_META[c]["cat"],
            "degree": deg,
            "strength": strength,
            "betweenness": float(betw[c]),
        })
    node_df = pd.DataFrame(node_rows).sort_values("strength", ascending=False)
    node_df.to_csv(TAB_DIR / "ggm_node_centrality.csv", index=False)

    r1_df = returns.loc[returns.index <= "2022-12-31"]
    r2_df = returns.loc[returns.index >= "2023-01-01"]
    Z_r1 = (r1_df.values - r1_df.mean().values) / r1_df.std(ddof=0).values
    Z_r2 = (r2_df.values - r2_df.mean().values) / r2_df.std(ddof=0).values
    fit_r1 = fit_glasso_with_ebic(Z_r1, gamma=0.5)["best"]
    fit_r2 = fit_glasso_with_ebic(Z_r2, gamma=0.5)["best"]
    adj1 = np.triu(fit_r1["adj"], 1).astype(bool)
    adj2 = np.triu(fit_r2["adj"], 1).astype(bool)
    jaccard = float(np.sum(adj1 & adj2) / np.sum(adj1 | adj2))

    D_inv = np.diag(1.0 / sd_tr)
    S_tr_ret = np.cov(train_df.values.T, bias=True)
    Theta_mle_ret = np.linalg.inv(S_tr_ret)
    Theta_gl_ret = D_inv @ best["Theta_gl"] @ D_inv
    Theta_refit_ret = D_inv @ best["Theta_refit"] @ D_inv
    Theta_lw_ret = np.linalg.inv(LedoitWolf(assume_centered=False).fit(train_df.values).covariance_)

    static_weights = {
        "等权组合 (1/N)": np.ones(p) / p,
        "样本协方差 MLE": gmvp_weights(Theta_mle_ret),
        "Graphical Lasso": gmvp_weights(Theta_gl_ret),
        "GGM 两步精估 (Alg1)": gmvp_weights(Theta_refit_ret),
        "Ledoit-Wolf 收缩": gmvp_weights(Theta_lw_ret),
    }
    static_metrics = {}
    for name, w in static_weights.items():
        r_oos = pd.Series(test_df.values @ w, index=test_df.index)
        w_mat = np.tile(w, (len(test_df), 1))
        static_metrics[name] = portfolio_metrics(r_oos, w_mat)

    roll_rets, roll_metrics = run_rolling_gmvp_backtest(
        returns, test_start="2024-01-01", alpha_fixed=best["alpha"], window=252, rebal_every=21
    )
    roll_rets.to_csv(TAB_DIR / "oos_rolling_gmvp_returns.csv")
    pd.DataFrame(roll_metrics).T.to_csv(TAB_DIR / "oos_rolling_gmvp_metrics.csv")
    pd.DataFrame(static_metrics).T.to_csv(TAB_DIR / "oos_static_gmvp_metrics.csv")

    boot_roll_mle_vs_ggm = block_bootstrap_vol_test(
        roll_rets["样本协方差 MLE"].values, roll_rets["GGM 两步精估 (Alg1)"].values
    )
    boot_roll_eq_vs_ggm = block_bootstrap_vol_test(
        roll_rets["等权组合 (1/N)"].values, roll_rets["GGM 两步精估 (Alg1)"].values
    )

    plot_fig1_heatmaps(corr_train, pcorr_refit, cols)
    plot_fig2_network(pcorr_refit, cols, node_df)
    plot_fig3_path(path_df, best["alpha"])
    plot_fig4_regimes(fit_r1["pcorr_refit"], fit_r2["pcorr_refit"], cols, jaccard)
    plot_fig5_oos_backtest(roll_rets, roll_metrics)
    plot_fig6_centrality_weights(node_df, static_weights, cols)

    summary = {
        "dataset": {
            "n_total_days": int(len(returns)),
            "n_assets": p,
            "assets": cols,
            "date_start": str(returns.index.min()),
            "date_end": str(returns.index.max()),
            "train_start": str(train_df.index.min()),
            "train_end": str(train_df.index.max()),
            "n_train": int(len(train_df)),
            "test_start": str(test_df.index.min()),
            "test_end": str(test_df.index.max()),
            "n_test": int(len(test_df)),
        },
        "ebic_selected_model": {
            "alpha": best["alpha"],
            "n_edges": best["n_edges"],
            "max_possible_edges": int(p * (p - 1) / 2),
            "sparsity": best["sparsity"],
            "bic": best["bic"],
            "ebic": best["ebic"],
            "cv_5fold_nll": best["cv_nll"],
            "alg1_primal_err": alg1_primal_err,
            "alg1_zero_err": alg1_zero_err,
            "min_eigenvalue_theta_refit": float(np.linalg.eigvalsh(best["Theta_refit"]).min()),
        },
        "path_edge_range": {
            "min_alpha": float(path_df["alpha"].min()),
            "max_edges": int(path_df["n_edges"].max()),
            "max_alpha": float(path_df["alpha"].max()),
            "min_edges": int(path_df["n_edges"].min()),
        },
        "test_nll_comparison": nll_comparison,
        "top_positive_edges": edge_df[edge_df["pcorr_refit"] > 0].head(8).to_dict(orient="records"),
        "top_negative_edges": edge_df[edge_df["pcorr_refit"] < 0].sort_values("pcorr_refit").head(5).to_dict(orient="records"),
        "node_centrality_top5": node_df.head(5).to_dict(orient="records"),
        "node_centrality_all": node_df.to_dict(orient="records"),
        "regime_comparison": {
            "regime1_dates": f"{r1_df.index.min()} ~ {r1_df.index.max()} (n={len(r1_df)})",
            "regime1_alpha": fit_r1["alpha"],
            "regime1_edges": fit_r1["n_edges"],
            "regime2_dates": f"{r2_df.index.min()} ~ {r2_df.index.max()} (n={len(r2_df)})",
            "regime2_alpha": fit_r2["alpha"],
            "regime2_edges": fit_r2["n_edges"],
            "edge_jaccard_similarity": jaccard,
            "n_shared_edges": int(np.sum(adj1 & adj2)),
        },
        "static_gmvp_oos_metrics": static_metrics,
        "rolling_gmvp_oos_metrics": roll_metrics,
        "bootstrap_vol_tests_rolling": {
            "MLE_minus_GGM_Refit": boot_roll_mle_vs_ggm,
            "EqualWeight_minus_GGM_Refit": boot_roll_eq_vs_ggm,
        },
    }

    with open(OUT_DIR / "results_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("=== Version 1 (GGM) Summary ===")
    print(f"Train n={len(train_df)}, Test n={len(test_df)}, EBIC alpha={best['alpha']:.4f}, edges={best['n_edges']}/105 (sparsity={best['sparsity']*100:.1f}%)")
    print(f"Path edges range: {path_df['n_edges'].max()} -> {path_df['n_edges'].min()}")
    print("Alg1 primal err:", alg1_primal_err, "zero err:", alg1_zero_err)
    print("Test NLL:", nll_comparison)
    print("Rolling OOS GMVP metrics:")
    for k, v in roll_metrics.items():
        print(f"  {k}: vol={v['ann_vol_pct']:.2f}%, ret={v['ann_ret_pct']:.2f}%, SR={v['sharpe_rf0']:.2f}, L1={v['avg_l1_leverage']:.2f}")


if __name__ == "__main__":
    main()
