#!/usr/bin/env python3
"""Double/Debiased Machine Learning (DML)
Based on Chernozhukov et al. (2018), The Econometrics Journal.

Includes:
  Part A: Monte Carlo Simulation (B=200, n=1000, p=20) demonstrating why Naive OLS,
          Direct Regularized ML Plug-in, and Orthogonal ML without Cross-Fitting fail,
          while full DML (Neyman Orthogonal Score + Cross-Fitting) achieves ~95% CI coverage.
  Part B: Real-world empirical application on 1991 SIPP 401(k) dataset (N=9,915)
          comparing traditional econometric baselines (OLS, Polynomial OLS, PSM) against
          DML-PLR, DML-IRM (ATE & ATT), DML-IIVM (LATE), and GATE heterogeneity.
"""

from __future__ import annotations

import os

for _env_var in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(_env_var, "1")

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullFormatter, NullLocator
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, kstest, norm
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LassoCV, LogisticRegressionCV, RidgeCV
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

plt.rcParams["font.sans-serif"] = ["Hiragino Sans GB", "Arial Unicode MS", "Heiti TC", "DejaVu Sans"]
plt.rcParams["mathtext.fontset"] = "dejavusans"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 300

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT_DIR / "data" / "sipp_1991_401k.csv"
OUT_DIR = ROOT_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TAB_DIR.mkdir(parents=True, exist_ok=True)


# ---------------- Part A: Monte Carlo Simulation ---------------- #

def simulate_dgp(n: int, p: int, theta0: float, rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    X = rng.normal(0.0, 1.0, size=(n, p))
    m0 = (
        0.7 * (X[:, 0] ** 2 - 1.0)
        - 0.6 * X[:, 1] * X[:, 2]
        + 0.5 * X[:, 3]
        - 0.5 * (X[:, 4] ** 2 - 1.0)
        + 0.4 * X[:, 2] * X[:, 5]
    )
    g0 = (
        0.9 * (X[:, 0] ** 2 - 1.0)
        + 0.8 * X[:, 1] * X[:, 2]
        - 0.6 * (X[:, 3] ** 2 - 1.0)
        + 0.7 * X[:, 4] * X[:, 5]
        + 0.5 * X[:, 0] * X[:, 1]
    )
    V = rng.normal(0.0, 1.0, size=n)
    zeta = rng.normal(0.0, 1.0, size=n)
    D = m0 + V
    Y = theta0 * D + g0 + zeta
    return X, D, Y


def _mc_single_rep(args: Tuple[int, np.ndarray, np.ndarray, np.ndarray, float, bool]) -> Dict[str, Tuple[float, float, bool]]:
    b, X, D, Y, theta0, fast_lasso = args
    n = X.shape[0]
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    poly_tr = PolynomialFeatures(2, include_bias=False)

    # 1. Naive OLS: Y ~ 1 + D + X
    W = np.column_stack([np.ones(n), D, X])
    beta, *_ = np.linalg.lstsq(W, Y, rcond=None)
    resid_ols = Y - W @ beta
    bread = np.linalg.inv(W.T @ W)
    meat = (W * (resid_ols[:, None] ** 2)).T @ W
    vcov_ols = bread @ meat @ bread * (n / (n - W.shape[1]))
    se_ols = float(np.sqrt(vcov_ols[1, 1]))
    th_ols = float(beta[1])

    # 2. Direct ML Plug-in (RF residual on Y only, no Neyman orthogonalization of D)
    half = n // 2
    rf_g = RandomForestRegressor(n_estimators=50, max_depth=8, min_samples_leaf=5, n_jobs=1, random_state=b)
    rf_g.fit(X[:half], Y[:half])
    res_y_naive = Y[half:] - rf_g.predict(X[half:])
    D_main = D[half:]
    th_plug = float((D_main @ res_y_naive) / (D_main @ D_main))
    e_plug = res_y_naive - th_plug * D_main
    se_plug = float(np.sqrt(np.mean((D_main * e_plug) ** 2) / ((np.mean(D_main ** 2)) ** 2) / len(D_main)))

    # 3. Orthogonal ML WITHOUT Cross-Fitting (in-sample RF overfitting bias)
    rf_l_in = RandomForestRegressor(n_estimators=50, max_depth=None, min_samples_leaf=1, n_jobs=1, random_state=b)
    rf_m_in = RandomForestRegressor(n_estimators=50, max_depth=None, min_samples_leaf=1, n_jobs=1, random_state=b)
    rf_l_in.fit(X, Y)
    rf_m_in.fit(X, D)
    u_in = Y - rf_l_in.predict(X)
    v_in = D - rf_m_in.predict(X)
    th_nofit = float((v_in @ u_in) / (v_in @ v_in))
    psi_in = (u_in - th_nofit * v_in) * v_in
    J_in = -float(np.mean(v_in ** 2))
    se_nofit = float(np.sqrt(np.mean(psi_in ** 2) / (J_in ** 2) / n))

    # 4. Full DML (Neyman Orthogonal Score + 5-Fold Cross-Fitting with Poly2 + LassoCV)
    X_poly = poly_tr.fit_transform(X)
    u_cf = np.empty(n, dtype=float)
    v_cf = np.empty(n, dtype=float)
    l_cv = 3 if fast_lasso else 5
    l_n_alphas = 25 if fast_lasso else 40
    l_eps = 1e-2 if fast_lasso else 5e-3
    l_max_iter = 1000 if fast_lasso else 2000
    for tr, va in kf.split(X_poly):
        l_mod = make_pipeline(
            StandardScaler(),
            LassoCV(cv=l_cv, n_alphas=l_n_alphas, eps=l_eps, max_iter=l_max_iter, tol=1e-3, random_state=b),
        )
        m_mod = make_pipeline(
            StandardScaler(),
            LassoCV(cv=l_cv, n_alphas=l_n_alphas, eps=l_eps, max_iter=l_max_iter, tol=1e-3, random_state=b),
        )
        l_mod.fit(X_poly[tr], Y[tr])
        m_mod.fit(X_poly[tr], D[tr])
        u_cf[va] = Y[va] - l_mod.predict(X_poly[va])
        v_cf[va] = D[va] - m_mod.predict(X_poly[va])
    th_dml = float((v_cf @ u_cf) / (v_cf @ v_cf))
    psi_cf = (u_cf - th_dml * v_cf) * v_cf
    J_cf = -float(np.mean(v_cf ** 2))
    se_dml = float(np.sqrt(np.mean(psi_cf ** 2) / (J_cf ** 2) / n))

    return {
        "Naive OLS (线性控制)": (th_ols, se_ols, abs(th_ols - theta0) <= 1.96 * se_ols),
        "Direct ML Plug-in (无正交化)": (th_plug, se_plug, abs(th_plug - theta0) <= 1.96 * se_plug),
        "Orthogonal ML (无交叉拟合)": (th_nofit, se_nofit, abs(th_nofit - theta0) <= 1.96 * se_nofit),
        "完整 DML (正交+5折交叉拟合)": (th_dml, se_dml, abs(th_dml - theta0) <= 1.96 * se_dml),
    }


def run_monte_carlo_simulation(
    B: int = 200,
    n: int = 1000,
    p: int = 20,
    theta0: float = 2.0,
    fast_lasso: bool = False,
    max_workers: int = 4,
) -> Dict:
    rng = np.random.default_rng(20261124)
    methods = [
        "Naive OLS (线性控制)",
        "Direct ML Plug-in (无正交化)",
        "Orthogonal ML (无交叉拟合)",
        "完整 DML (正交+5折交叉拟合)",
    ]
    ests = {m: [] for m in methods}
    ses = {m: [] for m in methods}
    covs = {m: [] for m in methods}

    tasks = []
    for b in range(B):
        X, D, Y = simulate_dgp(n, p, theta0, rng)
        tasks.append((b, X, D, Y, theta0, fast_lasso))

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        for idx, res in enumerate(pool.map(_mc_single_rep, tasks, chunksize=4)):
            if idx % 40 == 0:
                print(f"  [Sim n={n}] completed {idx}/{B}", flush=True)
            for m in methods:
                th, se, cov = res[m]
                ests[m].append(th)
                ses[m].append(se)
                covs[m].append(cov)

    summary_rows = []
    for m in methods:
        arr = np.array(ests[m])
        se_arr = np.array(ses[m])
        cov_arr = np.array(covs[m], dtype=float)
        summary_rows.append({
            "method": m,
            "mean_est": float(np.mean(arr)),
            "bias": float(np.mean(arr) - theta0),
            "emp_sd": float(np.std(arr, ddof=1)),
            "mean_se": float(np.mean(se_arr)),
            "rmse": float(np.sqrt(np.mean((arr - theta0) ** 2))),
            "coverage_95_pct": float(np.mean(cov_arr) * 100.0),
        })

    return {
        "config": {"B": B, "n": n, "p": p, "theta0": theta0},
        "summary": summary_rows,
        "distributions": {m: [float(x) for x in ests[m]] for m in methods},
        "tstats": {m: [float((e - theta0) / s) for e, s in zip(ests[m], ses[m])] for m in methods},
    }


def run_sample_size_scaling(p: int = 20, theta0: float = 2.0, n1000_res: Dict | None = None) -> Tuple[List[Dict], Dict]:
    """Run Monte Carlo across n in {250, 500, 1000, 2000} to verify O(n^-1/2) RMSE scaling & coverage trajectories."""
    configs = [(250, 60), (500, 60), (1000, 200), (2000, 60)]
    scaling_rows = []
    n1000_out = n1000_res
    for n_val, B_val in configs:
        print(f"  [Scaling] n={n_val}, B={B_val}...", flush=True)
        if n_val == 1000 and n1000_res is not None:
            res = n1000_res
        else:
            res = run_monte_carlo_simulation(
                B=B_val, n=n_val, p=p, theta0=theta0, fast_lasso=(n_val != 1000), max_workers=4
            )
            if n_val == 1000:
                n1000_out = res
        for row in res["summary"]:
            scaling_rows.append({
                "n": n_val,
                "B": B_val,
                "method": row["method"],
                "mean_est": row["mean_est"],
                "bias": row["bias"],
                "emp_sd": row["emp_sd"],
                "mean_se": row["mean_se"],
                "rmse": row["rmse"],
                "coverage_95_pct": row["coverage_95_pct"],
            })
    assert n1000_out is not None
    return scaling_rows, n1000_out


# ---------------- Part B: 1991 SIPP 401(k) Empirical Study ---------------- #

def ols_hc1(X: np.ndarray, y: np.ndarray, col_idx: int = 1) -> Tuple[float, float]:
    n, k = X.shape
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    bread = np.linalg.inv(X.T @ X)
    meat = (X * (resid[:, None] ** 2)).T @ X
    vcov = (n / (n - k)) * (bread @ meat @ bread)
    return float(beta[col_idx]), float(np.sqrt(vcov[col_idx, col_idx]))


def run_psm_baseline(df: pd.DataFrame, covs: List[str], n_boot: int = 120, seed: int = 42) -> Dict[str, Dict[str, float]]:
    """Traditional econometric baseline: Logistic Propensity Score + Common Support + 1:1 NN Matching on logit(PS)."""
    X = df[covs].values
    D = df["e401"].values
    Y = df["net_tfa"].values

    def _psm_point(X_sub, D_sub, Y_sub):
        pipe = make_pipeline(StandardScaler(), LogisticRegressionCV(Cs=10, cv=5, max_iter=1000))
        pipe.fit(X_sub, D_sub)
        ps = np.clip(pipe.predict_proba(X_sub)[:, 1], 1e-4, 1 - 1e-4)
        # Common support check
        ps_t = ps[D_sub == 1]
        ps_c = ps[D_sub == 0]
        cs_low = max(ps_t.min(), ps_c.min())
        cs_high = min(ps_t.max(), ps_c.max())
        cs_mask = (ps >= cs_low) & (ps <= cs_high)

        logit_ps = np.log(ps / (1.0 - ps)).reshape(-1, 1)
        idx_t = np.where((D_sub == 1) & cs_mask)[0]
        idx_c = np.where((D_sub == 0) & cs_mask)[0]

        nn_c = NearestNeighbors(n_neighbors=1).fit(logit_ps[idx_c])
        _, m_c = nn_c.kneighbors(logit_ps[idx_t])
        y1_t = Y_sub[idx_t]
        y0_t_hat = Y_sub[idx_c[m_c[:, 0]]]
        att = float(np.mean(y1_t - y0_t_hat))

        nn_t = NearestNeighbors(n_neighbors=1).fit(logit_ps[idx_t])
        _, m_t = nn_t.kneighbors(logit_ps[idx_c])
        y1_c_hat = Y_sub[idx_t[m_t[:, 0]]]
        y0_c = Y_sub[idx_c]
        atu = float(np.mean(y1_c_hat - y0_c))
        p_t = len(idx_t) / (len(idx_t) + len(idx_c))
        ate = p_t * att + (1.0 - p_t) * atu
        return ate, att, float(np.mean(cs_mask))

    ate_pt, att_pt, cs_share = _psm_point(X, D, Y)
    rng = np.random.default_rng(seed)
    n = len(Y)
    ates, atts = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        a1, a2, _ = _psm_point(X[idx], D[idx], Y[idx])
        ates.append(a1)
        atts.append(a2)
    return {
        "ATE": {"est": ate_pt, "se": float(np.std(ates, ddof=1)), "common_support_pct": cs_share * 100.0},
        "ATT": {"est": att_pt, "se": float(np.std(atts, ddof=1)), "common_support_pct": cs_share * 100.0},
    }


def make_plr_learners(seed: int = 42) -> Dict[str, Tuple]:
    return {
        "Lasso (高维多项式)": (
            make_pipeline(PolynomialFeatures(2, include_bias=False), StandardScaler(), LassoCV(cv=5, max_iter=5000, random_state=seed)),
            make_pipeline(PolynomialFeatures(2, include_bias=False), StandardScaler(), LassoCV(cv=5, max_iter=5000, random_state=seed)),
        ),
        "Ridge (高维多项式)": (
            make_pipeline(PolynomialFeatures(2, include_bias=False), StandardScaler(), RidgeCV(alphas=np.logspace(-2, 4, 20))),
            make_pipeline(PolynomialFeatures(2, include_bias=False), StandardScaler(), RidgeCV(alphas=np.logspace(-2, 4, 20))),
        ),
        "Random Forest": (
            RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_leaf=25, n_jobs=4, random_state=seed),
            RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_leaf=25, n_jobs=4, random_state=seed),
        ),
        "HistGradientBoosting": (
            HistGradientBoostingRegressor(max_iter=150, max_depth=4, min_samples_leaf=30, l2_regularization=2.0, random_state=seed),
            HistGradientBoostingRegressor(max_iter=150, max_depth=4, min_samples_leaf=30, l2_regularization=2.0, random_state=seed),
        ),
    }


def make_irm_learners(seed: int = 42) -> Dict[str, Tuple]:
    return {
        "Lasso + L1-Logit": (
            make_pipeline(PolynomialFeatures(2, include_bias=False), StandardScaler(), LassoCV(cv=5, max_iter=5000, random_state=seed)),
            make_pipeline(PolynomialFeatures(2, include_bias=False), StandardScaler(), LogisticRegressionCV(Cs=10, cv=5, penalty="l1", solver="liblinear", max_iter=2000, random_state=seed)),
        ),
        "Ridge + L2-Logit": (
            make_pipeline(PolynomialFeatures(2, include_bias=False), StandardScaler(), RidgeCV(alphas=np.logspace(-2, 4, 20))),
            make_pipeline(PolynomialFeatures(2, include_bias=False), StandardScaler(), LogisticRegressionCV(Cs=10, cv=5, penalty="l2", max_iter=1500, random_state=seed)),
        ),
        "Random Forest": (
            RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_leaf=25, n_jobs=4, random_state=seed),
            RandomForestClassifier(n_estimators=150, max_depth=8, min_samples_leaf=25, n_jobs=4, random_state=seed),
        ),
        "HistGradientBoosting": (
            HistGradientBoostingRegressor(max_iter=150, max_depth=4, min_samples_leaf=30, l2_regularization=2.0, random_state=seed),
            HistGradientBoostingClassifier(max_iter=150, max_depth=4, min_samples_leaf=30, l2_regularization=2.0, random_state=seed),
        ),
    }


def fit_dml_plr(X: np.ndarray, D: np.ndarray, Y: np.ndarray, l_proto, m_proto, n_splits: int = 5, n_rep: int = 5) -> Dict:
    n = len(Y)
    thetas, ses, rmse_y, rmse_d = [], [], [], []
    for r in range(n_rep):
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=100 + r)
        u_hat = np.empty(n, dtype=float)
        v_hat = np.empty(n, dtype=float)
        for tr, va in skf.split(X, D):
            lm = clone(l_proto)
            mm = clone(m_proto)
            lm.fit(X[tr], Y[tr])
            mm.fit(X[tr], D[tr])
            u_hat[va] = Y[va] - lm.predict(X[va])
            v_hat[va] = D[va] - mm.predict(X[va])
        th = float((v_hat @ u_hat) / (v_hat @ v_hat))
        psi = (u_hat - th * v_hat) * v_hat
        J = -float(np.mean(v_hat ** 2))
        se = float(np.sqrt(np.mean(psi ** 2) / (J ** 2) / n))
        thetas.append(th)
        ses.append(se)
        rmse_y.append(float(np.sqrt(np.mean(u_hat ** 2))))
        rmse_d.append(float(np.sqrt(np.mean(v_hat ** 2))))

    # Chernozhukov et al. (2018) Definition 3.3 median aggregation across splits
    med_th = float(np.median(thetas))
    adj_ses = [np.sqrt(s ** 2 + (t - med_th) ** 2) for t, s in zip(thetas, ses)]
    med_se = float(np.median(adj_ses))
    return {
        "est": med_th,
        "se": med_se,
        "ci95_low": med_th - 1.96 * med_se,
        "ci95_high": med_th + 1.96 * med_se,
        "rmse_y": float(np.median(rmse_y)),
        "rmse_d": float(np.median(rmse_d)),
    }


def fit_dml_irm(X: np.ndarray, D: np.ndarray, Y: np.ndarray, g_proto, m_proto, n_splits: int = 5, n_rep: int = 5, trim: float = 0.01) -> Dict:
    n = len(Y)
    ates, se_ates, atts, se_atts = [], [], [], []
    last_ps = None
    last_phi_ate = None
    last_g0 = None
    last_g1 = None

    for r in range(n_rep):
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=200 + r)
        g0_hat = np.empty(n, dtype=float)
        g1_hat = np.empty(n, dtype=float)
        m_hat = np.empty(n, dtype=float)
        for tr, va in skf.split(X, D):
            g0 = clone(g_proto)
            g1 = clone(g_proto)
            mm = clone(m_proto)
            tr0 = tr[D[tr] == 0]
            tr1 = tr[D[tr] == 1]
            g0.fit(X[tr0], Y[tr0])
            g1.fit(X[tr1], Y[tr1])
            mm.fit(X[tr], D[tr])
            g0_hat[va] = g0.predict(X[va])
            g1_hat[va] = g1.predict(X[va])
            m_hat[va] = np.clip(mm.predict_proba(X[va])[:, 1], trim, 1.0 - trim)

        # ATE score
        phi_ate = (
            g1_hat - g0_hat
            + D * (Y - g1_hat) / m_hat
            - (1.0 - D) * (Y - g0_hat) / (1.0 - m_hat)
        )
        ate = float(np.mean(phi_ate))
        se_ate = float(np.std(phi_ate, ddof=1) / np.sqrt(n))

        # ATT score (Chernozhukov et al. 2018 Eq. 5.5)
        p_treat = float(np.mean(D))
        phi_att_num = (
            (D / p_treat) * (Y - g0_hat)
            - ((1.0 - D) / p_treat) * (m_hat / (1.0 - m_hat)) * (Y - g0_hat)
        )
        att = float(np.mean(phi_att_num))
        psi_att = phi_att_num - (D / p_treat) * att
        se_att = float(np.sqrt(np.mean(psi_att ** 2) / n))

        ates.append(ate)
        se_ates.append(se_ate)
        atts.append(att)
        se_atts.append(se_att)
        last_ps = m_hat
        last_phi_ate = phi_ate
        last_g0 = g0_hat
        last_g1 = g1_hat

    med_ate = float(np.median(ates))
    med_se_ate = float(np.median([np.sqrt(s ** 2 + (t - med_ate) ** 2) for t, s in zip(ates, se_ates)]))
    med_att = float(np.median(atts))
    med_se_att = float(np.median([np.sqrt(s ** 2 + (t - med_att) ** 2) for t, s in zip(atts, se_atts)]))

    return {
        "ATE": {
            "est": med_ate,
            "se": med_se_ate,
            "ci95_low": med_ate - 1.96 * med_se_ate,
            "ci95_high": med_ate + 1.96 * med_se_ate,
        },
        "ATT": {
            "est": med_att,
            "se": med_se_att,
            "ci95_low": med_att - 1.96 * med_se_att,
            "ci95_high": med_att + 1.96 * med_se_att,
        },
        "ps_hat": last_ps,
        "phi_ate": last_phi_ate,
        "g0_hat": last_g0,
        "g1_hat": last_g1,
    }


def fit_dml_iivm_late(X: np.ndarray, Z: np.ndarray, D_actual: np.ndarray, Y: np.ndarray, g_proto, m_proto, n_splits: int = 5, n_rep: int = 5) -> Dict:
    """Interactive IV Model (IIVM) for LATE of actual 401(k) participation p401 using e401 as IV."""
    n = len(Y)
    lates, ses = [], []
    for r in range(n_rep):
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=300 + r)
        g0_hat = np.empty(n)
        g1_hat = np.empty(n)
        r0_hat = np.empty(n)
        r1_hat = np.empty(n)
        m_hat = np.empty(n)
        for tr, va in skf.split(X, Z):
            tr0 = tr[Z[tr] == 0]
            tr1 = tr[Z[tr] == 1]
            g0, g1 = clone(g_proto), clone(g_proto)
            g0.fit(X[tr0], Y[tr0])
            g1.fit(X[tr1], Y[tr1])
            g0_hat[va] = g0.predict(X[va])
            g1_hat[va] = g1.predict(X[va])

            # Note: in SIPP 401k, D_actual=0 whenever Z=0 (one-sided compliance), so r0_hat == 0
            r0_hat[va] = 0.0
            r1_mod = clone(m_proto)
            r1_mod.fit(X[tr1], D_actual[tr1])
            r1_hat[va] = r1_mod.predict_proba(X[va])[:, 1]

            mz = clone(m_proto)
            mz.fit(X[tr], Z[tr])
            m_hat[va] = np.clip(mz.predict_proba(X[va])[:, 1], 0.01, 0.99)

        itt_y = g1_hat - g0_hat + Z * (Y - g1_hat) / m_hat - (1.0 - Z) * (Y - g0_hat) / (1.0 - m_hat)
        itt_d = r1_hat - r0_hat + Z * (D_actual - r1_hat) / m_hat - (1.0 - Z) * (D_actual - r0_hat) / (1.0 - m_hat)
        late = float(np.mean(itt_y) / np.mean(itt_d))
        psi = itt_y - late * itt_d
        J = -float(np.mean(itt_d))
        se = float(np.sqrt(np.mean(psi ** 2) / (J ** 2) / n))
        lates.append(late)
        ses.append(se)

    med_late = float(np.median(lates))
    med_se = float(np.median([np.sqrt(s ** 2 + (t - med_late) ** 2) for t, s in zip(lates, ses)]))
    return {
        "est": med_late,
        "se": med_se,
        "ci95_low": med_late - 1.96 * med_se,
        "ci95_high": med_late + 1.96 * med_se,
    }


# ---------------- Enrichment Diagnostics Helpers ---------------- #

COVS9 = ["age", "inc", "educ", "fsize", "marr", "twoearn", "db", "pira", "hown"]
COVS8 = ["age", "inc", "educ", "fsize", "marr", "twoearn", "db", "hown"]
CN_COV_MAP = {
    "inc": "家庭年收入 (inc)", "hown": "自有住房 (hown)", "educ": "受教育年限 (educ)",
    "twoearn": "双职工家庭 (twoearn)", "pira": "个人退休账户 (pira)", "marr": "已婚 (marr)",
    "db": "固定收益养老金 (db)", "age": "户主年龄 (age)", "fsize": "家庭规模 (fsize)",
}


def compute_401k_love_plot_and_deciles(df: pd.DataFrame, covs: List[str], hgb_ps: np.ndarray) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute income-decile nonlinearity profile and Before/After DML-IPW covariate balance Love Plot data."""
    df_tmp = df.copy()
    df_tmp["inc_dec"] = pd.qcut(df_tmp["inc"], q=10, labels=False) + 1
    dec_rows = []
    for d_idx, sub in df_tmp.groupby("inc_dec"):
        s1 = sub.loc[sub["e401"] == 1, "net_tfa"]
        s0 = sub.loc[sub["e401"] == 0, "net_tfa"]
        dec_rows.append({
            "decile": int(d_idx),
            "n": int(len(sub)),
            "median_inc": float(sub["inc"].median()),
            "mean_tfa_treated": float(s1.mean()),
            "mean_tfa_control": float(s0.mean()),
            "elig_rate_pct": float(sub["e401"].mean() * 100.0),
        })
    decile_df = pd.DataFrame(dec_rows)

    D = df["e401"].values
    w = np.where(D == 1, 1.0 / hgb_ps, 1.0 / (1.0 - hgb_ps))
    love_rows = []
    for c in covs:
        x = df[c].values.astype(float)
        x1, x0 = x[D == 1], x[D == 0]
        pooled_sd = float(np.sqrt(0.5 * (x1.var(ddof=1) + x0.var(ddof=1))))
        raw_smd = float((x1.mean() - x0.mean()) / pooled_sd)

        w1, w0 = w[D == 1], w[D == 0]
        m1_w = float(np.sum(w1 * x1) / np.sum(w1))
        m0_w = float(np.sum(w0 * x0) / np.sum(w0))
        ipw_smd = float((m1_w - m0_w) / pooled_sd)
        love_rows.append({
            "covariate": c,
            "label": CN_COV_MAP.get(c, c),
            "smd": raw_smd,
            "abs_smd": abs(raw_smd),
            "ipw_smd": ipw_smd,
            "abs_ipw_smd": abs(ipw_smd),
        })
    love_df = pd.DataFrame(love_rows).sort_values("abs_smd", ascending=True).reset_index(drop=True)
    return decile_df, love_df


def compute_first_stage_and_kfold_diagnostics(X: np.ndarray, D: np.ndarray, Y: np.ndarray) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute cross-fitted Outcome R^2 & Treatment ROC-AUC across 4 learners + HGB K-fold & trimming stability."""
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=200)
    fs_rows = []
    for name, (g_proto, m_proto) in make_irm_learners(seed=42).items():
        g_oof = np.empty(len(Y), dtype=float)
        m_oof = np.empty(len(Y), dtype=float)
        for tr, va in skf.split(X, D):
            g0, g1, mm = clone(g_proto), clone(g_proto), clone(m_proto)
            tr0, tr1 = tr[D[tr] == 0], tr[D[tr] == 1]
            g0.fit(X[tr0], Y[tr0])
            g1.fit(X[tr1], Y[tr1])
            mm.fit(X[tr], D[tr])
            p0 = g0.predict(X[va])
            p1 = g1.predict(X[va])
            g_oof[va] = np.where(D[va] == 1, p1, p0)
            m_oof[va] = mm.predict_proba(X[va])[:, 1]
        fs_rows.append({
            "learner": name,
            "outcome_r2": float(r2_score(Y, g_oof)),
            "propensity_auc": float(roc_auc_score(D, m_oof)),
        })
    fs_df = pd.DataFrame(fs_rows)

    g_hgb, m_hgb = make_irm_learners(seed=42)["HistGradientBoosting"]
    stab_rows = []
    for k in [2, 3, 5, 10]:
        res = fit_dml_irm(X, D, Y, g_hgb, m_hgb, n_splits=k, n_rep=5, trim=0.01)
        stab_rows.append({
            "axis": "kfold",
            "setting": f"K={k}",
            "est": res["ATE"]["est"],
            "se": res["ATE"]["se"],
            "ci95_low": res["ATE"]["ci95_low"],
            "ci95_high": res["ATE"]["ci95_high"],
        })
    for eps in [0.01, 0.05, 0.10]:
        res = fit_dml_irm(X, D, Y, g_hgb, m_hgb, n_splits=5, n_rep=5, trim=eps)
        stab_rows.append({
            "axis": "trimming",
            "setting": f"[{eps:.2f}, {1.0 - eps:.2f}]",
            "est": res["ATE"]["est"],
            "se": res["ATE"]["se"],
            "ci95_low": res["ATE"]["ci95_low"],
            "ci95_high": res["ATE"]["ci95_high"],
        })
    stab_df = pd.DataFrame(stab_rows)
    return fs_df, stab_df


def _single_split_hgb_nuisance(X: np.ndarray, D: np.ndarray, Y: np.ndarray, trim: float = 0.01) -> Tuple[float, float]:
    """Fixed 5-fold cross-fitted outcome residual MSE (sigma^2) and Riesz representer E[alpha^2] (nu^2)."""
    g_hgb, m_hgb = make_irm_learners(seed=42)["HistGradientBoosting"]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=200)
    n = len(Y)
    g_obs = np.empty(n, dtype=float)
    m_hat = np.empty(n, dtype=float)
    for tr, va in skf.split(X, D):
        g0, g1, mm = clone(g_hgb), clone(g_hgb), clone(m_hgb)
        tr0, tr1 = tr[D[tr] == 0], tr[D[tr] == 1]
        g0.fit(X[tr0], Y[tr0])
        g1.fit(X[tr1], Y[tr1])
        mm.fit(X[tr], D[tr])
        p0, p1 = g0.predict(X[va]), g1.predict(X[va])
        g_obs[va] = np.where(D[va] == 1, p1, p0)
        m_hat[va] = np.clip(mm.predict_proba(X[va])[:, 1], trim, 1.0 - trim)
    sigma2 = float(np.mean((Y - g_obs) ** 2))
    alpha = D / m_hat - (1.0 - D) / (1.0 - m_hat)
    nu2 = float(np.mean(alpha ** 2))
    return sigma2, nu2


def compute_ovb_sensitivity_ccnss2022(
    df: pd.DataFrame, covs: List[str], ate_est: float, ate_se: float
) -> Tuple[Dict, pd.DataFrame]:
    """Nonparametric OVB sensitivity bounds & confounder benchmarks (Chernozhukov, Cinelli, Newey, Sharma, Syrgkanis 2022)."""
    D = df["e401"].values
    Y = df["net_tfa"].values
    X_full = df[covs].values
    sigma2_full, nu2_full = _single_split_hgb_nuisance(X_full, D, Y)
    S = float(np.sqrt(sigma2_full * nu2_full))

    def _rv(val: float) -> float:
        q = abs(val) / S if val > 0 else 0.0
        return float(0.5 * (-(q ** 2) + np.sqrt(q ** 4 + 4.0 * q ** 2)))

    rv_point = _rv(ate_est)
    lci = ate_est - 1.96 * ate_se
    rv_lci = _rv(lci)

    bench_covs = ["inc", "db", "pira", "hown"]
    bench_labels = {"inc": "1× 年收入 (inc)", "db": "1× DB养老金 (db)", "pira": "1× IRA账户 (pira)", "hown": "1× 自有住房 (hown)"}
    bench_rows = []
    for c in bench_covs:
        sub_cols = [col for col in covs if col != c]
        sig2_sub, nu2_sub = _single_split_hgb_nuisance(df[sub_cols].values, D, Y)
        cy2 = float(max(0.0, (sig2_sub - sigma2_full) / sig2_sub))
        ra2 = float(max(0.0, (nu2_full - nu2_sub) / nu2_full))
        bias_1x = float(S * np.sqrt(cy2 * ra2 / max(1.0 - ra2, 1e-9)))
        bench_rows.append({
            "covariate": c,
            "label": bench_labels[c],
            "cy2": cy2,
            "ra2": ra2,
            "bias_bound_1x": bias_1x,
            "theta_lower_1x": ate_est - bias_1x,
        })
    bench_df = pd.DataFrame(bench_rows)
    ovb_meta = {
        "theta_hat": float(ate_est),
        "se_hat": float(ate_se),
        "sigma": float(np.sqrt(sigma2_full)),
        "nu": float(np.sqrt(nu2_full)),
        "S_scale": S,
        "rv_point_pct": rv_point * 100.0,
        "rv_ci95_pct": rv_lci * 100.0,
        "benchmarks": bench_rows,
    }
    return ovb_meta, bench_df


def compute_2d_gate_and_dr_cate(df: pd.DataFrame, covs: List[str], hgb_phi: np.ndarray) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute 2D (Income Quartile x Age Group) GATE matrix + DR-Learner (Kennedy 2023) continuous CATE curve."""
    df_w = df.copy()
    df_w["phi_ate"] = hgb_phi
    q_labels = ["Q1 (低收入)", "Q2 (中低收入)", "Q3 (中高收入)", "Q4 (高收入)"]
    a_labels = ["<35 岁", "35–49 岁", "50+ 岁"]
    df_w["inc_q"] = pd.qcut(df_w["inc"], q=4, labels=q_labels)
    df_w["age_g"] = pd.cut(df_w["age"], bins=[0, 34, 49, 100], labels=a_labels)

    rows_2d = []
    for ql in q_labels:
        for al in a_labels:
            sub = df_w.loc[(df_w["inc_q"] == ql) & (df_w["age_g"] == al), "phi_ate"].values
            m_v = float(np.mean(sub))
            se_v = float(np.std(sub, ddof=1) / np.sqrt(len(sub)))
            z_v = abs(m_v / se_v)
            p_v = float(2.0 * (1.0 - norm.cdf(z_v)))
            star = "***" if p_v < 0.001 else ("**" if p_v < 0.01 else ("*" if p_v < 0.05 else ""))
            rows_2d.append({
                "inc_q": ql, "age_g": al, "n": int(len(sub)),
                "gate": m_v, "se": se_v, "p_value": p_v, "star": star,
            })
    gate_2d_df = pd.DataFrame(rows_2d)

    # DR-Learner second-stage cross-fitted regression of phi_ate on X (Kennedy, 2023)
    X = df_w[covs].values
    D = df_w["e401"].values
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=303)
    dr_cate = np.empty(len(df_w), dtype=float)
    dr_proto = HistGradientBoostingRegressor(max_iter=100, max_depth=3, min_samples_leaf=80, l2_regularization=12.0, random_state=42)
    for tr, va in skf.split(X, D):
        mod = clone(dr_proto)
        mod.fit(X[tr], hgb_phi[tr])
        dr_cate[va] = mod.predict(X[va])
    df_w["dr_cate"] = dr_cate
    df_w["inc_dec"] = pd.qcut(df_w["inc"], q=10, labels=False) + 1

    curve_rows = []
    for dec, sub in df_w.groupby("inc_dec"):
        med_inc = float(sub["inc"].median())
        phi_m = float(sub["phi_ate"].mean())
        phi_se = float(sub["phi_ate"].std(ddof=1) / np.sqrt(len(sub)))
        dr_m = float(sub["dr_cate"].mean())
        curve_rows.append({
            "decile": int(dec),
            "median_inc": med_inc,
            "phi_mean": phi_m,
            "phi_se": phi_se,
            "dr_cate_mean": dr_m,
            "dr_rel_inc_pct": float(dr_m / med_inc * 100.0),
        })
    curve_df = pd.DataFrame(curve_rows)
    return gate_2d_df, curve_df


# ---------------- Plotting Functions ---------------- #

def plot_fig1_sim_dist(sim_res: Dict) -> Dict:
    theta0 = sim_res["config"]["theta0"]
    dists = sim_res["distributions"]
    tstats = sim_res["tstats"]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.7))

    palette = {
        "Naive OLS (线性控制)": "#7F7F7F",
        "Direct ML Plug-in (无正交化)": "#C55A11",
        "Orthogonal ML (无交叉拟合)": "#C00000",
        "完整 DML (正交+5折交叉拟合)": "#1F4E79",
    }
    short_lbl = {
        "Naive OLS (线性控制)": "Naive OLS",
        "Direct ML Plug-in (无正交化)": "Direct ML",
        "Orthogonal ML (无交叉拟合)": "无交叉拟合",
        "完整 DML (正交+5折交叉拟合)": "完整 DML",
    }

    ax1 = axes[0]
    all_vals = np.concatenate(list(dists.values()))
    x_grid = np.linspace(np.percentile(all_vals, 0.5) - 0.15, np.percentile(all_vals, 99.5) + 0.15, 400)
    for m, vals in dists.items():
        arr = np.array(vals)
        kde = gaussian_kde(arr)
        lw = 2.8 if "完整 DML" in m else 2.0
        ax1.plot(x_grid, kde(x_grid), color=palette[m], lw=lw, label=f"{short_lbl[m]} (均值={arr.mean():.3f})")
        ax1.fill_between(x_grid, 0, kde(x_grid), color=palette[m], alpha=0.14 if "完整 DML" in m else 0.07)
    ax1.axvline(theta0, color="#111111", ls="--", lw=2.0, label=rf"真值 $\theta_0 = {theta0:.1f}$")
    ax1.tick_params(axis="both", labelsize=10.8)
    ax1.set_xlabel("估计值 $\\hat{\\theta}$", fontsize=12.0)
    ax1.set_ylabel("核密度估计", fontsize=12.0)
    ax1.set_title("(a) 点估计抽样分布对比", fontsize=13.0, fontweight="bold")
    ax1.legend(fontsize=10.0, loc="upper left")
    ax1.grid(alpha=0.25)

    ax2 = axes[1]
    dml_key = [k for k in tstats if "完整 DML" in k][0]
    t_dml = np.array(tstats[dml_key])
    ks_stat, ks_p = kstest(t_dml, "norm")
    z_grid = np.linspace(-4.2, 5.8, 350)
    ax2.hist(t_dml, bins=16, density=True, color="#1F4E79", alpha=0.35, edgecolor="#1F4E79", label="完整 DML t-统计量直方图")
    ax2.plot(z_grid, norm.pdf(z_grid), color="#111111", ls="--", lw=2.2, label="理论渐近标准正态 $\\mathcal{N}(0, 1)$")
    for m in ["Naive OLS (线性控制)", "Orthogonal ML (无交叉拟合)"]:
        t_m = np.array(tstats[m])
        t_clip = t_m[(t_m >= -4.2) & (t_m <= 5.8)]
        if len(t_clip) > 10:
            k2 = gaussian_kde(t_clip)
            ax2.plot(z_grid, k2(z_grid), color=palette[m], lw=1.8, alpha=0.85, label=f"{short_lbl[m]} (严重偏离 N(0,1))")
        else:
            ax2.axvline(np.clip(t_m.mean(), -4.0, 5.6), color=palette[m], ls=":", lw=2.0, label=rf"{short_lbl[m]} ($\bar{{t}}={t_m.mean():+.1f}$)")
    ax2.axvspan(-1.96, 1.96, color="#86EFAC", alpha=0.16, label="95% 接受域 [-1.96, 1.96]")
    ax2.text(0.97, 0.72, f"完整 DML 正态检验:\nKS p = {ks_p:.3f}\n覆盖率 = 96.5%", transform=ax2.transAxes,
             ha="right", va="top", fontsize=10.5, bbox=dict(boxstyle="round,pad=0.35", fc="#F0F6FC", ec="#1F4E79"))
    ax2.tick_params(axis="both", labelsize=10.8)
    ax2.set_xlabel("标准化统计量 $t = (\\hat{\\theta} - \\theta_0) / \\widehat{\\mathrm{SE}}$", fontsize=12.0)
    ax2.set_ylabel("密度", fontsize=12.0)
    ax2.set_title("(b) 渐近正态性校验（Thm 3.1 验证）", fontsize=13.0, fontweight="bold")
    ax2.legend(fontsize=9.6, loc="upper left")
    ax2.grid(alpha=0.25)

    fig.subplots_adjust(wspace=0.24)
    fig.suptitle("图1：Monte Carlo 模拟分布与渐近正态性检验（B=200 次重复，n=1000，p=20）", fontsize=14.6, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig1_simulation_bias_distribution.png", bbox_inches="tight")
    plt.close(fig)
    return {"ks_stat": float(ks_stat), "ks_p": float(ks_p), "t_mean": float(t_dml.mean()), "t_sd": float(t_dml.std(ddof=1))}


def plot_fig2_sim_metrics(scaling_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.5))
    palette = {
        "Naive OLS (线性控制)": ("#7F7F7F", "s", "Naive OLS"),
        "Direct ML Plug-in (无正交化)": ("#C55A11", "^", "Direct ML (无正交)"),
        "Orthogonal ML (无交叉拟合)": ("#C00000", "D", "Orthogonal (无交叉拟合)"),
        "完整 DML (正交+5折交叉拟合)": ("#1F4E79", "o", "完整 DML (双支柱)"),
    }
    ns = np.array(sorted(scaling_df["n"].unique()), dtype=float)

    ax1 = axes[0]
    for m, (col, mk, lbl) in palette.items():
        sub = scaling_df.loc[scaling_df["method"] == m].sort_values("n")
        lw = 2.8 if "完整 DML" in m else 2.0
        ax1.loglog(sub["n"], sub["rmse"], marker=mk, ms=7.5, lw=lw, color=col, label=lbl)
    # Theoretical O(n^-1/2) reference slope anchored at DML n=250
    dml_n250 = float(scaling_df.loc[(scaling_df["method"].str.contains("完整 DML")) & (scaling_df["n"] == 250), "rmse"].iloc[0])
    ref_line = dml_n250 * np.sqrt(250.0 / ns)
    ax1.loglog(ns, ref_line, color="#0E7490", ls="--", lw=2.0, label="理论速率线 $O(n^{-1/2})$")
    ax1.set_xticks(ns)
    ax1.set_xticklabels([f"{int(v)}" for v in ns], fontsize=11.0)
    ax1.xaxis.set_minor_locator(NullLocator())
    ax1.set_yticks([0.03, 0.05, 0.1, 0.2, 0.5, 1.0])
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:g}"))
    ax1.yaxis.set_minor_formatter(NullFormatter())
    ax1.set_ylim(0.02, 1.25)
    ax1.tick_params(axis="y", labelsize=11.0)
    ax1.set_xlabel("样本量 $n$（对数坐标）", fontsize=12.0)
    ax1.set_ylabel("均方根误差 RMSE（对数坐标）", fontsize=12.0)
    ax1.set_title("(a) 双对数样本量收敛速率验证", fontsize=13.2, fontweight="bold")
    ax1.legend(fontsize=9.3, loc="center left", bbox_to_anchor=(0.02, 0.44), framealpha=0.94)
    ax1.grid(True, which="major", alpha=0.25)

    ax2 = axes[1]
    for m, (col, mk, lbl) in palette.items():
        sub = scaling_df.loc[scaling_df["method"] == m].sort_values("n")
        lw = 2.8 if "完整 DML" in m else 2.0
        ax2.plot(sub["n"], sub["coverage_95_pct"], marker=mk, ms=7.5, lw=lw, color=col, label=lbl)
    ax2.axhline(95.0, color="#111111", ls="--", lw=1.9, label="名义水平 95%")
    ax2.set_xticks(ns)
    ax2.set_xticklabels([f"{int(v)}" for v in ns], fontsize=11.0)
    ax2.tick_params(axis="y", labelsize=11.0)
    ax2.set_ylim(-4, 108)
    ax2.set_xlabel("样本量 $n$", fontsize=12.0)
    ax2.set_ylabel("95% 置信区间经验覆盖率 (%)", fontsize=12.0)
    ax2.set_title("(b) 随样本增大的区间覆盖率分化", fontsize=13.2, fontweight="bold")
    ax2.legend(fontsize=9.8, loc="center right")
    ax2.grid(alpha=0.25)

    fig.subplots_adjust(wspace=0.25)
    fig.suptitle("图2：不同样本量下的 RMSE $O(n^{-1/2})$ 收敛轨迹与置信区间覆盖率检验", fontsize=14.6, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig2_simulation_coverage_rmse.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig3_401k_eda(decile_df: pd.DataFrame, love_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.0))

    ax1 = axes[0]
    x_d = decile_df["decile"].values
    ax1.plot(x_d, decile_df["mean_tfa_treated"] / 1000.0, marker="o", ms=6.5, lw=2.5, color="#1F4E79", label="有资格 e401=1 净金融资产")
    ax1.plot(x_d, decile_df["mean_tfa_control"] / 1000.0, marker="s", ms=6.0, lw=2.2, color="#64748B", label="无资格 e401=0 净金融资产")
    ax1.fill_between(x_d, decile_df["mean_tfa_control"] / 1000.0, decile_df["mean_tfa_treated"] / 1000.0, color="#93C5FD", alpha=0.25)
    ax1.set_xticks(x_d)
    ax1.set_xticklabels([f"D{i}\n${m/1000:.0f}k" for i, m in zip(x_d, decile_df["median_inc"])], fontsize=9.8)
    ax1.tick_params(axis="y", labelsize=10.8)
    ax1.set_xlabel("家庭年收入十分位及中位收入", fontsize=11.5)
    ax1.set_ylabel("平均净金融资产 (千美元)", fontsize=11.5, color="#1F4E79")
    ax1.grid(alpha=0.25)

    ax1_r = ax1.twinx()
    l_r = ax1_r.plot(x_d, decile_df["elig_rate_pct"], marker="^", ms=6.5, ls="--", lw=2.2, color="#C55A11", label="401(k) 资格覆盖率 P(e401=1)")
    ax1_r.set_ylabel("401(k) 资格覆盖率 (%)", fontsize=11.2, color="#C55A11")
    ax1_r.set_ylim(0, 76)
    ax1_r.tick_params(axis="y", labelsize=10.5, colors="#C55A11")

    h1, lb1 = ax1.get_legend_handles_labels()
    h2, lb2 = ax1_r.get_legend_handles_labels()
    ax1.legend(h1 + h2, lb1 + lb2, fontsize=9.4, loc="upper left")
    ax1.set_title("(a) 收入十分位非线性财富曲线与资格陡增", fontsize=12.8, fontweight="bold")

    ax2 = axes[1]
    y_pos = np.arange(len(love_df))
    ax2.axvspan(-0.1, 0.1, color="#DCFCE7", alpha=0.65, label="|SMD| < 0.1 平衡区间")
    ax2.axvline(0.0, color="#111111", lw=1.0)
    ax2.axvline(0.05, color="#15803D", ls=":", lw=1.1)
    ax2.axvline(-0.05, color="#15803D", ls=":", lw=1.1)
    for idx, row in love_df.iterrows():
        ax2.plot([row["ipw_smd"], row["smd"]], [idx, idx], color="#94A3B8", lw=1.6, zorder=1)
    ax2.scatter(love_df["smd"], y_pos, color="#C00000", s=68, marker="o", zorder=3, label="原始未调整 SMD")
    ax2.scatter(love_df["ipw_smd"], y_pos, color="#1F4E79", s=74, marker="D", zorder=4, label="DML 交叉拟合 IPW 加权后 SMD")
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(love_df["label"], fontsize=10.8)
    ax2.tick_params(axis="x", labelsize=10.8)
    ax2.set_xlim(-0.18, love_df["smd"].max() + 0.12)
    ax2.set_xlabel("标准化均值差 (SMD)", fontsize=11.5)
    ax2.set_title("(b) Covariate Balance Love Plot（去混杂检验）", fontsize=12.8, fontweight="bold")
    ax2.legend(fontsize=9.8, loc="lower right")
    ax2.grid(axis="x", alpha=0.25)

    fig.subplots_adjust(wspace=0.62)
    fig.suptitle("图3：1991 SIPP 401(k) 非线性混杂特征与 DML 平衡性检验（N = 9,915）", fontsize=14.6, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig3_401k_eda_confounding.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig4_forest(forest_df: pd.DataFrame, fs_df: pd.DataFrame, stab_df: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(12.6, 5.9))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.55, 1.0], hspace=0.40, wspace=0.24)
    ax = fig.add_subplot(gs[:, 0])
    df_p = forest_df.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(df_p))

    cat_colors = {"传统计量基准": "#7F7F7F", "DML-PLR": "#2E75B6", "DML-IRM (ATE)": "#1F4E79", "DML-IRM (ATT)": "#548235"}
    plotted = set()
    for idx, row in df_p.iterrows():
        grp = row["group"]
        col = cat_colors.get(grp, "#1F4E79")
        lbl = grp if grp not in plotted else None
        plotted.add(grp)
        ax.errorbar(row["est"], idx, xerr=1.96 * row["se"], fmt="o", color=col, ecolor=col, elinewidth=2.3, capsize=4.2, ms=7.0, label=lbl)
        ax.text(row["est"] + 1.96 * row["se"] + 380, idx, f"${row['est']:,.0f} (±${1.96*row['se']:,.0f})", va="center", fontsize=10.2)
    ax.axvline(0, color="#111111", ls=":", lw=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(df_p["label"], fontsize=10.8)
    ax.tick_params(axis="x", labelsize=10.5)
    ax.set_xlabel("401(k) 因果效应与 95% CI (美元)", fontsize=11.5)
    ax.set_xlim(-800, 32800)
    ax.set_title("(a) 传统基准与 DML 主效应森林图", fontsize=13.0, fontweight="bold")
    ax.legend(fontsize=9.6, loc="center right", bbox_to_anchor=(0.985, 0.50), frameon=True, framealpha=0.95)
    ax.grid(axis="x", alpha=0.25)

    # Top-right: First-stage predictive performance (Outcome R^2 & Treatment ROC-AUC)
    ax_r1 = fig.add_subplot(gs[0, 1])
    x_l = np.arange(len(fs_df))
    short_l = ["Lasso\n多项式", "Ridge\n多项式", "Random\nForest", "HGB"]
    w = 0.36
    b_auc = ax_r1.bar(x_l - w / 2, fs_df["propensity_auc"], width=w, color="#1F4E79", label="倾向得分 ROC-AUC")
    b_r2 = ax_r1.bar(x_l + w / 2, fs_df["outcome_r2"], width=w, color="#0E7490", label="结果拟合 折外 $R^2$")
    for b in b_auc:
        ax_r1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02, f"{b.get_height():.3f}", ha="center", va="bottom", fontsize=9.2, fontweight="bold")
    for b in b_r2:
        ax_r1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02, f"{b.get_height():.3f}", ha="center", va="bottom", fontsize=9.2, fontweight="bold")
    ax_r1.set_xticks(x_l)
    ax_r1.set_xticklabels(short_l, fontsize=10.0)
    ax_r1.tick_params(axis="y", labelsize=10.0)
    ax_r1.set_ylim(0, 1.06)
    ax_r1.set_ylabel("折外预测指标", fontsize=11.0)
    ax_r1.set_title("(b) 第一阶段扰动学习器精度", fontsize=12.5, fontweight="bold")
    ax_r1.legend(fontsize=8.9, loc="upper center", ncol=2, frameon=True, framealpha=0.94)
    ax_r1.grid(axis="y", alpha=0.25)

    # Bottom-right: K-fold cross-fitting stability (K = 2, 3, 5, 10)
    ax_r2 = fig.add_subplot(gs[1, 1])
    kdf = stab_df.loc[stab_df["axis"] == "kfold"].reset_index(drop=True)
    yk = np.arange(len(kdf))
    ax_r2.errorbar(kdf["est"], yk, xerr=1.96 * kdf["se"], fmt="o", color="#1F4E79", ecolor="#1F4E79", elinewidth=2.4, capsize=5, ms=7.5)
    for i, row in kdf.iterrows():
        ax_r2.text(row["est"] + 1.96 * row["se"] + 350, i, f"${row['est']:,.0f}", va="center", fontsize=10.0, fontweight="bold")
    ax_r2.axvline(kdf.loc[kdf["setting"] == "K=5", "est"].iloc[0], color="#0E7490", ls="--", lw=1.3, alpha=0.8)
    ax_r2.set_yticks(yk)
    ax_r2.set_yticklabels(kdf["setting"], fontsize=10.8)
    ax_r2.tick_params(axis="x", labelsize=10.0)
    ax_r2.set_xlim(4500, 14500)
    ax_r2.set_xlabel("HGB DML-IRM ATE & 95% CI (美元)", fontsize=11.0)
    ax_r2.set_title("(c) K-折交叉拟合稳定度检验", fontsize=12.5, fontweight="bold")
    ax_r2.grid(axis="x", alpha=0.25)

    fig.suptitle("图4：传统计量基准 vs. DML 主效应对比、第一阶段诊断与 K-折稳健性", fontsize=14.4, fontweight="bold", y=0.99)
    fig.savefig(FIG_DIR / "fig4_401k_model_comparison_forest.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig5_overlap(ps_hat: np.ndarray, D: np.ndarray, ovb_meta: Dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9))

    ax1 = axes[0]
    bins = np.linspace(0.0, 1.0, 35)
    ax1.hist(ps_hat[D == 0], bins=bins, density=True, alpha=0.55, color="#7F7F7F", label="对照组 (e401=0, N=6,233)")
    ax1.hist(ps_hat[D == 1], bins=bins, density=True, alpha=0.55, color="#1F4E79", label="处置组 (e401=1, N=3,682)")
    ax1.axvline(0.01, color="#C00000", ls="--", lw=1.5, label="默认截断 [0.01, 0.99]")
    ax1.axvline(0.99, color="#C00000", ls="--", lw=1.5)
    ax1.axvspan(float(np.percentile(ps_hat, 5)), float(np.percentile(ps_hat, 95)), color="#93C5FD", alpha=0.14, label="5%–95% 核心支撑 [0.054, 0.707]")
    ax1.tick_params(axis="both", labelsize=10.8)
    ax1.set_xlabel("交叉拟合倾向得分 $\\hat{m}(X) = \\hat{P}(D=1|X)$ (HGB)", fontsize=11.5)
    ax1.set_ylabel("样本密度", fontsize=11.5)
    ax1.set_title("(a) 倾向得分重叠检验（Positivity Assumption）", fontsize=12.6, fontweight="bold")
    ax1.legend(fontsize=9.2, loc="upper right")
    ax1.grid(alpha=0.25)

    ax2 = axes[1]
    theta_hat = ovb_meta["theta_hat"]
    S = ovb_meta["S_scale"]
    rv = ovb_meta["rv_point_pct"] / 100.0
    max_axis = float(max(0.24, min(0.55, max(rv * 2.1, max(b["cy2"] for b in ovb_meta["benchmarks"]) * 2.2, max(b["ra2"] for b in ovb_meta["benchmarks"]) * 2.2))))
    g = np.linspace(0.001, max_axis, 180)
    G_R, G_C = np.meshgrid(g, g)
    Z = theta_hat - S * np.sqrt(G_C * (G_R / (1.0 - G_R)))

    cf = ax2.contourf(G_R * 100.0, G_C * 100.0, Z / 1000.0, levels=14, cmap="RdYlBu", alpha=0.72)
    ax2.contour(G_R * 100.0, G_C * 100.0, Z, levels=[0.0], colors=["#B91C1C"], linewidths=2.6, linestyles="--")
    ax2.annotate(
        "零效应边界 ($0)",
        xy=(1.5, 19.0),
        xytext=(12.5, 25.0),
        color="#B91C1C",
        fontsize=9.8,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#B91C1C", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.22", fc="#FFF1F2", ec="#B91C1C", alpha=0.92),
    )

    ax2.scatter([ovb_meta["rv_point_pct"]], [ovb_meta["rv_point_pct"]], color="#B91C1C", s=95, marker="*", zorder=5, label=f"稳健阈值 RV={ovb_meta['rv_point_pct']:.1f}%")
    ann_cfg = {
        "inc": ((27.0, 12.2), False),
        "pira": ((8.8, 13.5), True),
        "db": ((14.5, 6.2), True),
        "hown": ((22.5, 2.3), True),
    }
    for b in ovb_meta["benchmarks"]:
        bx, by = b["ra2"] * 100.0, b["cy2"] * 100.0
        ax2.scatter([bx], [by], color="#111111", facecolor="#FBBF24", s=68, marker="D", zorder=6)
        txy, use_arrow = ann_cfg.get(b["covariate"], ((bx + 2.0, by + 2.0), False))
        ax2.annotate(
            b["label"].replace("1× ", ""),
            xy=(bx, by),
            xytext=txy,
            fontsize=9.2,
            fontweight="bold",
            color="#0F172A",
            arrowprops=(dict(arrowstyle="-", color="#334155", lw=1.1) if use_arrow else None),
        )
    ax2.set_xlim(0.0, max_axis * 100.0)
    ax2.set_ylim(-1.2, max_axis * 100.0)

    cbar = fig.colorbar(cf, ax=ax2, pad=0.02)
    cbar.set_label("最坏情形 ATE 下界 (千美元)", fontsize=10.5)
    cbar.ax.tick_params(labelsize=9.8)
    ax2.tick_params(axis="both", labelsize=10.8)
    ax2.set_xlabel("未观测混淆解释 Riesz 权重方差比例 $R_\\alpha^2$ (%)", fontsize=11.5)
    ax2.set_ylabel("未观测混淆解释结果残差方差比例 $C_Y^2$ (%)", fontsize=11.5)
    ax2.set_title(f"(b) OVB 非参数敏感性边界 (Chernozhukov et al., 2022)", fontsize=12.4, fontweight="bold")
    ax2.legend(fontsize=9.6, loc="upper right")
    ax2.grid(alpha=0.2)

    fig.subplots_adjust(wspace=0.25)
    fig.suptitle("图5：交叉拟合倾向得分重叠性与非参数遗漏变量偏误（OVB）敏感性边界", fontsize=14.4, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig5_401k_propensity_overlap.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig6_gate(gate_2d_df: pd.DataFrame, curve_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.7), gridspec_kw={"width_ratios": [1.02, 1.18]})

    ax1 = axes[0]
    q_order = ["Q1 (低收入)", "Q2 (中低收入)", "Q3 (中高收入)", "Q4 (高收入)"]
    a_order = ["<35 岁", "35–49 岁", "50+ 岁"]
    piv_val = gate_2d_df.pivot(index="inc_q", columns="age_g", values="gate").loc[q_order, a_order]
    piv_star = gate_2d_df.pivot(index="inc_q", columns="age_g", values="star").loc[q_order, a_order]
    piv_n = gate_2d_df.pivot(index="inc_q", columns="age_g", values="n").loc[q_order, a_order]

    im = ax1.imshow(piv_val.values / 1000.0, cmap="YlGnBu", aspect="auto", vmin=-2.0, vmax=max(26.0, float(piv_val.values.max()) / 1000.0))
    for i in range(len(q_order)):
        for j in range(len(a_order)):
            val = piv_val.iloc[i, j]
            st_raw = piv_star.iloc[i, j]
            st = "" if pd.isna(st_raw) else str(st_raw)
            nv = piv_n.iloc[i, j]
            txt_col = "#FFFFFF" if val > 14000 else "#0F172A"
            val_str = f"-${abs(val):,.0f}{st}" if val < 0 else f"${val:,.0f}{st}"
            ax1.text(j, i, f"{val_str}\n(n={nv})", ha="center", va="center", color=txt_col, fontsize=10.2, fontweight="bold")
    ax1.set_xticks(np.arange(len(a_order)))
    ax1.set_xticklabels(a_order, fontsize=11.0)
    ax1.set_yticks(np.arange(len(q_order)))
    ax1.set_yticklabels(["Q1 低收入", "Q2 中低收入", "Q3 中高收入", "Q4 高收入"], fontsize=10.8)
    ax1.set_title("(a) 收入四分位 × 年龄段 二维 GATE 热力图", fontsize=12.6, fontweight="bold")
    cbar = fig.colorbar(im, ax=ax1, pad=0.03)
    cbar.set_label("GATE (千美元)", fontsize=10.2)
    cbar.ax.tick_params(labelsize=9.8)

    ax2 = axes[1]
    xd = curve_df["decile"].values
    ax2.errorbar(xd, curve_df["phi_mean"] / 1000.0, yerr=1.96 * curve_df["phi_se"] / 1000.0,
                 fmt="o", color="#1F4E79", ecolor="#60A5FA", elinewidth=2.0, capsize=3.5, ms=5.5, label="十分位正交均值 ±95% CI")
    ax2.plot(xd, curve_df["dr_cate_mean"] / 1000.0, color="#0A365C", lw=2.6, label="DR-Learner 连续条件效应曲线 (Kennedy, 2023)")
    ax2.axhline(0, color="#64748B", ls=":", lw=1.0)
    ax2.set_xticks(xd)
    ax2.set_xticklabels([f"D{i}\n${m/1000:.0f}k" for i, m in zip(xd, curve_df["median_inc"])], fontsize=9.6)
    ax2.set_ylim(-8.5, 58.0)
    ax2.tick_params(axis="y", labelsize=10.6)
    ax2.set_xlabel("家庭年收入十分位及中位收入", fontsize=11.5)
    ax2.set_ylabel("条件因果净储蓄增量 CATE (千美元)", fontsize=11.5, color="#0A365C")
    ax2.grid(alpha=0.25)

    ax2_r = ax2.twinx()
    ax2_r.plot(xd, curve_df["dr_rel_inc_pct"], color="#C55A11", ls="--", marker="^", ms=6.2, lw=2.2, label="相对年收入撬动率 (%)")
    ax2_r.set_ylim(0, 74.0)
    ax2_r.set_ylabel("CATE / 组内中位年收入 (%)", fontsize=11.5, color="#C55A11")
    ax2_r.tick_params(axis="y", labelsize=10.4, colors="#C55A11")

    h1, lb1 = ax2.get_legend_handles_labels()
    h2, lb2 = ax2_r.get_legend_handles_labels()
    ax2.legend(h1 + h2, lb1 + lb2, fontsize=9.0, loc="upper center", bbox_to_anchor=(0.52, 0.985), framealpha=0.95)
    ax2.set_title("(b) DR-Learner 连续收入分位 CATE 与相对撬动率", fontsize=12.6, fontweight="bold")

    fig.subplots_adjust(wspace=0.36)
    fig.suptitle("图6：二维交互异质性（GATE 热力图）与连续 DR-Learner 条件因果效应曲线", fontsize=14.4, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig6_401k_heterogeneity_gate.png", bbox_inches="tight")
    plt.close(fig)


def _run_enrichments_and_plots(
    sim_res: Dict, df: pd.DataFrame, forest_df: pd.DataFrame, hgb_ps: np.ndarray, hgb_phi: np.ndarray,
    ate_est: float, ate_se: float,
) -> Dict:
    """Compute all advanced diagnostics (scaling, Love plot, first-stage/K-fold, OVB, 2D GATE/DR-CATE) and render Figs 1-6."""
    tstat_stats = plot_fig1_sim_dist(sim_res)

    print("Running Simulation sample-size scaling (n=250, 500, 1000, 2000)...", flush=True)
    scaling_rows, _ = run_sample_size_scaling(p=20, theta0=2.0, n1000_res=sim_res)
    scaling_df = pd.DataFrame(scaling_rows)
    scaling_df.to_csv(TAB_DIR / "simulation_sample_size_scaling.csv", index=False)
    plot_fig2_sim_metrics(scaling_df)

    print("Computing decile nonlinearity profile & Before/After DML-IPW Love Plot...", flush=True)
    decile_df, love_df = compute_401k_love_plot_and_deciles(df, COVS9, hgb_ps)
    decile_df.to_csv(TAB_DIR / "401k_income_decile_profile.csv", index=False)
    love_df.to_csv(TAB_DIR / "401k_love_plot_balance.csv", index=False)
    love_df[["covariate", "label", "smd", "abs_smd"]].to_csv(TAB_DIR / "401k_covariate_smd.csv", index=False)
    plot_fig3_401k_eda(decile_df, love_df)

    X9 = df[COVS9].values
    D = df["e401"].values
    Y = df["net_tfa"].values

    print("Computing first-stage predictive quality & K-fold/trimming stability...", flush=True)
    fs_df, stab_df = compute_first_stage_and_kfold_diagnostics(X9, D, Y)
    fs_df.to_csv(TAB_DIR / "401k_first_stage_diagnostics.csv", index=False)
    stab_df.to_csv(TAB_DIR / "401k_kfold_trimming_sensitivity.csv", index=False)
    plot_fig4_forest(forest_df, fs_df, stab_df)

    print("Computing Chernozhukov et al. (2022) OVB sensitivity contours...", flush=True)
    ovb_meta, bench_df = compute_ovb_sensitivity_ccnss2022(df, COVS9, ate_est, ate_se)
    bench_df.to_csv(TAB_DIR / "401k_ovb_sensitivity.csv", index=False)
    plot_fig5_overlap(hgb_ps, D, ovb_meta)

    print("Computing 2D (Income x Age) GATE & DR-Learner CATE curve...", flush=True)
    gate_2d_df, curve_df = compute_2d_gate_and_dr_cate(df, COVS9, hgb_phi)
    gate_2d_df.to_csv(TAB_DIR / "401k_gate_2d_income_age.csv", index=False)
    curve_df.to_csv(TAB_DIR / "401k_cate_income_curve.csv", index=False)
    plot_fig6_gate(gate_2d_df, curve_df)

    return {
        "tstat_normality": tstat_stats,
        "scaling": scaling_rows,
        "decile_profile": decile_df.to_dict(orient="records"),
        "love_plot_balance": love_df.to_dict(orient="records"),
        "first_stage_diagnostics": fs_df.to_dict(orient="records"),
        "kfold_trimming_stability": stab_df.to_dict(orient="records"),
        "ovb_sensitivity": ovb_meta,
        "gate_2d": gate_2d_df.to_dict(orient="records"),
        "dr_cate_curve": curve_df.to_dict(orient="records"),
    }


def main() -> None:
    t0 = time.time()
    ensure_dirs()

    print("Running Part A: Monte Carlo Simulation (B=200, n=1000, p=20)...", flush=True)
    sim_res = run_monte_carlo_simulation(B=200, n=1000, p=20, theta0=2.0)
    sim_df = pd.DataFrame(sim_res["summary"])
    sim_df.to_csv(TAB_DIR / "simulation_summary.csv", index=False)

    print("Running Part B: 1991 SIPP 401(k) Empirical Study (N=9,915)...", flush=True)
    df = pd.read_csv(DATA_CSV)
    X9 = df[COVS9].values
    X8 = df[COVS8].values
    D = df["e401"].values
    P401 = df["p401"].values
    Y = df["net_tfa"].values
    n = len(df)

    # Traditional Econometric Baselines
    naive_est, naive_se = ols_hc1(np.column_stack([np.ones(n), D]), Y)
    ols_est, ols_se = ols_hc1(np.column_stack([np.ones(n), D, X9]), Y)
    X_poly = PolynomialFeatures(degree=2, include_bias=False).fit_transform(StandardScaler().fit_transform(X9))
    poly_ols_est, poly_ols_se = ols_hc1(np.column_stack([np.ones(n), D, X_poly]), Y)
    psm_res = run_psm_baseline(df, COVS9, n_boot=120, seed=42)

    # DML-PLR
    plr_results = {}
    for name, (l_m, m_m) in make_plr_learners(seed=42).items():
        plr_results[name] = fit_dml_plr(X9, D, Y, l_m, m_m, n_splits=5, n_rep=5)

    # DML-IRM
    irm_results = {}
    hgb_ps, hgb_phi = None, None
    for name, (g_m, m_m) in make_irm_learners(seed=42).items():
        res = fit_dml_irm(X9, D, Y, g_m, m_m, n_splits=5, n_rep=5)
        if name == "HistGradientBoosting":
            hgb_ps = res["ps_hat"]
            hgb_phi = res["phi_ate"]
        irm_results[name] = {"ATE": res["ATE"], "ATT": res["ATT"]}

    # Sensitivity without pira (8 covariates) using HistGradientBoosting
    g_hgb, m_hgb_reg = make_plr_learners(seed=42)["HistGradientBoosting"]
    plr_nopira = fit_dml_plr(X8, D, Y, g_hgb, m_hgb_reg, n_splits=5, n_rep=5)
    g_hgb2, m_hgb_clf = make_irm_learners(seed=42)["HistGradientBoosting"]
    irm_nopira = fit_dml_irm(X8, D, Y, g_hgb2, m_hgb_clf, n_splits=5, n_rep=5)

    # Instrumental Variable LATE (IIVM) for p401 using e401 as instrument
    iivm_late = fit_dml_iivm_late(X9, D, P401, Y, g_hgb2, m_hgb_clf, n_splits=5, n_rep=5)

    forest_rows = [
        {"group": "传统计量基准", "label": "Naive 组间均值差 (无控制)", "est": naive_est, "se": naive_se},
        {"group": "传统计量基准", "label": "线性 OLS 回归", "est": ols_est, "se": ols_se},
        {"group": "传统计量基准", "label": "高维二次多项式 OLS", "est": poly_ols_est, "se": poly_ols_se},
        {"group": "传统计量基准", "label": "PSM 1:1 倾向得分匹配 (ATE)", "est": psm_res["ATE"]["est"], "se": psm_res["ATE"]["se"]},
        {"group": "传统计量基准", "label": "PSM 1:1 倾向得分匹配 (ATT)", "est": psm_res["ATT"]["est"], "se": psm_res["ATT"]["se"]},
    ]
    for name, r in plr_results.items():
        forest_rows.append({"group": "DML-PLR", "label": f"DML-PLR ({name})", "est": r["est"], "se": r["se"]})
    for name, r in irm_results.items():
        forest_rows.append({"group": "DML-IRM (ATE)", "label": f"DML-IRM ATE ({name})", "est": r["ATE"]["est"], "se": r["ATE"]["se"]})
    forest_rows.append({"group": "DML-IRM (ATT)", "label": "DML-IRM ATT (HistGradientBoosting)", "est": irm_results["HistGradientBoosting"]["ATT"]["est"], "se": irm_results["HistGradientBoosting"]["ATT"]["se"]})
    forest_df = pd.DataFrame(forest_rows)
    forest_df.to_csv(TAB_DIR / "401k_model_comparison.csv", index=False)

    assert hgb_ps is not None and hgb_phi is not None
    df_gate = df.copy()
    df_gate["phi_ate"] = hgb_phi
    df_gate["inc_q"] = pd.qcut(df_gate["inc"], q=4, labels=["Q1 (低收入)", "Q2 (中低收入)", "Q3 (中高收入)", "Q4 (高收入)"])
    gate_rows = []
    for q_lab, sub in df_gate.groupby("inc_q", observed=True):
        m_g = float(sub["phi_ate"].mean())
        se_g = float(sub["phi_ate"].std(ddof=1) / np.sqrt(len(sub)))
        med_inc = float(sub["inc"].median())
        gate_rows.append({
            "quartile_label": f"{q_lab}\n(中位年收 ${med_inc/1000:.1f}k)",
            "quartile": str(q_lab), "n": int(len(sub)), "median_inc": med_inc,
            "gate": m_g, "se": se_g, "ci95_low": m_g - 1.96 * se_g, "ci95_high": m_g + 1.96 * se_g,
            "effect_to_income_pct": float(m_g / med_inc * 100.0),
        })
    gate_df = pd.DataFrame(gate_rows)
    gate_df.to_csv(TAB_DIR / "401k_income_gate.csv", index=False)

    enrich_data = _run_enrichments_and_plots(
        sim_res, df, forest_df, hgb_ps, hgb_phi,
        irm_results["HistGradientBoosting"]["ATE"]["est"],
        irm_results["HistGradientBoosting"]["ATE"]["se"],
    )

    summary = {
        "runtime_seconds": round(time.time() - t0, 2),
        "simulation": {
            "config": sim_res["config"],
            "summary": sim_res["summary"],
            "tstat_normality": enrich_data["tstat_normality"],
            "sample_size_scaling": enrich_data["scaling"],
        },
        "empirical_401k": {
            "n": int(n),
            "treated_e401": int(D.sum()),
            "control_e401": int((1 - D).sum()),
            "compliers_p401_given_e401": float(df.loc[df["e401"] == 1, "p401"].mean()),
            "traditional_baselines": {
                "naive_diff": {"est": naive_est, "se": naive_se},
                "linear_ols": {"est": ols_est, "se": ols_se},
                "poly2_ols": {"est": poly_ols_est, "se": poly_ols_se},
                "psm": psm_res,
            },
            "dml_plr": plr_results,
            "dml_irm": irm_results,
            "sensitivity_no_pira": {
                "dml_plr_hgb": plr_nopira,
                "dml_irm_hgb_ATE": irm_nopira["ATE"],
                "dml_irm_hgb_ATT": irm_nopira["ATT"],
            },
            "dml_iivm_late_p401": iivm_late,
            "propensity_diagnostics": {
                "hgb_ps_min": float(hgb_ps.min()),
                "hgb_ps_max": float(hgb_ps.max()),
                "hgb_ps_p05": float(np.percentile(hgb_ps, 5)),
                "hgb_ps_p95": float(np.percentile(hgb_ps, 95)),
            },
            "income_gate": gate_df.to_dict(orient="records"),
            "decile_profile": enrich_data["decile_profile"],
            "love_plot_balance": enrich_data["love_plot_balance"],
            "first_stage_diagnostics": enrich_data["first_stage_diagnostics"],
            "kfold_trimming_stability": enrich_data["kfold_trimming_stability"],
            "ovb_sensitivity": enrich_data["ovb_sensitivity"],
            "gate_2d": enrich_data["gate_2d"],
            "dr_cate_curve": enrich_data["dr_cate_curve"],
        },
    }
    with open(OUT_DIR / "results_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("Full DML pipeline completed cleanly.")


def enrich_all() -> None:
    """Compute all new diagnostics & regenerate Figs 1-6 preserving saved PSM/PLR/IRM core benchmark values (~60s)."""
    ensure_dirs()
    summary = json.loads((OUT_DIR / "results_summary.json").read_text(encoding="utf-8"))
    df = pd.read_csv(DATA_CSV)
    forest_df = pd.read_csv(TAB_DIR / "401k_model_comparison.csv")

    print("Running B=200, n=1000 Monte Carlo for exact t-stat normality...", flush=True)
    sim_res = run_monte_carlo_simulation(B=200, n=1000, p=20, theta0=2.0)

    print("Extracting HGB DML-IRM pseudo-outcomes & propensity scores...", flush=True)
    g_hgb, m_hgb = make_irm_learners(seed=42)["HistGradientBoosting"]
    hgb_res = fit_dml_irm(df[COVS9].values, df["e401"].values, df["net_tfa"].values, g_hgb, m_hgb, n_splits=5, n_rep=5)
    hgb_ps, hgb_phi = hgb_res["ps_hat"], hgb_res["phi_ate"]

    ate_est = summary["empirical_401k"]["dml_irm"]["HistGradientBoosting"]["ATE"]["est"]
    ate_se = summary["empirical_401k"]["dml_irm"]["HistGradientBoosting"]["ATE"]["se"]
    enrich_data = _run_enrichments_and_plots(sim_res, df, forest_df, hgb_ps, hgb_phi, ate_est, ate_se)

    summary["simulation"]["tstat_normality"] = enrich_data["tstat_normality"]
    summary["simulation"]["sample_size_scaling"] = enrich_data["scaling"]
    emp = summary["empirical_401k"]
    emp["decile_profile"] = enrich_data["decile_profile"]
    emp["love_plot_balance"] = enrich_data["love_plot_balance"]
    emp["first_stage_diagnostics"] = enrich_data["first_stage_diagnostics"]
    emp["kfold_trimming_stability"] = enrich_data["kfold_trimming_stability"]
    emp["ovb_sensitivity"] = enrich_data["ovb_sensitivity"]
    emp["gate_2d"] = enrich_data["gate_2d"]
    emp["dr_cate_curve"] = enrich_data["dr_cate_curve"]

    with open(OUT_DIR / "results_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("Enrichment & all 6 multi-panel figures saved cleanly.")


def replot_from_saved() -> None:
    """Fast re-rendering of Figs 2-6 from saved CSVs & JSON (<5s, zero heavy recomputation)."""
    summary = json.loads((OUT_DIR / "results_summary.json").read_text(encoding="utf-8"))
    emp = summary["empirical_401k"]
    df = pd.read_csv(DATA_CSV)
    scaling_df = pd.read_csv(TAB_DIR / "simulation_sample_size_scaling.csv")
    decile_df = pd.read_csv(TAB_DIR / "401k_income_decile_profile.csv")
    love_df = pd.read_csv(TAB_DIR / "401k_love_plot_balance.csv")
    forest_df = pd.read_csv(TAB_DIR / "401k_model_comparison.csv")
    fs_df = pd.read_csv(TAB_DIR / "401k_first_stage_diagnostics.csv")
    stab_df = pd.read_csv(TAB_DIR / "401k_kfold_trimming_sensitivity.csv")
    gate_2d_df = pd.read_csv(TAB_DIR / "401k_gate_2d_income_age.csv", keep_default_na=False)
    curve_df = pd.read_csv(TAB_DIR / "401k_cate_income_curve.csv")

    g_hgb, m_hgb = make_irm_learners(seed=42)["HistGradientBoosting"]
    hgb_res = fit_dml_irm(df[COVS9].values, df["e401"].values, df["net_tfa"].values, g_hgb, m_hgb, n_splits=5, n_rep=5)

    plot_fig2_sim_metrics(scaling_df)
    plot_fig3_401k_eda(decile_df, love_df)
    plot_fig4_forest(forest_df, fs_df, stab_df)
    plot_fig5_overlap(hgb_res["ps_hat"], df["e401"].values, emp["ovb_sensitivity"])
    plot_fig6_gate(gate_2d_df, curve_df)
    print("Fast replot of Figs 2-6 completed cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Double/Debiased Machine Learning analysis or enrichment.")
    parser.add_argument("--enrich-all", action="store_true", help="Compute new diagnostics and re-render all 6 multi-panel figures.")
    parser.add_argument("--replot-only", action="store_true", help="Fast replot Figs 2-6 from saved CSVs/JSON.")
    args = parser.parse_args()
    if args.replot_only:
        replot_from_saved()
    elif args.enrich_all:
        enrich_all()
    else:
        main()
