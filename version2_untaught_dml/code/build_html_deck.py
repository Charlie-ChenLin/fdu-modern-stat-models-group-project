#!/usr/bin/env python3
"""Build Double/Debiased Machine Learning (DML) 15-slide 1280x720 self-contained HTML deck
and synchronized academic presentation script, dynamically reading outputs/results_summary.json.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT_DIR / "outputs" / "results_summary.json"
OUT_HTML = ROOT_DIR / "presentation" / "版本二_双重机器学习与养老金因果评估.html"
OUT_SPEECH = ROOT_DIR / "docs" / "演讲稿_12分钟展示与3分钟拓展.md"


V2_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', -apple-system, sans-serif;
  background: #0F172A;
  color: #1E293B;
  -webkit-font-smoothing: antialiased;
}
#deck {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 16px;
}
section.slide {
  width: 1280px;
  height: 720px;
  background: #F6F8FB;
  color: #1E293B;
  position: relative;
  overflow: hidden;
  display: none;
  flex-direction: column;
  border-radius: 8px;
  box-shadow: 0 22px 60px rgba(2, 6, 23, 0.55);
  transform-origin: center center;
}
section.slide.active { display: flex; }

body.export-mode { background: #FFFFFF; }
body.export-mode #deck {
  display: block;
  min-height: auto;
  padding: 0;
}
body.export-mode section.slide {
  display: flex !important;
  border-radius: 0;
  box-shadow: none;
  margin: 0;
  transform: none !important;
}
body.export-mode #nav-controls,
body.export-mode #notes-drawer { display: none !important; }

/* Cover slide */
section.slide.cover {
  background: linear-gradient(135deg, #072642 0%, #0A365C 58%, #0E5A75 100%);
  color: #FFFFFF;
  padding: 32px 44px 26px 44px;
  justify-content: space-between;
}
.cover-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15.5px;
  color: #CBD5E1;
  border-bottom: 1px solid rgba(255,255,255,0.18);
  padding-bottom: 10px;
}
.cover-pill {
  background: rgba(217, 119, 6, 0.24);
  border: 1px solid rgba(251, 191, 36, 0.55);
  color: #FDE68A;
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 14.5px;
  font-weight: 600;
}
.cover-main { margin: 8px 0 4px 0; }
.cover-kicker {
  font-size: 19px;
  color: #7DD3FC;
  font-weight: 600;
  letter-spacing: 0.4px;
  margin-bottom: 8px;
}
.cover-title {
  font-size: 44px;
  line-height: 1.22;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 12px;
}
.cover-sub {
  font-size: 19.5px;
  line-height: 1.46;
  color: #E2E8F0;
  max-width: 1180px;
}
.cover-kpis {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 16px;
}
.cover-kpi {
  background: rgba(255,255,255,0.09);
  border: 1px solid rgba(255,255,255,0.22);
  border-radius: 10px;
  padding: 14px 18px;
}
.cover-kpi .val {
  font-size: 27px;
  font-weight: 700;
  color: #FBBF24;
  margin-bottom: 5px;
  white-space: nowrap;
}
.cover-kpi .lbl {
  font-size: 18px;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 5px;
}
.cover-kpi .desc {
  font-size: 16px;
  color: #E2E8F0;
  line-height: 1.40;
}
.cover-bottom {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-top: 1px solid rgba(255,255,255,0.18);
  padding-top: 12px;
  font-size: 15.5px;
  color: #E2E8F0;
}

/* Standard slide chrome */
.sec-bar {
  height: 32px;
  background: #0A365C;
  padding: 0 26px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.sec-nav { display: flex; gap: 6px; align-items: center; }
.sec-item {
  font-size: 14px;
  color: rgba(255,255,255,0.70);
  padding: 2px 10px;
  border-radius: 4px;
  cursor: pointer;
}
.sec-item.on {
  background: rgba(255,255,255,0.20);
  color: #FFFFFF;
  font-weight: 700;
}
.sec-course { font-size: 14px; color: #93C5FD; font-weight: 500; }

.slide-header {
  background: #FFFFFF;
  padding: 8px 26px 7px 26px;
  border-bottom: 1.5px solid #DCE3EC;
  flex-shrink: 0;
}
.slide-title {
  font-size: 27px;
  font-weight: 700;
  color: #0A365C;
  line-height: 1.20;
}
.slide-sub {
  font-size: 16.5px;
  color: #0E7490;
  margin-top: 3px;
  font-weight: 500;
}

.slide-body {
  flex: 1;
  min-height: 0;
  padding: 8px 26px 6px 26px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

.slide-footer {
  height: 26px;
  background: #FFFFFF;
  border-top: 1px solid #E2E8F0;
  padding: 0 26px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13.5px;
  color: #64748B;
  flex-shrink: 0;
}
.page-num { font-weight: 700; color: #0A365C; font-size: 14px; }

/* Lead methodological framing banner */
.lead-banner {
  background: #EDF4FB;
  border: 1px solid #C5DAF0;
  border-left: 5px solid #0A365C;
  border-radius: 0 7px 7px 0;
  padding: 6px 12px;
  font-size: 16.5px;
  line-height: 1.38;
  color: #0F172A;
  flex-shrink: 0;
}
.lead-banner strong { color: #0A365C; }

/* Grids & Cards */
.row { display: flex; gap: 12px; min-height: 0; }
.col { display: flex; flex-direction: column; gap: 8px; min-height: 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; min-height: 0; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 11px; min-height: 0; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; min-height: 0; }

.card {
  background: #FFFFFF;
  border: 1px solid #DCE3EC;
  border-radius: 8px;
  padding: 10px 14px;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
}
.card.blue { background: #F0F6FC; border-color: #BFDBFE; }
.card.teal { background: #ECFEFF; border-color: #A5F3FC; }
.card.amber { background: #FFFBEB; border-color: #FDE68A; }
.card.red { background: #FEF2F2; border-color: #FECACA; }
.card.dark { background: #0A365C; border-color: #0A365C; color: #FFFFFF; }

.card-hd {
  font-size: 19px;
  font-weight: 700;
  color: #0A365C;
  display: flex;
  align-items: center;
  gap: 7px;
  border-left: 4.5px solid #0E7490;
  padding-left: 8px;
  line-height: 1.24;
}
.card.amber .card-hd { border-left-color: #D97706; color: #92400E; }
.card.red .card-hd { border-left-color: #B91C1C; color: #991B1B; }
.card.dark .card-hd { border-left-color: #FBBF24; color: #FFFFFF; }

.ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 18px;
  line-height: 1.46;
  color: #1E293B;
}
.ul.compact { font-size: 16.5px; line-height: 1.38; gap: 5px; }
.card.dark .ul { color: #E2E8F0; }
.ul li { position: relative; padding-left: 15px; }
.ul li::before {
  content: "•";
  position: absolute;
  left: 0;
  top: 0;
  color: #0E7490;
  font-weight: 700;
}
.card.amber .ul li::before { color: #D97706; }
.card.red .ul li::before { color: #B91C1C; }
.card.dark .ul li::before { color: #FBBF24; }

.p-text { font-size: 18px; line-height: 1.46; color: #1E293B; }
.p-text.compact { font-size: 16.5px; line-height: 1.38; }
.card.dark .p-text { color: #E2E8F0; }
.hl { font-weight: 700; color: #0A365C; }
.hl-teal { font-weight: 700; color: #0E7490; }
.hl-red { font-weight: 700; color: #B91C1C; }
.hl-amber { font-weight: 700; color: #B45309; }

/* Math styling */
.math-box {
  background: #F8FAFC;
  border: 1px solid #CBD5E1;
  border-left: 4.5px solid #0A365C;
  border-radius: 6px;
  padding: 7px 12px;
  font-family: 'Cambria Math', 'Times New Roman', 'PingFang SC', serif;
  font-size: 19px;
  color: #0F172A;
  text-align: center;
  line-height: 1.32;
}
.frac {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  vertical-align: middle;
  margin: 0 3px;
  font-size: 0.90em;
  line-height: 1.08;
}
.frac .num { border-bottom: 1.5px solid currentColor; padding: 0 4px 1px 4px; }
.frac .den { padding: 1px 4px 0 4px; }
.hat {
  position: relative;
  display: inline-block;
}
.hat::before {
  content: "^";
  position: absolute;
  top: -0.46em;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.75em;
  font-weight: 700;
}

/* Tables */
table.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 15.5px;
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  flex-shrink: 0;
}
table.tbl th {
  background: #0A365C;
  color: #FFFFFF;
  font-weight: 600;
  padding: 5.5px 8px;
  text-align: left;
  border-bottom: 1px solid #0A365C;
}
table.tbl td {
  padding: 4.8px 8px;
  border-bottom: 1px solid #E2E8F0;
  color: #1E293B;
  line-height: 1.30;
}
table.tbl tr:nth-child(even) td { background: #F8FAFC; }
table.tbl tr.hl-row td { background: #E0F2FE; font-weight: 700; color: #0A365C; }
.num-col { text-align: right !important; font-variant-numeric: tabular-nums; }

/* Figure frame */
.fig-box {
  background: #FFFFFF;
  border: 1px solid #DCE3EC;
  border-radius: 8px;
  padding: 5px 7px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 0;
  overflow: hidden;
}
.fig-box img {
  max-width: 100%;
  max-height: 100%;
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.note-strip {
  background: #F1F5F9;
  border-left: 4.5px solid #0E7490;
  padding: 6px 12px;
  border-radius: 0 6px 6px 0;
  font-size: 15.5px;
  color: #1E293B;
  line-height: 1.38;
  flex-shrink: 0;
}

/* Browser viewer controls */
#nav-controls {
  position: fixed;
  bottom: 16px;
  right: 20px;
  background: rgba(15, 23, 42, 0.88);
  color: #FFFFFF;
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 999px;
  padding: 6px 14px;
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 13px;
  z-index: 999;
  backdrop-filter: blur(8px);
}
#nav-controls button {
  background: rgba(255,255,255,0.12);
  color: #FFFFFF;
  border: none;
  border-radius: 999px;
  padding: 4px 10px;
  cursor: pointer;
  font-size: 12.5px;
}
#nav-controls button:hover { background: rgba(255,255,255,0.24); }
#notes-drawer {
  position: fixed;
  bottom: 58px;
  right: 20px;
  width: 560px;
  max-width: calc(100vw - 40px);
  background: rgba(15, 23, 42, 0.94);
  color: #E2E8F0;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 13.5px;
  line-height: 1.55;
  display: none;
  z-index: 998;
}
#notes-drawer.open { display: block; }
"""


VIEWER_JS = """
<script>
(function() {
  const params = new URLSearchParams(window.location.search);
  const isExport = params.get('export') === '1';
  const slides = Array.from(document.querySelectorAll('section.slide'));
  const total = slides.length;
  let current = 0;

  if (isExport) {
    document.body.classList.add('export-mode');
    return;
  }

  const counter = document.getElementById('slide-counter');
  const notesBody = document.getElementById('notes-body');
  const drawer = document.getElementById('notes-drawer');

  function fitScale() {
    const pad = 28;
    const scale = Math.min((window.innerWidth - pad) / 1280, (window.innerHeight - pad) / 720, 1.0);
    slides.forEach(s => { s.style.transform = `scale(${scale.toFixed(4)})`; });
  }

  function show(idx) {
    current = Math.max(0, Math.min(total - 1, idx));
    slides.forEach((s, i) => s.classList.toggle('active', i === current));
    if (counter) counter.textContent = `${current + 1} / ${total}`;
    if (notesBody) notesBody.textContent = slides[current].getAttribute('data-notes') || '';
  }

  window.goSlide = show;
  document.getElementById('btn-prev').onclick = () => show(current - 1);
  document.getElementById('btn-next').onclick = () => show(current + 1);
  document.getElementById('btn-notes').onclick = () => drawer.classList.toggle('open');

  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') { e.preventDefault(); show(current + 1); }
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); show(current - 1); }
    else if (e.key === 'n' || e.key === 'N') { drawer.classList.toggle('open'); }
  });

  window.addEventListener('resize', fitScale);
  fitScale();
  show(0);
})();
</script>
"""


def sec_bar_html(active_idx: int) -> str:
    secs = [
        ("01 模型介绍", 1),
        ("02 模拟分析", 5),
        ("03 研究背景与数据", 7),
        ("04 实证分析", 8),
        ("05 结论、拓展与 Q&A", 11),
    ]
    items = []
    for i, (label, target) in enumerate(secs):
        cls = "sec-item on" if i == active_idx else "sec-item"
        items.append(f'<span class="{cls}" onclick="goSlide({target})">{label}</span>')
    return (
        '<div class="sec-bar">'
        f'<div class="sec-nav">{"".join(items)}</div>'
        '<div class="sec-course">双重机器学习（DML）：理论、模拟与实证</div>'
        '</div>'
    )


def wrap_slide(page: int, sec_idx: int, title: str, subtitle: str, body_html: str, notes: str) -> str:
    sub_html = f'<p class="slide-sub">{subtitle}</p>' if subtitle else ""
    return (
        f'<section class="slide" data-notes="{html.escape(notes, quote=True)}">'
        f'{sec_bar_html(sec_idx)}'
        '<div class="slide-header">'
        f'<h2 class="slide-title">{title}</h2>'
        f'{sub_html}'
        '</div>'
        f'<div class="slide-body">{body_html}</div>'
        '<div class="slide-footer">'
        '<span>复旦大学管理学院 DSBA · 双重机器学习（DML）理论与应用研究</span>'
        f'<span class="page-num">{page:02d} / 15</span>'
        '</div>'
        '</section>'
    )


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    cfg = d["simulation"]["config"]
    sim = d["simulation"]["summary"]
    emp = d["empirical_401k"]
    base = emp["traditional_baselines"]
    plr = emp["dml_plr"]
    irm = emp["dml_irm"]
    sens = emp["sensitivity_no_pira"]
    late = emp["dml_iivm_late_p401"]
    ps = emp["propensity_diagnostics"]
    gates = emp["income_gate"]
    ts_norm = d["simulation"]["tstat_normality"]
    scaling_dml = [r for r in d["simulation"]["sample_size_scaling"] if "完整 DML" in r["method"]]
    love = {r["covariate"]: r for r in emp["love_plot_balance"]}
    fs_diag = {r["learner"]: r for r in emp["first_stage_diagnostics"]}
    stab = emp["kfold_trimming_stability"]
    ovb = emp["ovb_sensitivity"]
    ovb_b = {r["covariate"]: r for r in ovb["benchmarks"]}
    gate_2d = {(r["inc_q"], r["age_g"]): r for r in emp["gate_2d"]}
    dr_curve = emp["dr_cate_curve"]

    notes_list: List[str] = [
        # 1
        "各位老师、同学好！本次汇报的主题是《双重机器学习（DML）与高维因果推断：理论原理、模拟验证与 401(k) 实证研究》。针对高维非线性混杂下传统参数方法易误设、直接机器学习又导致置信区间失效的问题，本研究系统剖析 Chernozhukov 等 (2018) 提出的双重机器学习框架，依次通过跨样本量的 Monte Carlo 模拟与 9,915 户 1991 SIPP 401(k) 养老金实证全面评估其性能与边界。",
        # 2
        "首先介绍模型提出背景与文献演进脉络。从潜在结果框架出发，因果推断经历了 Robinson (1988) 部分线性半参数回归与 Rosenbaum & Rubin (1983) 倾向得分匹配，再发展到 Robins 等 (1994) 的双稳健 AIPW 估计、Belloni 等 (2014) 高维稀疏控制以及 Kennedy (2023) 的双稳健条件效应学习，最终在 Chernozhukov 等 (2018, 2022) 形成兼顾非参数估计、渐近推断与遗漏变量敏感性检验的完整 DML 体系。",
        # 3
        "接着从部分线性回归模型（Robinson, 1988）出发，剖析普通机器学习直接代入因果估计的两类核心偏误：第一，正则化偏误（Regularization Bias），惩罚项导致扰动函数收敛速度仅为 n^(-1/4) 量级，一阶误差乘以 √n 后趋于发散；第二，过拟合偏误（Overfitting Bias），复杂机器学习模型若在同一全样本上拟合与预测残差，会因样本内拟合噪声产生虚假相关性，同样破坏估计量的一阶渐近无偏性。",
        # 4
        "为克服上述两类偏误，DML 引入第一项核心机制——Neyman 正交化。通过构造局部 Gateaux 导数为零的正交得分函数 ψ(W; θ, η)，同时对结果变量 Y 与处置变量 D 进行条件期望建模并取残差，从而将估计偏误的一阶项完全消除，仅余两项扰动估计误差的二阶乘积 ||ℓ̂−ℓ₀||₂ × ||m̂−m₀||₂。当各学习器达到 o(n^(-1/4)) 收敛速率时，乘积项即可达到 o(n^(-1/2))，从而严格恢复 √n-一致性与渐近正态性。",
        # 5
        "在此基础上，DML 进一步引入第二项核心机制——K-折交叉拟合（Cross-Fitting）。通过将样本随机均分为 5 折、每次仅使用折外 K−1 折训练所得的扰动模型来计算当前验证折的残差，彻底阻断样本内过拟合引发的噪声相关，并保留全样本统计效率；实证中依据 Chernozhukov 等 (2018) 定义 3.3 重复 5 次分层切分取中位数并计入切分间方差。由此构建起同质斜率 PLR、异质双稳健 IRM 以及工具变量 IIVM 的统一因果推断框架。",
        # 6
        f"针对有限样本下的去偏与渐近正态性，本研究设计了 B={cfg['B']} 次重复、n={cfg['n']}、p={cfg['p']} 维（含二阶平方及交互项，真值 θ₀={cfg['theta0']:.1f}）的 Monte Carlo 模拟。图 1(a) 显示 Naive OLS（2.254）、Direct ML（1.134）与无交叉拟合（1.640）均严重偏离真值；图 1(b) 进一步依据定理 3.1 检验标准化 t 统计量分布，仅完整 DML 完美贴合 N(0,1)（均值 {ts_norm['t_mean']:+.3f}、SD {ts_norm['t_sd']:.3f}，KS 检验 p={ts_norm['ks_p']:.3f}）。",
        # 7
        f"进一步在 n=250, 500, 1000, 2000 四个样本量尺度下验证收敛速率与覆盖率（图 2）。完整 DML 的 RMSE 沿理论速率线 O(n^(-1/2)) 从 {scaling_dml[0]['rmse']:.3f} 稳定降至 {scaling_dml[-1]['rmse']:.3f}，95% 区间覆盖率始终保持在 90.0%–96.5%；而前三种方法因非零偏误主导，样本量越大置信区间越偏离真值，在 n=1000 时覆盖率全部跌落至 0.0%。",
        # 8
        f"在验证模拟性质后，转向 1991 SIPP 401(k) 家庭数据（N={emp['n']:,}，零缺失）。图 3(a) 揭示了强烈的非线性选择机制：从年收入 D1（$9k）到 D10（$86k），雇主资格覆盖率由 9.0% 陡增至 60.9% 且净金融资产呈指数攀升，导致原始均值差虚高至 +$19,559；图 3(b) Covariate Balance Love Plot 则证实，经 DML 交叉拟合倾向得分加权后，9 项协变量 |SMD| 全部由最高 0.637 收敛至 0.058 以内，成功达成平衡。",
        # 9
        "在主效应对比与模型诊断中（图 4），线性 OLS 因误设低估效应至 +$5,896，1:1 PSM 的 ATT 标准误达 $3,026；而 DML-IRM 在四类异质算法下紧凑收敛于 +$7,822 至 +$8,693，标准误降至 $1,142–$1,250。图 4(b) 与 4(c) 进一步证实第一阶段倾向得分 ROC-AUC 稳定在 0.734–0.740、结果折外 R² 为 0.232–0.283，且在 K=2,3,5,10 及多种倾向得分截断设定下估计值稳定在 +$8,434 至 +$8,693。",
        # 10
        f"随后从正性支撑、非参数 OVB 敏感性与工具变量三维度展开核验（图 5）。首先，HGB 倾向得分 5%–95% 核心支撑为 [{ps['hgb_ps_p05']:.3f}, {ps['hgb_ps_p95']:.3f}]；其次，依据 Chernozhukov 等 (2022) OVB 边界，推翻 +$8,693 结论需未观测因子同时解释 5.1% 的结果与权重残差方差（RV=5.1%），即便引入等同 db 或 pira 强度的混淆因子，下界仍高达 +$5,265 与 +$4,624（剔除 pira 实测 +$8,923）；最后以 e401 为工具变量测得依从者 LATE 为 +$12,107。",
        # 11
        f"最后深入刻画异质性因果效应（图 6）。四分位 GATE 表显示高收入 Q4 绝对增量最大（+${gates[3]['gate']:,.0f}），低收入 Q1（+${gates[0]['gate']:,.0f}）占中位年收 36.6%。图 6(a) 二维热力图进一步揭示年龄×收入协同分化：Q4×50+ 岁单户净增高达 +${gate_2d[('Q4 (高收入)', '50+ 岁')]['gate']:,.0f}*（n=600），而 Q1 内部中老年家庭亦获 +$7,364 至 +$9,054 显著提升；图 6(b) Kennedy (2023) DR-Learner 连续曲线显示效应从 D4（+$2,004）单调攀升至 D10（+$27,989），而 D1 相对收入撬动率高达 {dr_curve[0]['dr_rel_inc_pct']:.1f}%。",
        # 12
        f"综合模拟与实证，可以从模型性能与决策启示两方面凝练结论。性能方面：DML 不仅验证了 t 统计量正态性（KS p={ts_norm['ks_p']:.3f}）与 O(n^(-1/2)) 收敛速率、将模拟覆盖率恢复至 96.5%，还在 401(k) 中使全部 9 项协变量 |SMD| 降至 0.058 以下、跨学习器与超参高度稳健，并以 OVB RV=5.1% 与 DR-Learner 拓展展现强大严密性。实践方面：证实税收递延养老金净储蓄创造效应，建议机构重点服务中老年高收入群体（Q4×50+ 达 +$31,444），普惠政策则应聚焦克服年轻低收入人群流动性约束。",
        # 13
        "同时需清晰界定模型假设边界与前沿延伸方向。边界上：DML 仍受条件可忽略性约束，根据 OVB 基准，若出现与家庭年收入同等量级（R²≈24.2%）的未观测主观储蓄偏好仍会逆转结论；极端倾向得分下逆概率权重敏感，且需满足扰动学习器 o(n^(-1/4)) 收敛速率。未来可进一步融合面板双重差分（DID-DML）、依托 Causal Forest 构造最优 Policy Tree 靶向投放规则，并延伸至动态多期纵贯 DML 评估长期退休财富积累。",
        # 14
        "最后进入每人 1 分钟的模型拓展应用阐述。结合我在量化多因子研究与大模型 Agent 强化学习中的实践，DML 可直接用于剥离非线性市值、波动率与行业暴露混杂以检验新因子的真实增量 Alpha，以及在高维状态空间中对策略改进进行双稳健反事实回报归因。接下来请另外两位组员结合各自实习或研究场景依次介绍模型应用价值。",
        # 15
        "以上为本研究依托的核心文献索引，以及围绕 DML 与 PSM 本质差异、无交叉拟合过拟合机制、多学习器选择逻辑与未观测混杂检验准备的四项核心 Q&A 议题，敬请各位老师和同学批评指正！",
    ]

    slides: List[str] = []

    # Slide 1: Cover
    slides.append(
        f'<section class="slide cover" data-notes="{html.escape(notes_list[0], quote=True)}">'
        '<div class="cover-top">'
        '<span>复旦大学管理学院 · 数据科学与商务分析（DSBA）</span>'
        '<span class="cover-pill">Chernozhukov et al. (2018) · 高维因果推断</span>'
        '</div>'
        '<div class="cover-main">'
        '<div class="cover-kicker">《现代统计模型及应用》课程大作业汇报</div>'
        '<h1 class="cover-title">双重机器学习（DML）与高维因果推断：<br>理论原理、模拟验证与 401(k) 实证研究</h1>'
        f'<p class="cover-sub">针对高维非线性混杂下传统参数回归误设与直接机器学习推断失效的难题，系统阐述 Neyman 正交化与 K-折交叉拟合理论；通过 B={cfg["B"]} 次 Monte Carlo 模拟验证有限样本性能，并应用于 {emp["n"]:,} 户美国家庭 401(k) 养老金净储蓄因果效应评估。</p>'
        '<div class="cover-kpis">'
        '<div class="cover-kpi">'
        f'<div class="val">{sim[3]["coverage_95_pct"]:.1f}% vs. 0.0%</div>'
        '<div class="lbl">模拟 95% 置信区间覆盖率</div>'
        f'<div class="desc">完整 DML 均值 {sim[3]["mean_est"]:.3f}（真值 2.0，RMSE {sim[3]["rmse"]:.3f}），其余三种方法覆盖率均为 0.0%</div>'
        '</div>'
        '<div class="cover-kpi">'
        f'<div class="val">+$7,822 ~ +${irm["HistGradientBoosting"]["ATE"]["est"]:,.0f}</div>'
        '<div class="lbl">四类学习器 IRM-ATE 收敛区间</div>'
        f'<div class="desc">标准误降至 $1,142–$1,250；以 e401 为工具变量测得实际参与 LATE 达 +${late["est"]:,.0f}</div>'
        '</div>'
        '<div class="cover-kpi">'
        f'<div class="val">Q4 +${gates[3]["gate"]:,.0f} ｜ Q1 {gates[0]["effect_to_income_pct"]:.1f}%</div>'
        '<div class="lbl">收入四分位异质性（GATE）</div>'
        f'<div class="desc">高收入组绝对增量最大，低收入组（+${gates[0]["gate"]:,.0f}）占其中位年收达 36.6%（p&lt;0.001）</div>'
        '</div>'
        '</div>'
        '</div>'
        '<div class="cover-bottom">'
        '<span>汇报框架：模型介绍 → 模拟分析 → 研究背景与数据 → 实证分析 → 结论与拓展（12+3 分钟）</span>'
        '<span>小组成员：陈霖、组员 B、组员 C</span>'
        '</div>'
        '</section>'
    )

    # Slide 2: Literature Review & Method Positioning
    s2_body = (
        '<div class="lead-banner">'
        '<strong>方法论演进脉络：</strong>高维数据下因果推断需兼顾“高维非线性混杂控制”与“√n 渐近有效推断”，DML 融合了半参数正交得分、双稳健估计与机器学习正则化理论，具体脉络与方法对比如下：'
        '</div>'
        '<div class="grid-4">'
        '<div class="card blue"><div class="card-hd" style="font-size:18px;">1. 潜在结果与匹配</div><p class="p-text" style="font-size:16px;line-height:1.42;">Neyman (1923)、Rubin (1974) 与 Rosenbaum &amp; Rubin (1983) 奠定条件可忽略性与倾向得分匹配基础。</p></div>'
        '<div class="card blue"><div class="card-hd" style="font-size:18px;">2. 半参数残差化</div><p class="p-text" style="font-size:16px;line-height:1.42;">Robinson (1988) 提出部分线性回归（PLR）去残差方法，在低维非参数场景实现 √n-一致性。</p></div>'
        '<div class="card blue"><div class="card-hd" style="font-size:18px;">3. 双稳健 AIPW</div><p class="p-text" style="font-size:16px;line-height:1.42;">Robins 等 (1994) 联合结果回归与倾向得分加权构建双稳健得分，降低单方程误设风险。</p></div>'
        '<div class="card teal"><div class="card-hd" style="font-size:18px;">4. 高维去偏 DML</div><p class="p-text" style="font-size:16px;line-height:1.42;">Belloni 等 (2014) 与 Chernozhukov 等 (2018) 结合正交化与交叉拟合，打通机器学习因果推断。</p></div>'
        '</div>'
        '<table class="tbl" style="font-size:15.5px;">'
        '<thead><tr><th>因果估计方法</th><th>核心思想与参数设定</th><th>非线性与高维适应性</th><th>渐近推断性质</th><th class="num-col">核心优势与局限</th></tr></thead>'
        '<tbody>'
        '<tr><td style="padding:7px 9px;">线性 OLS 回归</td><td style="padding:7px 9px;">假定协变量 X 对 Y 线性可加</td><td style="padding:7px 9px;">难以捕捉高阶非线性与交互</td><td style="padding:7px 9px;">函数误设时产生系统偏误</td><td class="num-col" style="padding:7px 9px;">结构透明，但易低估非线性混杂</td></tr>'
        '<tr><td style="padding:7px 9px;">二次多项式 OLS</td><td style="padding:7px 9px;">手工构造平方与交叉项</td><td style="padding:7px 9px;">高维下特征维数呈 O(p²) 膨胀</td><td style="padding:7px 9px;">过拟合导致方差显著放大</td><td class="num-col" style="padding:7px 9px;">依赖先验设定，外推稳定性较弱</td></tr>'
        '<tr><td style="padding:7px 9px;">PSM 1:1 倾向得分匹配</td><td style="padding:7px 9px;">基于 Logit 倾向得分近邻配对</td><td style="padding:7px 9px;">受限于参数化倾向得分模型</td><td style="padding:7px 9px;">Bootstrap 推断，丢弃未配对样本</td><td class="num-col" style="padding:7px 9px;">匹配直观，但 ATT 方差偏高</td></tr>'
        '<tr><td style="padding:7px 9px;">直接 ML 代入估计</td><td style="padding:7px 9px;">仅对结果 Y 用树/正则回归去趋势</td><td style="padding:7px 9px;">擅长拟合高维非线性特征交互</td><td class="hl-red" style="padding:7px 9px;">一阶偏误发散，CI 覆盖率崩溃</td><td class="num-col hl-red" style="padding:7px 9px;">预测精度高，但不可直代因果推断</td></tr>'
        '<tr class="hl-row"><td style="padding:7px 9px;">双重机器学习 (DML)</td><td style="padding:7px 9px;">Neyman 正交化 ＋ K-折交叉拟合</td><td style="padding:7px 9px;">兼容 Lasso/Ridge/RF/GBDT 模型</td><td style="padding:7px 9px;">在 o(n⁻¹/⁴) 速率下恢复 √n 正态</td><td class="num-col" style="padding:7px 9px;">兼具非线性拟合与合法置信区间</td></tr>'
        '</tbody>'
        '</table>'
    )
    slides.append(wrap_slide(2, 0, "一、模型背景与文献综述：高维因果推断的演进脉络",
                           "", s2_body, notes_list[1]))

    # Slide 3: Model Principle I - PLR & Two Biases
    s3_body = (
        '<div class="card blue" style="padding:8px 14px;">'
        '<div class="card-hd">基础设定：Robinson (1988) 部分线性因果模型（PLR）与条件外生性</div>'
        '<div class="row" style="align-items:center;">'
        '<div class="math-box" style="flex:1.25;font-size:18px;">Y = θ₀ D + g₀(X) + ζ，&nbsp; E[ζ | X, D] = 0 &nbsp;&nbsp;|&nbsp;&nbsp; D = m₀(X) + V，&nbsp; E[V | X] = 0</div>'
        '<p class="p-text" style="flex:1;font-size:16.5px;line-height:1.42;">其中 <span class="hl">θ₀</span> 为待估结构因果效应，<span class="hl">g₀(X)</span> 与 <span class="hl">m₀(X)</span> 为高维未知非线性扰动函数，高维情形下需由机器学习算法估计。</p>'
        '</div>'
        '</div>'
        '<div class="grid-2" style="flex:1;">'
        '<div class="card red" style="padding:11px 15px;gap:8px;">'
        '<div class="card-hd" style="font-size:19.5px;">偏误机制一：正则化偏误（Regularization Bias）</div>'
        '<p class="p-text" style="font-size:17.5px;line-height:1.48;">若仅用森林或 Lasso 拟合 <span class="hat">g</span>(X) 并直接将残差 (Y − <span class="hat">g</span>(X)) 对 D 回归，正则化惩罚使 <span class="hat">g</span> 收敛速度慢于 √n（仅 O<sub>p</sub>(n<sup>−1/4</sup>)）：</p>'
        '<div class="math-box" style="border-left-color:#B91C1C;font-size:17px;padding:8px 10px;">'
        '√n (<span class="hat">θ</span><sub>plug</sub> − θ₀) ≈ <span class="frac"><span class="num">1</span><span class="den">√n</span></span> ∑ m₀(X<sub>i</sub>)(g₀(X<sub>i</sub>) − <span class="hat">g</span>(X<sub>i</sub>)) ≈ √n·n<sup>−1/4</sup> = n<sup>+1/4</sup> → ∞'
        '</div>'
        '<ul class="ul" style="font-size:17.5px;line-height:1.48;gap:8px;">'
        '<li><span class="hl-red">一阶泄露效应</span>：因 m₀(X) ≠ 0，扰动估计的一阶偏误乘以 √n 后直接渗入 <span class="hat">θ</span><sub>plug</sub>。</li>'
        '<li><span class="hl-red">推断失效后果</span>：点估计系统偏移且标准误低估不确定性，95% 区间覆盖率坍塌至零。</li>'
        '</ul>'
        '</div>'
        '<div class="card amber" style="padding:11px 15px;gap:8px;">'
        '<div class="card-hd" style="font-size:19.5px;">偏误机制二：过拟合偏误（Overfitting Bias）</div>'
        '<p class="p-text" style="font-size:17.5px;line-height:1.48;">即便同时对结果 Y 与处置 D 做残差化，若在<strong>同一全样本</strong>上直接训练高复杂度模型（如深层随机森林）并提取样本内残差：</p>'
        '<div class="math-box" style="border-left-color:#D97706;font-size:17px;padding:8px 10px;">'
        'E<sub>n</sub>[<span class="hat">v</span><sub>in</sub> · (<span class="hat">u</span><sub>in</sub> − θ₀<span class="hat">v</span><sub>in</sub>)] ≠ 0 &nbsp;（模型同时记忆扰动噪声 ζ<sub>i</sub> 与 V<sub>i</sub>）'
        '</div>'
        '<ul class="ul" style="font-size:17.5px;line-height:1.48;gap:8px;">'
        '<li><span class="hl-amber">样本内伪相关</span>：高自由度学习器过度拟合样本噪声，诱发两项残差间的人为相关。</li>'
        '<li><span class="hl-amber">破坏无偏条件</span>：经验正交矩偏离零均值条件，同样造成显著偏误并破坏渐近正态分布。</li>'
        '</ul>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(3, 0, "二、模型原理（一）：部分线性框架与机器学习的两类偏误",
                           "直接套用机器学习会受到 n⁻¹/⁴ 正则化偏误与样本内过拟合偏误双重侵蚀，导致统计推断失效",
                           s3_body, notes_list[2]))

    # Slide 4: Model Principle II - Neyman Orthogonality
    s4_body = (
        '<div class="grid-2" style="flex:1;">'
        '<div class="card blue" style="padding:11px 15px;gap:7px;">'
        '<div class="card-hd" style="font-size:19.5px;">支柱一：Neyman 正交得分构造（一阶敏感度归零）</div>'
        '<p class="p-text" style="font-size:17.2px;line-height:1.46;">不直接估 g₀(X)，而是同时对 <span class="hl">ℓ(X) = E[Y | X]</span> 与 <span class="hl">m(X) = E[D | X]</span> 建模，构造去残差正交得分：</p>'
        '<div class="math-box" style="font-size:17.5px;padding:7px 10px;">'
        'ψ(W; θ, ℓ, m) = (Y − ℓ(X) − θ(D − m(X))) · (D − m(X))'
        '</div>'
        '<ul class="ul" style="font-size:17.2px;line-height:1.46;gap:7px;">'
        '<li><span class="hl">正交矩估计量</span>：令 E<sub>n</sub>[ψ]=0 得 <span class="hat">θ</span><sub>DML</sub> = (<span class="hat">v</span><sup>T</sup><span class="hat">u</span>) / (<span class="hat">v</span><sup>T</sup><span class="hat">v</span>)，其中 <span style="white-space:nowrap;">u = Y − <span class="hat">ℓ</span>(X)</span>，<span style="white-space:nowrap;">v = D − <span class="hat">m</span>(X)</span>。</li>'
        '<li><span class="hl">Neyman 正交性</span>：真值 η₀=(ℓ₀, m₀) 处 Gateaux 导数为零 <span class="hl-teal">∂<sub>η</sub> E[ψ(W; θ₀, η₀)] = 0</span>，一阶扰动偏误完全消除。</li>'
        '</ul>'
        '</div>'
        '<div class="card" style="padding:11px 15px;gap:7px;">'
        '<div class="card-hd" style="font-size:19.5px;">渐近理论保证：二阶误差乘积与三明治方差估计</div>'
        '<ul class="ul" style="font-size:17.2px;line-height:1.46;gap:7px;">'
        '<li><span class="hl">为什么只需慢收敛学习器？</span>一阶偏误消除后，主导偏误转化为两预测器估计误差乘积与倾向误差平方和。</li>'
        '<li><span class="hl">√n-一致性（Chernozhukov et al., 2018 Thm 3.1）</span><br>在正则与交叉拟合条件下 √n(<span class="hat">θ</span><sub>DML</sub> − θ₀) →<sub>d</sub> N(0, σ²)，渐近方差为三明治形式：</li>'
        '</ul>'
        '<div class="math-box" style="font-size:17.5px;padding:7px 10px;">'
        'σ² = J₀<sup>−1</sup> E[ψ(W; θ₀, η₀)²] (J₀<sup>−1</sup>)<sup>T</sup>，&nbsp; J₀ = −E[(D − m₀(X))²]'
        '</div>'
        '<p class="p-text" style="font-size:16.5px;line-height:1.42;">Eicker-Huber-White 异方差稳健标准误与 95% 置信区间重新具备严格统计合法性。</p>'
        '</div>'
        '</div>'
        '<div class="card dark" style="padding:9px 15px;gap:5px;">'
        '<div class="card-hd" style="font-size:18px;">关键收敛阶数条件：从 O(n⁻¹/⁴) 预测精度到 o(n⁻¹/²) 因果推断</div>'
        '<div class="row" style="align-items:center;">'
        '<div style="font-size:25px;font-weight:700;color:#FBBF24;min-width:500px;">||<span class="hat">ℓ</span> − ℓ₀||₂ × ||<span class="hat">m</span> − m₀||₂ = O<sub>p</sub>(n<sup>−1/4</sup>) × O<sub>p</sub>(n<sup>−1/4</sup>) = o<sub>p</sub>(n<sup>−1/2</sup>)</div>'
        '<p class="p-text" style="flex:1;font-size:16px;line-height:1.38;">只要结果与处置学习器的 L₂ 误差速率快于 <span style="color:#7DD3FC;font-weight:700;">n<sup>−1/4</sup></span>（如 Lasso、随机森林、GBDT 或神经网络），二阶乘积即快于 n<sup>−1/2</sup>，不影响主参数 √n 渐近正态分布。</p>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(4, 0, "二、模型原理（二）：Neyman 正交化与误差二阶乘积收敛",
                           "正交得分令一阶导数为零，将主导偏误压缩为两预测器误差乘积 n⁻¹/⁴×n⁻¹/⁴ = o(n⁻¹/²)",
                           s4_body, notes_list[3]))

    # Slide 5: Model Principle III - Cross-Fitting & Unified Framework
    s5_body = (
        '<div class="card" style="padding:8px 14px;">'
        '<div class="card-hd" style="font-size:18.5px;">支柱二：K-折交叉拟合（Cross-Fitting）与多次切分聚合（Chernozhukov et al., 2018 Def. 3.3）</div>'
        '<svg viewBox="0 0 1160 108" style="width:100%;height:102px;">'
        '<rect x="6" y="8" width="112" height="52" rx="6" fill="#0E7490"/><text x="62" y="30" text-anchor="middle" fill="#FFF" font-size="15.5" font-weight="700">Fold 1 (验证)</text><text x="62" y="50" text-anchor="middle" fill="#E0F2FE" font-size="13.5">计算折外残差</text>'
        '<rect x="124" y="8" width="112" height="52" rx="6" fill="#0A365C"/><text x="180" y="30" text-anchor="middle" fill="#FFF" font-size="15.5" font-weight="700">Fold 2 (训练)</text><text x="180" y="50" text-anchor="middle" fill="#CBD5E1" font-size="13.5">训练 ℓ⁻¹ 与 m⁻¹</text>'
        '<rect x="242" y="8" width="112" height="52" rx="6" fill="#0A365C"/><text x="298" y="30" text-anchor="middle" fill="#FFF" font-size="15.5" font-weight="700">Fold 3 (训练)</text><text x="298" y="50" text-anchor="middle" fill="#CBD5E1" font-size="13.5">训练 ℓ⁻¹ 与 m⁻¹</text>'
        '<rect x="360" y="8" width="112" height="52" rx="6" fill="#0A365C"/><text x="416" y="30" text-anchor="middle" fill="#FFF" font-size="15.5" font-weight="700">Fold 4 (训练)</text><text x="416" y="50" text-anchor="middle" fill="#CBD5E1" font-size="13.5">训练 ℓ⁻¹ 与 m⁻¹</text>'
        '<rect x="478" y="8" width="112" height="52" rx="6" fill="#0A365C"/><text x="534" y="30" text-anchor="middle" fill="#FFF" font-size="15.5" font-weight="700">Fold 5 (训练)</text><text x="534" y="50" text-anchor="middle" fill="#CBD5E1" font-size="13.5">训练 ℓ⁻¹ 与 m⁻¹</text>'
        '<rect x="604" y="6" width="548" height="90" rx="8" fill="#F0F6FC" stroke="#0A365C" stroke-width="1.4"/>'
        '<text x="618" y="30" fill="#0A365C" font-size="15.5" font-weight="700">切断过拟合伪相关并保持 100% 样本效率：</text>'
        '<text x="618" y="55" fill="#1E293B" font-size="14.5">① 轮流将各折设为验证折，汇聚全部 N 个折外正交残差统一求解矩方程；</text>'
        '<text x="618" y="80" fill="#1E293B" font-size="14.5">② 重复 R=5 次随机分层切分，取中位数点估计与 SE √(s²+(θ_r−θ_med)²)。</text>'
        '<text x="6" y="90" fill="#0E7490" font-size="14.5" font-weight="700">→ 训练折噪声与验证折正交残差条件独立，彻底消除样本内过拟合偏误。</text>'
        '</svg>'
        '</div>'
        '<div class="grid-3" style="flex:1;">'
        '<div class="card" style="padding:11px 14px;gap:8px;">'
        '<div class="card-hd" style="font-size:18.5px;">1. PLR 部分线性回归</div>'
        '<div class="math-box" style="font-size:17.5px;padding:7px 8px;">Y = θ₀ D + g₀(X) + ζ</div>'
        '<ul class="ul" style="font-size:17px;line-height:1.46;gap:7px;">'
        '<li>假定处置变量对结果的平均因果斜率 θ₀ 为常数。</li>'
        '<li>分别用机器学习拟合 ℓ(X)=E[Y|X] 与 m(X)=E[D|X]。</li>'
        '<li>结构简洁、方差低，适合作为基准稳健性对照。</li>'
        '</ul>'
        '</div>'
        '<div class="card blue" style="padding:11px 14px;gap:8px;">'
        '<div class="card-hd" style="font-size:18.5px;">2. IRM 交互回归（异质性）</div>'
        '<div class="math-box" style="font-size:14.8px;padding:6px 8px;">φ<sub>i</sub> = g(1,X)−g(0,X) + D(Y−g(1,X))/m(X)<br>− (1−D)(Y−g(0,X))/(1−m(X))</div>'
        '<ul class="ul" style="font-size:17px;line-height:1.46;gap:7px;">'
        '<li>基于双稳健 AIPW 得分，允许处置效应随 X 任意变化。</li>'
        '<li>同时估 ATE、ATT，且可按组平均正交伪结果 <span class="hat">φ</span><sub>i</sub> 求得 <span class="hl-teal">GATE</span>。</li>'
        '</ul>'
        '</div>'
        '<div class="card teal" style="padding:11px 14px;gap:8px;">'
        '<div class="card-hd" style="font-size:18.5px;">3. IIVM 交互工具变量</div>'
        '<div class="math-box" style="font-size:17px;padding:7px 8px;">LATE = E[ITT<sub>Y</sub>] / E[ITT<sub>D</sub>]</div>'
        '<ul class="ul" style="font-size:17px;line-height:1.46;gap:7px;">'
        '<li>针对不完全服从的内生处置场景，引入合法工具变量 Z。</li>'
        '<li>在控制高维非线性混杂后，通过双稳健得分识别依从者（Compliers）的局部平均效应 LATE。</li>'
        '</ul>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(5, 0, "二、模型原理（三）：K-折交叉拟合与 PLR / IRM / IIVM 统一框架",
                           "折外交叉拟合切断过拟合通道，并将同一正交机制拓展至异质性处理效应（IRM）与工具变量（IIVM）",
                           s5_body, notes_list[4]))

    # Slide 6: Simulation Analysis I
    s6_body = (
        '<div class="lead-banner">'
        f'<strong>研究问题与方法说明：</strong>针对“高维非线性混杂下的偏误机制与渐近正态性（定理 3.1）”，构建 B={cfg["B"]} 次、n={cfg["n"]}、p={cfg["p"]} 维（真值 θ₀={cfg["theta0"]:.1f}）Monte Carlo 模拟。结果表明<strong>仅完整 DML 居中无偏且通过 N(0,1) 正态检验（KS p={ts_norm["ks_p"]:.3f}）</strong>：'
        '</div>'
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.42;">'
        '<img src="../outputs/figures/fig1_simulation_bias_distribution.png" alt="图1 模拟抽样分布与t统计量正态性检验"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd" style="font-size:17.5px;">数据生成过程（DGP）与模型设定</div>'
        '<ul class="ul compact" style="font-size:15.5px;">'
        f'<li><span class="hl">规模</span>：X ~ N(0, I₂₀)，前 6 维为有效混杂，后 14 维为无关噪声；真值 θ₀ = {cfg["theta0"]:.1f}。</li>'
        '<li><span class="hl">非线性项</span>：m₀(X) 与 g₀(X) 含平方与二阶交互项；DML 用二阶展开（230 维）+ LassoCV 做 5-折交叉拟合。</li>'
        '</ul>'
        '</div>'
        '<div class="card" style="flex:1;">'
        '<div class="card-hd" style="font-size:17.5px;">抽样分布与 Thm 3.1 t-统计量正态性诊断</div>'
        '<ul class="ul compact" style="font-size:15.5px;">'
        f'<li><span class="hl">Naive OLS ({sim[0]["mean_est"]:.3f})</span> / <span class="hl-amber">Direct ML ({sim[1]["mean_est"]:.3f})</span> / <span class="hl-red">无交叉拟合 ({sim[2]["mean_est"]:.3f})</span> 均严重偏离真值且 t 统计量偏离 N(0,1)。</li>'
        f'<li><span class="hl-teal">完整 DML ({sim[3]["mean_est"]:.3f})</span>：偏误仅 {sim[3]["bias"]:+.3f}；t 统计量均值 {ts_norm["t_mean"]:+.3f}、SD {ts_norm["t_sd"]:.3f}，KS 检验 p = <span class="hl-teal">{ts_norm["ks_p"]:.3f}</span>（不拒绝标准正态）。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(6, 1, "三、模拟分析（一）：非线性高维混杂 DGP、抽样分布与正态性校验",
                           "", s6_body, notes_list[5]))

    # Slide 7: Simulation Analysis II
    rows7 = []
    for r in sim:
        cls = ' class="hl-row"' if "完整 DML" in r["method"] else ""
        rows7.append(
            f'<tr{cls}><td>{r["method"]}</td>'
            f'<td class="num-col">{r["mean_est"]:.3f}</td>'
            f'<td class="num-col">{r["bias"]:+.3f}</td>'
            f'<td class="num-col">{r["emp_sd"]:.3f}</td>'
            f'<td class="num-col">{r["mean_se"]:.3f}</td>'
            f'<td class="num-col">{r["rmse"]:.3f}</td>'
            f'<td class="num-col">{r["coverage_95_pct"]:.1f}%</td></tr>'
        )
    s7_body = (
        '<div class="lead-banner">'
        f'<strong>定量与跨样本量评估：</strong>扩展样本量至 n ∈ {{250, 500, 1000, 2000}} 检验 O(n<sup>−1/2</sup>) 收敛速率与区间覆盖率分化。结果表明<strong>完整 DML 将 n=1000 下 RMSE 降至 {sim[3]["rmse"]:.3f} 且覆盖率达 {sim[3]["coverage_95_pct"]:.1f}%</strong>：'
        '</div>'
        '<div class="row" style="flex:1.18;">'
        '<div class="fig-box" style="flex:1.85;">'
        '<img src="../outputs/figures/fig2_simulation_coverage_rmse.png" alt="图2 跨样本量RMSE收敛速率与95%覆盖率分化"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card dark" style="flex:1;justify-content:center;">'
        '<div class="card-hd" style="font-size:18px;">O(n<sup>−1/2</sup>) 收敛与推断有效性</div>'
        f'<div style="font-size:32px;font-weight:700;color:#86EFAC;">{sim[3]["coverage_95_pct"]:.1f}% <span style="font-size:16.5px;color:#CBD5E1;">vs. 0.0%</span></div>'
        '<ul class="ul compact" style="font-size:15.2px;">'
        f'<li><span style="color:#7DD3FC;font-weight:700;">RMSE 严格贴合理论线</span>：n 由 250 增至 2000 时，完整 DML RMSE 由 {scaling_dml[0]["rmse"]:.3f} 稳定降至 {scaling_dml[-1]["rmse"]:.3f}，覆盖率保持 90%–96.5%。</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">非正交/不切分随大样本恶化</span>：系统偏误不随 n 消退，n=1000 时前三种方法覆盖率全部塌缩至 0.0%。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
        '<table class="tbl" style="font-size:14.6px;">'
        '<thead><tr><th>模拟估计方法 (B=200, n=1000, p=20, θ₀=2.0)</th><th class="num-col">估计均值</th><th class="num-col">偏误 Bias</th><th class="num-col">经验 SD</th><th class="num-col">平均理论 SE</th><th class="num-col">RMSE</th><th class="num-col">95% 区间覆盖率</th></tr></thead>'
        f'<tbody>{"".join(rows7)}</tbody>'
        '</table>'
    )
    slides.append(wrap_slide(7, 1, "三、模拟分析（二）：O(n⁻¹/²) 收敛速率、RMSE 与置信区间覆盖率检验",
                           "", s7_body, notes_list[6]))

    # Slide 8: Empirical Background & Data Diagnostics
    s8_body = (
        '<div class="lead-banner">'
        f'<strong>研究背景与数据诊断：</strong>基于 1991 SIPP 家庭金融数据（N={emp["n"]:,}，零缺失值），依次检验收入十分位非线性混杂结构与 DML 加权前后协变量平衡性。诊断显示<strong>原始差距 +$19,559 存在严重失衡，而 DML 加权后全项 |SMD| 降至 &lt;0.06</strong>：'
        '</div>'
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.42;">'
        '<img src="../outputs/figures/fig3_401k_eda_confounding.png" alt="图3 收入十分位非线性特征与Love Plot平衡性检验"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd" style="font-size:17.5px;">非线性混杂与资格陡增特征（图 3a）</div>'
        '<ul class="ul compact" style="font-size:15.4px;">'
        f'<li><span class="hl">处置与净资产分布</span>：雇主资格 e401 占 37.1%（{emp["treated_e401"]:,} vs {emp["control_e401"]:,}），实际参与率 {emp["compliers_p401_given_e401"]*100:.2f}%；net_tfa 中位数仅 $1,499、原始均值差 <span class="hl-red">+${base["naive_diff"]["est"]:,.0f}</span>。</li>'
        '<li><span class="hl">双陡增选择偏误</span>：收入由 D1（$9k）升至 D10（$86k）时，401(k) 资格率由 9.0% 陡增至 60.9%，且净金融资产呈指数跃升（~$7k→$83.7k）。</li>'
        '</ul>'
        '</div>'
        '<div class="card teal" style="flex:1;">'
        '<div class="card-hd" style="font-size:17.5px;">Covariate Balance Love Plot 去混杂检验（图 3b）</div>'
        '<ul class="ul compact" style="font-size:15.4px;">'
        f'<li><span class="hl-red">加权前严重失衡</span>：9 维控制变量中 7 项 |SMD| &gt; 0.1，年收入 inc（{love["inc"]["smd"]:+.3f}）、DB 养老金（{love["db"]["smd"]:+.3f}）与自有住房（{love["hown"]["smd"]:+.3f}）高度偏向处置组。</li>'
        f'<li><span class="hl-teal">DML 交叉拟合 IPW 加权后全项达标</span>：全部 9 项协变量收敛入 |SMD| &lt; 0.1 绿区（inc 降至 {abs(love["inc"]["ipw_smd"]):.3f}，db 降至 {abs(love["db"]["ipw_smd"]):.3f}）。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(8, 2, "四、实证研究背景与数据诊断：非线性选择偏误与 DML 平衡性检验",
                           "", s8_body, notes_list[7]))

    # Slide 9: Empirical Analysis I - Forest Plot, First-Stage & K-Fold Stability
    s9_body = (
        '<div class="lead-banner">'
        '<strong>主效应识别与超参稳健性：</strong>在同一 9 维协变量下对比传统基准、四类算法 DML-PLR/IRM，并检验第一阶段精度与 K-折稳健性。结果表明 <strong>DML-IRM 稳健收敛于 +$7,822 至 +$8,693 且对折数与截断高度不敏感</strong>：'
        '</div>'
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.38;">'
        '<img src="../outputs/figures/fig4_401k_model_comparison_forest.png" alt="图4 传统方法与DML森林图、第一阶段精度与K折稳健性"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card">'
        '<div class="card-hd" style="font-size:17px;">跨四类学习器 DML 稳健性（5 次切分中位数）</div>'
        '<table class="tbl" style="font-size:13.8px;">'
        '<thead><tr><th>底层机器学习器</th><th class="num-col">PLR 估计 (SE)</th><th class="num-col">IRM ATE (SE)</th></tr></thead>'
        '<tbody>'
        f'<tr><td>Lasso (高维多项式)</td><td class="num-col">+${plr["Lasso (高维多项式)"]["est"]:,.0f} (${plr["Lasso (高维多项式)"]["se"]:,.0f})</td><td class="num-col">+${irm["Lasso + L1-Logit"]["ATE"]["est"]:,.0f} (${irm["Lasso + L1-Logit"]["ATE"]["se"]:,.0f})</td></tr>'
        f'<tr><td>Ridge (高维多项式)</td><td class="num-col">+${plr["Ridge (高维多项式)"]["est"]:,.0f} (${plr["Ridge (高维多项式)"]["se"]:,.0f})</td><td class="num-col">+${irm["Ridge + L2-Logit"]["ATE"]["est"]:,.0f} (${irm["Ridge + L2-Logit"]["ATE"]["se"]:,.0f})</td></tr>'
        f'<tr><td>Random Forest</td><td class="num-col">+${plr["Random Forest"]["est"]:,.0f} (${plr["Random Forest"]["se"]:,.0f})</td><td class="num-col">+${irm["Random Forest"]["ATE"]["est"]:,.0f} (${irm["Random Forest"]["ATE"]["se"]:,.0f})</td></tr>'
        f'<tr class="hl-row"><td>HistGradientBoosting</td><td class="num-col">+${plr["HistGradientBoosting"]["est"]:,.0f} (${plr["HistGradientBoosting"]["se"]:,.0f})</td><td class="num-col">+${irm["HistGradientBoosting"]["ATE"]["est"]:,.0f} (${irm["HistGradientBoosting"]["ATE"]["se"]:,.0f})</td></tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '<div class="card blue" style="flex:1;">'
        '<div class="card-hd" style="font-size:17px;">对比发现、扰动精度（图 4b）与 K-折稳健性（图 4c）</div>'
        '<ul class="ul compact" style="font-size:15px;">'
        f'<li><span class="hl">精度占优</span>：IRM 标准误（$1,142–$1,250）明显低于线性 OLS（$1,524，且偏低至 +$5,896）和 PSM ATT（$3,026）；HGB 下 ATT 达 <span class="hl-teal">+${irm["HistGradientBoosting"]["ATT"]["est"]:,.0f}</span>。</li>'
        '<li><span class="hl">第一阶段折外预测</span>：四类学习器倾向得分 AUC 均达 <span class="hl-teal">0.734–0.740</span>，结果折外 R² 为 0.232–0.283。</li>'
        f'<li><span class="hl">K-折与截断不敏感</span>：K ∈ {{2,3,5,10}} 下 HGB ATE 仅微幅波动于 +${stab[3]["est"]:,.0f} ~ +${stab[2]["est"]:,.0f}；截断 0.01/0.05/0.10 稳定于 +$8,641 ~ +$8,693。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(9, 3, "五、实证分析（一）：主效应对比、第一阶段诊断与 K-折稳健性",
                           "", s9_body, notes_list[8]))

    # Slide 10: Empirical Analysis II - Overlap, OVB Sensitivity & IV LATE
    s10_body = (
        '<div class="lead-banner">'
        f'<strong>假设核验、OVB 敏感性与工具变量：</strong>依次检验倾向得分重叠度、Chernozhukov 等 (2022) 非参数 OVB 边界、剔除 pira 重估与 IIVM 工具变量效应。结果证实<strong>重叠充分，稳健阈值 RV={ovb["rv_point_pct"]:.1f}%（CI {ovb["rv_ci95_pct"]:.1f}%），LATE 达 +${late["est"]:,.0f}</strong>：'
        '</div>'
        '<div class="row" style="flex:1;">'
        '<div class="col" style="flex:1.25;">'
        '<div class="fig-box" style="flex:1;">'
        '<img src="../outputs/figures/fig5_401k_propensity_overlap.png" alt="图5 倾向得分重叠性与OVB非参数敏感性边界"/>'
        '</div>'
        '<div class="note-strip" style="font-size:14.2px;">'
        f'<strong>OVB 定量敏感性（图 5b）：</strong>若未观测混杂解释力等同 <span class="hl">1× db</span> 或 <span class="hl">1× pira</span>，ATE 下界仍高达 <strong>+${ovb_b["db"]["theta_lower_1x"]:,.0f}</strong> 与 <strong>+${ovb_b["pira"]["theta_lower_1x"]:,.0f}</strong>；仅当媲美年收入 inc（R²=24.2%）方能逆转。核心支撑 [{ps["hgb_ps_p05"]:.3f}, {ps["hgb_ps_p95"]:.3f}]。'
        '</div>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card">'
        '<div class="card-hd" style="font-size:17px;">特征剥离敏感性：剔除个人退休账户 pira</div>'
        '<p class="p-text compact" style="font-size:14.5px;">排除主观储蓄偏好关联变量 pira 后以 8 项协变量重估 HGB：</p>'
        '<table class="tbl" style="font-size:13.8px;">'
        '<thead><tr><th>HGB 模型设定</th><th class="num-col">9 协变量基准</th><th class="num-col">剔除 pira (8 协变量)</th></tr></thead>'
        '<tbody>'
        f'<tr><td>DML-PLR</td><td class="num-col">+${plr["HistGradientBoosting"]["est"]:,.0f}</td><td class="num-col">+${sens["dml_plr_hgb"]["est"]:,.0f} (SE ${sens["dml_plr_hgb"]["se"]:,.0f})</td></tr>'
        f'<tr class="hl-row"><td>DML-IRM (ATE)</td><td class="num-col">+${irm["HistGradientBoosting"]["ATE"]["est"]:,.0f}</td><td class="num-col">+${sens["dml_irm_hgb_ATE"]["est"]:,.0f} (SE ${sens["dml_irm_hgb_ATE"]["se"]:,.0f})</td></tr>'
        f'<tr><td>DML-IRM (ATT)</td><td class="num-col">+${irm["HistGradientBoosting"]["ATT"]["est"]:,.0f}</td><td class="num-col">+${sens["dml_irm_hgb_ATT"]["est"]:,.0f} (SE ${sens["dml_irm_hgb_ATT"]["se"]:,.0f})</td></tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '<div class="card dark" style="flex:1;">'
        '<div class="card-hd" style="font-size:17px;">工具变量拓展（DML-IIVM）：实际参与效应 LATE</div>'
        f'<div style="font-size:27px;font-weight:700;color:#FBBF24;">LATE = +${late["est"]:,.0f} <span style="font-size:15px;color:#CBD5E1;">(SE ${late["se"]:,.0f})</span></div>'
        '<ul class="ul compact" style="font-size:14.8px;">'
        f'<li>合格家庭实际参与 p401 占比为 <span style="color:#7DD3FC;font-weight:700;">{emp["compliers_p401_given_e401"]*100:.2f}%</span>（无资格组 0%，严格单边服从）。</li>'
        f'<li>以 e401 为工具变量，依从者净增 +${late["est"]:,.0f}（95% CI [${late["ci95_low"]:,.0f}, ${late["ci95_high"]:,.0f}]），符合 ATE÷0.7045 尺度关系。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(10, 3, "五、实证分析（二）：重叠性检验、OVB 敏感性与工具变量 LATE",
                           "", s10_body, notes_list[9]))

    # Slide 11: Empirical Analysis III - 2D Income x Age GATE & DR-Learner CATE
    rows11 = []
    for i, g in enumerate(gates):
        cls = ' class="hl-row"' if i in (0, 3) else ""
        rows11.append(
            f'<tr{cls}><td>{g["quartile"]}</td>'
            f'<td class="num-col">{g["n"]:,}</td>'
            f'<td class="num-col">${g["median_inc"]:,.0f}</td>'
            f'<td class="num-col">+${g["gate"]:,.0f}</td>'
            f'<td class="num-col">${g["se"]:,.0f}</td>'
            f'<td class="num-col">[${g["ci95_low"]:,.0f}, ${g["ci95_high"]:,.0f}]</td>'
            f'<td class="num-col">{g["effect_to_income_pct"]:.1f}%</td></tr>'
        )
    q4_50 = gate_2d[("Q4 (高收入)", "50+ 岁")]["gate"]
    q1_mid = gate_2d[("Q1 (低收入)", "35–49 岁")]["gate"]
    q1_old = gate_2d[("Q1 (低收入)", "50+ 岁")]["gate"]
    s11_body = (
        '<div class="lead-banner">'
        f'<strong>二维交互异质性与连续 CATE：</strong>基于正交伪结果 <span class="hat">φ</span><sub>i</sub>，拓展至“收入 × 年龄”二维 GATE 与 Kennedy (2023) DR-Learner 连续曲线。结果揭示<strong>年龄与收入协同分化：Q4 × 50+ 岁达 +${q4_50:,.0f}</strong>：'
        '</div>'
        '<div class="row" style="flex:1.18;">'
        '<div class="fig-box" style="flex:1.68;">'
        '<img src="../outputs/figures/fig6_401k_heterogeneity_gate.png" alt="图6 二维GATE热力图与DR-Learner连续CATE曲线"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card blue" style="flex:1;justify-content:center;">'
        '<div class="card-hd" style="font-size:17.5px;">二维交互（6a）与 DR-Learner 机制（6b）</div>'
        '<ul class="ul compact" style="font-size:15px;">'
        f'<li><span class="hl">绝对峰值在 Q4×50+ 岁</span>：达 <span class="hl-teal">+${q4_50:,.0f}*</span>（n=600）；Q4×35–49 岁达 +$18,337***（n=1,342）。</li>'
        f'<li><span class="hl-amber">Q1 年龄结构显著分化</span>：35 岁前仅 +$155（刚性支出束缚），而 35–49 岁与 50+ 岁升至 <span class="hl">+${q1_mid:,.0f}***</span> 与 +${q1_old:,.0f}**。</li>'
        f'<li><span class="hl">连续 CATE 曲线</span>：由 D4 低谷（+$2,004）单调爬升至 D10（+${dr_curve[-1]["dr_cate_mean"]:,.0f}），而 D1 相对年收撬动率达 <span class="hl-red">{dr_curve[0]["dr_rel_inc_pct"]:.1f}%</span>。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
        '<table class="tbl" style="font-size:14.4px;">'
        '<thead><tr><th>家庭年收入分层</th><th class="num-col">样本量</th><th class="num-col">组内中位年收</th><th class="num-col">GATE 因果增量</th><th class="num-col">标准误 SE</th><th class="num-col">95% 置信区间</th><th class="num-col">增量 / 中位年收</th></tr></thead>'
        f'<tbody>{"".join(rows11)}</tbody>'
        '</table>'
    )
    slides.append(wrap_slide(11, 3, "五、实证分析（三）：二维交互 GATE 与 DR-Learner 连续异质性",
                           "", s11_body, notes_list[10]))

    # Slide 12: Conclusions I - Model Performance & Empirical Implications
    s12_body = (
        '<div class="grid-2" style="flex:1;">'
        '<div class="card blue" style="padding:14px 18px;gap:10px;">'
        '<div class="card-hd" style="font-size:20.5px;">一、DML 模型性能综合评估（核心结论）</div>'
        '<ul class="ul" style="font-size:17.5px;line-height:1.48;gap:11px;">'
        f'<li><span class="hl">1. 理论机制验证：双支柱收敛与渐近正态</span><br>Monte Carlo 模拟验证 t 统计量服从 N(0,1)（KS p={ts_norm["ks_p"]:.3f}），n∈{{250..2000}} 严格沿 O(n<sup>−1/2</sup>) 收敛（RMSE 降至 <span class="hl-teal">0.032</span>），95% 覆盖率恢复至 <span class="hl-teal">96.5%</span>。</li>'
        '<li><span class="hl">2. 实证去混杂、多算法收敛与超参稳健性</span><br>9 项协变量 |SMD| 全部压至 0.058 以下；四类算法 IRM-ATE 紧凑收敛于 <span class="hl-teal">+$7,822 ~ +$8,693</span>，K=2..10 与截断阈值变动下结果极稳健。</li>'
        '<li><span class="hl">3. 统一框架高维敏感性与异质拓展能力</span><br>同一正交体系平滑导出 OVB 边界（RV=5.1%）、工具变量 LATE（+$12,107）与二维 GATE / DR-Learner 曲线。</li>'
        '</ul>'
        '</div>'
        '<div class="card teal" style="padding:14px 18px;gap:10px;">'
        '<div class="card-hd" style="font-size:20.5px;">二、401(k) 实证发现与商业政策决策启示</div>'
        '<ul class="ul" style="font-size:17.5px;line-height:1.48;gap:11px;">'
        '<li><span class="hl">1. 证实税收递延养老金的净储蓄创造效应</span><br>剥离年收入与 DB 等高阶混杂且经 OVB 与剔除 pira 检验后，401(k) 资格与参与仍分别净增 +$8,693 与 +$12,107，拒绝“纯资产替代”假说。</li>'
        f'<li><span class="hl">2. 金融机构分层获客：锁定中老年高收入客群</span><br>Q4 单户净增 +$20,588 且 <span class="hl-teal">Q4×50+ 岁高达 +${q4_50:,.0f}</span>，应作为个人养老金综合财富管理与净 AUM 考核的核心锚点。</li>'
        '<li><span class="hl">3. 普惠政策精准滴灌：缓解青年低收入流动性约束</span><br>Q1 相对撬动率达 36.6%（D1 达 60.2%）且 35 岁前无显著增量，宜通过“自动加入＋财政配比＋紧急支取通道”激活青年储蓄。</li>'
        '</ul>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(12, 4, "六、研究结论（一）：DML 模型性能总结与实证决策启示",
                           "DML 在有限样本渐近正态、收敛速率、去混杂平衡与跨学习器稳定性方面全面优于传统基准模型",
                           s12_body, notes_list[11]))

    # Slide 13: Conclusions II - Model Boundaries & Extensions
    s13_body = (
        '<div class="grid-2" style="flex:1;">'
        '<div class="card amber" style="padding:14px 18px;gap:10px;">'
        '<div class="card-hd" style="font-size:20.5px;">一、模型统计假设边界与现实应用局限</div>'
        '<ul class="ul" style="font-size:17.8px;line-height:1.48;gap:12px;">'
        '<li><span class="hl-amber">1. 条件可忽略性边界与强未观测混淆风险</span><br>虽已测得稳健阈值 RV=5.1%（对 db/pira 稳健），但若存在与家庭年收入同等强度的未观测储蓄意愿仍足以推翻截面因果结论，须借工具变量或纵贯设计补强。</li>'
        '<li><span class="hl-amber">2. 极端倾向得分下的逆概率权重方差膨胀</span><br>IRM 正交得分包含 1/<span class="hat">m</span>(X) 与 1/(1−<span class="hat">m</span>(X))；当极度不平衡场景下 <span class="hat">m</span>(X) 趋近 0 或 1 时，需依赖截断或重叠加权（Overlap Weights）控制方差。</li>'
        '<li><span class="hl-amber">3. 学习器速率门槛与跨时代外推限制</span><br>理论保证要求扰动估计量均达到 o(n<sup>−1/4</sup>)；此外 1991 年美国家庭截面特征外推至当代本土个人养老金制度仍须本地纵贯数据重新标定。</li>'
        '</ul>'
        '</div>'
        '<div class="card blue" style="padding:14px 18px;gap:10px;">'
        '<div class="card-hd" style="font-size:20.5px;">二、前沿方法论延伸方向</div>'
        '<ul class="ul" style="font-size:17.8px;line-height:1.48;gap:12px;">'
        '<li><span class="hl">1. 面板双重差分与双向固定效应融合（DID-DML）</span><br>将多期差分或个体固定效应嵌入 DML 正交得分，同时剥离不随时间变化的未观测个人禀赋与时变高维非线性混杂。</li>'
        '<li><span class="hl">2. 个体条件效应与可解释 Policy Tree 靶向配置</span><br>在本文 DR-Learner 连续曲线基础上结合诚实因果森林（GRF）与深度限制策略树（Policy Tree），直接输出兼顾净收益与合规解释的精准补贴规则。</li>'
        '<li><span class="hl">3. 动态序贯处理效应（Dynamic DML）</span><br>将单期资格框架推广至多年连续缴费轨迹，采用序贯双重稳健估计评估长期复利累进与提前支取规则调整的跨期总效应。</li>'
        '</ul>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(13, 4, "六、研究结论（二）：模型适用边界、局限性与前沿延伸",
                           "明确 OVB 定量边界、正性重叠与速率约束，并衔接 DID-DML、Policy Tree 与动态序贯因果推断",
                           s13_body, notes_list[12]))

    # Slide 14: 3-Min Extended Applications
    s14_body = (
        '<div class="grid-3" style="flex:1;">'
        '<div class="card blue" style="padding:13px 16px;gap:9px;">'
        '<div class="card-hd" style="font-size:19.5px;">成员 A｜陈霖（量化与 Agent RL）</div>'
        '<ul class="ul" style="font-size:17.2px;line-height:1.46;gap:9px;">'
        '<li><span class="hl">实践背景</span>：Trexquant 美股多因子实习 ＋ 上海 AI 实验室大模型与 Agent 强化学习研究。</li>'
        '<li><span class="hl">拓展 1｜真 Alpha 识别</span>：合成非线性因子时，市值与行业暴露与收益呈高维混杂；以 DML 同步正交交叉拟合，无偏检验真实增量 Alpha。</li>'
        '<li><span class="hl">拓展 2｜Agent RL 离线评估</span>：在高维状态空间借助双稳健得分做反事实回报归因，抑制奖励正则偏误。</li>'
        '</ul>'
        '</div>'
        '<div class="card" style="padding:13px 16px;gap:9px;">'
        '<div class="card-hd" style="font-size:19.5px;">成员 B｜[请填姓名]（互联网 Uplift）</div>'
        '<ul class="ul" style="font-size:17.2px;line-height:1.46;gap:9px;">'
        '<li><span class="hl">应用场景</span>：电商优惠券补贴、会员定价或流量干预评估（请结合个人实习替换）。</li>'
        '<li><span class="hl">混杂痛点</span>：历史营销偏向高活跃用户，直接对比转化率产生严重选择偏差。</li>'
        '<li><span class="hl">DML 方案</span>：GBDT 控制数十维点击复购特征，IRM 正交得分识别真正敏感客群。</li>'
        '<li><span class="hl">预期价值</span>：剔除自然转化人群，提升补贴边际 ROI。</li>'
        '</ul>'
        '</div>'
        '<div class="card teal" style="padding:13px 16px;gap:9px;">'
        '<div class="card-hd" style="font-size:19.5px;">成员 C｜[请填姓名]（信贷风控评估）</div>'
        '<ul class="ul" style="font-size:17.2px;line-height:1.46;gap:9px;">'
        '<li><span class="hl">应用场景</span>：消费信贷额度调整、分期利率优惠因果评估（请结合个人实习替换）。</li>'
        '<li><span class="hl">混杂痛点</span>：风控授信依赖非线性信用评分卡，授信额度与客户资质高度纠缠。</li>'
        '<li><span class="hl">DML 方案</span>：保留 XGBoost 吸收征信特征，输出带 95% 置信区间的提额净收益与坏账响应。</li>'
        '<li><span class="hl">边界兜底</span>：结合小比例随机保留实验组检验无未观测混杂。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '<div class="note-strip">'
        '<strong>协作提示：</strong>汇报最后 3 分钟由小组成员依次陈述（每人 ≤ 1 分钟）；成员 B、C 更新个人案例与姓名后运行 <code>python3 html_to_pptx.py --version v2</code> 即可同步更新 PPTX。'
        '</div>'
    )
    slides.append(wrap_slide(14, 4, "七、模型拓展应用：结合实习与研究领域的 3 分钟个人阐述",
                           "围绕各自业务场景界定“处置变量—高维非线性混杂—净因果目标”，说明 DML 的实际落地价值",
                           s14_body, notes_list[13]))

    # Slide 15: References & Q&A
    s15_body = (
        '<div class="row" style="flex:1;">'
        '<div class="card" style="flex:1.45;padding:12px 16px;gap:6px;">'
        '<div class="card-hd" style="font-size:18.5px;">主要学术参考文献（已核对刊名、年份与卷期页码）</div>'
        '<ul class="ul" style="font-size:14.6px;line-height:1.36;gap:5px;">'
        '<li><span class="hl">[1] Chernozhukov et al. (2018).</span> Double/debiased machine learning for treatment and structural parameters. <em>The Econometrics Journal</em>, 21(1), C1–C68.</li>'
        '<li><span class="hl">[2] Chernozhukov, V., Cinelli, C., Newey, W. K., Sharma, A., &amp; Syrgkanis, V. (2022).</span> Long story short: Omitted variable bias in causal machine learning. <em>NBER WP 30302</em>.</li>'
        '<li><span class="hl">[3] Kennedy, E. H. (2023).</span> Towards optimal doubly robust estimation of heterogeneous causal effects. <em>Electron. J. Stat.</em>, 17(2), 3008–3049.</li>'
        '<li><span class="hl">[4] Robinson, P. M. (1988).</span> Root-N-consistent semiparametric regression. <em>Econometrica</em>, 56(4), 931–954.</li>'
        '<li><span class="hl">[5] Robins, J. M., Rotnitzky, A., &amp; Zhao, L. P. (1994).</span> Estimation of regression coefficients when some regressors are not always observed. <em>JASA</em>, 89(427), 846–866.</li>'
        '<li><span class="hl">[6] Rosenbaum, P. R., &amp; Rubin, D. B. (1983).</span> The central role of the propensity score in observational studies for causal effects. <em>Biometrika</em>, 70(1), 41–55.</li>'
        '<li><span class="hl">[7] Poterba, J. M., Venti, S. F., &amp; Wise, D. A. (1995).</span> Do 401(k) contributions crowd out other personal saving? <em>J. Public Econ.</em>, 58(1), 1–32.</li>'
        '<li><span class="hl">[8] Abadie, A. (2003); Chernozhukov &amp; Hansen (2004); Belloni et al. (2014).</span> <em>J. Econometrics</em> 113(2); <em>Rev. Econ. Stat.</em> 86(3); <em>Rev. Econ. Stud.</em> 81(2).</li>'
        '</ul>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card dark" style="flex:1;padding:13px 17px;gap:9px;">'
        '<div class="card-hd" style="font-size:19.5px;">Q&amp;A 核心讨论议题</div>'
        '<ul class="ul" style="font-size:17px;line-height:1.46;gap:10px;margin-top:2px;">'
        '<li><span style="color:#FBBF24;font-weight:700;">Q1：DML-IRM 与传统 PSM 的本质差异</span><br>双稳健正交得分把偏差压低为乘积 n<sup>−1/4</sup>×n<sup>−1/4</sup>，同时保留全样本信息，将 ATT 标准误从 $3,026 降至 $1,683。</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">Q2：无交叉拟合为何产生负偏误（1.640）？</span><br>深层树模型在全样本上过度拟合噪声，诱发正交残差间人为负相关偏移。</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">Q3：模拟与实证中底层学习器选择逻辑</span><br>模拟以 Poly2+Lasso 检验已知二阶结构；实证并行四类异质模型印证稳健性。</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">Q4：未观测储蓄偏好的进一步检验路径</span><br>除剔除 pira（+$8,923）与借 e401 估 LATE（+$12,107）外，已通过 OVB 非参数边界测得 RV=5.1%，后续可衔接面板 DID-DML。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(15, 4, "八、主要参考文献与 Q&A 交流",
                           "全部模拟程序、1991 SIPP 实证脚本与检验结果可完整复现，敬请各位老师与同学批评指正！",
                           s15_body, notes_list[14]))

    html_doc = (
        '<!DOCTYPE html>\n'
        '<html lang="zh-CN">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>双重机器学习（DML）与高维因果推断：理论、模拟与 401(k) 实证研究</title>\n'
        f'<style>{V2_CSS}</style>\n'
        '</head>\n'
        '<body>\n'
        '<div id="deck">\n'
        + "\n".join(slides)
        + '\n</div>\n'
        '<div id="notes-drawer"><strong>本页口播提示（按 N 切换）：</strong><div id="notes-body" style="margin-top:4px;"></div></div>\n'
        '<div id="nav-controls">'
        '<button id="btn-prev">← 上一页</button>'
        '<span id="slide-counter">1 / 15</span>'
        '<button id="btn-next">下一页 →</button>'
        '<button id="btn-notes">口播提示 (N)</button>'
        '</div>\n'
        + VIEWER_JS
        + '\n</body>\n</html>\n'
    )
    OUT_HTML.write_text(html_doc, encoding="utf-8")

    # Sync academic speech script aligned with the 15 slide titles
    slide_titles = [
        "Slide 1｜封面：双重机器学习（DML）与高维因果推断：理论原理、模拟验证与 401(k) 实证研究",
        "Slide 2｜一、模型背景与文献综述：高维因果推断的演进脉络",
        "Slide 3｜二、模型原理（一）：部分线性框架与机器学习的两类偏误",
        "Slide 4｜二、模型原理（二）：Neyman 正交化与误差二阶乘积收敛",
        "Slide 5｜二、模型原理（三）：K-折交叉拟合与 PLR / IRM / IIVM 统一框架",
        "Slide 6｜三、模拟分析（一）：非线性高维混杂 DGP、抽样分布与正态性校验",
        "Slide 7｜三、模拟分析（二）：O(n⁻¹/²) 收敛速率、RMSE 与置信区间覆盖率检验",
        "Slide 8｜四、实证研究背景与数据诊断：非线性选择偏误与 DML 平衡性检验",
        "Slide 9｜五、实证分析（一）：主效应对比、第一阶段诊断与 K-折稳健性",
        "Slide 10｜五、实证分析（二）：重叠性检验、OVB 敏感性与工具变量 LATE",
        "Slide 11｜五、实证分析（三）：二维交互 GATE 与 DR-Learner 连续异质性",
        "Slide 12｜六、研究结论（一）：DML 模型性能总结与实证决策启示",
        "Slide 13｜六、研究结论（二）：模型适用边界、局限性与前沿延伸",
        "Slide 14｜七、模型拓展应用：结合实习与研究领域的 3 分钟个人阐述",
        "Slide 15｜八、主要参考文献与 Q&A 交流",
    ]
    timings = ["30秒", "45秒", "55秒", "60秒", "55秒", "50秒", "45秒", "45秒", "60秒", "50秒", "55秒", "50秒", "40秒", "3分钟(每人≤1分)", "Q&A"]
    speech_lines = [
        "# 双重机器学习（DML）与高维因果推断汇报口播稿",
        "",
        "> **汇报节奏**：前 13 页主讲严格控制在 **11 分 30 秒 – 12 分 00 秒**；第 14 页组内 3 人每人 **≤ 1 分钟**拓展；第 15 页进入 Q&A 交流。",
        "> **叙事架构**：严格遵循“模型介绍与文献综述 → 模型核心原理 → Monte Carlo 模拟验证 → 实证背景与数据诊断 → 多维度实证分析 → 模型性能总结与边界”。",
        "",
        "---",
        "",
        "## 一、逐页口播指南（与 HTML / PPTX 演讲者备注 100% 同步）",
        "",
    ]
    for st_title, tm, nt in zip(slide_titles, timings, notes_list):
        speech_lines.append(f"### {st_title}（预计 {tm}）")
        speech_lines.append(f"> **口播提示**：{nt}")
        speech_lines.append("")

    speech_lines.extend([
        "---",
        "",
        "## 二、第 14 页 3 分钟个人拓展详稿（每人 ≤ 55 秒）",
        "",
        "- **成员 A｜陈霖（量化多因子与大模型 Agent RL，约 50 秒）**：",
        "  “结合我在 Trexquant 美股多因子研究与上海人工智能实验室 Agent 强化学习的实践，DML 主要有两方面应用价值：第一，在利用非线性算法合成高频或情绪类因子时，市值、波动率与行业暴露常与预期收益存在复杂非线性混杂，利用 DML 对目标因子与超额收益同步做交叉拟合正交残差，可更准确地评估信号的净增量 Alpha；第二，在 Agent RL 离线评估中，借助双稳健正交得分可在高维状态空间实现无偏反事实回报归因。”",
        "- **成员 B｜[请填姓名]（互联网用户增长 Uplift 模板，约 50 秒，请替换为个人真实实习）**：",
        "  “【请成员 B 替换姓名与场景】：在互联网用户增长与优惠券营销中，历史触达策略往往偏向高活跃或高价值用户，直接对比触达与未触达组转化率存在显著选择偏误。采用 DML-IRM 框架，可借助梯度提升树充分控制数十维用户历史行为协变量，通过正交得分识别对激励真正敏感的高增量客群，从而优化补贴投放效率。”",
        "- **成员 C｜[请填姓名]（金融科技信贷风控模板，约 50 秒，请替换为个人真实实习）**：",
        "  “【请成员 C 替换姓名与场景】：在消费信贷额度管理中，平台授信本身依赖于多维非线性的信用评分体系。引入 DML 框架后，风控团队既可保留 XGBoost/LightGBM 等高维非线性学习器对征信特征的表征优势，又能够获得具备严格 95% 置信区间的提额因果收益与风险响应评估。”",
        "",
        "---",
        "",
        "## 三、第 15 页核心 Q&A 备答（学术答辩参考）",
        "",
        "1. **DML-IRM 与传统倾向得分匹配（PSM）相比，最本质的理论与实践改进是什么？**",
        "   - **答**：在理论上，传统单方程倾向得分方法若嵌入机器学习估计，会面临 $O(n^{-1/4})$ 量级正则化偏误并导致 $\\sqrt{n}$ 尺度发散；DML-IRM 通过结合结果回归 $\\hat{g}$ 与倾向得分 $\\hat{m}$ 构造双稳健 Neyman 正交得分，将主导误差压低为乘积 $O_p(n^{-1/4}) \\times O_p(n^{-1/4}) = o_p(n^{-1/2})$。在实证精度上，DML-IRM 保留全样本信息而无须丢弃未匹配样本，将 401(k) ATT 标准误从 1:1 PSM 的 $3,026 显著降低至 $1,683。",
        "2. **为什么在模拟实验中，无交叉拟合的 Orthogonal ML 会出现显著负偏误（1.640）？**",
        "   - **答**：在该对比设定中，未限制深度的随机森林在全样本上直接拟合结果与处置，导致模型部分记忆了结构误差项 $V_i$ 与 $\\zeta_i$，从而在样本内残差 $\\hat{u}_i$ 与 $\\hat{v}_i$ 之间诱发系统性负向过拟合相关性，破坏正交矩无偏条件。",
        "3. **为什么模拟实验使用 Poly2 + LassoCV，而 401(k) 实证采用四类学习器？**",
        "   - **答**：在模拟 DGP 中，真实扰动函数已知为 20 维中的二阶多项式与交互结构，采用与函数族匹配的 Poly2 + LassoCV（收敛速率满足 $o(n^{-1/4})$）可清晰剥离并检验正交化与交叉拟合的独立贡献；而在真实 401(k) 数据中真实函数形式未知，因此并行采用 Lasso、Ridge、随机森林与 HistGradientBoosting 四类差异化算法进行交叉验证，四者均收敛于 $7,822–$8,693，证明结论不依赖特定模型设定。",
        "4. **如果雇主提供 401(k) 与员工未观测到的主观储蓄偏好相关，如何进一步检验或缓解？**",
        "   - **答**：条件可忽略性假设无法直接控制未观测变量，这是截面观测因果推断的核心边界。本研究通过三层防线加以定量应对：第一，剔除争议变量 `pira` 重估后 ATE 仍达 `$8,923`；第二，依据 Chernozhukov 等 (2022) 非参数 OVB 边界测得稳健阈值 `RV=5.1%`，即使引入等同 `db` 或 `pira` 解释力的未观测混杂，ATE 下界仍高达 `+$5,265` 与 `+$4,624`；第三，以 `e401` 为 `p401` 工具变量借助 DML-IIVM 估得依从者 LATE 为 `$12,107`。",
    ])
    OUT_SPEECH.write_text("\n".join(speech_lines) + "\n", encoding="utf-8")
    print(f"Built {OUT_HTML.name} and {OUT_SPEECH.name}")


if __name__ == "__main__":
    main()
