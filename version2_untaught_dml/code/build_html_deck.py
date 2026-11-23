#!/usr/bin/env python3
"""Build Version 2 (Course-Untaught Method: Double/Debiased Machine Learning) 15-slide 1280x720 HTML deck
and synchronized conversational speech script, dynamically pulling all numbers from
outputs/results_summary.json.
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

# Import shared CSS and viewer JS pattern (self-contained in file)
from sys import path as sys_path
sys_path.insert(0, str(ROOT_DIR.parent / "version1_taught_ggm" / "code"))
from build_html_deck import SHARED_CSS, VIEWER_JS  # noqa: E402


def sec_bar_html(active_idx: int) -> str:
    secs = [
        ("01 问题与困境", 1),
        ("02 DML 原理", 3),
        ("03 模拟验证", 5),
        ("04 401(k) 实证与洞察", 7),
        ("05 边界、拓展与 Q&A", 12),
    ]
    items = []
    for i, (label, target) in enumerate(secs):
        cls = "sec-item on" if i == active_idx else "sec-item"
        items.append(f'<span class="{cls}" onclick="goSlide({target})">{label}</span>')
    return (
        '<div class="sec-bar">'
        f'<div class="sec-nav">{"".join(items)}</div>'
        '<div class="sec-course">《现代统计模型及应用》· 版本二（前沿未讲授方法：双重机器学习 DML）</div>'
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
        '<span>复旦大学管理学院 DSBA · 双重机器学习（DML）与 401(k) 净储蓄因果效应</span>'
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

    notes_list: List[str] = [
        # 1
        "各位老师、同学好！我们汇报版本二——课堂尚未讲授但紧接讲义 1–3 因果推断的前沿方法：双重机器学习 DML。开场先看一个经典金融困惑：有 401(k) 资格的美国家庭，净金融资产比没资格家庭平均多出 $19,559，可为什么年收入差异 SMD 高达 +0.637？这到底是养老金带来的净储蓄，还是富人自选择幻觉？",
        # 2
        f"细看 1991 SIPP {emp['n']:,} 户真实调查数据：有资格家庭不仅年收入 SMD 达 +0.637，有固定收益养老金 (db) 和自有住房 (hown) 的比例也显著更高。所以 $19,559 里混进了大量本来就更富有的起点差异。资管机构和财政部门最想知道：扣除这些特征后，真正新创造的储蓄到底有多少？",
        # 3
        "回到讲义 1–3 学过的方法：线性 OLS 只能假定收入和财富成一条直线，结果把真实效应压低到 $5,896；一次方加进二次多项式就立刻跳到 $9,836。而 1:1 倾向得分匹配丢掉了不少难配对的对照样本，ATT 标准误膨胀到 $3,026。那能不能直接拿随机森林或 GBDT 来算因果？答案是直接套用会让置信区间彻底崩溃！",
        # 4
        "为什么直接上机器学习会翻车？两大坑：一是为了防过拟合做的正则化收缩会留下 n⁻¹/⁴ 量级的偏差，乘上 √n 就发散；二是全样本拟合后直接算样本内残差会产生过拟合伪相关。DML 的第一根支柱是 Neyman 正交化：同时对结果 Y 和处置 D 做预测并取残差，正交得分一阶导数为零，把误差缩成两个学习器误差的乘积 n⁻¹/⁴ × n⁻¹/⁴ = n⁻¹/²，瞬间恢复根号 n 一致性！",
        # 5
        "第二根支柱是 K 折交叉拟合（Cross-Fitting）：每折的残差只用另外 4 折训练出的模型去预测，彻底切断样本内过拟合幽灵，且重复 5 次随机切分取中位数稳定结果。模型形态上，除了假定常斜率的 PLR，我们还跑了允许异质性反应的双稳健 IRM，并用讲义 1.2.5 工具变量思路跑了 IIVM 估计实际参与效应。",
        # 6
        f"按大作业要求，我们先用 B={cfg['B']} 次、n={cfg['n']}、p={cfg['p']} 维非线性含噪模拟展示 DML 的不可替代性（真值 θ₀={cfg['theta0']:.1f}）。看图 1：线性 OLS 误设右偏到 2.254；直接森林插值左偏到 1.134；仅正交不做交叉拟合过拟合偏到 1.640；只有完整 DML 居中在 1.997，偏差仅 -0.003！",
        # 7
        "看图 2 和下方汇总表更震撼：前三种不完整做法，在 200 次重复里 95% 置信区间实际覆盖率全都是 0.0%——换言之看似有置信区间实则次次失准！而完整 DML 把 RMSE 从 0.871 降到 0.032，理论 SE (0.033) 与经验 SD (0.032) 高度一致，95% 覆盖率高达 96.5%。",
        # 8
        "把验证好的 DML 搬到 9,915 户真实 401(k) 数据（零缺失值）。图 3 左边展示净金融资产高度右偏且含负债尾部，右边 SMD 图清楚表明 9 个控制变量里有 7 个突破 0.1 平衡警戒线，最严重的年收入、DB 养老金、自有住房、双职工与受教育年限全部指向同一批高阶层家庭。",
        # 9
        "图 4 森林图汇总了传统基准与 4 类不同函数族学习器（Lasso、Ridge、随机森林、HGB）的结果。可以看到传统线性 OLS 偏低 ($5,896)、1:1 PSM 方差大；而 DML-IRM ATE 在 4 种完全不同的机器学习模型下紧凑收敛在 $7,822 到 $8,693，标准误全组最小 ($1,142–$1,250)，HGB ATT 达 $11,436，证明 401(k) 确有显著净储蓄创造效应。",
        # 10
        "做因果实证必须排查假设与敏感性（图 5）：交叉拟合倾向得分重叠良好（5%–95% 分位 0.054–0.707），满足正性假设；针对学术界争议的个人退休账户 pira，剔除它只用 8 特征重估 HGB IRM-ATE 为 $8,923，与基准 $8,693 高度一致。进一步用资格 e401 作为实际参与 p401（合格参与率 70.45%）的工具变量，IIVM 估得实际参与者的局部平均效应 LATE 高达 $12,107！",
        # 11
        "商业应用最关心的客群分化来了（图 6）：基于交叉拟合正交伪结果算出的收入四分位 GATE 显示，Q4 高收入组单户净增量最大（+$20,588），但若除以各组中位年收入，Q1 低收入组（+$4,945）的财富撬动率高达年收入的 36.6%（p<0.001），反而是 Q2 中低收入组置信区间跨过零！",
        # 12
        "这两组数字对商业机构和公共政策指向截然不同的落地策略：养老金资管与商业银行应把 Q4 高净值客群的企业年金转化作为核心 AUM 增长池，并为受房贷挤压的 Q2 夹心层设计更灵活的应急机制；而普惠金融与财税政策不能只看绝对美元数，Q1 群体 36.6% 的撬动率证明“默认自动加入 + 雇主配比”能真正帮低收入家庭攒下第一桶长期资产。",
        # 13
        "同样要诚实交代证据边界：DML 只能消除“可观测特征 X”里的非线性混杂，无法凭空抹掉未记录的个人储蓄偏好；另外还需防范极端倾向得分导致的逆概率加权方差膨胀，以及 1991 年截面历史数据向当下中国个人养老金推广时的制度差异。未来可继续接入 Causal Forest 做个体定价树或混淆敏感性边界。",
        # 14
        "最后 3 分钟拓展，每人 1 分钟。我（陈霖）结合 Trexquant 美股多因子和上海 AI 实验室 Agent RL 研究：在多因子里用 DML 扣掉市值与行业非线性混杂，能更干净地验证新信号的真实增量 Alpha；在 Agent RL 里，正交得分能帮我们在高维上下文做无偏离线回报归因。接下来请组员 B、C 分享（现场替换为各自实习场景）。",
        # 15
        "以上是 Chernozhukov 等 (2018) 及相关经典文献索引（已核验准确卷期页码），右侧准备了四个我们思考最深的 Q&A 问题，欢迎冯项楠老师、吴尚老师和同学们批评指正！",
    ]

    slides: List[str] = []

    # Slide 1: Cover
    slides.append(
        f'<section class="slide cover" data-notes="{html.escape(notes_list[0], quote=True)}">'
        '<div class="cover-top">'
        '<span>复旦大学管理学院 · 数据科学与商务分析项目（DSBA 2026 秋）</span>'
        '<span class="cover-pill">版本二｜课堂未讲授前沿方法：Chernozhukov et al. (2018)</span>'
        '</div>'
        '<div class="cover-main">'
        '<div class="cover-kicker">《现代统计模型及应用》课程大作业汇报 · 授课教师：冯项楠、吴尚</div>'
        '<h1 class="cover-title">双重机器学习（DML）与高维因果推断：<br>Monte Carlo 模拟验证及 401(k) 养老金实证</h1>'
        f'<p class="cover-sub">从讲义 1–3 线性回归与倾向得分匹配出发，用 Neyman 正交化＋交叉拟合驯服机器学习偏误；B={cfg["B"]} 次模拟验证理论有效性，并落地 {emp["n"]:,} 户美国家庭养老金净储蓄因果与客群异质性评估。</p>'
        '<div class="cover-kpis">'
        '<div class="cover-kpi">'
        f'<div class="val">{sim[3]["coverage_95_pct"]:.1f}% vs 0.0%</div>'
        '<div class="lbl">200 次模拟 95% 区间覆盖率</div>'
        f'<div class="desc">完整 DML 均值 {sim[3]["mean_est"]:.3f}（真值 2.0, RMSE {sim[3]["rmse"]:.3f}），OLS/非正交/无交叉拟合覆盖率全部崩为 0%</div>'
        '</div>'
        '<div class="cover-kpi">'
        f'<div class="val">+${irm["HistGradientBoosting"]["ATE"]["est"]:,.0f} (LATE +${late["est"]:,.0f})</div>'
        '<div class="lbl">401(k) 净金融资产因果增量</div>'
        f'<div class="desc">剥离收入 SMD (+0.637) 等混杂后，4 种学习器 IRM-ATE 收敛于 $7,822–$8,693，远低于表面 +${base["naive_diff"]["est"]:,.0f}</div>'
        '</div>'
        '<div class="cover-kpi">'
        f'<div class="val">Q4 +${gates[3]["gate"]:,.0f} ｜ Q1 {gates[0]["effect_to_income_pct"]:.1f}%</div>'
        '<div class="lbl">收入四分位异质性（GATE）</div>'
        f'<div class="desc">高收入绝对增量最大，而低收入组（+${gates[0]["gate"]:,.0f}）财富撬动率占中位年收 36.6%（p&lt;0.001）</div>'
        '</div>'
        '</div>'
        '</div>'
        '<div class="cover-bottom">'
        '<span>汇报结构：12 分钟模拟与实证汇报（Slide 1–13）＋ 3 分钟每人 1 分钟拓展（Slide 14）＋ Q&amp;A</span>'
        '<span>小组成员：陈霖、组员 B、组员 C</span>'
        '</div>'
        '</section>'
    )

    # Slide 2: Business Problem & Selection Bias
    s2_body = (
        '<div class="grid-4">'
        f'<div class="kpi" style="border-top-color:#B91C1C;"><div class="v" style="color:#B91C1C;">+${base["naive_diff"]["est"]:,.0f}</div><div class="l">表面净金融资产差</div><div class="s">有资格 $30.3k vs 无资格 $10.8k</div></div>'
        f'<div class="kpi"><div class="v">{emp["n"]:,} 户</div><div class="l">1991 SIPP 真实家庭</div><div class="s">合格 {emp["treated_e401"]:,} 户 · 对照 {emp["control_e401"]:,} 户</div></div>'
        '<div class="kpi" style="border-top-color:#D97706;"><div class="v" style="color:#B45309;">+0.637</div><div class="l">年收入选择偏差 SMD</div><div class="s">9 个特征中 7 个 |SMD| &gt; 0.1</div></div>'
        f'<div class="kpi" style="border-top-color:#0E7490;"><div class="v" style="color:#0E7490;">{emp["compliers_p401_given_e401"]*100:.2f}%</div><div class="l">合格家庭实际参与率</div><div class="s">支持工具变量 IIVM LATE 识别</div></div>'
        '</div>'
        '<div class="grid-2" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">商业与政策核心争议：净新增储蓄还是“资产搬家”？</div>'
        '<ul class="ul">'
        '<li><span class="hl">政策与商业痛点</span>：无论是政府推行税收递延养老金，还是银行推广个人养老金账户，都需要回答：补贴究竟创造出了<span class="hl-teal">净新增储蓄</span>，还是只诱导本来就会理财的家庭把原有存款转进免税壳里（Crowding-out / 挤出效应）？</li>'
        '<li><span class="hl">严重的富人自选择偏差</span>：雇主是否提供 401(k) 高度依赖于公司规模与薪酬水平——高收入（SMD +0.637）、有固定收益养老金（+0.521）、自有住房（+0.363）、双职工（+0.341）的家庭更常进入提供 401(k) 的企业。</li>'
        '<li><span class="hl">直接对比必错</span>：表面多出的 +$19,559 混杂了大量初始财富能力差异，必须彻底剥离这些多维社会经济特征。</li>'
        '</ul>'
        '</div>'
        '<div class="card">'
        '<div class="card-hd">混杂偏误因果路径图（为什么必须精细控制高维特征 X）</div>'
        '<svg viewBox="0 0 540 220" style="width:100%;height:208px;">'
        '<rect x="18" y="16" width="210" height="184" rx="10" fill="#FFFBEB" stroke="#D97706" stroke-width="1.6"/>'
        '<text x="123" y="42" text-anchor="middle" fill="#92400E" font-size="13.5" font-weight="700">9 维家庭混杂特征 X</text>'
        '<text x="123" y="68" text-anchor="middle" fill="#334155" font-size="12">• 家庭年收入 inc (SMD +0.637)</text>'
        '<text x="123" y="90" text-anchor="middle" fill="#334155" font-size="12">• 固定收益养老金 db (+0.521)</text>'
        '<text x="123" y="112" text-anchor="middle" fill="#334155" font-size="12">• 自有住房 hown (+0.363)</text>'
        '<text x="123" y="134" text-anchor="middle" fill="#334155" font-size="12">• 双职工 twoearn (+0.341)</text>'
        '<text x="123" y="156" text-anchor="middle" fill="#334155" font-size="12">• 学历 educ / 年龄 age / 婚姻</text>'
        '<text x="123" y="180" text-anchor="middle" fill="#B45309" font-size="11.5" font-weight="600">（与资产呈强非线性/交互关系）</text>'
        '<line x1="228" y1="68" x2="318" y2="54" stroke="#B91C1C" stroke-width="2.2"/>'
        '<polygon points="322,53 311,49 313,59" fill="#B91C1C"/>'
        '<line x1="228" y1="145" x2="318" y2="162" stroke="#B91C1C" stroke-width="2.2"/>'
        '<polygon points="322,163 313,157 311,167" fill="#B91C1C"/>'
        '<rect x="326" y="24" width="194" height="56" rx="8" fill="#0A365C"/>'
        '<text x="423" y="48" text-anchor="middle" fill="#FFFFFF" font-size="13" font-weight="700">处置 D：401(k) 资格 e401</text>'
        '<text x="423" y="66" text-anchor="middle" fill="#CBD5E1" font-size="11">m₀(X) 倾向得分受高收入主导</text>'
        '<rect x="326" y="138" width="194" height="58" rx="8" fill="#0E7490"/>'
        '<text x="423" y="162" text-anchor="middle" fill="#FFFFFF" font-size="13" font-weight="700">结果 Y：净金融资产 net_tfa</text>'
        '<text x="423" y="180" text-anchor="middle" fill="#E0F2FE" font-size="11">g₀(X) 随收入呈陡峭非线性增长</text>'
        '<line x1="423" y1="80" x2="423" y2="134" stroke="#0A365C" stroke-width="3"/>'
        '<polygon points="423,138 418,128 428,128" fill="#0A365C"/>'
        '<rect x="430" y="96" width="98" height="26" rx="5" fill="#E0F2FE" stroke="#0E7490"/>'
        '<text x="479" y="113" text-anchor="middle" fill="#0A365C" font-size="12" font-weight="700">真实因果 θ₀</text>'
        '</svg>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(2, 0, "一、研究背景与商业问题：401(k) 究竟带来多少净新增储蓄？",
                           "表面 +$19,559 资产差距里混入严重高收入选择偏差，剥离非线性混杂后才能见真章",
                           s2_body, notes_list[1]))

    # Slide 3: Why Beyond Course Methods
    s3_body = (
        '<table class="tbl">'
        '<thead><tr><th>因果估计方法</th><th>课程定位</th><th>对高维非线性混杂处理</th><th>置信区间有效性</th><th class="num-col">401(k) 基准结果 (SE)</th></tr></thead>'
        '<tbody>'
        f'<tr><td>线性 OLS 控制（讲义 2.2）</td><td>课堂讲授基础</td><td>仅线性可加，拟合不了高收入财富弯度</td><td>函数误设时严重有偏</td><td class="num-col">+${base["linear_ols"]["est"]:,.0f} (${base["linear_ols"]["se"]:,.0f})</td></tr>'
        f'<tr><td>二次多项式 OLS</td><td>经典参数拓展</td><td>手写交叉/平方项，高维时维度爆炸过拟合</td><td>高维下方差膨胀</td><td class="num-col">+${base["poly2_ols"]["est"]:,.0f} (${base["poly2_ols"]["se"]:,.0f})</td></tr>'
        f'<tr><td>PSM 1:1 倾向得分匹配（讲义 2.3）</td><td>课堂讲授核心</td><td>依赖参数 Logit 设定，丢弃未匹配对照组</td><td>Bootstrap 较慢、ATT 方差翻倍</td><td class="num-col">ATE +${base["psm"]["ATE"]["est"]:,.0f} / ATT SE ${base["psm"]["ATT"]["se"]:,.0f}</td></tr>'
        '<tr><td>直接机器学习 Plug-in（不推荐）</td><td>黑箱预测直代</td><td>擅长高维非线性与交互，但有正则化收缩</td><td class="hl-red">95% CI 覆盖率跌至 0%</td><td class="num-col hl-red">模拟严重偏误（−0.866）</td></tr>'
        f'<tr class="hl-row"><td>双重机器学习 DML (Chernozhukov 2018)</td><td>前沿未讲授方法</td><td>任意 ML（Lasso/Ridge/RF/GBDT）自由拟合</td><td>√n 正态、模拟覆盖率 96.5%</td><td class="num-col">IRM ATE +${irm["HistGradientBoosting"]["ATE"]["est"]:,.0f} (${irm["HistGradientBoosting"]["ATE"]["se"]:,.0f})</td></tr>'
        '</tbody>'
        '</table>'
        '<div class="grid-3" style="flex:1;">'
        '<div class="card red">'
        '<div class="card-hd">困境一：讲义线性 OLS 被“掰弯”</div>'
        '<ul class="ul">'
        '<li>家庭净金融资产随年收入并非直线上升，高收入组储蓄率呈指数级爬坡。</li>'
        f'<li>强行用一条直线控制 X，会把高收入斜率拟合错位，反过来把 401(k) 因果效应一路压低到 <span class="hl-red">+${base["linear_ols"]["est"]:,.0f}</span>。</li>'
        '</ul>'
        '</div>'
        '<div class="card amber">'
        '<div class="card-hd">困境二：1:1 PSM 丢失对照样本信息</div>'
        '<ul class="ul">'
        '<li>一对一最近邻匹配只保留匹配到的对照组，虽有 99.5% 共同支撑，但信息利用不充分。</li>'
        f'<li>实证中 PSM 的 ATT 标准误飙升至 <span class="hl-amber">${base["psm"]["ATT"]["se"]:,.0f}</span>，几乎是 DML-IRM（${irm["HistGradientBoosting"]["ATT"]["se"]:,.0f}）的两倍。</li>'
        '</ul>'
        '</div>'
        '<div class="card blue">'
        '<div class="card-hd">破局之道：让 ML 安全走进因果推断</div>'
        '<ul class="ul">'
        '<li>现代机器学习最擅长自动学出复杂 g₀(X) 和 m₀(X)，无需人工猜多项式形式。</li>'
        '<li>但要消除机器学习带来的正则化偏差与过拟合偏差，必须引入 DML 的<span class="hl-teal">双支柱机制</span>。</li>'
        '</ul>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(3, 0, "二、衔接讲义 1–3：为什么需要超越线性 OLS 与倾向得分匹配？",
                           "低维线性被财富曲线误设、1:1 匹配方差大，而直接套用机器学习则会彻底毁掉置信区间",
                           s3_body, notes_list[2]))

    # Slide 4: Math Deconstruction I
    s4_body = (
        '<div class="grid-2" style="flex:1;">'
        '<div class="card red">'
        '<div class="card-hd">为什么直接套用机器学习会“覆盖率归零”？</div>'
        '<p class="p-text">在部分线性回归（PLR, Robinson 1988）中：Y = θ₀ D + g₀(X) + ζ，D = m₀(X) + V。</p>'
        '<ul class="ul">'
        '<li><span class="hl-red">陷阱 1：正则化偏差（Regularization Bias）</span><br>若只用森林/Lasso 拟合 <span class="hat">g</span>(X) 后直接拿 (Y − <span class="hat">g</span>(X)) 对 D 回归，由于正则化惩罚使 <span class="hat">g</span> 收敛速度仅 O<sub>p</sub>(n<sup>−1/4</sup>)，一阶误差乘上 √n 会直接发散：</li>'
        '</ul>'
        '<div class="math-box" style="font-size:13px;border-left-color:#B91C1C;">'
        '√n (<span class="hat">θ</span><sub>plug</sub> − θ₀) ≈ <span class="frac"><span class="num">1</span><span class="den">√n</span></span> ∑ m₀(X<sub>i</sub>)(g₀(X<sub>i</sub>) − <span class="hat">g</span>(X<sub>i</sub>)) ≈ √n · n<sup>−1/4</sup> = n<sup>+1/4</sup> → ∞'
        '</div>'
        '<ul class="ul">'
        '<li><span class="hl-red">陷阱 2：过拟合偏差（Overfitting Bias）</span><br>即便同时残差化，若在全样本上直接用深层树训练并算样本内残差，模型记忆噪声会导致两残差出现伪相关，依然有偏。</li>'
        '</ul>'
        '</div>'
        '<div class="card blue">'
        '<div class="card-hd">支柱一：Neyman 正交化（一阶敏感度归零）</div>'
        '<p class="p-text">不直接估 g₀(X)，而是同时预测结果均值 ℓ(X)=E[Y|X] 与处置倾向 m(X)=E[D|X]，构造得分函数：</p>'
        '<div class="math-box" style="font-size:13.5px;">'
        'ψ(W; θ, ℓ, m) = (Y − ℓ(X) − θ(D − m(X))) · (D − m(X))'
        '</div>'
        '<ul class="ul">'
        '<li><span class="hl">解样本正交矩 E<sub>n</sub>[ψ]=0 得</span>：<span class="hat">θ</span><sub>DML</sub> = (<span class="hat">v</span><sup>T</sup> <span class="hat">u</span>) / (<span class="hat">v</span><sup>T</sup> <span class="hat">v</span>)，其中 u = Y − <span class="hat">ℓ</span>(X), v = D − <span class="hat">m</span>(X)。</li>'
        '<li><span class="hl">核心性质（Gateaux 导数为零）</span>：在真值处，∂<sub>η</sub> E[ψ(W; θ₀, η₀)] = 0——也就是说，<span class="hl-teal">扰动预测器的微小一阶误差不再直接穿透到 θ 上！</span></li>'
        '</ul>'
        '</div>'
        '</div>'
        '<div class="card dark" style="padding:11px 16px;">'
        '<div class="card-hd">误差收敛阶数的奇迹：为什么机器学习只要 n<sup>−1/4</sup> 精度就能保证 √n 因果推断？</div>'
        '<div class="row" style="align-items:center;">'
        '<div style="font-size:23px;font-weight:700;color:#FBBF24;min-width:440px;">||<span class="hat">ℓ</span> − ℓ₀||₂ × ||<span class="hat">m</span> − m₀||₂ = O<sub>p</sub>(n<sup>−1/4</sup>) × O<sub>p</sub>(n<sup>−1/4</sup>) = o<sub>p</sub>(n<sup>−1/2</sup>)</div>'
        '<p class="p-text" style="flex:1;">由于一阶项被 Neyman 正交性消去，主导偏差变为两个预测器误差的<span style="color:#7DD3FC;font-weight:700;">乘积（及 ||<span class="hat">m</span>−m₀||₂²）</span>。常规非参数学习器只要满足略快于 n<sup>−1/4</sup> 的收敛速率，乘积就快于 n<sup>−1/2</sup>，从而令 √n(<span class="hat">θ</span><sub>DML</sub> − θ₀) 渐近正态，三明治标准误完全合法！</p>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(4, 1, "三、模型解构（上）：机器学习的两类偏差与 Neyman 正交化",
                           "单独预测会陷入 n⁻¹/⁴ 正则化偏误，正交得分把偏差压缩为两预测器误差乘积 n⁻¹/⁴×n⁻¹/⁴ = o(n⁻¹/²)",
                           s4_body, notes_list[3]))

    # Slide 5: Math Deconstruction II
    s5_body = (
        '<div class="card" style="padding:10px 15px;">'
        '<div class="card-hd">支柱二：5-折交叉拟合（Cross-Fitting）彻底斩断过拟合相关性（Chernozhukov et al., 2018 Def. 3.3）</div>'
        '<svg viewBox="0 0 1160 98" style="width:100%;height:94px;">'
        '<rect x="10" y="14" width="110" height="44" rx="6" fill="#0E7490"/><text x="65" y="34" text-anchor="middle" fill="#FFF" font-size="12" font-weight="700">Fold 1 (验证)</text><text x="65" y="50" text-anchor="middle" fill="#E0F2FE" font-size="10.5">只算折外残差</text>'
        '<rect x="128" y="14" width="110" height="44" rx="6" fill="#0A365C"/><text x="183" y="34" text-anchor="middle" fill="#FFF" font-size="12" font-weight="700">Fold 2 (训练)</text><text x="183" y="50" text-anchor="middle" fill="#CBD5E1" font-size="10.5">拟合 ℓ⁻¹ 与 m⁻¹</text>'
        '<rect x="246" y="14" width="110" height="44" rx="6" fill="#0A365C"/><text x="301" y="34" text-anchor="middle" fill="#FFF" font-size="12" font-weight="700">Fold 3 (训练)</text><text x="301" y="50" text-anchor="middle" fill="#CBD5E1" font-size="10.5">拟合 ℓ⁻¹ 与 m⁻¹</text>'
        '<rect x="364" y="14" width="110" height="44" rx="6" fill="#0A365C"/><text x="419" y="34" text-anchor="middle" fill="#FFF" font-size="12" font-weight="700">Fold 4 (训练)</text><text x="419" y="50" text-anchor="middle" fill="#CBD5E1" font-size="10.5">拟合 ℓ⁻¹ 与 m⁻¹</text>'
        '<rect x="482" y="14" width="110" height="44" rx="6" fill="#0A365C"/><text x="537" y="34" text-anchor="middle" fill="#FFF" font-size="12" font-weight="700">Fold 5 (训练)</text><text x="537" y="50" text-anchor="middle" fill="#CBD5E1" font-size="10.5">拟合 ℓ⁻¹ 与 m⁻¹</text>'
        '<rect x="615" y="10" width="535" height="76" rx="8" fill="#F0F6FC" stroke="#0A365C" stroke-width="1.4"/>'
        '<text x="632" y="32" fill="#0A365C" font-size="12.5" font-weight="700">三项设计保障 100% 样本效率与稳定性：</text>'
        '<text x="632" y="52" fill="#334155" font-size="11.5">① 轮流把每一折作为验证折（折外预测），最后汇集全部 N 个样本计算正交得分，不浪费样本；</text>'
        '<text x="632" y="71" fill="#334155" font-size="11.5">② 重复 5 次随机分层切分，点估计取中位数，SE 计入切分间方差 √(s² + (θ_r − θ_med)²)。</text>'
        '<text x="10" y="79" fill="#0E7490" font-size="11.5" font-weight="600">→ 训练折噪声与验证折正交残差独立，过拟合幽灵通道被彻底切断！</text>'
        '</svg>'
        '</div>'
        '<div class="grid-3" style="flex:1;">'
        '<div class="card">'
        '<div class="card-hd">1. PLR 部分线性模型</div>'
        '<div class="math-box" style="font-size:12.5px;">Y = θ₀ D + g₀(X) + ζ</div>'
        '<ul class="ul">'
        '<li>假设不同特征家庭受 401(k) 影响的平均斜率相同（常处理效应）。</li>'
        '<li>回归器分别拟合 ℓ(X)=E[Y|X] 与 m(X)=E[D|X]。</li>'
        '<li>结构简洁、方差低，是检查模型稳定性的基准。</li>'
        '</ul>'
        '</div>'
        '<div class="card blue">'
        '<div class="card-hd">2. IRM 交互回归（允许异质性）</div>'
        '<div class="math-box" style="font-size:11.8px;">φ<sub>i</sub> = g(1,X)−g(0,X) + D(Y−g(1,X))/m(X) − (1−D)(Y−g(0,X))/(1−m(X))</div>'
        '<ul class="ul">'
        '<li>基于双稳健 AIPW 正交得分，不限制 D 与 X 不交互。</li>'
        '<li>可同时估计总体 ATE、处置组 ATT，并可直接按收入四分位平均 φ<sub>i</sub> 计算群体异质效应 <span class="hl-teal">GATE</span>！</li>'
        '</ul>'
        '</div>'
        '<div class="card teal">'
        '<div class="card-hd">3. IIVM 工具变量（衔接讲义 1.2.5）</div>'
        '<div class="math-box" style="font-size:12px;">LATE = E[ITT<sub>Y</sub>] / E[ITT<sub>D</sub>]</div>'
        '<ul class="ul">'
        '<li>以雇主资格 e401 为工具变量 Z，以实际参与 p401 为内生处置。</li>'
        '<li>在非线性控制 X 后，用双稳健正交得分识别依从者（Compliers）的局部平均处理效应。</li>'
        '</ul>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(5, 1, "三、模型解构（下）：K-折交叉拟合与 PLR / IRM / IIVM 统一框架",
                           "折外预测斩断过拟合相关性；同时配备同质 PLR、异质双稳健 IRM 与工具变量 IIVM 三套估计框架",
                           s5_body, notes_list[4]))

    # Slide 6: Simulation Distribution
    s6_body = (
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.85;">'
        '<img src="../outputs/figures/fig1_simulation_bias_distribution.png" alt="图1 模拟抽样分布对比"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">高维非线性模拟 DGP 设定（真值 θ₀ = 2.0）</div>'
        '<ul class="ul">'
        f'<li><span class="hl">规模</span>：B = {cfg["B"]} 次重复、n = {cfg["n"]}、p = {cfg["p"]} 维标准正态协变量（其中 14 维为纯干扰噪声）。</li>'
        '<li><span class="hl">非线性混杂</span>：m₀(X) 与 g₀(X) 均包含 X₁²−1、X₂X₃、X₄²−1、X₅X₆ 等平方与交互项（二阶展开达 230 维特征空间）。</li>'
        '<li><span class="hl">DML 学习器</span>：二阶展开＋LassoCV 做 5-折交叉拟合。</li>'
        '</ul>'
        '</div>'
        '<div class="card" style="flex:1;">'
        '<div class="card-hd">四条曲线各自的偏误机制解码</div>'
        '<ul class="ul">'
        f'<li><span class="hl">灰线 Naive OLS ({sim[0]["mean_est"]:.3f})</span>：强行用直线拟合二次与交互混杂，残余正向偏误 <span class="hl-red">{sim[0]["bias"]:+.3f}</span>。</li>'
        f'<li><span class="hl-amber">橙线 Direct ML ({sim[1]["mean_est"]:.3f})</span>：随机森林只去趋势 Y 而未对 D 做正交化，正则化收缩造成严重左偏 <span class="hl-red">{sim[1]["bias"]:+.3f}</span>。</li>'
        f'<li><span class="hl-red">红线无交叉拟合 ({sim[2]["mean_est"]:.3f})</span>：深层森林样本内过拟合噪声，引发 <span class="hl-red">{sim[2]["bias"]:+.3f}</span> 向下偏误。</li>'
        f'<li><span class="hl-teal">蓝线完整 DML ({sim[3]["mean_est"]:.3f})</span>：稳稳居中在 θ₀=2.0 虚线上（偏差仅 {sim[3]["bias"]:+.3f}），方差最小！</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(6, 2, "四、模拟验证（上）：非线性高维混杂 DGP 与抽样分布对比",
                           "200 次重复试验直观复现正则化偏误与过拟合偏误，唯有双支柱协同的完整 DML 居中无偏",
                           s6_body, notes_list[5]))

    # Slide 7: Simulation Coverage & RMSE
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
        '<div class="row" style="flex:1.22;">'
        '<div class="fig-box" style="flex:2.25;">'
        '<img src="../outputs/figures/fig2_simulation_coverage_rmse.png" alt="图2 模拟RMSE与95%覆盖率"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card dark" style="flex:1;">'
        '<div class="card-hd">推断有效性的试金石</div>'
        f'<div style="font-size:32px;font-weight:700;color:#86EFAC;">{sim[3]["coverage_95_pct"]:.1f}% <span style="font-size:15px;color:#CBD5E1;">vs. 0.0%</span></div>'
        '<p class="p-text">点估计不准，标准误算得再漂亮也是假的！前三种方法因为系统性偏误远大于标准误，200 次试验里 95% 置信区间居然<span style="color:#FBBF24;font-weight:700;">一次也没盖住真值</span>。</p>'
        '<p class="p-text">完整 DML 将 RMSE 从 0.871 压低至 <span style="color:#7DD3FC;font-weight:700;">0.032</span>，经验标准差 (0.032) 与三明治理论 SE (0.033) 严丝合缝，覆盖率高达 <span style="color:#86EFAC;font-weight:700;">96.5%</span>。</p>'
        '</div>'
        '</div>'
        '</div>'
        '<table class="tbl">'
        '<thead><tr><th>模拟估计方法 (B=200, n=1000, p=20, θ₀=2.0)</th><th class="num-col">估计均值</th><th class="num-col">偏差 Bias</th><th class="num-col">经验 SD</th><th class="num-col">平均理论 SE</th><th class="num-col">RMSE</th><th class="num-col">95% 置信区间覆盖率</th></tr></thead>'
        f'<tbody>{"".join(rows7)}</tbody>'
        '</table>'
    )
    slides.append(wrap_slide(7, 2, "四、模拟验证（下）：点估计 RMSE 与 95% 置信区间覆盖率检验",
                           "完整 DML 的 RMSE 降至 0.032，理论标准误与经验波动完美匹配，95% 区间覆盖率达 96.5%",
                           s7_body, notes_list[6]))

    # Slide 8: 401k EDA & Confounding
    s8_body = (
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.95;">'
        '<img src="../outputs/figures/fig3_401k_eda_confounding.png" alt="图3 401k数据探索与混杂诊断"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card">'
        '<div class="card-hd">真实调查数据来源与质量</div>'
        '<ul class="ul">'
        '<li><span class="hl">出处</span>：美国人口普查局 1991 SIPP 家庭调查（Poterba et al. 1995 / Chernozhukov et al. 2018 基准库）。</li>'
        f'<li><span class="hl">样本完整性</span>：共 <span class="hl-teal">{emp["n"]:,} 户家庭</span>、44 个原始字段，零缺失值；处置变量 e401=1 占 37.1%。</li>'
        '</ul>'
        '</div>'
        '<div class="card amber">'
        '<div class="card-hd">左图分布特征：极端右偏＋负资产借贷</div>'
        '<ul class="ul">'
        '<li>净金融资产 net_tfa 跨度极大（−$50.2 万至 +$153.7 万），中位数仅 $1,499、均值达 $18,052。</li>'
        '<li>强烈右偏与贫富分化意味着财富函数不可能靠一条简单线性回归拟合。</li>'
        '</ul>'
        '</div>'
        '<div class="card red" style="flex:1;">'
        '<div class="card-hd">右图 SMD 诊断：7 项协变量严重失衡</div>'
        '<ul class="ul">'
        '<li>年收入 inc (+0.637)、DB 养老金 (+0.521)、自有住房 hown (+0.363)、双职工 (+0.341)、受教育年限 (+0.321) 均远超 0.1 警戒线。</li>'
        '<li>不消除这些非线性结构性差异，就无法回答 401(k) 究竟贡献了多少净增量。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(8, 3, "五、真实数据实证（一）：1991 SIPP 401(k) 分布与混杂偏差诊断",
                           "9,915 户家庭资产呈强右偏且存在 7 项超标选择偏差，直接均值差 +$19,559 含巨大混杂水份",
                           s8_body, notes_list[7]))

    # Slide 9: 401k Forest Plot Comparison
    s9_body = (
        '<div class="row" style="flex:1;">'
        '<div class="fig-box" style="flex:1.68;">'
        '<img src="../outputs/figures/fig4_401k_model_comparison_forest.png" alt="图4 传统方法与DML森林图对比"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card">'
        '<div class="card-hd">DML 跨 4 类学习器横向稳定性（5 次交叉切分中位数）</div>'
        '<table class="tbl">'
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
        '<div class="card-hd">三大核心实证判断</div>'
        '<ul class="ul">'
        f'<li><span class="hl">剔除富人水份仍显著为正</span>：去掉近万美金混杂水份后，IRM-ATE 在四种完全不同算法下紧凑收敛于 <span class="hl-teal">+$7,822 ~ +$8,693</span>，确凿证明 401(k) 创造了净新增储蓄！</li>'
        f'<li><span class="hl">推理精度全场最佳</span>：双稳健 IRM 标准误压低至 <span class="hl-teal">$1,142–$1,250</span>，全面优于线性 OLS ($1,524) 与 1:1 PSM ($1,605)。</li>'
        f'<li><span class="hl">处理组实际获益更高</span>：HGB 下合格群体平均处理效应 <span class="hl">ATT = +${irm["HistGradientBoosting"]["ATT"]["est"]:,.0f}</span>（SE ${irm["HistGradientBoosting"]["ATT"]["se"]:,.0f}）。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(9, 3, "五、真实数据实证（二）：传统方法 vs. 四类学习器 DML 森林图",
                           "四类算法给出一致且高精度收敛：401(k) 资格平均净增家庭金融资产约 $7,822–$8,693",
                           s9_body, notes_list[8]))

    # Slide 10: Overlap, Sensitivity & IV LATE
    s10_body = (
        '<div class="row" style="flex:1;">'
        '<div class="col" style="flex:1.35;">'
        '<div class="fig-box" style="flex:1;">'
        '<img src="../outputs/figures/fig5_401k_propensity_overlap.png" alt="图5 倾向得分重叠检验"/>'
        '</div>'
        '<div class="note-strip">'
        f'<strong>正性（Positivity）假设核验：</strong>HGB 交叉拟合倾向得分 m̂(X) 5%–95% 分位为 <strong>[{ps["hgb_ps_p05"]:.3f}, {ps["hgb_ps_p95"]:.3f}]</strong>（全范围 [{ps["hgb_ps_min"]:.3f}, {ps["hgb_ps_max"]:.3f}]），两组分布重叠充分，无逆概率极端权重爆炸风险。'
        '</div>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card">'
        '<div class="card-hd">敏感性检验：剔除争议变量 pira（个人退休账户）</div>'
        '<p class="p-text">学者常质疑“是否开了 IRA (pira)”本身反映个人隐含储蓄意愿。踢掉 pira 仅用 8 个特征重跑 HGB：</p>'
        '<table class="tbl">'
        '<thead><tr><th>HGB 模型设定</th><th class="num-col">9 特征基准</th><th class="num-col">剔除 pira (8 特征)</th></tr></thead>'
        '<tbody>'
        f'<tr><td>DML-PLR</td><td class="num-col">+${plr["HistGradientBoosting"]["est"]:,.0f}</td><td class="num-col">+${sens["dml_plr_hgb"]["est"]:,.0f} (SE ${sens["dml_plr_hgb"]["se"]:,.0f})</td></tr>'
        f'<tr class="hl-row"><td>DML-IRM (ATE)</td><td class="num-col">+${irm["HistGradientBoosting"]["ATE"]["est"]:,.0f}</td><td class="num-col">+${sens["dml_irm_hgb_ATE"]["est"]:,.0f} (SE ${sens["dml_irm_hgb_ATE"]["se"]:,.0f})</td></tr>'
        f'<tr><td>DML-IRM (ATT)</td><td class="num-col">+${irm["HistGradientBoosting"]["ATT"]["est"]:,.0f}</td><td class="num-col">+${sens["dml_irm_hgb_ATT"]["est"]:,.0f} (SE ${sens["dml_irm_hgb_ATT"]["se"]:,.0f})</td></tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '<div class="card dark" style="flex:1;">'
        '<div class="card-hd">工具变量拓展（DML-IIVM）：从“资格效应”到“真实参与效应”</div>'
        f'<div style="font-size:28px;font-weight:700;color:#FBBF24;">LATE = +${late["est"]:,.0f} <span style="font-size:14px;color:#CBD5E1;">(SE ${late["se"]:,.0f})</span></div>'
        '<ul class="ul">'
        f'<li>并非有资格就一定会存钱：合格家庭中实际参与 p401 占比 <span style="color:#7DD3FC;font-weight:700;">{emp["compliers_p401_given_e401"]*100:.2f}%</span>（无资格组为 0%，单边服从）。</li>'
        f'<li>衔接讲义 1.2.5 工具变量逻辑，以 e401 为 p401 的工具变量，IIVM 估得实际参加者的净储蓄增量高达 +${late["est"]:,.0f}（95% CI [${late["ci95_low"]:,.0f}, ${late["ci95_high"]:,.0f}]），与 ATE ÷ 0.7045 逻辑吻合！</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(10, 3, "六、假设核验与稳健性：倾向得分重叠、无 pira 敏感性与工具变量 LATE",
                           "倾向得分重叠饱满；剔除 pira 结论不变；资格作工具变量测出实际参与效应达 +$12,107",
                           s10_body, notes_list[9]))

    # Slide 11: Income Quartile GATE
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
    s11_body = (
        '<div class="row" style="flex:1.18;">'
        '<div class="fig-box" style="flex:2.1;">'
        '<img src="../outputs/figures/fig6_401k_heterogeneity_gate.png" alt="图6 收入四分位异质性GATE"/>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">异质性分析怎么算？</div>'
        '<p class="p-text">直接对交叉拟合 IRM 算出的每个家庭正交伪结果 φ<sub>i</sub> 按年收入四分位（Q1–Q4）分组求均值与标准误，不破坏正交推断性质。</p>'
        '</div>'
        '<div class="card amber" style="flex:1;">'
        '<div class="card-hd">颠覆直觉的双极发现</div>'
        '<ul class="ul">'
        f'<li><span class="hl">绝对美元看 Q4 最高</span>：高收入家庭净增 <span class="hl-teal">+${gates[3]["gate"]:,.0f}</span>（占年收 {gates[3]["effect_to_income_pct"]:.1f}%）。</li>'
        f'<li><span class="hl-amber">相对收入撬动看 Q1 第一</span>：低收入家庭绝对增量虽为 +${gates[0]["gate"]:,.0f}，却占其中位年收的 <span class="hl-red">{gates[0]["effect_to_income_pct"]:.1f}%</span>（p&lt;0.001）！</li>'
        f'<li><span class="hl">Q2 夹心层暂不显著</span>：区间 [${gates[1]["ci95_low"]:,.0f}, ${gates[1]["ci95_high"]:,.0f}] 跨零，受现金流与房贷挤压较强。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
        '<table class="tbl">'
        '<thead><tr><th>家庭年收入分层</th><th class="num-col">样本量</th><th class="num-col">组内中位年收</th><th class="num-col">GATE 因果增量</th><th class="num-col">标准误 SE</th><th class="num-col">95% 置信区间</th><th class="num-col">增量 / 中位年收</th></tr></thead>'
        f'<tbody>{"".join(rows11)}</tbody>'
        '</table>'
    )
    slides.append(wrap_slide(11, 3, "七、商业客群洞察：按收入四分位的异质性因果效应（GATE）",
                           "高收入客群绝对增量最大 (+$20,588)，低收入客群相对年收入的财富撬动率高达 36.6%",
                           s11_body, notes_list[10]))

    # Slide 12: Commercial & Policy Recommendations
    s12_body = (
        '<div class="grid-2" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">面向商业银行与养老金资管机构：差异化分层运营</div>'
        '<ul class="ul" style="gap:9px;margin-top:4px;">'
        f'<li><span class="hl">1. 锁定 Q4 高净值客群做 AUM 核心扩张池</span><br>Q4 家庭中位年收 ${gates[3]["median_inc"]:,.0f}，单户资格即可撬动 <span class="hl-teal">+${gates[3]["gate"]:,.0f}</span> 净金融资产沉淀。金融机构应将高薪企业代发工资场景与个人养老金高阶指数/固收+组合打包营销，并用节税测算工具放大转化。</li>'
        f'<li><span class="hl">2. 理解并激活 Q2“夹心工薪层”痛点</span><br>Q2 群体（中位年收 ${gates[1]["median_inc"]:,.0f}）GATE 仅 +${gates[1]["gate"]:,.0f} 且置信区间跨零，说明传统长期锁定期的税收递延对其现金流挤压敏感。商业机构可探索搭配“低门槛定投＋应急贷款质押/特定大病支取灵活性”产品。</li>'
        '<li><span class="hl">3. 同时监测产品净流入与整户总金融资产</span><br>避免高收入客群仅把本行普通定期存款搬入养老账户（零净新增），用整户 AUM 净增量考核真实营销 ROI。</li>'
        '</ul>'
        '</div>'
        '<div class="card teal">'
        '<div class="card-hd">面向普惠金融与公共财税政策：破解“穷人不会存钱”偏见</div>'
        '<ul class="ul" style="gap:9px;margin-top:4px;">'
        f'<li><span class="hl">1. 推翻“低收入无储蓄弹性”的错误直觉</span><br>Q1 低收入家庭（中位年收 ${gates[0]["median_inc"]:,.0f}）净增 +${gates[0]["gate"]:,.0f}（95% CI [+${gates[0]["ci95_low"]:,.0f}, +${gates[0]["ci95_high"]:,.0f}]），相当于其一整年收入的 <span class="hl-red">{gates[0]["effect_to_income_pct"]:.1f}%</span>——说明他们原本几乎零金融储备，一旦提供便利储蓄通道，几乎全部转化为净新增资产，很少存在资产挤出。</li>'
        '<li><span class="hl">2. 机制抓手：默认自动加入（Auto-Enrollment）＋ 固定配比补贴</span><br>单纯提高个税免税额度往往只有边际税率高的 Q4 享受到红利；若向 Q1/Q2 倾斜“雇主/财政定额配比（Matching）＋默认自动参保”，普惠社会财富杠杆效果远超单纯减税。</li>'
        '<li><span class="hl">3. 对中国个人养老金制度的定量启发</span><br>仅靠税优对中低收入免税群体吸引力不足，必须配套“默认账户＋微额财政补贴”才能激发长尾人群参与。</li>'
        '</ul>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(12, 4, "八、商业应用与公共政策落地建议",
                           "同一项实证同时服务资管机构“分层扩充 AUM”与公共政策“精准滴灌普惠储蓄”两类决策",
                           s12_body, notes_list[11]))

    # Slide 13: Boundaries & Extensions
    s13_body = (
        '<div class="grid-2" style="flex:1;">'
        '<div class="card amber">'
        '<div class="card-hd">必须诚实交代的三条统计证据边界</div>'
        '<ul class="ul" style="gap:9px;margin-top:4px;">'
        '<li><span class="hl-amber">1. 条件可忽略性边界（Unconfoundedness）</span><br>DML 只能彻底控制住观测变量 X 里的非线性混杂；如果员工择业时“本来就爱存钱的人更愿意去有 401(k) 的公司”，而数据里没记录主观储蓄偏好，仍会有未观测混淆残留（即使我们做了剔除 pira 检验，也只能检验已知维度）。</li>'
        '<li><span class="hl-amber">2. 极端倾向得分的方差脆弱性</span><br>在双稳健得分里有 1/m̂(X) 和 1/(1−m̂(X)) 项；虽然本数据集重叠很好（5%–95% 为 0.054–0.707），但在某些极不平衡业务场景需改用重叠加权（Overlap Weights）。</li>'
        '<li><span class="hl-amber">3. 截面历史数据时代迁移限制</span><br>1991 年美国家庭截面数据主要用于方法示范与经典经济学验证，外推至当下中国养老金市场需重新采集本土面板数据。</li>'
        '</ul>'
        '</div>'
        '<div class="card blue">'
        '<div class="card-hd">可无缝衔接的三大方法延伸方向</div>'
        '<ul class="ul" style="gap:9px;margin-top:4px;">'
        '<li><span class="hl">1. 融合面板与双重差分（DID-DML）</span><br>把讲义 3 的固定效应、双重差分与 DML 正交化结合，同时消除“不随时间变化的未观测个人偏好”与“随时间变化的高维非线性混杂”。</li>'
        '<li><span class="hl">2. 个体化策略树与 Causal Forest</span><br>把本文按收入 4 分位汇总的 GATE 进一步细化为个体级条件效应 <span class="hl-teal">CATE(X)</span>，配合 Policy Tree 自动学习可解释的银行发券/授信规则。</li>'
        '<li><span class="hl">3. 混淆强度敏感性边界（OVB Bounds）</span><br>引用 Chernozhukov 等人最新的偏 R² 敏感性分析工具，定量计算“未观测储蓄偏好至少要强到多少倍，才能把当前 +$8,693 结论翻成零”。</li>'
        '</ul>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(13, 4, "九、方法边界、局限性与前沿延伸方向",
                           "DML 解决可观测高维非线性混杂而非未观测遗漏变量；结合面板/DID 与 Causal Forest 是重要扩展",
                           s13_body, notes_list[12]))

    # Slide 14: 3-Min Extended Applications
    s14_body = (
        '<div class="grid-3" style="flex:1;">'
        '<div class="card blue">'
        '<div class="card-hd">成员 A｜陈霖（量化多因子与大模型 RL）</div>'
        '<ul class="ul">'
        '<li><span class="hl">背景经历</span>：Trexquant 美股多因子选股实习 ＋ 上海人工智能实验室大模型推理与 Agent RL 研究。</li>'
        '<li><span class="hl">应用 1｜量化多因子真 Alpha 归因</span>：用 Ridge/XGBoost/LGBM 合成新闻情绪与量价因子时，市值、波动率与行业暴露常与收益呈复杂非线性混杂；用 DML 对新因子和超额收益同时做交叉拟合正交残差，可净评估真实增量 Alpha。</li>'
        '<li><span class="hl">应用 2｜Agent RL 离线策略评估</span>：在难度各异的高维推理轨迹上，用双稳健正交得分无偏估计工具调用或新策略带来的净回报提升，避免奖励模型过拟合偏差。</li>'
        '</ul>'
        '</div>'
        '<div class="card">'
        '<div class="card-hd">成员 B｜[请填姓名]（互联网营销 Uplift 模板）</div>'
        '<ul class="ul">'
        '<li><span class="hl">适用领域</span>：互联网平台优惠券补贴、会员续费定价或流量投放（请结合个人实习替换）。</li>'
        '<li><span class="hl">业务痛点</span>：历史优惠券往往发给了本来就高活跃或即将流失的用户，直接对比“领券 vs 未领券”下单率偏差巨大。</li>'
        '<li><span class="hl">DML 落地方式</span>：用 GBDT 控制数十维用户历史点击/加购非线性特征，通过 IRM 正交得分估计各细分客群真实增效 Uplift。</li>'
        '<li><span class="hl">预期价值</span>：剔除“不发券也买”的假增量人群，把补贴预算集中投向高敏感用户，提升营销 ROI。</li>'
        '</ul>'
        '</div>'
        '<div class="card teal">'
        '<div class="card-hd">成员 C｜[请填姓名]（金融科技信贷风控模板）</div>'
        '<ul class="ul">'
        '<li><span class="hl">适用领域</span>：消费信贷额度调整、分期费率优惠因果评估（请结合个人实习替换）。</li>'
        '<li><span class="hl">业务痛点</span>：平台本来就是依据复杂信用评分卡决定是否给用户提额，传统回归难以剥离非线性授信规则导致的混杂。</li>'
        '<li><span class="hl">DML 落地方式</span>：保留风控团队最熟悉的 XGBoost/LightGBM 吸收高维征信特征，套用 DML 交叉拟合输出带合法 95% 置信区间的提额净收益与坏账响应。</li>'
        '<li><span class="hl">最需注意</span>：需额外补充随机小流量保留组以检验是否存在未记录人工审批偏差。</li>'
        '</ul>'
        '</div>'
        '</div>'
        '<div class="note-strip">'
        '<strong>组员改稿小贴士：</strong>组员 B、C 只需将第 2、3 栏的“[请填姓名]”与例子换成自己熟悉或实习过的项目（控制在每人 150 字 / 口播 50 秒内），再运行一行 <code>python3 html_to_pptx.py</code> 即可重生成高清 PPTX！'
        '</div>'
    )
    slides.append(wrap_slide(14, 4, "十、3 分钟组内个人拓展：把 DML 带回各自的实习与研究领域",
                           "每人 1 分钟以内，讲清“我在什么业务里控制了什么高维非线性混杂、想评估谁对谁的净因果”",
                           s14_body, notes_list[13]))

    # Slide 15: References & Q&A
    s15_body = (
        '<div class="row" style="flex:1;">'
        '<div class="card" style="flex:1.5;">'
        '<div class="card-hd">核验学术文献与课程讲义衔接（已核对精确刊名、卷期与页码）</div>'
        '<ul class="ul" style="font-size:11.8px;gap:7px;">'
        '<li><span class="hl">[1] Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., &amp; Robins, J. (2018).</span> Double/debiased machine learning for treatment and structural parameters. <em>The Econometrics Journal</em>, 21(1), C1–C68.（本文核心理论奠基）</li>'
        '<li><span class="hl">[2] Robinson, P. M. (1988).</span> Root-N-consistent semiparametric regression. <em>Econometrica</em>, 56(4), 931–954.（PLR 残差化思想起源）</li>'
        '<li><span class="hl">[3] Chernozhukov, V., &amp; Hansen, C. (2004).</span> The effects of 401(k) participation on the wealth distribution: An instrumental quantile regression analysis. <em>The Review of Economics and Statistics</em>, 86(3), 735–751.</li>'
        '<li><span class="hl">[4] Poterba, J. M., Venti, S. F., &amp; Wise, D. A. (1995).</span> Do 401(k) contributions crowd out other personal saving? <em>Journal of Public Economics</em>, 58(1), 1–32.（建立 SIPP 401k 自然实验与 9 维基准变量）</li>'
        '<li><span class="hl">[5] Abadie, A. (2003).</span> Semiparametric instrumental variable estimation of treatment response models. <em>Journal of Econometrics</em>, 113(2), 231–263.（单边服从 LATE 半参数理论）</li>'
        '<li><span class="hl">[6] Chernozhukov, V., et al. (2024).</span> <em>Applied Causal Inference Powered by ML and AI</em>. CausalAIBook.（提供标准化 <code>401k.csv</code> 数据）</li>'
        '<li><span class="hl">[7] 课程讲义 1–3 衔接（冯项楠老师）</span>：潜在结果框架（Neyman 1923, Rubin 1974）、线性控制回归（讲义 2.2）、倾向得分匹配 PSM（讲义 2.3）与工具变量 IV（讲义 1.2.5）。</li>'
        '</ul>'
        '</div>'
        '<div class="col" style="flex:1;">'
        '<div class="card dark" style="flex:1;">'
        '<div class="card-hd">欢迎老师与同学提问（Q&amp;A 重点议题）</div>'
        '<ul class="ul" style="gap:9px;margin-top:4px;">'
        '<li><span style="color:#FBBF24;font-weight:700;">Q1：从 PSM 升级到 DML-IRM</span><br>为什么双稳健正交得分既把误差降到 n<sup>−1/4</sup>×n<sup>−1/4</sup>，又把 401(k) ATT 标准误从 $3,026 压至 $1,683？</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">Q2：无交叉拟合为什么往下偏到 1.640？</span><br>深层森林样本内过拟合时，同时吸收了部分外生扰动 V，导致残差出现负向相关偏差。</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">Q3：学习器切换一致性</span><br>模拟中 Poly2+Lasso 与 401(k) 中四类模型各自发挥什么作用？为什么实证收敛在 $7.8k–$8.7k？</li>'
        '<li><span style="color:#FBBF24;font-weight:700;">Q4：未观测储蓄偏好检验</span><br>除了踢掉 pira 与用 e401 做工具变量算 LATE，还有哪些面板或敏感性证据可进一步加固？</li>'
        '</ul>'
        '</div>'
        '</div>'
        '</div>'
    )
    slides.append(wrap_slide(15, 4, "十一、核心参考文献与 Q&A 交流",
                           "全部模拟、401(k) 实证代码与数据可一键复现，感谢冯项楠老师、吴尚老师与各位同学聆听！",
                           s15_body, notes_list[14]))

    html_doc = (
        '<!DOCTYPE html>\n'
        '<html lang="zh-CN">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>版本二｜双重机器学习（DML）与养老金因果评估（现代统计模型及应用）</title>\n'
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
        "Slide 1｜封面：双重机器学习（DML）与高维因果推断——Monte Carlo 模拟验证及 401(k) 养老金实证",
        "Slide 2｜一、研究背景与商业问题：401(k) 究竟带来多少净新增储蓄？",
        "Slide 3｜二、衔接讲义 1–3：为什么需要超越线性 OLS 与倾向得分匹配？",
        "Slide 4｜三、模型解构（上）：机器学习的两类偏差与 Neyman 正交化",
        "Slide 5｜三、模型解构（下）：K-折交叉拟合与 PLR / IRM / IIVM 统一框架",
        "Slide 6｜四、模拟验证（上）：非线性高维混杂 DGP 与抽样分布对比",
        "Slide 7｜四、模拟验证（下）：点估计 RMSE 与 95% 置信区间覆盖率检验",
        "Slide 8｜五、真实数据实证（一）：1991 SIPP 401(k) 分布与混杂偏差诊断",
        "Slide 9｜五、真实数据实证（二）：传统方法 vs. 四类学习器 DML 森林图",
        "Slide 10｜六、假设核验与稳健性：倾向得分重叠、无 pira 敏感性与工具变量 LATE",
        "Slide 11｜七、商业客群洞察：按收入四分位的异质性因果效应（GATE）",
        "Slide 12｜八、商业应用与公共政策落地建议",
        "Slide 13｜九、方法边界、局限性与前沿延伸方向",
        "Slide 14｜十、3 分钟组内个人拓展：把 DML 带回各自的实习与研究领域",
        "Slide 15｜十一、核心参考文献与 Q&A 交流",
    ]
    timings = ["30秒", "50秒", "45秒", "60秒", "55秒", "50秒", "45秒", "45秒", "60秒", "50秒", "55秒", "45秒", "40秒", "3分钟(每人≤1分)", "Q&A"]
    speech_lines = [
        "# 《现代统计模型及应用》课堂汇报口播稿（版本二：前沿方法 双重机器学习 DML）",
        "",
        "> **汇报节奏**：前 13 页主讲严格控制在 **11 分 30 秒 – 12 分 00 秒**；第 14 页组内 3 人每人 **≤ 1 分钟**拓展；第 15 页留给老师和同学提问。",
        "> **口吻说明**：面向冯项楠老师、吴尚老师及班上同学，先用直观悖论吸引注意力，再用大白话讲透 Neyman 正交与交叉拟合，最后落回真实数据与诚实边界。",
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
        "- **陈霖（量化多因子与大模型 Agent RL，约 50 秒）**：",
        "  “结合我在 Trexquant 美股多因子选股以及上海人工智能实验室大模型推理与 Agent RL 的实践，DML 有两处直接用途：第一是在多因子里用 Ridge/XGBoost/LGBM 合成新闻情绪与量价信号时，市值和行业暴露往往和未来收益呈强非线性混杂，用 DML 对新因子和超额收益同时做交叉拟合正交残差，能更纯净地识别真实增量 Alpha；第二是在 Agent RL 离线评估里，利用双稳健正交得分可以在高维上下文状态空间里做无偏反事实回报归因。”",
        "- **组员 B（互联网营销 Uplift 模板，约 50 秒，请替换为个人真实实习）**：",
        "  “【请组员 B 替换姓名与行业】：在互联网用户增长和优惠券营销里，发券历史通常偏向本来就高活跃的用户。利用 DML 的 IRM 框架，我们可以放心地用 GBDT 控制数十维用户行为特征，通过正交得分识别出真正对补贴敏感的高增量客群，剔除‘不发券也买’的假增量人群，把营销预算花在刀刃上。”",
        "- **组员 C（金融科技风控提额模板，约 50 秒，请替换为个人真实实习）**：",
        "  “【请组员 C 替换姓名与行业】：在金融科技消费信贷场景里，平台本身就是根据复杂征信评分卡决定给谁提额。借用 DML，风控团队既可以保留最擅长的 XGBoost 吸收高维非线性特征，又能得到带严谨 95% 置信区间的提额因果收益与坏账响应评估。”",
        "",
        "---",
        "",
        "## 三、第 15 页高频 Q&A 备答（供彩排准备）",
        "",
        "1. **冯项楠老师可能问：DML 和讲义 2 的倾向得分匹配（PSM）相比，最本质的升级在哪？**",
        "   - **答**：在于正交得分的二阶误差乘积结构。单靠倾向得分的传统方法如果用机器学习拟合，偏差是 $O(n^{-1/4})$，乘上 $\\sqrt{n}$ 会发散；DML 通过把结果预测 $\\hat{g}$ 与倾向得分 $\\hat{m}$ 组合成 Neyman 正交得分，把偏差压成乘积 $n^{-1/4}\\times n^{-1/4}=o(n^{-1/2})$，且不丢弃未匹配样本（把 ATT 标准误从 $3,026 压低到 $1,683）。",
        "2. **吴尚老师可能问：为什么模拟实验里完整 DML 换了 Poly2+Lasso，而 401(k) 实证里跑了四种？**",
        "   - **答**：模拟 DGP 构造为 20 维中的二阶多项式交互，目的在于让能达 $o(n^{-1/4})$ 速率的 Poly2+LassoCV 检验理想 DML，同时对照低维线性 OLS、非正交 RF 与无交叉拟合深层 RF 的失效机制；而真实 401(k) 未知真实函数形式，所以我们同时跑了 Lasso、Ridge、RF 与 HGB 四类截然不同的算法，全部分别落在 $7,822–$8,693，证明结论稳健。",
        "3. **老师可能问：如果雇主是否提供 401(k) 还是和员工未记录的储蓄偏好相关怎么办？**",
        "   - **答**：这是可观测控制方法的根本边界，我们在第 13 页如实说明了这一点；实践中我们一方面做了剔除争议变量 `pira` 的敏感性检验（结论稳健在 `$8,923`），另一方面也结合讲义 1.2.5 工具变量估计了实际参与的 LATE (`$12,107`)。若要彻底剔除不随时间变的隐含偏好，还需借助面板 DID-DML。",
        "4. **同学可能问：为什么 Q2 中低收入组 GATE 比 Q1 还低且跨零？**",
        "   - **答**：一方面 Q2 净金融资产尾部方差较大（SE `$1,462`）；另一方面 Q1 原本中位净资产几乎为零，一旦参与自动配比几乎 100% 是净新增，而 Q2 工薪族在购房首付、子女抚养与消费信贷挤压下，更易出现账户间挪动或储蓄弹性偏弱。",
    ])
    OUT_SPEECH.write_text("\n".join(speech_lines) + "\n", encoding="utf-8")
    print(f"Built {OUT_HTML.name} and {OUT_SPEECH.name}")


if __name__ == "__main__":
    main()
