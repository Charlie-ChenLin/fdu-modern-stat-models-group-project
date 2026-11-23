# 《现代统计模型及应用》小组大作业总览

> 本文件由课程任务图 `README.jpg`（来源于课程讲义 1 第 8 页）完整转录整理，并附英文对照、评分标准与双版本完整解决方案导航。（注：课程原始讲义与 `README.jpg` 涉及版权，仅本地保留，不上传本公开仓库。）

---

## 一、`README.jpg` 原文转录（1.1.4 成绩评估 — 评分细则）

- **小组作业 25%**：共 6 组，各组 3 人，自由组队
  - 请在 **10 月 11 日（周日）晚 8 点前**，将小组名单 + 组长名称发送给助教
  - **具体内容**：选择一个统计学模型，该模型要与本课内容有关，即，与因果关系（包括试验）、图模型、马尔可夫网络、贝叶斯网络等有关
    - PPT 讲解这个模型，并利用其进行一个数据分析
    - 如果是课堂上**没有讲到**的模型，可以利用**模拟数据**对模型进行展示
    - 如果是课堂上**讲到**的模型，可在**实际数据**上应用，作为案例讲解
  - **作业材料**：最后一节 **12 分钟的展示 + 3 分钟模型拓展介绍 + PPT 本身 + 过程材料（程序、数据、分析过程、模型文献等）**
    - **第九周课，12 月 03 日**：12 分钟介绍与分析模型
    - **余 3 分钟**：组内每人 1 分钟内拓展介绍（结合自己实习或者感兴趣的领域，介绍这个模型的用处和价值）

### English Translation of `README.jpg` (1.1.4 Grading Criteria)

- **Group Project (25%)**: 6 groups in total, 3 students per group, self-organized teams.
  - **Team Registration**: Send the team roster and team leader's name to the TA before **8:00 PM on Sunday, Oct 11**.
  - **Core Content**: Select a statistical model related to the course topics—i.e., causal inference (including experiments), graphical models, Markov networks, Bayesian networks, etc.
    - Explain the model via PPT slides and conduct a data analysis using it.
    - If the model **was not covered in class**, you may demonstrate it using **simulated data** (in Version 2, we provide both rigorous Monte Carlo simulations and a real-world benchmark dataset).
    - If the model **was covered in class**, apply it to **real-world data** as a case study.
  - **Deliverables**: Final class **12-minute presentation + 3-minute extended applications + PPT file + supporting materials (code, data, analysis workflow, model references, etc.)**.
    - **Week 9 Class (Dec 03)**: 12 minutes for model introduction and empirical/data analysis.
    - **Remaining 3 minutes**: Up to 1 minute per group member for extended applications (introducing the utility and value of the model based on each member's internship experience or areas of interest).

---

## 二、Presentation 评分标准（来自 `course_files_export/pre评分表.pdf`）

| 序号 | 分项 | 小项 | 分值 |
| :--- | :--- | :--- | :---: |
| 1 | **研究选题** | 选题价值、商业应用 | **10** |
| 2 | **模型和结论** | 模型背景、模型解构、数据分析处理、结论和可能的拓展 | **50** |
| 3 | **PPT 文本** | 完整性、图示、文字表述清晰 | **20** |
| 4 | **陈述和 Q&A** | 逻辑性强、思路清晰、时间控制 | **20** |
| **合计** | | | **100** |

---

## 三、课程讲义知识点核查范围（来自 `course_files_export/`）

为严格区分“课堂教过的方法”与“课堂没教过的方法”，已逐一核对全部 7 份讲义：
- **前半部分（因果推断，冯项楠老师）**：
  - 讲义 1：混杂偏差、路径图、因果识别方法总览（简单回归、匹配、面板固定效应、工具变量、双重差分、断点回归、Heckman 自选择）
  - 讲义 2：潜在结果框架（Neyman-Rubin）、回归法、匹配法（精确匹配与倾向得分匹配 PSM）
  - 讲义 3：双重差分法（DID）、Heckman 样本自选择模型
  - 讲义 4：A/B 试验探讨与业务应用场景探讨
- **后半部分（概率图模型，吴尚老师）**：
  - 讲义 5：马尔可夫网络（无向图、条件独立与图分隔、团分解、**5.3 连续变量高斯图模型 [精度矩阵、算法一约束 MLE、算法二图结构估计 $L_1$ 惩罚]**、伊辛模型、CRF）
  - 讲义 6：伊辛模型等价泊松模型、隐变量/RBM、贝叶斯网络 1（有向无环图 DAG、d-分隔、马尔可夫边界）
  - 讲义 7：贝叶斯网络 2（局部马尔可夫性、因果马尔可夫假设、端正化、变量消元推理、MAP）

---

## 四、双版本大作业方案导航（均含可全屏演示 HTML + 2K 视网膜 PPTX）

本目录提供两套**均包含完整真实数据/模拟数据、可复现代码、高清图表、学术分析报告、润色后 12+3 分钟口播讲稿、核查文献、离线交互式 15 页 HTML 演示文稿以及无损转换的 2K PPTX（附带每页 Speaker Notes）**的独立成品：

1. **[版本一（课程教过的方法）：高斯图模型与 Graphical Lasso](version1_taught_ggm/)**
   - **对应讲义**：讲义 5（5.2–5.3 连续变量高斯图模型、精度矩阵条件独立、算法一约束 MLE 与算法二稀疏结构估计）
   - **真实应用数据集**：Yahoo Finance 美股 15 支跨资产与标普 500 一级行业 ETF 日频复权价格（2020-01-01 至 2025-12-31），揭示共同因子剥离后的真实金融风险传导拓扑，并在 2024–2025 样本外进行全局最小方差组合（GMVP）风控回测。
   - **核心交付**：
     - 浏览器交互式演示 HTML（克隆后本地双击用浏览器打开，支持键盘翻页与备注开关）：[版本一_高斯图模型与跨资产风险传染网络.html](version1_taught_ggm/presentation/版本一_高斯图模型与跨资产风险传染网络.html)
     - 15 页高清逐页预览图（GitHub 网页端可直接点开看每页效果）：[slides_preview/](version1_taught_ggm/presentation/slides_preview/)
     - 2K 无损转换 PPTX（含演讲者备注）：[版本一_高斯图模型与跨资产风险传染网络.pptx](version1_taught_ggm/presentation/版本一_高斯图模型与跨资产风险传染网络.pptx)
     - 润色口播演讲稿：[演讲稿_12分钟展示与3分钟拓展.md](version1_taught_ggm/docs/演讲稿_12分钟展示与3分钟拓展.md)
     - 学术分析报告：[分析报告_高斯图模型与金融风险网络.md](version1_taught_ggm/docs/分析报告_高斯图模型与金融风险网络.md)

2. **[版本二（课程没教过的方法）：双重机器学习 DML](version2_untaught_dml/)**
   - **方法来源**：Chernozhukov et al. (2018), *The Econometrics Journal* — 基于讲义 1–3 因果推断的现代机器学习延伸（**课堂未讲授**）
   - **数据验证**：① 200 次 Monte Carlo 非线性高维混杂模拟（直观展示正则化偏差、过拟合偏差与 DML 去偏正态性）；② **真实应用数据集**：1991 SIPP 401(k) 美国家庭金融调查数据（$N = 9,915$），评估养老金资格对家庭净金融资产的真实因果效应及收入分位异质性。
   - **核心交付**：
     - 浏览器交互式演示 HTML：[版本二_双重机器学习与养老金因果评估.html](version2_untaught_dml/presentation/版本二_双重机器学习与养老金因果评估.html)
     - 15 页高清逐页预览图（GitHub 网页端可直接点开看每页效果）：[slides_preview/](version2_untaught_dml/presentation/slides_preview/)
     - 2K 无损转换 PPTX（含演讲者备注）：[版本二_双重机器学习与养老金因果评估.pptx](version2_untaught_dml/presentation/版本二_双重机器学习与养老金因果评估.pptx)
     - 润色口播演讲稿：[演讲稿_12分钟展示与3分钟拓展.md](version2_untaught_dml/docs/演讲稿_12分钟展示与3分钟拓展.md)
     - 学术分析报告：[分析报告_双重机器学习与401k净储蓄因果效应.md](version2_untaught_dml/docs/分析报告_双重机器学习与401k净储蓄因果效应.md)

3. **团队起步与分工指引**：
   - [组员导览报告_大作业启动与分工指南.md](组员导览报告_大作业启动与分工指南.md)
   - [两版本方案对比与选用建议.md](两版本方案对比与选用建议.md)
   - 一键 HTML 转 PPTX 脚本：[html_to_pptx.py](html_to_pptx.py)（修改 HTML 第 14 页组员姓名/拓展后运行 `python3 html_to_pptx.py` 即可重新导出 PPTX）

---

## 五、给组员的快速协作说明 / Quick Start for Teammates

- **在线直接看每页效果**：如果暂时不想克隆到本地，可以直接点开上面的 `slides_preview/` 文件夹，在 GitHub 网页端直接浏览全部 15 页 PPT 的 2K 预览图。
- **克隆到本地编辑与重导出 PPTX**：
  ```bash
  git clone https://github.com/Charlie-ChenLin/fdu-modern-stat-models-group-project.git
  cd fdu-modern-stat-models-group-project
  ```
  1. 先阅读 [组员导览报告_大作业启动与分工指南.md](组员导览报告_大作业启动与分工指南.md)，对照 [两版本方案对比与选用建议.md](两版本方案对比与选用建议.md) 拍板选用版本一或版本二。
  2. 用浏览器直接打开选定版本的 `presentation/*.html` 文件查看交互演示与演讲者备注。
  3. 确定组员姓名及第 14 页“1 分钟个人拓展”文本并更新对应 `.html`（或 `code/build_html_deck.py`）后，运行 `python3 html_to_pptx.py` 与 `python3 verify_deliverables.py` 即可自动完成溢出体检并更新 `.pptx`。
