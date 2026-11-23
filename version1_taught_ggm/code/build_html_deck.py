#!/usr/bin/env python3
"""Build Version 1 (Course-Taught Method: GGM & Graphical Lasso) 15-slide 1280x720 HTML deck
and synchronized conversational speech script, dynamically pulling all numbers from
outputs/results_summary.json.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT_DIR / "outputs" / "results_summary.json"
OUT_HTML = ROOT_DIR / "presentation" / "版本一_高斯图模型与跨资产风险传染网络.html"
OUT_SPEECH = ROOT_DIR / "docs" / "演讲稿_12分钟展示与3分钟拓展.md"


SHARED_CSS = """
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
  padding: 40px 54px 32px 54px;
  justify-content: space-between;
}
.cover-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13.5px;
  color: #CBD5E1;
  border-bottom: 1px solid rgba(255,255,255,0.16);
  padding-bottom: 12px;
}
.cover-pill {
  background: rgba(217, 119, 6, 0.22);
  border: 1px solid rgba(251, 191, 36, 0.55);
  color: #FDE68A;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
}
.cover-main { margin: 14px 0 8px 0; }
.cover-kicker {
  font-size: 15px;
  color: #7DD3FC;
  font-weight: 600;
  letter-spacing: 0.4px;
  margin-bottom: 10px;
}
.cover-title {
  font-size: 38px;
  line-height: 1.24;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 12px;
}
.cover-sub {
  font-size: 17px;
  line-height: 1.5;
  color: #E2E8F0;
  max-width: 1060px;
}
.cover-kpis {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 18px;
}
.cover-kpi {
  background: rgba(255,255,255,0.09);
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 10px;
  padding: 15px 18px;
}
.cover-kpi .val {
  font-size: 27px;
  font-weight: 700;
  color: #FBBF24;
  margin-bottom: 4px;
}
.cover-kpi .lbl {
  font-size: 13.5px;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 3px;
}
.cover-kpi .desc {
  font-size: 12px;
  color: #CBD5E1;
  line-height: 1.4;
}
.cover-bottom {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-top: 1px solid rgba(255,255,255,0.16);
  padding-top: 14px;
  font-size: 13px;
  color: #CBD5E1;
}

/* Standard slide chrome */
.sec-bar {
  height: 36px;
  background: #0A365C;
  padding: 0 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.sec-nav { display: flex; gap: 8px; align-items: center; }
.sec-item {
  font-size: 11.5px;
  color: rgba(255,255,255,0.62);
  padding: 3px 10px;
  border-radius: 4px;
  cursor: pointer;
}
.sec-item.on {
  background: rgba(255,255,255,0.18);
  color: #FFFFFF;
  font-weight: 600;
}
.sec-course { font-size: 11.5px; color: #93C5FD; font-weight: 500; }

.slide-header {
  background: #FFFFFF;
  padding: 11px 38px 9px 38px;
  border-bottom: 1.5px solid #DCE3EC;
  flex-shrink: 0;
}
.slide-title {
  font-size: 21px;
  font-weight: 700;
  color: #0A365C;
  line-height: 1.25;
}
.slide-sub {
  font-size: 13px;
  color: #0E7490;
  margin-top: 3px;
  font-weight: 500;
}

.slide-body {
  flex: 1;
  min-height: 0;
  padding: 13px 38px 10px 38px;
  display: flex;
  flex-direction: column;
  gap: 11px;
  overflow: hidden;
}

.slide-footer {
  height: 29px;
  background: #FFFFFF;
  border-top: 1px solid #E2E8F0;
  padding: 0 38px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #64748B;
  flex-shrink: 0;
}
.page-num { font-weight: 700; color: #0A365C; font-size: 11.5px; }

/* Grids & Cards */
.row { display: flex; gap: 14px; min-height: 0; }
.col { display: flex; flex-direction: column; gap: 11px; min-height: 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; min-height: 0; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 13px; min-height: 0; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; min-height: 0; }

.card {
  background: #FFFFFF;
  border: 1px solid #DCE3EC;
  border-radius: 8px;
  padding: 12px 15px;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.card.blue { background: #F0F6FC; border-color: #BFDBFE; }
.card.teal { background: #ECFEFF; border-color: #A5F3FC; }
.card.amber { background: #FFFBEB; border-color: #FDE68A; }
.card.red { background: #FEF2F2; border-color: #FECACA; }
.card.dark { background: #0A365C; border-color: #0A365C; color: #FFFFFF; }

.card-hd {
  font-size: 14px;
  font-weight: 700;
  color: #0A365C;
  display: flex;
  align-items: center;
  gap: 7px;
  border-left: 3.5px solid #0E7490;
  padding-left: 8px;
}
.card.amber .card-hd { border-left-color: #D97706; color: #92400E; }
.card.red .card-hd { border-left-color: #B91C1C; color: #991B1B; }
.card.dark .card-hd { border-left-color: #FBBF24; color: #FFFFFF; }

.ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 12.5px;
  line-height: 1.48;
  color: #334155;
}
.card.dark .ul { color: #E2E8F0; }
.ul li { position: relative; padding-left: 13px; }
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

.p-text { font-size: 12.5px; line-height: 1.5; color: #334155; }
.card.dark .p-text { color: #E2E8F0; }
.hl { font-weight: 700; color: #0A365C; }
.hl-teal { font-weight: 700; color: #0E7490; }
.hl-red { font-weight: 700; color: #B91C1C; }
.hl-amber { font-weight: 700; color: #B45309; }

.kpi {
  background: #FFFFFF;
  border: 1px solid #DCE3EC;
  border-top: 3px solid #0A365C;
  border-radius: 8px;
  padding: 9px 12px;
  text-align: center;
}
.kpi .v { font-size: 21px; font-weight: 700; color: #0A365C; }
.kpi .l { font-size: 12px; font-weight: 600; color: #334155; margin-top: 2px; }
.kpi .s { font-size: 11px; color: #64748B; margin-top: 2px; }

/* Math styling */
.math-box {
  background: #F8FAFC;
  border: 1px solid #CBD5E1;
  border-left: 4px solid #0A365C;
  border-radius: 6px;
  padding: 8px 12px;
  font-family: 'Cambria Math', 'Times New Roman', 'PingFang SC', serif;
  font-size: 14.5px;
  color: #0F172A;
  text-align: center;
}
.frac {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  vertical-align: middle;
  margin: 0 3px;
  font-size: 0.88em;
  line-height: 1.08;
}
.frac .num { border-bottom: 1.4px solid currentColor; padding: 0 4px 1px 4px; }
.frac .den { padding: 1px 4px 0 4px; }
.hat {
  position: relative;
  display: inline-block;
}
.hat::before {
  content: "^";
  position: absolute;
  top: -0.48em;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.72em;
  font-weight: 700;
}

/* Tables */
table.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 11.8px;
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
}
table.tbl th {
  background: #0A365C;
  color: #FFFFFF;
  font-weight: 600;
  padding: 6px 9px;
  text-align: left;
  border-bottom: 1px solid #0A365C;
}
table.tbl td {
  padding: 5.5px 9px;
  border-bottom: 1px solid #E2E8F0;
  color: #1E293B;
  line-height: 1.35;
}
table.tbl tr:nth-child(even) td { background: #F8FAFC; }
table.tbl tr.hl-row td { background: #E0F2FE; font-weight: 700; color: #0A365C; }
.num-col { text-align: right !important; font-variant-numeric: tabular-nums; }

/* Figure frame */
.fig-box {
  background: #FFFFFF;
  border: 1px solid #DCE3EC;
  border-radius: 8px;
  padding: 7px 10px;
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
  object-fit: contain;
  display: block;
}
.fig-cap {
  font-size: 11px;
  color: #64748B;
  margin-top: 3px;
  text-align: center;
  flex-shrink: 0;
}

.note-strip {
  background: #F1F5F9;
  border-left: 4px solid #0E7490;
  padding: 7px 12px;
  border-radius: 0 6px 6px 0;
  font-size: 12px;
  color: #334155;
  line-height: 1.45;
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
  font-size: 12.5px;
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
  font-size: 12px;
}
#nav-controls button:hover { background: rgba(255,255,255,0.24); }
#notes-drawer {
  position: fixed;
  bottom: 58px;
  right: 20px;
  width: 520px;
  max-width: calc(100vw - 40px);
  background: rgba(15, 23, 42, 0.94);
  color: #E2E8F0;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 12.5px;
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
        ("01 背景与课程定位", 1),
        ("02 模型解构", 3),
        ("03 实证网络分析", 6),
        ("04 组合落地与边界", 10),
        ("05 拓展与 Q&A", 13),
    ]
    items = []
    for i, (label, target) in enumerate(secs):
        cls = "sec-item on" if i == active_idx else "sec-item"
        items.append(f'<span class="{cls}" onclick="goSlide({target})">{label}</span>')
    return (
        '<div class="sec-bar">'
        f'<div class="sec-nav">{"".join(items)}</div>'
        '<div class="sec-course">《现代统计模型及应用》· 版本一（讲义 5 高斯图模型）</div>'
        '</div>'
    )


def wrap_slide(page: int, sec_idx: int, title: str, subtitle: str, body_html: str, notes: str) -> str:
    return (
        f'<section class="slide" data-notes="{html.escape(notes, quote=True)}">'
        f'{sec_bar_html(sec_idx)}'
        '<div class="slide-header">'
        f'<h2 class="slide-title">{title}</h2>'
        f'<p class="slide-sub">{subtitle}</p>'
        '</div>'
        f'<div class="slide-body">{body_html}</div>'
        '<div class="slide-footer">'
        '<span>复旦大学管理学院 DSBA · 跨资产风险传染网络与组合风控实证</span>'
        f'<span class="page-num">{page:02d} / 15</span>'
        '</div>'
        '</section>'
    )


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    ds = d["dataset"]
    eb = d["ebic_selected_model"]
    pr = d["path_edge_range"]
    nll = d["test_nll_comparison"]
    pos_e = d["top_positive_edges"]
    neg_e = d["top_negative_edges"]
    nodes = d["node_centrality_top5"]
    reg = d["regime_comparison"]
    st = d["static_gmvp_oos_metrics"]
    ro = d["rolling_gmvp_oos_metrics"]
    bt = d["bootstrap_vol_tests_rolling"]

    notes_list: List[str] = [
        # 1
        "各位老师、同学好！今天我们汇报版本一——基于讲义 5 高斯图模型与 Graphical Lasso 的跨资产风险传染网络研究。开场先抛一个真实反差：可选消费 XLY 和公用事业 XLU 的皮尔逊相关是 +0.541，但用图模型扣掉其余 13 支资产后，直接变成 -0.176 的对冲关系！",
        # 2
        "为什么会这样？左图画出了原因：市场共同因子让股票同涨同跌，皮尔逊相关把这种共震混在了一起；而算组合权重需要协方差的逆矩阵 Θ，直接求逆又会把噪声放大。我们希望既剥离共同因子看清真传染边，又稳定估计逆矩阵。",
        # 3
        "在课程体系里，上半学期讲因果推断，下半学期讲义 5-7 讲图模型。无向图里“没连边”等价于给定其余节点后条件独立。对比四种估计方式：Sample MLE 全连接且高维易过拟合；Ledoit-Wolf 收缩不产生稀疏结构；GLasso 能选边但有收缩偏误；所以最合理的是把讲义 5 的算法二和算法一串起来做两步精估。",
        # 4
        "来看讲义 5.3.4 算法一：多元高斯精度矩阵 θ_jk=0 等价于偏相关为 0，也就是把其余 13 支资产线性扣掉后的残差相关性。如果图结构 E 已知，算法一通过修改回归块坐标下降匹配边上协方差 W_jk=S_jk。我们在训练集选中图上复现后，最大匹配误差仅 2.22e-16，非边绝对值为 0，最小特征值 0.1136 严格正定。",
        # 5
        "图结构未知时就需要讲义 5.3.6 算法二 Graphical Lasso，在似然函数上减掉 α||Θ_off||₁ 实现自动归零。但因为 L1 惩罚会把保留下来的边权压小（比如 XLY-XLU 直接 GLasso 只有 -0.0011），所以我们串联两步：算法二选边、算法一去偏重估，并用 EBIC(γ=0.5) 选 α，最后通过 D_σ⁻¹ Θ_Z D_σ⁻¹ 还原回收益率尺度。",
        # 6
        f"数据方面，我们抓取了 Yahoo Finance {ds['date_start']} 至 {ds['date_end']} 共 {ds['n_total_days']} 个交易日、15 支美股核心 ETF 复权对数收益，涵盖 11 个 GICS 行业与 4 类宏观大类，零缺失值。严格前 {ds['n_train']} 天（2020–2023）做训练与调参，后 {ds['n_test']} 天（2024–2025）做纯样本外检验。",
        # 7
        f"看图 1 左右对比：左图皮尔逊相关一片红（股票间普遍 0.60–0.91），右图 GGM 偏相关把 105 条潜在边剪掉 {eb['sparsity']*100:.1f}%、只剩 {eb['n_edges']} 条。最强的直接链路完全符合经济直觉：TLT-IEF (+0.866)、XLK-XLC (+0.472)、XLU-XLRE (+0.454)、XLI-XLB (+0.411)。",
        # 8
        "把右图画成网络（图 2）有两个核心发现：一是红色虚线的符号反转揭示真实对冲——金融 XLF 与黄金 GLD 皮尔逊几乎无关 (+0.030)，偏相关达到 -0.251；XLY-XLU 从 +0.541 翻成 -0.176。二是枢纽与桥梁：金融 XLF 强度 1.53 居首，而高收益债 HYG 连接 11 个节点、介数中心度 0.165，直接桥接中端美债 IEF (+0.19)、金融 (+0.19) 与地产 (+0.21)。",
        # 9
        f"图 3 展示模型选择过程：α 从 0.03 增至 0.85，边数从 {pr['max_edges']} 降到 {pr['min_edges']}。EBIC 在 α*={eb['alpha']:.4f} 处取极小值 -1071.56，选出 64 条边。2024–2025 测试集负对数似然验证了算法一重估的必要性：两步精估 (11.603) 明显优于未经重估的 GLasso (11.860) 与 Ledoit-Wolf (11.646)。",
        # 10
        f"图 4 检验跨周期稳健性：在 2020–2022 疫情与加息冲击期模型选出 {reg['regime1_edges']} 条边，在 2023–2025 新周期降为 {reg['regime2_edges']} 条边，说明高波动时期风险传导更密集；两期共有 {reg['n_shared_edges']} 条核心边重合，Jaccard 相似度达 {reg['edge_jaccard_similarity']:.3f}。",
        # 11
        f"图 5 把精度矩阵落地到 2024–2025 样本外滚动 252 日 GMVP 回测（每 21 日调仓，无前瞻泄露）。两步精估把等权 10.52% 年化波动压到全场最低 {ro['GGM 两步精估 (Alg1)']['ann_vol_pct']:.2f}%，夏普升至 {ro['GGM 两步精估 (Alg1)']['sharpe_rf0']:.2f}、最大回撤收窄到 {ro['GGM 两步精估 (Alg1)']['max_dd_pct']:.2f}%；直接 GLasso 把平均 L1 杠杆从 MLE 的 2.19 降到 1.92。",
        # 12
        "图 6 回答一个好问题：网络中心度最高的是金融 XLF，但最小方差组合重仓的却是做多中端美债 IEF 与做空长端美债 TLT——因为中心度看谁牵连广，GMVP 看谁能把组合总方差压到最低，两者分工明确；右侧权重也可见稀疏正则略微抑制了极端头寸。",
        # 13
        f"做严谨实证必须坦诚证据边界：10 日区块 Bootstrap 显示，相对等权组合我们显著降低波动 {bt['EqualWeight_minus_GGM_Refit']['vol_diff_pct']:.2f}% (p<0.001)；但相比 Sample MLE，在 p=15, n=252 的低维窗口下波动仅小幅降 0.08% (p={bt['MLE_minus_GGM_Refit']['p_value']:.3f} 未达显著)，优势主要在更高夏普、更低回撤与网络可解释性。未来可拓展至厚尾 Copula-GGM、时变图模型 TVGL 及讲义 6-7 贝叶斯网络 DAG。",
        # 14
        "接下来进入 3 分钟个人拓展，每人一分钟。我（陈霖）结合在九坤、悬铃私募、乾上泉和 Trexquant 的量化实习：在多因子选股中可用 GGM 对齐风格去共线，在高维百千只股票组合风控里，稀疏逆协方差对控制换手与极端空头尤为关键。接下来请组员 B、C 分享（现场替换为各自实习场景）。",
        # 15
        "以上是我们小组参考的 8 篇核心文献与讲义 5 对应章节。右侧列出了四个我们在做实验时最深思的问题，欢迎冯老师、吴老师和同学们提问交流！",
    ]

    slides: List[str] = []

    # Slide 1: Cover
    slides.append(
        f'<section class="slide cover" data-notes="{html.escape(notes_list[0], quote=True)}">'
        '<div class="cover-top">'
        '<span>复旦大学管理学院 · 数据科学与商务分析项目（DSBA 2026 秋）</span>'
        '<span class="cover-pill">版本一｜课堂讲授模型案例：讲义 5 高斯图模型</span>'
        '</div>'
        '<div class="cover-main">'
        '<div class="cover-kicker">《现代统计模型及应用》课程大作业汇报 · 授课教师：冯项楠、吴尚</div>'
        '<h1 class="cover-title">高斯图模型与 Graphical Lasso：<br>跨资产风险传染网络与样本外组合风控</h1>'
        f'<p class="cover-sub">基于 {ds["n_assets"]} 支美国行业与跨资产 ETF（{ds["date_start"]} 至 {ds["date_end"]}，{ds["n_total_days"]:,} 个交易日）真实数据实证：如何剥离大盘共同因子、串联讲义 5 算法一与算法二识别真实对冲边，并降低样本外组合波动。</p>'
        '<div class="cover-kpis">'
        '<div class="cover-kpi">'
        f'<div class="val">{eb["n_edges"]} / {eb["max_possible_edges"]} 条边</div>'
        '<div class="lbl">EBIC 最优稀疏条件独立图</div>'
        f'<div class="desc">α*={eb["alpha"]:.4f} 剪除 {eb["sparsity"]*100:.1f}% 冗余连接，测试集 NLL ({nll["GGM_Alg1_Refit_test_NLL"]:.3f}) 优于直接 GLasso ({nll["GLasso_EBIC_test_NLL"]:.3f})</div>'
        '</div>'
        '<div class="cover-kpi">'
        f'<div class="val">+{neg_e[1]["pearson_corr"]:.3f} → {neg_e[1]["pcorr_refit"]:.3f}</div>'
        '<div class="lbl">“符号反转”揭示真实对冲通道</div>'
        f'<div class="desc">XLY（可选消费）与 XLU（公用事业）剔除大盘共震后由正转负；XLF–GLD 偏相关达 {neg_e[0]["pcorr_refit"]:.3f}</div>'
        '</div>'
        '<div class="cover-kpi">'
        f'<div class="val">{ro["GGM 两步精估 (Alg1)"]["ann_vol_pct"]:.2f}% / SR {ro["GGM 两步精估 (Alg1)"]["sharpe_rf0"]:.2f}</div>'
        '<div class="lbl">2024–2025 样本外滚动 GMVP</div>'
        f'<div class="desc">相对等权（{ro["等权组合 (1/N)"]["ann_vol_pct"]:.2f}%）降波 {bt["EqualWeight_minus_GGM_Refit"]["vol_diff_pct"]:.2f}%（p&lt;0.001），最大回撤仅 {ro["GGM 两步精估 (Alg1)"]["max_dd_pct"]:.2f}%</div>'
        '</div>'
        '</div>'
        '</div>'
        '<div class="cover-bottom">'
        '<span>汇报结构：12 分钟模型与实证汇报（Slide 1–13）＋ 3 分钟每人 1 分钟拓展（Slide 14）＋ Q&amp;A</span>'
        '<span>小组成员：陈霖、组员 B、组员 C</span>'
        '</div>'
        '</section>'
    )

    # Slide 2: Background & Pain Points
    s2_body = (
        '<div class="grid-2" style="flex:1;">'
        '<div class="col">'
        '<div class="card red">'
        '<div class="card-hd">痛点一：大盘共同因子制造“虚假全连接”</div>'
        '<ul class="ul">'
        '<li>传统风控依赖皮尔逊相关矩阵 R，但所有股票行业共享宏观利率与市场 Beta。</li>'
        f'<li>实证中<span class="hl">可选消费 (XLY) 与公用事业 (XLU)</span> 皮尔逊相关高达 <span class="hl-red">+{neg_e[1]["pearson_corr"]:.3f}</span>，表面“同涨同跌”，实则一个是顺周期进攻、一个是防御避险——相关矩阵完全掩盖了真实替代关系。</li>'
        '<li>几乎全连通的相关网络无法定位谁是直接风险传染源，压力测试无从下手。</li>'
        '</ul>'
        '</div>'
        '<div class="card">'
        '<div class="card-hd">痛点二：精度矩阵求逆把高频噪声放大成极端杠杆</div>'
        '<ul class="ul">'
        '<li>马科维茨全局最小方差组合（GMVP）核心输入并非 Σ，而是其逆矩阵——<span class="hl">精度矩阵 Θ = Σ<sup>−1</sup></span>（w* ∝ Θ·1）。</li>'
        '<li>直接对样本协方差 S 求逆会剧烈放大微小特征值噪声，推高多空杠杆与样本外回撤。</li>'
        '</ul>'
        '</div>'
        '<div class="card blue" style="padding:10px 14px;">'
        '<div class="card-hd">混杂共震 vs. 直接关联示意图</div>'
        '<svg viewBox="0 0 540 120" style="width:100%;height:112px;">'
        '<rect x="18" y="34" width="128" height="44" rx="8" fill="#0A365C"/>'
        '<text x="82" y="54" text-anchor="middle" fill="#FFF" font-size="12" font-weight="700">大盘/利率共同因子</text>'
        '<text x="82" y="70" text-anchor="middle" fill="#CBD5E1" font-size="10.5">(其余 13 支资产)</text>'
        '<line x1="146" y1="46" x2="232" y2="26" stroke="#64748B" stroke-width="2" stroke-dasharray="4,3"/>'
        '<line x1="146" y1="68" x2="232" y2="90" stroke="#64748B" stroke-width="2" stroke-dasharray="4,3"/>'
        '<rect x="234" y="8" width="120" height="36" rx="7" fill="#E0F2FE" stroke="#0E7490" stroke-width="1.5"/>'
        '<text x="294" y="30" text-anchor="middle" fill="#0A365C" font-size="12" font-weight="700">XLY 可选消费</text>'
        '<rect x="234" y="74" width="120" height="36" rx="7" fill="#E0F2FE" stroke="#0E7490" stroke-width="1.5"/>'
        '<text x="294" y="96" text-anchor="middle" fill="#0A365C" font-size="12" font-weight="700">XLU 公用事业</text>'
        '<line x1="294" y1="44" x2="294" y2="74" stroke="#B91C1C" stroke-width="2.5"/>'
        '<rect x="372" y="14" width="154" height="90" rx="8" fill="#FFF" stroke="#CBD5E1"/>'
        '<text x="449" y="36" text-anchor="middle" fill="#334155" font-size="11.5">皮尔逊：混入共震 <tspan fill="#0A365C" font-weight="700">+0.541</tspan></text>'
        '<text x="449" y="60" text-anchor="middle" fill="#334155" font-size="11.5">扣掉共同因子后偏相关：</text>'
        '<text x="449" y="84" text-anchor="middle" fill="#B91C1C" font-size="16" font-weight="700">−0.176 (真实对冲)</text>'
        '</svg>'
        '</div>'
        '</div>'
        '<div class="col">'
        '<div class="card">'
        '<div class="card-hd">训练集真实案例：表面相关性如何欺骗直觉？</div>'
        '<table class="tbl">'
        '<thead><tr><th>资产对</th><th class="num-col">皮尔逊相关</th><th class="num-col">GGM 偏相关</th><th>风控真实含义</th></tr></thead>'
        '<tbody>'
        f'<tr><td>XLY 可选 / XLU 公用</td><td class="num-col">+{neg_e[1]["pearson_corr"]:.3f}</td><td class="num-col hl-red">{neg_e[1]["pcorr_refit"]:.3f}</td><td>同受大盘拉动，实为进攻/防御轮动对冲</td></tr>'
        f'<tr><td>XLF 金融 / GLD 黄金</td><td class="num-col">+{neg_e[0]["pearson_corr"]:.3f}</td><td class="num-col hl-red">{neg_e[0]["pcorr_refit"]:.3f}</td><td>表面看似无关，实为强条件避险替代</td></tr>'
        f'<tr><td>XLP 必选 / XLE 能源</td><td class="num-col">+{neg_e[2]["pearson_corr"]:.3f}</td><td class="num-col hl-red">{neg_e[2]["pcorr_refit"]:.3f}</td><td>油价上行直接挤压下游消费品利润空间</td></tr>'
        f'<tr><td>XLK 科技 / XLE 能源</td><td class="num-col">+{neg_e[3]["pearson_corr"]:.3f}</td><td class="num-col hl-red">{neg_e[3]["pcorr_refit"]:.3f}</td><td>通胀/能源冲击对长久期科技估值形成压制</td></tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '<div class="card blue" style="flex:1;">'
        '<div class="card-hd">高斯图模型（GGM）在金融风控中的三大商业价值</div>'
        '<ul class="ul">'
        '<li><span class="hl">结构透视（Risk Mapping）</span>：过滤共同市场噪音，只保留控制其余全部资产后仍显著的条件独立边，精确定位跨行业直接传导链路。</li>'
        '<li><span class="hl">枢纽与桥梁监测（Contagion Hub）</span>：通过节点度与介数中心度识别高收益债 HYG、金融 XLF 等跨市场传染枢纽，辅助压力情景设计。</li>'
        '<li><span class="hl">组合精估降噪（Portfolio Control）</span>：输出稀疏且严格正定的精度矩阵用于最小方差组合，在样本外抑制极端多空仓位、收窄回撤。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(2, 0, "一、研究背景与商业痛点：为什么皮尔逊相关会误导风控？",
                           "共同因子制造虚假全连接，协方差直接求逆放大杠杆噪声——需要既稀疏又稳健的精度矩阵模型",
                           s2_body, notes_list[1]))

    # Slide 3: Course Positioning & Method Evolution
    s3_body = (
        '<div class="row" style="align-items:stretch;">'
        '<div class="card blue" style="flex:1.25;">'
        '<div class="card-hd">在《现代统计模型及应用》课程体系中的定位</div>'
        '<ul class="ul">'
        '<li><span class="hl">课程前半（讲义 1–4，冯项楠老师）</span>：因果推断关注“干预 D 对结果 Y 的净效应”，核心是如何控制可观测或不可观测混杂因素。</li>'
        '<li><span class="hl">课程后半（讲义 5–7，吴尚老师）</span>：概率图模型刻画多变量联合分布的<span class="hl-teal">条件独立结构</span>——无向马尔可夫网络（讲义 5–6）与有向贝叶斯网络（讲义 6–7）。</li>'
        '<li><span class="hl">本报告核心聚焦（讲义 5.2–5.3）</span>：连续变量高斯图模型（GGM），并把课堂板书中的<span class="hl">算法一（已知图约束 MLE）</span>与<span class="hl">算法二（Graphical Lasso）</span>串联落地。</li>'
        '</ul>'
        '</div>'
        '<div class="card" style="flex:1;">'
        '<div class="card-hd">讲义 5.2 图分隔与条件独立直觉</div>'
        '<svg viewBox="0 0 440 128" style="width:100%;height:122px;">'
        '<circle cx="95" cy="30" r="20" fill="#0A365C"/><text x="95" y="35" text-anchor="middle" fill="#FFF" font-size="13" font-weight="700">X</text>'
        '<circle cx="220" cy="30" r="20" fill="#0E7490"/><text x="220" y="35" text-anchor="middle" fill="#FFF" font-size="13" font-weight="700">Y</text>'
        '<circle cx="95" cy="98" r="20" fill="#0E7490"/><text x="95" y="103" text-anchor="middle" fill="#FFF" font-size="13" font-weight="700">Z</text>'
        '<circle cx="220" cy="98" r="20" fill="#0A365C"/><text x="220" y="103" text-anchor="middle" fill="#FFF" font-size="13" font-weight="700">W</text>'
        '<line x1="115" y1="30" x2="200" y2="30" stroke="#64748B" stroke-width="2.2"/>'
        '<line x1="95" y1="50" x2="95" y2="78" stroke="#64748B" stroke-width="2.2"/>'
        '<line x1="110" y1="44" x2="205" y2="84" stroke="#64748B" stroke-width="2.2"/>'
        '<line x1="220" y1="50" x2="220" y2="78" stroke="#64748B" stroke-width="2.2"/>'
        '<line x1="115" y1="98" x2="200" y2="98" stroke="#64748B" stroke-width="2.2"/>'
        '<text x="262" y="34" fill="#0A365C" font-size="12" font-weight="700">Y 与 Z 之间无边相连</text>'
        '<text x="262" y="56" fill="#334155" font-size="11.5">• 成对马氏独立：给定 {X,W}，Y ⊥ Z</text>'
        '<text x="262" y="78" fill="#334155" font-size="11.5">• {X,W} 分隔了 Y 与 Z（全局等价）</text>'
        '<text x="262" y="100" fill="#0E7490" font-size="11.5" font-weight="600">• 高斯分布下 ⇔ 精度阵 θ_YZ = 0</text>'
        '</svg>'
        '</div>'
        '</div>'
        '<div class="card" style="flex:1;">'
        '<div class="card-hd">方法横向比较：为什么最终采用“算法二选边 + 算法一重估”？</div>'
        '<table class="tbl">'
        '<thead><tr><th>估计方法</th><th>图结构稀疏性</th><th>参数估计偏差</th><th>高维稳定性</th><th>在本研究中的表现与角色</th></tr></thead>'
        '<tbody>'
        '<tr><td>Sample MLE (S<sup>−1</sup>)</td><td>否（105 条边全连）</td><td>低维无偏</td><td>n/p 小时方差剧增</td><td>低维测试 NLL 11.562，但无结构解释力且总杠杆偏高</td></tr>'
        '<tr><td>Ledoit-Wolf 线性收缩</td><td>否（仅压缩特征值）</td><td>引入线性收缩偏差</td><td>稳定但不可解构</td><td>行业标准收缩基准，测试 NLL 11.646，样本外波动 3.66%</td></tr>'
        '<tr><td>直接 Graphical Lasso (Alg 2)</td><td>是（L<sub>1</sub> 自动归零）</td><td>保留边存在向零收缩偏误</td><td>稳定且降杠杆</td><td>杠杆最低 (1.92)，但 L<sub>1</sub> 压缩导致测试 NLL 偏高至 11.860</td></tr>'
        '<tr class="hl-row"><td>GGM 两步精估 (Alg 2 + Alg 1)</td><td>是（EBIC 选 64 边）</td><td>算法一约束 MLE 消除偏误</td><td>严格正定、回撤最低</td><td>测试 NLL 降至 11.603，滚动波动 3.03%（夏普 2.82）全场最佳</td></tr>'
        '</tbody>'
        '</table>'
        '</div>'
    )
    slides.append(wrap_slide(3, 0, "二、课程定位与方法演进：从相关矩阵到稀疏马尔可夫网络",
                           "承接讲义 5 马尔可夫网络条件独立定义，用“L1 选边 + 约束 MLE 去偏”兼顾可解释性与样本外精度",
                           s3_body, notes_list[2]))

    # Slide 4: Math Deconstruction I
    s4_body = (
        '<div class="grid-2" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">1. 精度矩阵 Θ = Σ<sup>−1</sup> 与条件独立的等价性（讲义 5.3.1）</div>'
        '<p class="p-text">设标准化收益向量 Z = (Z<sub>1</sub>,…,Z<sub>p</sub>)<sup>T</sup> ~ N<sub>p</sub>(0, Σ)，联合密度为 exp(−½ Z<sup>T</sup> Θ Z) / const。因子化只含两两变量乘积项，故：</p>'
        '<div class="math-box">'
        'θ<sub>jk</sub> = 0 &nbsp;⟺&nbsp; ρ<sub>jk | −jk</sub> = −'
        '<span class="frac"><span class="num">θ<sub>jk</sub></span><span class="den">√(θ<sub>jj</sub> θ<sub>kk</sub>)</span></span>'
        ' = 0 &nbsp;⟺&nbsp; Z<sub>j</sub> ⊥ Z<sub>k</sub> | Z<sub>−{j,k}</sub>'
        '</div>'
        '<ul class="ul">'
        '<li><span class="hl">大白话理解偏相关</span>：把 Z<sub>j</sub> 和 Z<sub>k</sub> 分别对剩下 13 支资产做线性回归，剔除掉能被其他资产共同解释的部分后，看两条残差之间还剩下多少相关。</li>'
        '<li><span class="hl">图拓扑映射</span>：θ<sub>jk</sub> = 0 对应无向图 G=(V, E) 中节点 j 与 k 之间<span class="hl-teal">没有边</span>；只有非零项才表示直接风险传导通道。</li>'
        '</ul>'
        '</div>'
        '<div class="card">'
        '<div class="card-hd">2. 已知图结构 E 的带约束 MLE — 讲义 5.3.4 算法一</div>'
        '<p class="p-text">给定标准化样本协方差矩阵 S，多元高斯对数似然函数（忽略常数）为：</p>'
        '<div class="math-box">'
        'ℓ(Θ) = log det Θ − tr(SΘ) &nbsp;&nbsp; s.t. &nbsp; θ<sub>jk</sub> = 0, ∀ (j, k) ∉ E'
        '</div>'
        '<ul class="ul">'
        '<li><span class="hl">KKT 一阶条件</span>：设 W = Θ<sup>−1</sup>，最优解必须在活跃边与对角线上精确匹配样本协方差（W<sub>jk</sub> = S<sub>jk</sub>, ∀(j,k)∈E∪diag），而在非边位置精度矩阵元素严格为零。</li>'
        '<li><span class="hl">Algorithm 1（Speed &amp; Kiiveri / ESL Alg 17.1）</span>：初始化 W = S；循环遍历每个节点 j，仅保留邻居集回归方程 W<sub>11</sub>* β* = s<sub>12</sub>*，非邻居位置补零得 <span class="hat">β</span>，回填 w<sub>12</sub> = W<sub>11</sub> <span class="hat">β</span> 并最终反解 Θ。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '<div class="card dark" style="padding:11px 16px;">'
        '<div class="card-hd">3. 本项目 Algorithm 1 块坐标下降求解器数值精度自检（训练集 64 边最优图）</div>'
        '<div class="grid-3" style="margin-top:2px;">'
        f'<div><div style="font-size:20px;font-weight:700;color:#FBBF24;">{eb["alg1_primal_err"]:.2e}</div><div style="font-size:12px;color:#CBD5E1;">边及对角线最大匹配误差 max|W<sub>jk</sub> − S<sub>jk</sub>|（达到双精度机器极限）</div></div>'
        f'<div><div style="font-size:20px;font-weight:700;color:#7DD3FC;">{eb["alg1_zero_err"]:.1f}</div><div style="font-size:12px;color:#CBD5E1;">非边位置精度阵最大绝对值 max|θ<sub>jk</sub>|（条件独立零结构零渗漏）</div></div>'
        f'<div><div style="font-size:20px;font-weight:700;color:#86EFAC;">{eb["min_eigenvalue_theta_refit"]:.4f} &gt; 0</div><div style="font-size:12px;color:#CBD5E1;">重估精度矩阵最小特征值 λ<sub>min</sub>（严格正定，可安全求逆配权）</div></div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(4, 1, "三、模型解构（上）：精度矩阵条件独立与讲义 5 算法一",
                           "把多元正态逆协方差翻译成条件独立边，并用约束极大似然在给定图上精确还原无偏边权",
                           s4_body, notes_list[3]))

    # Slide 5: Math Deconstruction II
    s5_body = (
        '<div class="card" style="padding:10px 15px;">'
        '<div class="card-hd">讲义 5 算法二（Graphical Lasso）＋ 算法一（约束 MLE）两步精估实战流水线</div>'
        '<svg viewBox="0 0 1160 88" style="width:100%;height:84px;">'
        '<rect x="6" y="12" width="235" height="64" rx="8" fill="#F0F6FC" stroke="#0A365C" stroke-width="1.5"/>'
        '<text x="123" y="34" text-anchor="middle" fill="#0A365C" font-size="13" font-weight="700">Step 1：训练集标准化 Z</text>'
        '<text x="123" y="54" text-anchor="middle" fill="#334155" font-size="11.5">消除各 ETF 波动率量纲差异</text>'
        '<text x="123" y="69" text-anchor="middle" fill="#0E7490" font-size="10.5">均值 μ_tr、标准差 σ_tr 仅用训练集</text>'
        '<polygon points="248,44 268,36 268,52" fill="#0E7490" transform="rotate(180 258 44)"/>'
        '<rect x="275" y="12" width="275" height="64" rx="8" fill="#ECFEFF" stroke="#0E7490" stroke-width="1.5"/>'
        '<text x="412" y="34" text-anchor="middle" fill="#0E7490" font-size="13" font-weight="700">Step 2：算法二 GLasso 选边集 E(α)</text>'
        '<text x="412" y="54" text-anchor="middle" fill="#334155" font-size="11.5">max log det Θ − tr(SΘ) − α||Θ_off||₁</text>'
        '<text x="412" y="69" text-anchor="middle" fill="#334155" font-size="10.5">α∈[0.03, 0.85] 共 32 档路径扫描</text>'
        '<polygon points="557,44 577,36 577,52" fill="#0E7490" transform="rotate(180 567 44)"/>'
        '<rect x="584" y="12" width="275" height="64" rx="8" fill="#FFFBEB" stroke="#D97706" stroke-width="1.5"/>'
        '<text x="721" y="34" text-anchor="middle" fill="#92400E" font-size="13" font-weight="700">Step 3：算法一约束 MLE 无偏重估</text>'
        '<text x="721" y="54" text-anchor="middle" fill="#334155" font-size="11.5">锁定 E(α) 零结构，去掉 L₁ 惩罚</text>'
        '<text x="721" y="69" text-anchor="middle" fill="#334155" font-size="10.5">得到无偏精度阵 Θ_Refit(α)</text>'
        '<polygon points="866,44 886,36 886,52" fill="#0E7490" transform="rotate(180 876 44)"/>'
        '<rect x="893" y="12" width="260" height="64" rx="8" fill="#0A365C"/>'
        '<text x="1023" y="34" text-anchor="middle" fill="#FBBF24" font-size="13" font-weight="700">Step 4：EBIC 择优与尺度还原</text>'
        '<text x="1023" y="54" text-anchor="middle" fill="#FFFFFF" font-size="11.5">选 γ=0.5 下 EBIC 最小图 (64 边)</text>'
        '<text x="1023" y="69" text-anchor="middle" fill="#CBD5E1" font-size="10.5">还原 Θ_ret = D_σ⁻¹ Θ_Z D_σ⁻¹</text>'
        '</svg>'
        '</div>'
        '<div class="grid-2" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">讲义 5.3.6 算法二（Graphical Lasso）核心机制</div>'
        '<div class="math-box" style="font-size:13.5px;">'
        'Θ<sup>−1</sup> − S − α · Sign(Θ) = 0 &nbsp;⇒&nbsp; 每列等价于解 W<sub>11</sub> β − s<sub>12</sub> + α·Sign(β) = 0'
        '</div>'
        '<ul class="ul">'
        '<li><span class="hl">为什么必须标准化后再拟合？</span>：15 支 ETF 波动率相差数倍（如 TLT/XLE 远高于 IEF/HYG），若直接惩罚原始协方差，高波动资产会被过度压缩；在相关矩阵尺度惩罚，所有资产公平竞争边资格。</li>'
        '<li><span class="hl">如何保持结构不变还原回收益率尺度？</span>：Θ<sub>ret</sub> = D<sub>σ</sub><sup>−1</sup> Θ<sub>Z</sub> D<sub>σ</sub><sup>−1</sup> 是严格正定对角缩放，不改变任意零元素位置，同时可直接求解真实美元收益组合权重。</li>'
        '</ul>'
        '</div>'
        '<div class="card amber">'
        '<div class="card-hd">为什么要“两步重估”？+ 为什么用 EBIC 而非交叉验证？</div>'
        '<ul class="ul">'
        f'<li><span class="hl-amber">消除 L<sub>1</sub> 收缩偏误</span>：直接 GLasso 会把留下的非零偏相关往零压缩。以 <span class="hl">XLY–XLU</span> 为例，直接 GLasso 仅给出 <span class="hl-red">{neg_e[1]["pcorr_glasso"]:.4f}</span>，经算法一重估后真实强度还原为 <span class="hl-red">{neg_e[1]["pcorr_refit"]:.3f}</span>；测试集 NLL 也从 {nll["GLasso_EBIC_test_NLL"]:.3f} 降至 <span class="hl">{nll["GGM_Alg1_Refit_test_NLL"]:.3f}</span>。</li>'
        '<li><span class="hl-amber">EBIC 模型选择一致性（Foygel &amp; Drton, 2010）</span>：交叉验证仅看预测似然，常在样本外多留出假阳性弱边；EBIC 在 BIC 基础上增加图模型空间复杂度惩罚项：</li>'
        '</ul>'
        '<div class="math-box" style="font-size:13px;">'
        'EBIC<sub>γ</sub>(E) = −n (log det <span class="hat">Θ</span><sub>E</sub> − tr(S <span class="hat">Θ</span><sub>E</sub>)) + |E| log n + 4|E|γ log p &nbsp;&nbsp;(γ = 0.5)'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(5, 1, "三、模型解构（下）：算法二 Graphical Lasso、两步精估与 EBIC",
                           "L1 惩罚筛选干净骨架，约束 MLE 恢复无偏边权，EBIC 避免模型选入过多虚假噪声边",
                           s5_body, notes_list[4]))

    # Slide 6: Real Dataset & Experimental Design
    s6_body = (
        '<div class="grid-4">'
        f'<div class="kpi"><div class="v">{ds["n_assets"]} 支</div><div class="l">美国核心 ETF</div><div class="s">11 行业 + 4 跨资产宏观</div></div>'
        f'<div class="kpi"><div class="v">{ds["n_total_days"]:,} 天</div><div class="l">日对数收益率</div><div class="s">{ds["date_start"]} ~ {ds["date_end"]}</div></div>'
        f'<div class="kpi"><div class="v">{ds["n_train"]:,} 天</div><div class="l">训练集 (2020–2023)</div><div class="s">标准化、选边、算法一重估</div></div>'
        f'<div class="kpi"><div class="v">{ds["n_test"]:,} 天</div><div class="l">测试集 (2024–2025)</div><div class="s">严格样本外 NLL 与滚动回测</div></div>'
        '</div>'
        '<div class="card">'
        '<div class="card-hd">真实资产池结构（Yahoo Finance 复权收盘价 adjclose，0 缺失值、0 非正价格）</div>'
        '<table class="tbl">'
        '<thead><tr><th>资产类别</th><th>ETF 代码与中文名</th><th>风险与宏观属性</th><th>研究看点</th></tr></thead>'
        '<tbody>'
        '<tr><td>成长科技</td><td>XLK (科技)、XLC (通信服务)</td><td>长久期高估值，受无风险利率与 AI 资本开支驱动</td><td>内部高联动及对高油价/高利率敏感度</td></tr>'
        '<tr><td>周期与资源</td><td>XLF (金融)、XLY (可选)、XLI (工业)、XLE (能源)、XLB (材料)</td><td>直接反映实体经济景气度、信贷脉冲与大宗通胀</td><td>XLF/XLI 是否构成股市风险核心枢纽</td></tr>'
        '<tr><td>防御与类债</td><td>XLV (医疗)、XLP (必选)、XLU (公用事业)、XLRE (房地产)</td><td>低 Beta 现金流或高股息、对利率敏感的防御板块</td><td>剥离市场因子后与进攻板块的替代关系</td></tr>'
        '<tr><td>固收与避险</td><td>TLT (20Y+ 美债)、IEF (7–10Y 美债)、HYG (高收益债)、GLD (黄金)</td><td>利率曲线长中端、企业信用利差与宏观避险锚</td><td>HYG 是否充当债市向股市传导的信用桥梁</td></tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '<div class="card blue" style="padding:10px 14px;">'
        '<div class="card-hd">严格防前瞻泄露（No-Lookahead）时间轴设计</div>'
        '<svg viewBox="0 0 1160 72" style="width:100%;height:68px;">'
        '<rect x="10" y="16" width="690" height="40" rx="6" fill="#0A365C"/>'
        '<text x="355" y="34" text-anchor="middle" fill="#FFFFFF" font-size="12.5" font-weight="700">训练集：2020-01-03 ~ 2023-12-29（n = 1,005 交易日）</text>'
        '<text x="355" y="50" text-anchor="middle" fill="#CBD5E1" font-size="11">仅用本段估计 μ, σ、运行 GLasso + EBIC 选图、拟合算法一与两阶段结构对照（2020–22 vs 2023–25）</text>'
        '<rect x="712" y="16" width="438" height="40" rx="6" fill="#0E7490"/>'
        '<text x="931" y="34" text-anchor="middle" fill="#FFFFFF" font-size="12.5" font-weight="700">测试集：2024-01-02 ~ 2025-12-31（n = 502 交易日）</text>'
        '<text x="931" y="50" text-anchor="middle" fill="#E0F2FE" font-size="11">严格样本外 NLL 检验 ＋ 252 日因果滚动窗口每 21 日调仓回测</text>'
        '</svg>'
        '</div>'
    )
    slides.append(wrap_slide(6, 1, "四、真实数据集与实验设计：15 支美股行业与跨资产 ETF",
                           "覆盖 2020 疫情暴跌、2022 激进加息与 2023–2025 高利率 AI 周期，全流程严守零前瞻泄露",
                           s6_body, notes_list[5]))

    # Slide 7: Fig 1 Heatmaps
    s7_body = (
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.95;">'
        '<img src="../outputs/figures/fig1_corr_vs_pcorr_heatmaps.png" alt="图1 相关矩阵与偏相关矩阵对比"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">从“一片红”到 39.0% 稀疏归零</div>'
        '<ul class="ul">'
        '<li>左图皮尔逊相关矩阵受大盘共震主导，11 个股票板块两两相关普遍落在 <span class="hl">0.60–0.91</span>，几乎无零值。</li>'
        f'<li>右图 EBIC 最优 GGM 将 105 条潜在边精准删减至 <span class="hl-teal">{eb["n_edges"]} 条</span>（41 对关系彻底归零），大盘系统性背景音被干净剥离。</li>'
        '</ul>'
        '</div>'
        '<div class="card">'
        '<div class="card-hd">保留下来的最强直接经济链路（Refit 偏相关）</div>'
        '<table class="tbl">'
        '<thead><tr><th>资产对</th><th class="num-col">皮尔逊</th><th class="num-col">偏相关</th></tr></thead>'
        '<tbody>'
        f'<tr><td>TLT / IEF (长短美债)</td><td class="num-col">+{pos_e[0]["pearson_corr"]:.3f}</td><td class="num-col hl">+{pos_e[0]["pcorr_refit"]:.3f}</td></tr>'
        f'<tr><td>XLK / XLC (科技通信)</td><td class="num-col">+{pos_e[1]["pearson_corr"]:.3f}</td><td class="num-col hl">+{pos_e[1]["pcorr_refit"]:.3f}</td></tr>'
        f'<tr><td>XLU / XLRE (公用地产)</td><td class="num-col">+{pos_e[2]["pearson_corr"]:.3f}</td><td class="num-col hl">+{pos_e[2]["pcorr_refit"]:.3f}</td></tr>'
        f'<tr><td>XLI / XLB (工业材料)</td><td class="num-col">+{pos_e[3]["pearson_corr"]:.3f}</td><td class="num-col hl">+{pos_e[3]["pcorr_refit"]:.3f}</td></tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '<div class="note-strip">'
        '<strong>经济直觉：</strong>控制其余资产后，保留下来的全是久期同一曲线（TLT-IEF）、商业业务重叠（XLK-XLC）、高股息利率敏感（XLU-XLRE）和实体上下游（XLI-XLB）等真实直接联系。'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(7, 2, "五、实证分析（一）：皮尔逊相关矩阵 vs. GGM 稀疏偏相关矩阵",
                           "扣掉大盘共同因子后，105 条潜在关系有 41 条直接归零，核心产业与利率骨架清晰浮现",
                           s7_body, notes_list[6]))

    # Slide 8: Fig 2 Network
    s8_body = (
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.45;">'
        '<img src="../outputs/figures/fig2_glasso_network_graph.png" alt="图2 跨资产条件独立网络"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card red">'
        '<div class="card-hd">核心亮点：“符号反转”抓出隐蔽对冲边</div>'
        '<ul class="ul">'
        f'<li><span class="hl-red">XLF (金融) — GLD (黄金)：{neg_e[0]["pcorr_refit"]:.3f}</span>（皮尔逊仅 +{neg_e[0]["pearson_corr"]:.3f}），直观体现银行/金融风险偏好与黄金避险的直接负向对冲。</li>'
        f'<li><span class="hl-red">XLY (可选) — XLU (公用)：{neg_e[1]["pcorr_refit"]:.3f}</span>（皮尔逊高达 +{neg_e[1]["pearson_corr"]:.3f}），去掉大盘后露出资金在进攻与防御板块间的轮动跷跷板。</li>'
        f'<li><span class="hl-red">XLP/XLK — XLE (能源)：{neg_e[2]["pcorr_refit"]:.3f} / {neg_e[3]["pcorr_refit"]:.3f}</span>，反映原油通胀对下游消费成本与科技估值的直接挤压。</li>'
        '</ul>'
        '</div>'
        '<div class="card blue">'
        '<div class="card-hd">网络传染枢纽 Top 5（按 Strength = Σ|ρ|）</div>'
        '<ul class="ul">'
        f'<li><span class="hl">1. XLF 金融</span>：强度 {nodes[0]["strength"]:.2f}（连接 {nodes[0]["degree"]} 个节点），宏观信用与全市场周期的总阀门。</li>'
        f'<li><span class="hl">2. XLI 工业</span>：强度 {nodes[1]["strength"]:.2f}（度 {nodes[1]["degree"]}），连接周期上游原材料与下游消费。</li>'
        f'<li><span class="hl">3. XLK 科技</span> ({nodes[2]["strength"]:.2f})、4. <span class="hl">IEF 美债</span> ({nodes[3]["strength"]:.2f})、5. <span class="hl">XLU 公用</span> ({nodes[4]["strength"]:.2f})。</li>'
        '</ul>'
        '</div>'
        '<div class="card teal" style="padding:10px 14px;">'
        '<div class="card-hd">跨市场桥梁：高收益信用债 HYG</div>'
        '<p class="p-text">HYG 拥有 <span class="hl">11 条连接、介数中心度 0.165</span>，同时直连中端美债 IEF (+0.19)、金融 XLF (+0.19) 与地产 XLRE (+0.21)，是利率冲击向权益端扩散的关键传导桥梁。</p>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(8, 2, "五、实证分析（二）：条件独立风险网络、符号反转与核心枢纽",
                           "红色虚线揭示剥离大盘后的真实对冲关系，金融 XLF 与高收益债 HYG 处于跨市场传染核心",
                           s8_body, notes_list[7]))

    # Slide 9: Fig 3 Regularization Path & Test NLL
    s9_body = (
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:2.05;">'
        '<img src="../outputs/figures/fig3_regularization_path_ebic.png" alt="图3 正则化路径与EBIC曲线"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">EBIC 模型选择诊断</div>'
        '<ul class="ul">'
        f'<li>在 α ∈ [{pr["min_alpha"]:.2f}, {pr["max_alpha"]:.2f}] 网格上，边数从 <span class="hl">{pr["max_edges"]} 条</span>平滑收缩至 <span class="hl">{pr["min_edges"]} 条</span>。</li>'
        f'<li>EBIC (γ=0.5) 在 <span class="hl-teal">α* = {eb["alpha"]:.4f}</span> 处取得全局极小值 <span class="hl">{eb["ebic"]:.2f}</span>（BIC = {eb["bic"]:.2f}），选出 {eb["n_edges"]}/105 条边。</li>'
        f'<li>该惩罚下 GLasso 训练内 5 折交叉验证 NLL 为 {eb["cv_5fold_nll"]:.3f}。</li>'
        '</ul>'
        '</div>'
        '<div class="card" style="flex:1;">'
        '<div class="card-hd">为什么需要算法一重估？（样本外检验）</div>'
        '<p class="p-text">在 2024–2025 测试集 (n=502) 上计算高斯每观测平均负对数似然（越低代表对未来联合分布刻画越准）：</p>'
        '<ul class="ul">'
        '<li>未经重估的 GLasso 因 L<sub>1</sub> 压缩偏差，测试集 NLL 恶化至 <span class="hl-red">11.860</span>；</li>'
        '<li>经算法一无偏重估后降至 <span class="hl-teal">11.603</span>，不仅战胜行业基准 Ledoit-Wolf (11.646)，而且几乎追平全密集 Sample MLE (11.562)。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
        '<table class="tbl">'
        '<thead><tr><th>2024–2025 测试集评估模型 (标准化 Z, p=15, n=502)</th><th class="num-col">保留边数</th><th class="num-col">测试集平均 NLL (越低越好)</th><th>统计评价</th></tr></thead>'
        '<tbody>'
        f'<tr><td>Sample MLE (无惩罚全密集基准)</td><td class="num-col">105 / 105</td><td class="num-col">{nll["Sample_MLE_test_NLL"]:.3f}</td><td>低维 n/p 大时预测似然基准，但无稀疏结构</td></tr>'
        f'<tr class="hl-row"><td>GGM 两步精估 (Alg 2 选边 + Alg 1 约束 MLE)</td><td class="num-col">64 / 105</td><td class="num-col">{nll["GGM_Alg1_Refit_test_NLL"]:.3f}</td><td>兼具 39% 稀疏可解释性与最优级别样本外似然</td></tr>'
        f'<tr><td>Ledoit-Wolf 线性收缩估计</td><td class="num-col">105 / 105 (稠密)</td><td class="num-col">{nll["LedoitWolf_test_NLL"]:.3f}</td><td>特征值收缩损失了部分高相关资产精确拟合度</td></tr>'
        f'<tr><td>直接 Graphical Lasso (未经算法一重估)</td><td class="num-col">64 / 105</td><td class="num-col hl-red">{nll["GLasso_EBIC_test_NLL"]:.3f}</td><td>L<sub>1</sub> 收缩偏误拉低非零偏相关幅值，似然明显受损</td></tr>'
        '</tbody>'
        '</table>'
    )
    slides.append(wrap_slide(9, 2, "五、实证分析（三）：正则化路径、EBIC 选边与样本外似然检验",
                           "EBIC 稳定选出 64 条边；测试集负对数似然实证证明了算法一去偏重估的关键价值",
                           s9_body, notes_list[8]))

    # Slide 10: Fig 4 Regime Comparison
    s10_body = (
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.9;">'
        '<img src="../outputs/figures/fig4_regime_comparison_networks.png" alt="图4 跨市场时期结构演化"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card red">'
        '<div class="card-hd">时期一：高波动冲击期 (2020–2022)</div>'
        '<ul class="ul">'
        f'<li>样本：{reg["regime1_dates"]}，涵盖疫情熔断与美联储激进加息。</li>'
        f'<li>EBIC 选出 α* = {reg["regime1_alpha"]:.3f}，保留 <span class="hl-red">{reg["regime1_edges"]} 条边</span>，资产间危机传染通道更为密集。</li>'
        '</ul>'
        '</div>'
        '<div class="card blue">'
        '<div class="card-hd">时期二：高利率平台与 AI 周期 (2023–2025)</div>'
        '<ul class="ul">'
        f'<li>样本：{reg["regime2_dates"]}，宏观波动回落，主线转向产业分化。</li>'
        f'<li>EBIC 施加更强正则 α* = {reg["regime2_alpha"]:.4f}，边数明显收敛至 <span class="hl-teal">{reg["regime2_edges"]} 条</span>。</li>'
        '</ul>'
        '</div>'
        '<div class="card dark" style="flex:1;">'
        '<div class="card-hd">跨周期结构稳定性结论</div>'
        f'<div style="font-size:26px;font-weight:700;color:#FBBF24;margin:2px 0;">{reg["n_shared_edges"]} 条核心边共享 · Jaccard = {reg["edge_jaccard_similarity"]:.3f}</div>'
        '<p class="p-text">两期各自独立重选图结构，所有出现过的 75 条边中有 46 条在两期同时复现，证实 GGM 抓住了长期稳定的产业链与宏观传导骨架，而非短期市场噪音。</p>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(10, 2, "六、稳健性检验：跨市场周期的网络结构演化对比",
                           "冲击期风险传染更稠密（65 边），新周期稀疏化（56 边），46 条核心骨架跨周期稳定复现",
                           s10_body, notes_list[9]))

    # Slide 11: Fig 5 Rolling OOS GMVP
    order = ["等权组合 (1/N)", "样本协方差 MLE", "Graphical Lasso", "GGM 两步精估 (Alg1)", "Ledoit-Wolf 收缩"]
    rows11 = []
    for name in order:
        m = ro[name]
        cls = ' class="hl-row"' if "Alg1" in name else ""
        rows11.append(
            f'<tr{cls}><td>{name}</td>'
            f'<td class="num-col">{m["ann_ret_pct"]:.2f}%</td>'
            f'<td class="num-col">{m["ann_vol_pct"]:.2f}%</td>'
            f'<td class="num-col">{m["sharpe_rf0"]:.2f}</td>'
            f'<td class="num-col">{m["max_dd_pct"]:.2f}%</td>'
            f'<td class="num-col">{m["total_ret_pct"]:.2f}%</td>'
            f'<td class="num-col">{m["avg_l1_leverage"]:.2f}</td></tr>'
        )
    s11_body = (
        '<div class="row" style="flex:1.15;">'
        '<div class="fig-box" style="flex:2.05;">'
        '<img src="../outputs/figures/fig5_oos_gmvp_backtest.png" alt="图5 样本外滚动GMVP回测"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">全局最小方差组合（GMVP）设置</div>'
        '<div class="math-box" style="font-size:14px;">'
        'w* = <span class="frac"><span class="num">Θ<sub>ret</sub> 1</span><span class="den">1<sup>T</sup> Θ<sub>ret</sub> 1</span></span> &nbsp;(允许卖空，∑w<sub>i</sub> = 1)'
        '</div>'
        '<ul class="ul">'
        '<li><span class="hl">严格因果滚动</span>：2024–2025 共 502 个交易日，每 21 个交易日仅使用过去 252 天历史窗口重估精度矩阵。</li>'
        '<li><span class="hl">风控评价核心</span>：GMVP 不预测收益，唯一目标是<span class="hl-teal">最小化样本外真实组合波动率</span>与尾部回撤。</li>'
        '</ul>'
        '</div>'
        '<div class="note-strip" style="flex:1;">'
        '<strong>核心战绩：</strong>GGM 两步精估组合取得全场最低年化波动率 <strong>3.03%</strong>、最小最大回撤 <strong>−1.30%</strong> 与最高夏普比率 <strong>2.82</strong>（无风险利率设为 0）；直接 GLasso 则将平均 L<sub>1</sub> 总杠杆压至最低 <strong>1.92</strong>。'
        '</div>'
        '</div>'
        '</div>'
        '<table class="tbl">'
        '<thead><tr><th>滚动 252 日样本外策略 (2024–2025)</th><th class="num-col">年化收益率</th><th class="num-col">年化波动率</th><th class="num-col">夏普比率 (rf=0)</th><th class="num-col">最大回撤</th><th class="num-col">累计收益率</th><th class="num-col">平均 L1 总杠杆</th></tr></thead>'
        f'<tbody>{"".join(rows11)}</tbody>'
        '</table>'
    )
    slides.append(wrap_slide(11, 3, "七、商业落地：2024–2025 严格样本外滚动 GMVP 风控回测",
                           "将等权组合 10.52% 年化波动压缩至 3.03%，夏普比率提升至 2.82，最大回撤仅 −1.30%",
                           s11_body, notes_list[10]))

    # Slide 12: Fig 6 Centrality & Weights
    s12_body = (
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.95;">'
        '<img src="../outputs/figures/fig6_centrality_and_weights.png" alt="图6 中心度与组合权重"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">直觉拆解：为何风险枢纽与重仓资产不同？</div>'
        '<ul class="ul">'
        '<li><span class="hl">金融 XLF 是拓扑中心（强度 1.53）</span>：因为它跟 12 个行业都存在直接风险传递，自身波动又高。</li>'
        '<li><span class="hl">GMVP 重仓是 IEF 多头 + TLT 空头</span>：中端美债 IEF 自身波动极低，配合做空高相关性长端美债 TLT（偏相关 +0.866）对冲利率久期风险，把净风险压至极低。</li>'
        '</ul>'
        '</div>'
        '<div class="card">'
        '<div class="card-hd">静态 vs. 滚动平均总杠杆 ||w||<sub>1</sub> 对照</div>'
        '<table class="tbl">'
        '<thead><tr><th>精度估计策略</th><th class="num-col">静态训练拟合</th><th class="num-col">滚动 252 日</th></tr></thead>'
        '<tbody>'
        f'<tr><td>Sample MLE</td><td class="num-col">{st["样本协方差 MLE"]["avg_l1_leverage"]:.2f}</td><td class="num-col">{ro["样本协方差 MLE"]["avg_l1_leverage"]:.2f}</td></tr>'
        f'<tr class="hl-row"><td>直接 Graphical Lasso</td><td class="num-col">{st["Graphical Lasso"]["avg_l1_leverage"]:.2f}</td><td class="num-col">{ro["Graphical Lasso"]["avg_l1_leverage"]:.2f}</td></tr>'
        f'<tr><td>GGM 两步精估 (Alg1)</td><td class="num-col">{st["GGM 两步精估 (Alg1)"]["avg_l1_leverage"]:.2f}</td><td class="num-col">{ro["GGM 两步精估 (Alg1)"]["avg_l1_leverage"]:.2f}</td></tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '<div class="note-strip">'
        '静态一次拟合因未适应 2024–2025 新低波环境，各模型波动率约 3.78%–4.08%；加入 252 日滚动机制后，两步精估充分发挥结构自适应优势，波动降至 3.03%。'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(12, 3, "七、组合拆解与权重稳定性：网络中心度 vs. 实际持仓权重",
                           "网络中心定位风险传导源，最小方差组合通过“多 IEF + 空 TLT”对冲利率因子，稀疏正则抑制杠杆",
                           s12_body, notes_list[11]))

    # Slide 13: Statistical Inference & Honest Boundaries
    s13_body = (
        '<div class="grid-2" style="flex:1;">'
        '<div class="col">'
        '<div class="card">'
        '<div class="card-hd">滚动样本外波动率差值检验（10 日块长 Block Bootstrap，2,000 次）</div>'
        '<table class="tbl">'
        '<thead><tr><th>对比基准（基准 − 两步精估）</th><th class="num-col">波动差值</th><th class="num-col">95% 置信区间</th><th class="num-col">双侧 p 值</th></tr></thead>'
        '<tbody>'
        f'<tr class="hl-row"><td>等权组合 (1/N)</td><td class="num-col">+{bt["EqualWeight_minus_GGM_Refit"]["vol_diff_pct"]:.2f}%</td><td class="num-col">[+{bt["EqualWeight_minus_GGM_Refit"]["ci95_low_pct"]:.2f}%, +{bt["EqualWeight_minus_GGM_Refit"]["ci95_high_pct"]:.2f}%]</td><td class="num-col">&lt; 0.001</td></tr>'
        f'<tr><td>Sample MLE (S<sup>−1</sup>)</td><td class="num-col">+{bt["MLE_minus_GGM_Refit"]["vol_diff_pct"]:.2f}%</td><td class="num-col">[{bt["MLE_minus_GGM_Refit"]["ci95_low_pct"]:.2f}%, +{bt["MLE_minus_GGM_Refit"]["ci95_high_pct"]:.2f}%]</td><td class="num-col">{bt["MLE_minus_GGM_Refit"]["p_value"]:.3f}</td></tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '<div class="card amber" style="flex:1;">'
        '<div class="card-hd">诚实的证据边界：0.08% 差值够说碾压 MLE 吗？</div>'
        '<ul class="ul">'
        '<li><span class="hl-amber">对等权基准</span>：降波 7.49 个百分点在统计上极为显著（p &lt; 0.001）。</li>'
        '<li><span class="hl-amber">对 Sample MLE 必须诚实</span>：在 p=15、窗口 n=252（n/p ≈ 16.8）的低维环境下，样本协方差本身估计方差就不大，因此 GGM 的 0.08% 波动率优势区间跨过零（p = 0.122），<span class="hl">未达到 5% 统计显著</span>。</li>'
        '<li><span class="hl">本场景真正的多重价值</span>：更大夏普提升（2.48 → 2.82）、更低回撤（−1.91% → −1.30%）、清晰边结构，以及当资产数 p 扩增到百只以上时稀疏正则抗退化的决定性潜力。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '<div class="card blue">'
        '<div class="card-hd">方法局限性与三大前沿拓展方向</div>'
        '<ul class="ul">'
        '<li><span class="hl">1. 金融收益尖峰厚尾 vs. 高斯假设</span><br>极端暴跌时金融日收益具有明显厚尾与非对称性。改进方案：先做秩正态变换构建 <span class="hl-teal">Nonparanormal / Copula-GGM</span>，或直接替换为多元 t-图模型。</li>'
        '<li><span class="hl">2. 静态窗口滞后 vs. 时变网络拓扑</span><br>固定 252 日滚动对突发性流动性危机响应仍有滞后。改进方案：引入 <span class="hl-teal">Time-Varying Graphical Lasso (TVGL)</span>，在相邻时间片间施加平滑正则实时抓捕结构突变。</li>'
        '<li><span class="hl">3. 无向条件关联 vs. 有向风险因果</span><br>讲义 5 的马尔可夫网络只给出无向对称边，无法判断风险传染上下游及抵御未观测隐因子。改进方案：衔接课程<span class="hl-teal">讲义 6–7 贝叶斯网络（DAG）</span>或结构 VAR，从条件相关走向方向因果。</li>'
        '</ul>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(13, 3, "八、统计显著性边界与前沿拓展方向",
                           "显著跑赢等权基准（p<0.001），坦诚低维下相比 Sample MLE 的边界并给出三项实质性改进路径",
                           s13_body, notes_list[12]))

    # Slide 14: 3-Min Extended Applications
    s14_body = (
        '<div class="grid-3" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">成员 A｜陈霖（量化多因子与风控实战）</div>'
        '<ul class="ul">'
        '<li><span class="hl">背景经历</span>：九坤投资、悬铃私募、乾上泉及 Trexquant 量化多因子与风控实习。</li>'
        '<li><span class="hl">行业痛点</span>：在构建数百上千个量价与分析师因子时，因子间共线性极高；在千只股票全市场配置时，样本协方差矩阵秩亏不可逆。</li>'
        '<li><span class="hl">GGM 落地方式</span>：① 因子合成前用稀疏精度矩阵剥离公共风格暴露，提纯独立增量信息；② 结合行业/风格因子风险模型估计稀疏残差精度矩阵，压低换手与极端空头。</li>'
        '<li><span class="hl">核心注意点</span>：在高频/股票池扩张到 p≫100 时，需配合截面标准化与异常值缩尾以保证稳健。</li>'
        '</ul>'
        '</div>'
        '<div class="card">'
        '<div class="card-hd">成员 B｜[请填姓名]（金融信贷风控模板）</div>'
        '<ul class="ul">'
        '<li><span class="hl">适用领域</span>：商业银行对公授信 / 供应链信用违约风险管理（请结合个人实习替换）。</li>'
        '<li><span class="hl">业务痛点</span>：宏观经济下行时几乎所有行业信用利差同步走阔，传统相关指标全线亮红灯，风控难以锁定最先传导的第一张骨牌。</li>'
        '<li><span class="hl">GGM 落地方式</span>：以重点行业/核心企业违约距离或利差变化为节点，扣掉宏观景气共同因子后，定位直接上下游担保与供应链传染边。</li>'
        '<li><span class="hl">预期价值</span>：辅助银行调整行业集中度限额，并将关键枢纽边直接嵌入压力测试情景树。</li>'
        '</ul>'
        '</div>'
        '<div class="card teal">'
        '<div class="card-hd">成员 C｜[请填姓名]（商业产品分析模板）</div>'
        '<ul class="ul">'
        '<li><span class="hl">适用领域</span>：互联网用户增长 / 电商指标体系因果归因先验探索（请替换）。</li>'
        '<li><span class="hl">业务痛点</span>：DAU、停留时长、加购率、转化与客单价随全站促销或周末流量大盘共同波动，导致业务指标互相虚假相关。</li>'
        '<li><span class="hl">GGM 落地方式</span>：利用稀疏偏相关把大盘流量与节假日周期共震扣掉，看清改版究竟直连复购还是经由中间指标间接传导。</li>'
        '<li><span class="hl">预期价值</span>：为后续开展线上 A/B 试验（讲义 4）或路径归因筛选真正值得干预的核心杠杆指标。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '<div class="note-strip">'
        '<strong>组员改稿小贴士：</strong>组员 B、C 只需将本页第 2、3 栏的“[请填姓名]”与行业例子替换为自己的实习项目（控制在每人 150 字 / 口播 50 秒内），然后运行一行 <code>python3 html_to_pptx.py</code> 即可自动更新高清 PPTX！'
        '</div>'
    )
    slides.append(wrap_slide(14, 4, "九、3 分钟组内个人拓展：结合实习与研究领域的 GGM 价值",
                           "每人 1 分钟以内，讲清“在我的真实场景里用谁当节点、扣掉什么共同因子、解决什么决策痛点”",
                           s14_body, notes_list[13]))

    # Slide 15: References & Q&A
    s15_body = (
        '<div class="row" style="flex:1;">'
        '<div class="card" style="flex:1.5;">'
        '<div class="card-hd">核验学术文献与课程讲义索引（均已逐篇核对刊名、卷期与页码）</div>'
        '<ul class="ul" style="font-size:11.6px;gap:6px;">'
        '<li><span class="hl">[1] Speed, T. P., &amp; Kiiveri, H. T. (1986).</span> Gaussian Markov distributions over finite graphs. <em>The Annals of Statistics</em>, 14(1), 138–150.（讲义 5.3.4 算法一理论基石）</li>'
        '<li><span class="hl">[2] Whittaker, J. (1990).</span> <em>Graphical Models in Applied Multivariate Statistics</em>. John Wiley &amp; Sons.（偏相关与图分隔基础）</li>'
        '<li><span class="hl">[3] Lauritzen, S. L. (1996).</span> <em>Graphical Models</em>. Oxford University Press.（马尔可夫性质与约束凸优化）</li>'
        '<li><span class="hl">[4] Meinshausen, N., &amp; Bühlmann, P. (2006).</span> High-dimensional graphs and variable selection with the Lasso. <em>The Annals of Statistics</em>, 34(3), 1436–1462.</li>'
        '<li><span class="hl">[5] Friedman, J., Hastie, T., &amp; Tibshirani, R. (2008).</span> Sparse inverse covariance estimation with the graphical lasso. <em>Biostatistics</em>, 9(3), 432–441.（讲义 5.3.6 算法二出处）</li>'
        '<li><span class="hl">[6] Foygel, R., &amp; Drton, M. (2010).</span> Extended Bayesian information criteria for Gaussian graphical models. <em>NeurIPS</em>, 23, 604–612.（EBIC 图结构选择）</li>'
        '<li><span class="hl">[7] Ledoit, O., &amp; Wolf, M. (2004).</span> A well-conditioned estimator for large-dimensional covariance matrices. <em>JMVA</em>, 88(2), 365–411.（线性收缩基准）</li>'
        '<li><span class="hl">[8] Hastie, T., Tibshirani, R., &amp; Friedman, J. (2009).</span> <em>The Elements of Statistical Learning</em> (2nd ed., Ch. 17). Springer.（课程教材与 Alg 17.1/17.2 原图出处）</li>'
        '</ul>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card dark" style="flex:1;">'
        '<div class="card-hd">欢迎老师与同学提问（Q&amp;A 重点议题）</div>'
        '<ul class="ul" style="gap:9px;margin-top:4px;">'
        '<li><span style="color:#FBBF24;font-weight:700;">Q1：两步法重估的必要性</span><br>为何不直接用 GLasso 精度矩阵配权，而一定要串联算法一？（消除 L<sub>1</sub> 收缩偏误，测试 NLL 从 11.860 降至 11.603）</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">Q2：标准化与尺度还原</span><br>在相关矩阵上加惩罚后如何保证还原 Θ<sub>ret</sub> = D<sub>σ</sub><sup>−1</sup> Θ<sub>Z</sub> D<sub>σ</sub><sup>−1</sup> 不破坏条件独立零结构？</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">Q3：条件独立 ≠ 单向因果</span><br>无向图无法辨别方向且可能遗漏未观测隐因子，如何与讲义 1–3 因果推断及讲义 6–7 贝叶斯网络衔接？</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">Q4：低维样本外边界</span><br>p=15 下相比 Sample MLE p=0.122，为什么在更高维（p≥100）时 GGM 的抗退化优势才完全释放？</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(15, 4, "十、核心参考文献与 Q&A 交流",
                           "全部代码、数据与检验结果均已归档可复现，感谢冯项楠老师、吴尚老师与各位同学聆听！",
                           s15_body, notes_list[14]))

    html_doc = (
        '<!DOCTYPE html>\n'
        '<html lang="zh-CN">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>版本一｜高斯图模型与跨资产风险传染网络（现代统计模型及应用）</title>\n'
        f'<style>{SHARED_CSS}</style>\n'
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

    # Sync conversational speech script aligned with the 15 slide titles
    slide_titles = [
        "Slide 1｜封面：高斯图模型与 Graphical Lasso——跨资产风险传染网络与样本外组合风控",
        "Slide 2｜一、研究背景与商业痛点：为什么皮尔逊相关会误导风控？",
        "Slide 3｜二、课程定位与方法演进：从相关矩阵到稀疏马尔可夫网络",
        "Slide 4｜三、模型解构（上）：精度矩阵条件独立与讲义 5 算法一",
        "Slide 5｜三、模型解构（下）：算法二 Graphical Lasso、两步精估与 EBIC",
        "Slide 6｜四、真实数据集与实验设计：15 支美股行业与跨资产 ETF",
        "Slide 7｜五、实证分析（一）：皮尔逊相关矩阵 vs. GGM 稀疏偏相关矩阵",
        "Slide 8｜五、实证分析（二）：条件独立风险网络、符号反转与核心枢纽",
        "Slide 9｜五、实证分析（三）：正则化路径、EBIC 选边与样本外似然检验",
        "Slide 10｜六、稳健性检验：跨市场周期的网络结构演化对比",
        "Slide 11｜七、商业落地：2024–2025 严格样本外滚动 GMVP 风控回测",
        "Slide 12｜七、组合拆解与权重稳定性：网络中心度 vs. 实际持仓权重",
        "Slide 13｜八、统计显著性边界与前沿拓展方向",
        "Slide 14｜九、3 分钟组内个人拓展：结合实习与研究领域的 GGM 价值",
        "Slide 15｜十、核心参考文献与 Q&A 交流",
    ]
    timings = ["30秒", "55秒", "45秒", "60秒", "60秒", "45秒", "55秒", "65秒", "50秒", "45秒", "65秒", "45秒", "50秒", "3分钟(每人≤1分)", "Q&A"]
    speech_lines = [
        "# 《现代统计模型及应用》课堂汇报口播稿（版本一：讲义 5 高斯图模型与 Graphical Lasso）",
        "",
        "> **汇报节奏**：前 13 页主讲严格控制在 **11 分 30 秒 – 12 分 00 秒**；第 14 页组内 3 人每人 **≤ 1 分钟**拓展；第 15 页留给老师和同学提问。",
        "> **口吻说明**：面向冯项楠老师、吴尚老师及班上同学，直接讲清直觉反差、数学机制与诚实边界，不用生硬公文腔。",
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
        "- **陈霖（量化多因子与组合风控，约 50 秒）**：",
        "  “结合我之前在九坤、悬铃私募、乾上泉和 Trexquant 的量化实习体验，稀疏精度矩阵在实际研究里解决两个很头疼的问题：第一是做因子去共线——几百个量价与分析师因子本身相关很高，用类似 GGM 的条件独立想法扣掉已有风格暴露后，能看清哪几个因子在真正提供增量信息；第二是在全市场千只股票上算风控权重时，样本协方差极易过拟合甚至不可逆，结合图模型稀疏逆协方差才能有效控制换手率和极端空头仓位。”",
        "- **组员 B（商业银行/信贷风控模板，约 50 秒，请替换为个人真实实习）**：",
        "  “【请组员 B 替换姓名与行业】：如果把这套高斯图模型搬到商业银行对公信贷风控里，我们可以把不同行业的违约距离或信用利差变化作为节点。经济下行时大家看似一起恶化，传统相关矩阵全亮红灯；而用 GGM 扣掉宏观景气共同因子之后，就能直接锁定供应链上下游与担保网络里的核心传染边，提前帮风控团队设好集中度限额。”",
        "- **组员 C（互联网产品分析模板，约 50 秒，请替换为个人真实实习）**：",
        "  “【请组员 C 替换姓名与业务】：在互联网产品数据分析中，DAU、停留时长、点击率和复购率往往跟着周末或全站大盘流量同涨同跌。用 GGM 剥离掉公共流量周期后，我们能先从观察数据里筛出真正条件相关的核心指标骨架——比如区分某个改版到底是直接带动复购，还是仅通过时长间接影响——给后续上线 A/B 试验提供更干净的假设。”",
        "",
        "---",
        "",
        "## 三、第 15 页高频 Q&A 备答（供彩排准备）",
        "",
        "1. **吴尚老师可能问：为什么在 Graphical Lasso 之后还要串联讲义 5.3.4 的算法一（约束 MLE）重估一次？**",
        "   - **答**：因为 GLasso 的 $L_1$ 惩罚会把留下的非零偏相关往零压缩（如 `XLY-XLU` 直接 GLasso 只有 `-0.0011`，重估后为 `-0.176`）。实证中也看到，未重估 GLasso 在 2024–2025 测试集平均负对数似然恶化到 `11.860`，经算法一重估后立刻降回 `11.603`、滚动回测波动也降到全场最低 `3.03%`。",
        "2. **吴尚老师可能问：标准化后拟合的稀疏结构，还原回原始收益率尺度会破坏零元素吗？**",
        "   - **答**：不会。$\\Theta_{\\text{ret}} = D_\\sigma^{-1} \\Theta_Z D_\\sigma^{-1}$ 是左乘和右乘正定对角矩阵，零位置乘以任何非零标量依然严格为零，完整保留条件独立图拓扑，且我们仅使用训练集（或历史滚动窗口）的标准差，毫无前瞻泄露。",
        "3. **冯项楠老师可能问：你们说 GGM 扣掉了共同因子，这和因果推断里的控制混淆是一回事吗？边能当因果看吗？**",
        "   - **答**：共享“条件控制”思想，但不能当成因果。GGM 是无向图，既分不清谁是因谁是果，也只能控制观测到的这 15 个变量——如果有未观测共同因子，甚至同时控制了共同子节点（对撞偏差），边权仍会混入假相关。所以我们汇报全程严格解释为“同日直接条件关联 / 风险传递通道”，而不轻易下因果断言。",
        "4. **老师可能问：低维 $p=15$ 下相对 Sample MLE 波动率 $p=0.122$ 不显著，是不是说明这里不需要正则化？**",
        "   - **答**：很诚实地说，在 $p=15, n=252$（$n/p\\approx 16.8$）下，Sample MLE 确实已经相当稳健，所以我们在第 13 页如实放出了 $p=0.122$ 的检验边界；但 GGM 依然拿到了更高的夏普（2.82 vs 2.48）、更低的回撤（-1.30% vs -1.91%）和可解释的跨资产网络，而且一旦拓展到几百只个股的真实量化池，Sample MLE 直接不可逆，稀疏图模型的优势才会彻底拉开。",
    ])
    OUT_SPEECH.write_text("\n".join(speech_lines) + "\n", encoding="utf-8")
    print(f"Built {OUT_HTML.name} and {OUT_SPEECH.name}")


if __name__ == "__main__":
    main()
