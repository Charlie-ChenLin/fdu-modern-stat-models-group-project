#!/usr/bin/env python3
"""Version 2 (Course-Untaught Method): Double/Debiased Machine Learning (DML)
Based on Chernozhukov et al. (2018), The Econometrics Journal.

Includes:
  Part A: Monte Carlo Simulation (B=200, n=1000, p=20) proving why Naive OLS,
          Direct Regularized ML Plug-in, and Orthogonal ML without Cross-Fitting fail,
          while full DML (Neyman Orthogonal Score + Cross-Fitting) achieves ~95% CI coverage.
  Part B: Real-world empirical application on 1991 SIPP 401(k) dataset (N=9,915)
          comparing traditional course baselines (OLS, Polynomial OLS, PSM) against
          DML-PLR, DML-IRM (ATE & ATT), DML-IIVM (LATE), and GATE heterogeneity.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, norm
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LassoCV, LogisticRegressionCV, RidgeCV
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


def run_monte_carlo_simulation(B: int = 200, n: int = 1000, p: int = 20, theta0: float = 2.0) -> Dict:
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

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    poly_tr = PolynomialFeatures(2, include_bias=False)

    for b in range(B):
        if b % 40 == 0:
            print(f"  [Sim] iter {b}/{B}", flush=True)
        X, D, Y = simulate_dgp(n, p, theta0, rng)

        # 1. Naive OLS: Y ~ 1 + D + X
        W = np.column_stack([np.ones(n), D, X])
        beta, *_ = np.linalg.lstsq(W, Y, rcond=None)
        resid_ols = Y - W @ beta
        bread = np.linalg.inv(W.T @ W)
        meat = (W * (resid_ols[:, None] ** 2)).T @ W
        vcov_ols = bread @ meat @ bread * (n / (n - W.shape[1]))
        se_ols = float(np.sqrt(vcov_ols[1, 1]))
        th_ols = float(beta[1])
        ests[methods[0]].append(th_ols)
        ses[methods[0]].append(se_ols)
        covs[methods[0]].append(abs(th_ols - theta0) <= 1.96 * se_ols)

        # 2. Direct ML Plug-in (RF residual on Y only, no Neyman orthogonalization of D)
        half = n // 2
        rf_g = RandomForestRegressor(n_estimators=50, max_depth=8, min_samples_leaf=5, n_jobs=1, random_state=b)
        rf_g.fit(X[:half], Y[:half])
        res_y_naive = Y[half:] - rf_g.predict(X[half:])
        D_main = D[half:]
        th_plug = float((D_main @ res_y_naive) / (D_main @ D_main))
        e_plug = res_y_naive - th_plug * D_main
        se_plug = float(np.sqrt(np.mean((D_main * e_plug) ** 2) / ((np.mean(D_main ** 2)) ** 2) / len(D_main)))
        ests[methods[1]].append(th_plug)
        ses[methods[1]].append(se_plug)
        covs[methods[1]].append(abs(th_plug - theta0) <= 1.96 * se_plug)

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
        ests[methods[2]].append(th_nofit)
        ses[methods[2]].append(se_nofit)
        covs[methods[2]].append(abs(th_nofit - theta0) <= 1.96 * se_nofit)

        # 4. Full DML (Neyman Orthogonal Score + 5-Fold Cross-Fitting with Poly2 + LassoCV)
        X_poly = poly_tr.fit_transform(X)
        u_cf = np.empty(n, dtype=float)
        v_cf = np.empty(n, dtype=float)
        for tr, va in kf.split(X_poly):
            l_mod = make_pipeline(StandardScaler(), LassoCV(cv=5, max_iter=3000, random_state=b))
            m_mod = make_pipeline(StandardScaler(), LassoCV(cv=5, max_iter=3000, random_state=b))
            l_mod.fit(X_poly[tr], Y[tr])
            m_mod.fit(X_poly[tr], D[tr])
            u_cf[va] = Y[va] - l_mod.predict(X_poly[va])
            v_cf[va] = D[va] - m_mod.predict(X_poly[va])
        th_dml = float((v_cf @ u_cf) / (v_cf @ v_cf))
        psi_cf = (u_cf - th_dml * v_cf) * v_cf
        J_cf = -float(np.mean(v_cf ** 2))
        se_dml = float(np.sqrt(np.mean(psi_cf ** 2) / (J_cf ** 2) / n))
        ests[methods[3]].append(th_dml)
        ses[methods[3]].append(se_dml)
        covs[methods[3]].append(abs(th_dml - theta0) <= 1.96 * se_dml)

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
    }


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
    """Course Lecture 2.3 baseline: Logistic Propensity Score + Common Support + 1:1 NN Matching on logit(PS)."""
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
            RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_leaf=25, n_jobs=-1, random_state=seed),
            RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_leaf=25, n_jobs=-1, random_state=seed),
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
            RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_leaf=25, n_jobs=-1, random_state=seed),
            RandomForestClassifier(n_estimators=150, max_depth=8, min_samples_leaf=25, n_jobs=-1, random_state=seed),
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


def fit_dml_irm(X: np.ndarray, D: np.ndarray, Y: np.ndarray, g_proto, m_proto, n_splits: int = 5, n_rep: int = 5) -> Dict:
    n = len(Y)
    ates, se_ates, atts, se_atts = [], [], [], []
    last_ps = None
    last_phi_ate = None

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
            m_hat[va] = np.clip(mm.predict_proba(X[va])[:, 1], 0.01, 0.99)

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


# ---------------- Plotting Functions ---------------- #

def plot_fig1_sim_dist(sim_res: Dict) -> None:
    theta0 = sim_res["config"]["theta0"]
    dists = sim_res["distributions"]
    fig, ax = plt.subplots(figsize=(11.0, 5.6))

    palette = {
        "Naive OLS (线性控制)": "#7F7F7F",
        "Direct ML Plug-in (无正交化)": "#C55A11",
        "Orthogonal ML (无交叉拟合)": "#C00000",
        "完整 DML (正交+5折交叉拟合)": "#1F4E79",
    }
    all_vals = np.concatenate(list(dists.values()))
    x_grid = np.linspace(np.percentile(all_vals, 0.5) - 0.15, np.percentile(all_vals, 99.5) + 0.15, 400)

    for m, vals in dists.items():
        arr = np.array(vals)
        kde = gaussian_kde(arr)
        lw = 2.8 if "完整 DML" in m else 2.0
        ax.plot(x_grid, kde(x_grid), color=palette[m], lw=lw, label=f"{m} (均值={arr.mean():.3f})")
        ax.fill_between(x_grid, 0, kde(x_grid), color=palette[m], alpha=0.14 if "完整 DML" in m else 0.08)

    ax.axvline(theta0, color="#111111", ls="--", lw=2.0, label=rf"真实因果效应 $\theta_0 = {theta0:.1f}$")
    ax.set_xlabel("估计值 $\\hat{\\theta}$", fontsize=11)
    ax.set_ylabel("核密度估计", fontsize=11)
    ax.set_title("图1：Monte Carlo 模拟抽样分布对比（B=200 次重复，n=1000，非线性高维混杂）", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9.2, loc="upper left")
    ax.grid(alpha=0.25)
    fig.savefig(FIG_DIR / "fig1_simulation_bias_distribution.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig2_sim_metrics(sim_res: Dict) -> None:
    df_s = pd.DataFrame(sim_res["summary"])
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.0))
    colors = ["#7F7F7F", "#C55A11", "#C00000", "#1F4E79"]
    short_names = ["Naive\nOLS", "Direct ML\n(无正交)", "Orthogonal\n(无交叉拟合)", "完整 DML\n(双支柱)"]
    x = np.arange(len(df_s))

    b1 = axes[0].bar(x, df_s["rmse"], color=colors, width=0.55, alpha=0.92)
    for bar, v in zip(b1, df_s["rmse"]):
        axes[0].text(bar.get_x() + bar.get_width() / 2, v + 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=9.5, fontweight="bold")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(short_names, fontsize=9.5)
    axes[0].set_ylabel("均方根误差 RMSE（越低越好）", fontsize=10.5)
    axes[0].set_ylim(0, df_s["rmse"].max() * 1.22)
    axes[0].set_title("(a) 点估计 RMSE 对比", fontsize=11.5, fontweight="bold")
    axes[0].grid(axis="y", alpha=0.25)

    b2 = axes[1].bar(x, df_s["coverage_95_pct"], color=colors, width=0.55, alpha=0.92)
    axes[1].axhline(95.0, color="#111111", ls="--", lw=1.8, label="名义水平 95%")
    for bar, v in zip(b2, df_s["coverage_95_pct"]):
        axes[1].text(bar.get_x() + bar.get_width() / 2, v + 1.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=9.5, fontweight="bold")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(short_names, fontsize=9.5)
    axes[1].set_ylabel("95% 置信区间经验覆盖率 (%)", fontsize=10.5)
    axes[1].set_ylim(0, 112)
    axes[1].set_title("(b) 95% 置信区间覆盖率（推断有效性检验）", fontsize=11.5, fontweight="bold")
    axes[1].legend(fontsize=9.5, loc="upper left")
    axes[1].grid(axis="y", alpha=0.25)

    fig.suptitle("图2：DML 两大支柱（Neyman 正交化 + Cross-Fitting）的不可替代性验证", fontsize=13.5, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig2_simulation_coverage_rmse.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig3_401k_eda(df: pd.DataFrame, covs: List[str]) -> pd.DataFrame:
    fig, axes = plt.subplots(1, 2, figsize=(14.2, 5.4))

    ax1 = axes[0]
    y0 = df.loc[df["e401"] == 0, "net_tfa"] / 1000.0
    y1 = df.loc[df["e401"] == 1, "net_tfa"] / 1000.0
    # Winsorize display only at [1%, 99%] for readable histogram while noting full stats in text
    bins = np.linspace(-40, 220, 45)
    ax1.hist(np.clip(y0, -40, 220), bins=bins, density=True, alpha=0.55, color="#7F7F7F", label=f"无资格组 e401=0 (均值 ${y0.mean():.1f}k)")
    ax1.hist(np.clip(y1, -40, 220), bins=bins, density=True, alpha=0.55, color="#1F4E79", label=f"有资格组 e401=1 (均值 ${y1.mean():.1f}k)")
    ax1.axvline(y0.mean(), color="#4D4D4D", ls="--", lw=1.8)
    ax1.axvline(y1.mean(), color="#1F4E79", ls="--", lw=1.8)
    ax1.set_xlabel("家庭净金融资产 net_tfa (千美元，展示截断至 [-40k, 220k])", fontsize=10)
    ax1.set_ylabel("样本密度", fontsize=10)
    ax1.set_title("(a) 净金融资产分布：组间原始均值差达 +$19,559", fontsize=11.5, fontweight="bold")
    ax1.legend(fontsize=8.8)
    ax1.grid(alpha=0.25)

    ax2 = axes[1]
    smd_rows = []
    cn_map = {
        "inc": "家庭年收入 (inc)", "hown": "自有住房 (hown)", "educ": "受教育年限 (educ)",
        "twoearn": "双职工家庭 (twoearn)", "pira": "个人退休账户 (pira)", "marr": "已婚 (marr)",
        "db": "固定收益养老金 (db)", "age": "户主年龄 (age)", "fsize": "家庭规模 (fsize)"
    }
    for c in covs:
        x1 = df.loc[df["e401"] == 1, c]
        x0 = df.loc[df["e401"] == 0, c]
        pooled_sd = np.sqrt(0.5 * (x1.var(ddof=1) + x0.var(ddof=1)))
        smd = float((x1.mean() - x0.mean()) / pooled_sd)
        smd_rows.append({"covariate": c, "label": cn_map.get(c, c), "smd": smd, "abs_smd": abs(smd)})
    smd_df = pd.DataFrame(smd_rows).sort_values("smd", ascending=True)
    y_pos = np.arange(len(smd_df))
    bar_cols = ["#1F4E79" if s > 0 else "#C00000" for s in smd_df["smd"]]
    ax2.barh(y_pos, smd_df["smd"], color=bar_cols, alpha=0.88)
    ax2.axvline(0.1, color="#555555", ls="--", lw=1.1, label="|SMD| = 0.1 平衡警戒线")
    ax2.axvline(-0.1, color="#555555", ls="--", lw=1.1)
    for idx, s in enumerate(smd_df["smd"]):
        ax2.text(s + (0.015 if s >= 0 else -0.015), idx, f"{s:+.3f}", va="center", ha="left" if s >= 0 else "right", fontsize=8.5)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(smd_df["label"], fontsize=9.2)
    ax2.set_xlim(-0.22, smd_df["smd"].max() + 0.16)
    ax2.set_xlabel("标准化均值差 (SMD: Treated - Control)", fontsize=10)
    ax2.set_title("(b) 严重选择偏差：高收入/高学历/有房家庭更易获 401(k)", fontsize=11.5, fontweight="bold")
    ax2.legend(fontsize=8.5, loc="lower right")
    ax2.grid(axis="x", alpha=0.25)

    fig.subplots_adjust(wspace=0.44)
    fig.suptitle("图3：1991 SIPP 401(k) 真实数据探索与混杂偏差诊断（N = 9,915）", fontsize=13.5, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig3_401k_eda_confounding.png", bbox_inches="tight")
    plt.close(fig)
    return smd_df


def plot_fig4_forest(forest_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    df_p = forest_df.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(df_p))

    cat_colors = {"传统课堂基准": "#7F7F7F", "DML-PLR": "#2E75B6", "DML-IRM (ATE)": "#1F4E79", "DML-IRM (ATT)": "#548235"}
    for idx, row in df_p.iterrows():
        col = cat_colors.get(row["group"], "#1F4E79")
        ax.errorbar(
            row["est"], idx, xerr=1.96 * row["se"],
            fmt="o", color=col, ecolor=col, elinewidth=2.2, capsize=4.5, ms=7.0
        )
        ax.text(row["est"] + 1.96 * row["se"] + 350, idx, f"${row['est']:,.0f} (±${1.96*row['se']:,.0f})", va="center", fontsize=8.5)

    ax.axvline(0, color="#111111", ls=":", lw=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(df_p["label"], fontsize=9.2)
    ax.set_xlabel("401(k) 资格对净金融资产的因果效应估计与 95% 置信区间 (美元)", fontsize=10.5)
    ax.set_xlim(-500, (df_p["est"] + 1.96 * df_p["se"]).max() * 1.25)
    ax.set_title("图4：传统计量方法 vs. 双重机器学习（DML-PLR / IRM）因果效应横向森林图", fontsize=12.8, fontweight="bold", pad=10)
    ax.grid(axis="x", alpha=0.25)
    fig.savefig(FIG_DIR / "fig4_401k_model_comparison_forest.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig5_overlap(ps_hat: np.ndarray, D: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    bins = np.linspace(0.0, 1.0, 35)
    ax.hist(ps_hat[D == 0], bins=bins, density=True, alpha=0.55, color="#7F7F7F", label="对照组 (e401=0, N=6,233)")
    ax.hist(ps_hat[D == 1], bins=bins, density=True, alpha=0.55, color="#1F4E79", label="处置组 (e401=1, N=3,682)")
    ax.axvline(0.01, color="#C00000", ls="--", lw=1.3, label="截断边界 [0.01, 0.99]")
    ax.axvline(0.99, color="#C00000", ls="--", lw=1.3)
    ax.set_xlabel("交叉拟合估计倾向得分 $\\hat{m}(X) = \\hat{P}(D=1|X)$ (HistGradientBoosting)", fontsize=10.5)
    ax.set_ylabel("样本密度", fontsize=10.5)
    ax.set_title("图5：DML 交叉拟合倾向得分重叠检验（Positivity / Overlap Assumption）", fontsize=12.5, fontweight="bold")
    ax.legend(fontsize=9.2)
    ax.grid(alpha=0.25)
    fig.savefig(FIG_DIR / "fig5_401k_propensity_overlap.png", bbox_inches="tight")
    plt.close(fig)


def plot_fig6_gate(gate_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.8, 5.2))
    x = np.arange(len(gate_df))

    ax1 = axes[0]
    bars = ax1.bar(x, gate_df["gate"], yerr=1.96 * gate_df["se"], capsize=5, color=["#8FAADC", "#2E75B6", "#1F4E79", "#0F2C59"], alpha=0.92, width=0.56)
    for bar, v, se_v in zip(bars, gate_df["gate"], gate_df["se"]):
        top_y = v + 1.96 * se_v + 650
        ax1.text(bar.get_x() + bar.get_width() / 2, top_y, f"${v:,.0f}", ha="center", va="bottom", fontsize=9.2, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(gate_df["quartile_label"], fontsize=9.2)
    ax1.set_ylabel("群体平均处理效应 GATE (美元)", fontsize=10.5)
    ax1.set_ylim(0, (gate_df["gate"] + 1.96 * gate_df["se"]).max() * 1.18)
    ax1.set_title("(a) 按收入四分位的绝对净储蓄因果增量 (95% CI)", fontsize=11.5, fontweight="bold")
    ax1.grid(axis="y", alpha=0.25)

    ax2 = axes[1]
    b2 = ax2.bar(x, gate_df["effect_to_income_pct"], color=["#C55A11", "#D9822B", "#2E75B6", "#1F4E79"], alpha=0.9, width=0.56)
    for bar, v in zip(b2, gate_df["effect_to_income_pct"]):
        ax2.text(bar.get_x() + bar.get_width() / 2, v + 0.6, f"{v:.1f}%", ha="center", va="bottom", fontsize=9.2, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(gate_df["quartile_label"], fontsize=9.2)
    ax2.set_ylabel("因果效应 / 组内中位年收入 (%)", fontsize=10.5)
    ax2.set_ylim(0, gate_df["effect_to_income_pct"].max() * 1.2)
    ax2.set_title("(b) 相对年收入的边际财富撬动率（高收入效应绝对大、中低收入杠杆高）", fontsize=11.0, fontweight="bold")
    ax2.grid(axis="y", alpha=0.25)

    fig.suptitle("图6：基于 Neyman 正交伪结果的收入异质性因果效应（GATE）与商业客群洞察", fontsize=13.5, fontweight="bold", y=1.02)
    fig.savefig(FIG_DIR / "fig6_401k_heterogeneity_gate.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    t0 = time.time()
    ensure_dirs()

    # Part A: Monte Carlo Simulation
    print("Running Part A: Monte Carlo Simulation (B=200, n=1000, p=20)...")
    sim_res = run_monte_carlo_simulation(B=200, n=1000, p=20, theta0=2.0)
    sim_df = pd.DataFrame(sim_res["summary"])
    sim_df.to_csv(TAB_DIR / "simulation_summary.csv", index=False)
    plot_fig1_sim_dist(sim_res)
    plot_fig2_sim_metrics(sim_res)

    # Part B: Real-World 1991 SIPP 401(k)
    print("Running Part B: 1991 SIPP 401(k) Empirical Study (N=9,915)...")
    df = pd.read_csv(DATA_CSV)
    covs9 = ["age", "inc", "educ", "fsize", "marr", "twoearn", "db", "pira", "hown"]
    covs8 = ["age", "inc", "educ", "fsize", "marr", "twoearn", "db", "hown"]

    smd_df = plot_fig3_401k_eda(df, covs9)
    smd_df.to_csv(TAB_DIR / "401k_covariate_smd.csv", index=False)

    X9 = df[covs9].values
    X8 = df[covs8].values
    D = df["e401"].values
    P401 = df["p401"].values
    Y = df["net_tfa"].values
    n = len(df)

    # Traditional Baselines (Course Lectures 1-2)
    naive_est, naive_se = ols_hc1(np.column_stack([np.ones(n), D]), Y)
    ols_est, ols_se = ols_hc1(np.column_stack([np.ones(n), D, X9]), Y)

    X_poly = PolynomialFeatures(degree=2, include_bias=False).fit_transform(StandardScaler().fit_transform(X9))
    poly_ols_est, poly_ols_se = ols_hc1(np.column_stack([np.ones(n), D, X_poly]), Y)

    psm_res = run_psm_baseline(df, covs9, n_boot=120, seed=42)

    # DML-PLR
    plr_learners = make_plr_learners(seed=42)
    plr_results = {}
    for name, (l_m, m_m) in plr_learners.items():
        plr_results[name] = fit_dml_plr(X9, D, Y, l_m, m_m, n_splits=5, n_rep=5)

    # DML-IRM
    irm_learners = make_irm_learners(seed=42)
    irm_results = {}
    hgb_ps = None
    hgb_phi = None
    for name, (g_m, m_m) in irm_learners.items():
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

    # Forest comparison table
    forest_rows = [
        {"group": "传统课堂基准", "label": "Naive 组间均值差 (无控制)", "est": naive_est, "se": naive_se},
        {"group": "传统课堂基准", "label": "线性 OLS (讲义 2.2)", "est": ols_est, "se": ols_se},
        {"group": "传统课堂基准", "label": "高维二次多项式 OLS", "est": poly_ols_est, "se": poly_ols_se},
        {"group": "传统课堂基准", "label": "PSM 1:1 倾向得分匹配 ATE (讲义 2.3)", "est": psm_res["ATE"]["est"], "se": psm_res["ATE"]["se"]},
        {"group": "传统课堂基准", "label": "PSM 1:1 倾向得分匹配 ATT (讲义 2.3)", "est": psm_res["ATT"]["est"], "se": psm_res["ATT"]["se"]},
    ]
    for name, r in plr_results.items():
        forest_rows.append({"group": "DML-PLR", "label": f"DML-PLR ({name})", "est": r["est"], "se": r["se"]})
    for name, r in irm_results.items():
        forest_rows.append({"group": "DML-IRM (ATE)", "label": f"DML-IRM ATE ({name})", "est": r["ATE"]["est"], "se": r["ATE"]["se"]})
    forest_rows.append({"group": "DML-IRM (ATT)", "label": "DML-IRM ATT (HistGradientBoosting)", "est": irm_results["HistGradientBoosting"]["ATT"]["est"], "se": irm_results["HistGradientBoosting"]["ATT"]["se"]})

    forest_df = pd.DataFrame(forest_rows)
    forest_df.to_csv(TAB_DIR / "401k_model_comparison.csv", index=False)

    # GATE Heterogeneity by Income Quartiles using HGB IRM pseudo-outcomes
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
            "quartile": str(q_lab),
            "n": int(len(sub)),
            "median_inc": med_inc,
            "gate": m_g,
            "se": se_g,
            "ci95_low": m_g - 1.96 * se_g,
            "ci95_high": m_g + 1.96 * se_g,
            "effect_to_income_pct": float(m_g / med_inc * 100.0),
        })
    gate_df = pd.DataFrame(gate_rows)
    gate_df.to_csv(TAB_DIR / "401k_income_gate.csv", index=False)

    plot_fig4_forest(forest_df)
    plot_fig5_overlap(hgb_ps, D)
    plot_fig6_gate(gate_df)

    summary = {
        "runtime_seconds": round(time.time() - t0, 2),
        "simulation": {
            "config": sim_res["config"],
            "summary": sim_res["summary"],
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
        },
    }

    with open(OUT_DIR / "results_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("=== Version 2 (DML) Summary ===")
    print("Simulation:")
    print(sim_df.to_string(index=False))
    print("\n401(k) Empirical:")
    print(forest_df.to_string(index=False))
    print(f"\nIIVM LATE (actual participation p401): ${iivm_late['est']:,.0f} (SE=${iivm_late['se']:,.0f})")
    print("GATE by income quartiles:")
    print(gate_df[["quartile", "median_inc", "gate", "se", "effect_to_income_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
