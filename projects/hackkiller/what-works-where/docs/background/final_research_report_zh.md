# PATH Visualize 2 最终调研报告

**Malaria prevention evidence across settings and time**

初稿研究日期为 2026 年 11 月 13 日，最新整合更新于 11 月 14 日，美国东部时间。报告用于 System Public Challenge 参赛准备，基于用户提供的 Deep Research Report，进一步核查主办方资料、System Public Graph v1 实际返回、原始研究和 WHO 开放数据。本版已合并筛选快照全文件核验、全部候选导出、GitHub 自有运行源码审阅、Skill 检索与当前待办清单。

本轮采用定向证据核验。检索围绕题目明确列出的蚊帐、季节性疟疾化学预防 SMC 和疫苗，重点检查关键试验、比较组、结局、随访期及图谱可用性。下文中的产品范围和开发时间分配属于本报告的建议。文献结果按原研究适用人群与比较条件解释。

## 1. 建议先读的结论

**建议制作一个有来源核验功能的疟疾预防证据看板，按干预措施、比较组、结局、国家和随访期展示研究结果。** 首页覆盖蚊帐、SMC、疫苗三类，演示主线优先采用坦桑尼亚与贝宁的新型蚊帐试验，配合一组疫苗与 SMC 的组合干预证据。

**当前状态：调研、API 接通、原始快照与候选导出已完成；统一审核结果表、试验去重映射、可运行看板、部署链接和比赛提交包仍待完成。** 首个完整案例优先使用已完成 API、筛选 CSV 与原文三方核验的 Benin 蚊帐结果，再扩展 Tanzania 随访、SMC 与疫苗。第 9 节列出必须完成项与值得补充项，第 12–13 节给出具体代码和 Skill 的借鉴方式。

这个范围能体现题目要求，也有真实数据支撑。当前最大的技术难点是图谱抽取后的语义完整性。本轮发现同一试验中的干预组标签错配、比较组丢失、抗体水平比较被包装为疫苗效果等问题。原文核验应成为数据处理的一环。

本轮最重要的新增发现如下。

| 新发现 | 对参赛方案的影响 |
|---|---|
| 参赛 API 实际提供 concepts、variables、relationships、associations、studies 五类资源 | 数据接入按 Public Graph v1 构建，并以实际返回检查字段 |
| 41 次 System 请求全部返回 HTTP 200，得到 18 条去重关联，涉及 10 篇文献 | 已验证接入和小范围研究可行，可按日志复查 |
| 11 月 14 日扫描筛选版全部 1,999,877 条关联，原先 18 条 API 样本中 1 条存在、17 条缺失 | 主展示层优先从筛选版选择记录，再核对原文；API 返回量与筛选版覆盖分开统计 |
| 坦桑尼亚 36 个月论文的三个蚊帐组标签在 API 中均与原文不符 | 图表需要记录原标签、修正标签、修正依据和审核状态 |
| R21 三期试验存在 study 记录，但两个关联查询入口均返回空数组 | 可用原始论文补充，并明确标记来源与图谱覆盖状态 |
| 贝宁 chlorfenapyr 蚊帐在前两年有明确优势，第三年 HR 0.80 的区间跨过 1 | 原报告“持续两至三年优势”的表述应限定国家、结局和时点 |
| R21 的 75% 疫苗效力在原文中由 HR 定义 | 转换后保留 HR 类型，转换结果为 0.25，95% CI 0.21–0.29 |
| WHO 四类指标已成功抽样，IRS 指标的单位为人数 | 覆盖率、受保护人数和发病率分别展示单位与分母 |
| 三类词法候选已全部导出，去重 497 条，涉及 277 个 PMID；404 条有两个数值型区间端点 | 可以进入审核队列，候选数量与可展示结果数量分别统计 |
| 已完整阅读四个项目的 28 个自有运行源码文件，共 7,831 行 | 可借鉴共享筛选、证据矩阵、来源下钻和森林图，具体改造见第 12 节 |
| 已读三个 Skill 的主文件与全部五个 Python 脚本，并完成三项隔离行为验证 | 用于审核、元数据补齐和网页验收；下载审阅与实际接入分别记录 |
| 官方 GitHub 仓库要求每队提交 PR，再把 PR 链接填入 Devpost | 提交计划增加 PR、官方 README 模板和单文件小于 25 MB 的要求 |

System 官方文档披露，Beta API 约 20% 的 associations 存在抽取准确性问题，并建议与 Harvard Dataverse 的筛选版 CSV 交叉核对。这个比例来自官方内部质量检查。本轮的 18 条定向样本不足以估计整个 API 的错误率。[System API 文档](https://docs.system.com/system/public/v1.0-api-documentation)

筛选快照的本地词法预筛得到蚊帐候选 436 条、SMC 候选 35 条、疫苗候选 28 条，三类重叠去重后为 497 条，涉及 277 个 PMID。本版已导出全部命中行。候选中包含使用行为、接种意愿、免疫学指标等，仍需筛选真正的干预效果。已有数据足以启动少量核验案例的原型，尚未形成完整可比的干预证据库。计数、字段完整性和文件入口见第 11 节。

## 2. PATH 的实际题目与比赛条件

### 2.1 官方题目已取得

官方挑战文档的标题为 “How does the effect of malaria prevention vary by setting and over time?”，负责人是 PATH 的 Roberto Amato。

题目的完整要求可概括为，利用 System Public Graph，制作一个比较 SMC、杀虫剂处理蚊帐和疟疾疫苗所报告效果的 dashboard，显示这些结果如何随国家、研究环境和时间变化。题目也允许加入其他开放数据，例如 MalariaGEN 的耐药标记数据，探索 SMC 效果与相关药物耐药性之间的关系。最终产物是一份跨环境、跨时间比较疟疾预防方法的可视化。[主办方挑战文档](https://docs.google.com/document/d/1PZon0PcNrHA3gYPsYsRGbOJk0SqUY9Nq70vCYNLwK6s/edit)

因此，首页保留三类核心干预更贴近题意。IRS、住房、单克隆抗体和新兴媒介控制工具可作为扩展内容。原材料中对具体数字的核验程度存在差异，本轮证据锚点优先使用已核对的原始试验。

### 2.2 已核实的比赛安排

| 项目 | 已核实信息 |
|---|---|
| 地点 | System HQ，123 Lafayette St，四楼，纽约 |
| 开发时间 | 11 月 14 日 10:00–15:00 EST |
| 提交 | 15:00 前提交 GitHub PR，并在 Devpost 填入 PR 链接 |
| 现场展示 | 15:00 起，每队约 3 分钟 |
| 队伍 | 2–7 人，每人参与一队、一个挑战 |
| 评分 | Public Graph 使用、洞察或实用性、技术执行、沟通，各 25% |
| 奖项 | 每个类别冠军 2,000 美元，荣誉奖 500 美元 |
| 产物 | 可运行原型、公开代码、3 分钟 pitch deck |
| AI 使用 | 可以使用 AI coding tools，提交时披露 |

官方规则允许赛前研究、构思和线框设计，要求提交的项目实现代码在活动期间编写。参赛者指南则明确鼓励提前申请 key、运行示例 notebook 和探索数据。本次报告与数据查询属于准备工作，后续项目代码应遵循该时间要求。[官方规则](https://system-public-challenge.devpost.com/rules) [参赛者指南](https://docs.google.com/document/d/1jEDJKLsi2k-vmUmzkABaJGLVNNA-fHbwRWhYqdGmoxs/edit)

### 2.3 GitHub 提交要求已补充核实

[本届比赛提交仓库](https://github.com/SystemPublic/system-public-challenge-2026)的 README 要求每队 fork 仓库，在 `projects/<team-name>/` 下放项目，复制并填写 `TEMPLATE/README.md`，提交一个 PR，再将 PR 链接填入 Devpost 的 “Try it out”。README 写明截止时间为 11 月 14 日 15:00 ET。

单文件须小于 25 MB。约 422 MiB 的原始 association 快照保留在本地，提交包提供必要的小型数据、下载方式与版本说明。代码默认 MIT，包含或衍生自 System Public Graph 的数据采用 CC BY-NC 4.0；若复用其他代码，还需遵守相应许可。模板要求运行方式、数据来源、限制、演示材料及 AI 工具使用说明。[提交说明](https://github.com/SystemPublic/system-public-challenge-2026#how-to-submit) [官方模板](https://github.com/SystemPublic/system-public-challenge-2026/blob/main/TEMPLATE/README.md)

## 3. 原调研材料中需要修正的内容

| 原材料中的判断或设计 | 本轮核验结果 | 修订建议 |
|---|---|---|
| 采用 topics_api、synthesis、multi-hop，以及带完整 title/authors/publish_date 的 findings 对象 | 这些描述来自另一套平台接口，Public Graph v1 的返回结构更精简 | 使用第 4 节的实际资源与字段 |
| 将 2,339,807 变量、14.41% grounded 作为参赛图谱固定统计 | 引用的 Open Variable Index URL 本轮返回 404，且其口径与 Dataverse 快照、Beta API 有差异 | 该数字保留为原材料待复核信息，首页统计来自实际加载的数据 |
| Public Graph 数据可按 CC BY 使用 | Dataverse 页面与官方规则明确标示 CC BY-NC 4.0 | 展示数据出处与非商业许可，代码许可另行注明 |
| API 尚未确认、key 待现场领取 | 本机已经通过 API key 成功调用正式地址 | 接入阶段可直接复用当前配置 |
| country、age、study years 可以从 population 普遍提取 | population 部分缺失，其内容也可能只含人群描述 | 缺失值保留 unknown，并允许原文补充及人工确认 |
| 蚊帐 chlorfenapyr 整体具有持续两至三年的相同优势 | 贝宁第三年 HR 0.80，95% CI 0.56–1.17；坦桑尼亚 36 个月感染 OR 0.57，95% CI 0.38–0.86 | 按国家、结局和时点分别讲述 |
| 所有 VE/PE 转换为 RR，并形成统一强弱排序 | VE/PE 的底层估计量可能是 HR、OR 或 rate ratio | 保留原始类型和比较条件，分面展示 |
| 用 ≥3 项研究、≥75% 有利结果判定 broadly consistent | 这是人为阈值，缺少本项目适用性的验证 | 展示证据数量、估计值、区间及设计，综合标签需有预先说明的依据 |
| 按每篇 DOI 去重即可获得独立研究数 | 同一个随机试验可以发表多个 DOI，随访与二次分析共享受试者 | 增加 trial_family_id 或注册号 |
| p_value 可同时接受 bool 和 float 并转换 | 当前 Public v1 文档定义 float，布尔值无法提供有效精确 p 值 | 遇布尔值记录类型异常 |
| 20 次洗涤可归为第三年 | 实验洗涤与真实使用时长是不同暴露 | 单独记录 wash_count 和 followup_months |
| 社区使用率 >40% 可作为普遍保护阈值 | 原材料涉及特定二次分析，不能直接外推为通用政策阈值 | 保留研究内的定义和适用范围 |
| API 返回的 total 可直接作为某关键词证据量 | 一次空结果检索同时返回 total 5,654,715 | 当前总量字段需额外核验，计数优先依据实际去重记录 |

这些修订依据包括本轮保存的 API 原始返回、原始论文、System 的限制说明和 Cochrane 的综合方法指南。Cochrane 明确指出，以统计显著性进行研究“投票”会产生严重偏差。[API 请求与返回审计](PATH_Visualize2_调研核验记录/api_requests.jsonl) [System 限制说明](https://docs.system.com/system/public/limitations-and-known-biases) [Cochrane 方法指南第 12 章](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-12)

## 4. System Public Graph 实际接入与覆盖

### 4.1 本轮请求范围

System 查询发生在 11 月 13 日 23:31–23:36 EST。共发出 41 次 GET 请求，全部返回 HTTP 200。检索包括 11 组变量关键词、概念查询、按 PMID 找论文、按 study 或 variable 找关联，以及一个 total 字段的复查。不同入口存在重叠，所有已取回 association 按 system_id 去重后为 18 条，来自 10 个 study_id。

这是一份定向可行性样本，热门词首批结果上限为 100。下表的“100”表示本页达到上限，其检索总量仍需继续分页核实。

| variables 检索词 | 本页返回量 | 观察 |
|---|---:|---|
| malaria | 100 | 同时包含疾病严重程度、行为与治疗结局 |
| chlorfenapyr | 19 | 出现蚊帐，也出现蔬菜农药残留 |
| pyriproxyfen | 11 | 混有猫用药等非目标记录 |
| piperonyl | 24 | 既有蚊帐，也有除虱产品 |
| insecticide-treated nets | 100 | 包括覆盖、认知和妊娠干预组合 |
| indoor residual spraying | 100 | 有覆盖变量及不同方案组合 |
| seasonal malaria chemoprevention | 32 | 有不同年龄、轮次、年份与结局 |
| R21 | 4 | 主要是同名噪声及一项抗体测量变量 |
| RTS,S | 100 | 混入 RTS 评分、其他缩写 |
| Interceptor G2 | 8 | 能增加品牌层面的召回 |
| R21/Matrix-M | 0 | 本次精确字符串未发现变量 |

采用“关键词发现 → PMID/DOI 锚点定位 → 关联核验”的组合，能减少宽泛概念检索造成的遗漏和误匹配。19 个 chlorfenapyr 变量中有 12 个携带 concept_id，32 个 SMC 变量中有 18 个携带 concept_id。这两个局部比例描述了本次返回，无法代表全图谱 grounding 率。

还有一个具体例子，chlorfenapyr 概念 `-iZg8fIGDl` 对应 Wikidata `Q426475`，其概念变量入口只返回一个变量，概念关系入口返回零条。与此同时，关键词和 PMID 入口能够找到蚊帐试验结果。开发时应同时保留变量和论文入口。

### 4.2 已验证的请求形式

正式地址是 `https://public-api.system.com`，认证使用请求头 `x-api-key`，官方上限为每个 key 每天 10,000 次。分页采用 limit 和 offset。以下请求均已在本轮或本次会话中实际成功。

```http
GET /v1/variables?search=name%3Achlorfenapyr&limit=100
GET /v1/studies?filter=pubmed_id%3A36706778&limit=10
GET /v1/studies/feOrVjYqBk/associations?limit=200
GET /v1/variables/fbbkaUpq_A/associations?limit=100
GET /v1/concepts/-iZg8fIGDl/variables?limit=100
```

过滤与检索语法按各资源的文档使用。relationship_id 包含的分隔符需要 URL 编码。key 已保存在本机配置文件，报告、原始数据和请求日志均省略认证值。[System API 文档](https://docs.system.com/system/public/v1.0-api-documentation)

### 4.3 从实际返回得到的字段字典

| 对象 | 字段 | 本轮观察与用途 |
|---|---|---|
| Variable | system_id、name、concept_id | concept_id 可缺失，保留原始 name 用于追溯 |
| Association | system_id、study_id、pubmed_id | 数据行与文献的连接键 |
| Association | variable_1_id/name、variable_2_id/name | 原始两端变量，干预组与比较组仍需核验 |
| Association | variable_1/2_concept_id、variable_1/2_wikidata_id | 部分缺失，不能覆盖完整语义 |
| Association | statistic_type、system_statistic_type、statistic_value | 原始与归一化统计类型、点估计 |
| Association | ci_lower、ci_upper、ci_level | 有缺失，且已返回的 ci_level 多为 0 |
| Association | p_value、p_value_equality | p_value 可缺失，阈值符号也可能缺失 |
| Study | study_id、doi、pubmed_id、population、study_type | population 和 study_type 有缺失 |
| Relationship | relationship_id、source/target_concept、num_findings、num_studies、last_published_date、last_updated | 文档列出，关系样本覆盖需按题目继续核实 |

本轮 study 返回没有 title、authors、journal、publication_date、标准化 country 和 followup_months。补充元数据可通过 DOI/PMID 查询 PubMed、Europe PMC 或 OpenAlex，再保留来源字段。关系上的 last_published_date 表示该关系最新支持论文时间，无法替代每篇论文日期。[参赛者指南](https://docs.google.com/document/d/1jEDJKLsi2k-vmUmzkABaJGLVNNA-fHbwRWhYqdGmoxs/edit)

### 4.4 关键论文的图谱可用性

| 文献 | PMID | System study_id | 本次 study associations 返回量 |
|---|---|---|---:|
| Tanzania 24 个月蚊帐试验 | 35339225 | xrgxiAooFV | 3 |
| Tanzania 36 个月随访 | 37776879 | -Y2PnBarK4 | 3 |
| Benin 前两年试验 | 36706778 | feOrVjYqBk | 2 |
| Benin 第三年随访 | 38401551 | 79tcjm146y | 0 |
| R21 三期试验 | 38310910 | z0EDV_fZZ_ | 0 |
| 标准蚊帐 Cochrane 2018 | 30398672 | xgxcZktkeu | 0 |
| ACCESS-SMC | 33278936 | uVMAuzbN39 | 2 |
| RTS,S 与 SMC 随机试验 | 34432975 | 98tfoL5t5K | 1 |
| Senegal SMC 试验 | 27875528 | uoE0Zi0rRG | 2 |
| Mali 第五轮 SMC 研究 | 36704118 | cR37_M_xbV | 2 |
| RTS,S 抗体反应研究 | 34894221 | _neXKkOmo8 | 1 |

另外两条记录来自 South Sudan SMC 和 Uganda IRS 文献。R21 的 study 子资源和 associations 的 study_id 过滤均返回空数组。空数组描述本次 API 覆盖状态，相关试验的存在及结果已由原始文献确认。

## 5. 抽取数据的逐条核验发现

### 5.1 蚊帐组别错配

Tanzania 36 个月论文的主要比较，均以标准 pyrethroid 蚊帐为对照。

| Association ID | API 的 variable_1_name 含义 | 数值及 95% CI | 原论文中的实际组别 |
|---|---|---|---|
| v_jYJO5RWB | standard pyrethroid | OR 0.57，0.38–0.86 | chlorfenapyr-pyrethroid |
| lTQMC2ZnYM | PBO-pyrethroid | OR 0.82，0.55–1.23 | pyriproxyfen-pyrethroid |
| MrlZri8wZD | chlorfenapyr-pyrethroid | OR 0.95，0.64–1.42 | PBO-pyrethroid |

API 的数值与论文对应比较的数值一致，干预标签却发生错配。Tanzania 24 个月论文的三条关联则共用 `use of study LLINs` 和同一个 variable_1_id，实际代表三个不同蚊帐比较，点估计分别为 0.99、0.45、0.79。单靠变量 ID 不能恢复这些干预组。[Tanzania 36 个月论文](https://pubmed.ncbi.nlm.nih.gov/37776879/) [Tanzania 24 个月论文](https://pubmed.ncbi.nlm.nih.gov/35339225/)

### 5.2 一个看似疫苗效力的数值，实际来自抗体水平分组

`owr0kFL1O8` 将 RTS,S 季节性接种与 malaria incidence 相连，报告 HR 0.43，95% CI 0.28–0.66。原论文 PMID 34894221 实际比较接种后抗体反应最高与最低三分位儿童的后续发病情况。这个值适合说明接种人群内的免疫学关联，需要保留高低抗体组比较。[原始抗体研究](https://pubmed.ncbi.nlm.nih.gov/34894221/)

### 5.3 时间点和统计类型也会丢失

- Mali 研究 `3MplKeGfYy` 的 IRR 0.66 属于 11 月第四轮时的比较，12 月第五轮比较为 `V-7UaId_15` 的 IRR 0.49，95% CI 0.26–0.94。两个变量名都提到第五轮，原文时间信息决定解释。[原始 Mali 研究](https://pubmed.ncbi.nlm.nih.gov/36704118/)
- ACCESS-SMC 的两条返回都是耐药标记随时间变化的 prevalence ratio。其变量名把 SMC 写成暴露，但原文相应统计比较的是 2016 与 2018 年、10–30 岁未接受 SMC 人群的标记流行情况。这两条需要恢复真正的比较定义。[ACCESS-SMC 原文](https://pubmed.ncbi.nlm.nih.gov/33278936/)
- Senegal 的 `FcIN1xGcIf` 在 API 中为 relative_risk_ratio 0.90，原论文定义为全因死亡的 mortality rate ratio。指标类型应在人工核对字段中保留正确释义。[Senegal 原文](https://pubmed.ncbi.nlm.nih.gov/27875528/)
- 本轮 18 条唯一关联中，17 条 ci_level 为 0，1 条缺失。它无法证明这些区间都是 95%。95% 的标签应来自论文或其他已核实元数据。
- Benin 的 HR 0.54 在 API 中 p_value 为 0.0001，原文报告 p<0.0001。等号与小于号需要在文献层核对。

### 5.4 文献本身也可能存在错误或标签歧义

原材料指出的综述 PMC12294781 确实出现以 RR 标记负值的段落。负值无法直接作为风险比绘制到对数轴上。本轮确认了文本异常，具体统计量应回查相应森林图、方法与原始试验后再定性，修正时需要记录依据。[相关综述](https://pmc.ncbi.nlm.nih.gov/articles/PMC12294781/)

## 6. 经原始文献核对的核心证据锚点

下表用于开发时检查数值和比较定义。来源为综述的记录应与其中包含的原始试验建立包含关系。每个时间点都需保留原结局、原始统计量、对照组及研究设计。表内 API 状态来自 11 月 13 日查询，筛选快照成员状态以第 11 节的 11 月 14 日核验为准。API 数值存在与通过筛选快照核验分别记录。

| 证据 | 人群、环境与时间 | 原始结局与比较 | 已核对结果 | 图谱状态与使用方式 |
|---|---|---|---|---|
| 标准 ITN，Cochrane 2018 | 早期疟疾流行地区试验 | 全因儿童死亡，ITN 对无蚊帐 | rate ratio 0.83，95% CI 0.77–0.89 | study 已找到，关联为空，可作为论文补充 |
| 标准 ITN，同一综述 | 同上 | 单纯 P. falciparum 疟疾发作率，ITN 对无蚊帐 | rate ratio 0.55，0.48–0.64 | 保留综述年份与早期试验年代 |
| Tanzania 24 个月，chlorfenapyr | Misungwi，6 月龄–14 岁，高 pyrethroid 耐药环境 | 感染患病率，对标准蚊帐 | aOR 0.45，0.30–0.67；25.6% 对 45.8% | API 数值存在，干预组需人工恢复 |
| Tanzania 24 个月，PBO / pyriproxyfen | 同一试验 | 同一结局和对照 | PBO 0.99，0.67–1.45；PPF 0.79，0.54–1.17 | 与 chlorfenapyr 分开显示 |
| Tanzania 36 个月，chlorfenapyr | 同一试验家族，6 月龄–15 岁 | 感染患病率，对标准蚊帐 | OR 0.57，0.38–0.86；22.8% 对 37.4% | 三个组别均需纠正标签 |
| Benin 前两年，chlorfenapyr | Zou，6 月龄–10 岁 | 临床疟疾发生，对标准蚊帐 | HR 0.54，0.42–0.70；0.56 对 1.03 次/儿童年 | API、筛选 CSV 与原文均已核对 |
| Benin 前两年，pyriproxyfen | 同一试验 | 同上 | HR 0.86，0.65–1.14 | 区间允许有益、接近无差异及一定不利效应 |
| Benin 第三年，chlorfenapyr / PPF | 同一试验第三年 | 临床疟疾发生，对标准蚊帐 | chlorfenapyr HR 0.80，0.56–1.17；PPF 1.02，0.71–1.44 | API 关联为空，需论文补充 |
| ACCESS-SMC | 7 国，<5 岁，2015–2016 年 | 28 天病例对照保护效果 | PE 88.2%，78.7%–93.4% | API 返回的是其他结局，需论文补充此效果 |
| ACCESS-SMC | 同一项目，各国实施数据 | 门诊确诊病例减少 | Nigeria 25.5%，6.1%–40.9%；Gambia 55.2%，42.0%–65.3% | 保留国家、实施设计与观察窗口 |
| R21 三期 | 5–36 月龄，4 国，12 个月 | 首次临床疟疾，对狂犬疫苗对照 | 季节性站点 VE 75%，71%–79%；常年站点 68%，61%–74% | 原文给出完整区间，图谱关联为空 |
| RTS,S 与 SMC 试验 | Burkina Faso、Mali，起始 5–17 月龄，3 年 | 组合方案对 SMC 单用 | 临床疟疾 PE 62.8%，58.4%–66.8% | 组合效果需原文补充 |
| 同一 RTS,S 试验 | 同上 | 疫苗单用对 SMC 单用 | HR 0.92，0.84–1.01；预设非劣界值 1.20 | API 可取，比较组需补齐 |
| Mali 第五轮 SMC | Dangassa，5–14 岁 | 12 月发病率，额外第五轮比较 | IRR 0.49，0.26–0.94 | API 可取，保留月份与第四轮对照 |

上述数值分别核对自 [Cochrane 2018](https://pubmed.ncbi.nlm.nih.gov/30398672/)、[Tanzania 2022](https://pubmed.ncbi.nlm.nih.gov/35339225/)、[Tanzania 三年随访](https://pubmed.ncbi.nlm.nih.gov/37776879/)、[Benin 2023](https://pubmed.ncbi.nlm.nih.gov/36706778/)、[Benin 三年随访](https://pubmed.ncbi.nlm.nih.gov/38401551/)、[ACCESS-SMC](https://pubmed.ncbi.nlm.nih.gov/33278936/)、[R21 三期](https://pubmed.ncbi.nlm.nih.gov/38310910/)、[RTS,S 与 SMC 试验](https://pubmed.ncbi.nlm.nih.gov/34432975/)及 [Mali 第五轮研究](https://pubmed.ncbi.nlm.nih.gov/36704118/)。

### 6.1 最值得讲清的三条发现

**蚊帐效果的时间变化需要在具体试验内观察。** Tanzania 的两份随访与 Benin 的两份随访提供了不同时间点，但两国主要结局不同。可视化可以让用户看到这种差异，同时保留它们的可比性边界。

**相似的保护百分比可能来自不同问题。** SMC 的 28 天个体保护、项目层面的门诊病例变化，以及 R21 的首次临床事件预防，分别有不同设计、分母和观察窗。每个结果旁边展示这些条件，比单一百分比更能帮助判断适用性。

**组合方案的增益有直接随机试验证据。** RTS,S 与 SMC 试验比较了组合方案和各自单用方案。这个结果非常贴近题目的三类干预视角，也能引导观众检查“相对于什么”的效果定义。

### 6.2 对原材料因果解释的补充

PMC11212245 是 Tanzania 试验中关于织物耐久性的二次分析。其 aOR 0.40 与主试验 24 个月 aOR 0.45、36 个月 OR 0.57 对应不同分析人群或时间组织方式。表中没有发现 net type × survey timepoint 的交互证据，p=0.5010；net physical condition × net type 的交互 p=0.9814。因此，“使用率和耐久性下降”可作为有依据的解释线索，具体因果贡献仍需更完整分析。[耐久性二次分析](https://pmc.ncbi.nlm.nih.gov/articles/PMC11212245/)

PBO 的 2021 Cochrane 综述在高耐药环境下发现更好的感染控制证据，后续单项试验中某时点区间跨 1 的结果需要放回具体环境。IRS 的综述也指出，非 pyrethroid-like IRS 可降低患病率，但发病率效果存在异质性。[PBO 综述](https://www.cochrane.org/evidence/CD012776_pyrethroid-pbo-nets-prevent-malaria) [IRS 综述](https://www.cochrane.org/evidence/CD012688_adding-indoor-residual-spraying-communities-using-insecticide-treated-nets-prevention-malaria)

## 7. 比较研究结果时采用的方法

### 7.1 为每个结果保存完整比较条件

建议每条经核对的结果记录以下分析字段。这些是项目准备的数据结构建议，部分需要从原文补充。

| 字段组 | 建议字段 |
|---|---|
| 来源 | origin、association_id、system_study_id、PMID、DOI、source_url |
| 独立性 | trial_family_id、trial_registration_id、publication_id |
| 比较 | intervention、comparator、dose_or_product、cointerventions |
| 人群与环境 | country、site、age_min/max、resistance_context、setting_source |
| 时间 | publication_year、collection_start/end、followup_months、season、wash_count |
| 结果 | outcome_definition、effect_measure、estimate、ci_lower/upper、ci_level、p_value_operator |
| 核验 | original_label、verified_label、verification_status、verification_note |

country 的提取需要以研究地点为依据，作者单位无法替代。像 Benin 这样的国家名称也无法直接确定具体站点的季节性。年龄混合人群应保留范围，5–36 月龄与 6 月龄–14 岁需要不同标签。

### 7.2 保留 OR、RR、HR、IRR 的统计含义

这些量都可描述相对效应，但定义不同。即使采用一致的对数轴样式，也应将同一结局、相同统计类型和明确比较组组织在同一面板。不同类型的跨研究大小比较需要额外假设和转换信息。

VE 或 PE 的反推遵循原研究定义。本轮核对的 R21 原文明确使用 `VE = 1 − HR`，所以 75% 对应 HR 0.25，区间为 0.21–0.29。病例对照研究的保护效果也应先查原文的估计方法。用 1−PE 得到的数值要保留底层估计量名称。[R21 原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC7618965/)

### 7.3 先保证结果可解释，再进行综合

- 用试验注册号识别共同试验。Tanzania 两份主报告属于 NCT03554616，Benin 两份报告属于 NCT03931473，疫苗与 SMC 试验及其抗体子研究属于 NCT03143218。
- 同一试验可以保留多个时间点，研究数量按独立试验计数，论文数量另列。
- p≥0.05 或区间跨 1，说明数据对相关效应仍有不确定性。无效、等效或非劣结论分别需要对应研究设计与界值。
- 两个国家一个显著、一个不显著，不能单独证明国家间差异。正式差异判断需交互检验或合适的异质性分析。
- 蚊子死亡、感染患病率、临床发病、重症与人类死亡分面显示。蚊子死亡增加的方向与人类发病降低的方向不同。
- 首版使用结构化结果表和分面森林图。若要加入综合估计，应先满足研究独立性、结局、比较组和模型要求。[Cochrane 方法指南](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-12)

## 8. 外部数据与背景信息

### 8.1 WHO 背景与决策语境

WHO《World malaria report 2025》估计，2024 年全球约有 2.82 亿疟疾病例和 61 万死亡。这里的 2025 是报告年份，2024 是负担估计年份。[WHO 报告](https://www.who.int/teams/global-malaria-programme/reports/world-malaria-report-2025/)

WHO 2025 年的 subnational tailoring 手册强调，利用当地数据和环境信息来确定干预组合与资源分配，并通过分层、建模与成本效果分析回答当地问题。这与按研究环境和时间查看效果的产品方向一致。[WHO 分区干预手册](https://www.who.int/publications/i/item/9789240115712)

PATH 与 Tableau Foundation 的 Visualize No Malaria 项目证明了其长期关注操作层面的数据使用，例如帮助地区工作人员理解何时、何地干预。本次挑战资料提供了 Public Graph 及开放数据方向，本轮尚未找到 PATH 单独交付一份已整理疟疾效果 CSV 的承诺。[PATH 项目](https://www.path.org/visualize-no-malaria/)

### 8.2 WHO API 实测取得的指标

本轮先查询官方 Indicator 目录，再对 Tanzania 和 Benin、2018 年起的数据进行四项查询。全部返回 HTTP 200，结果为 53 条 country-year-indicator 记录。

| 指标代码 | 实际含义 | 单位 | 本次记录数 |
|---|---|---|---:|
| MALARIA_ITN_COVERAGE | 有 ITN 可及性的人口比例，modelled | % | 14 |
| MALARIA_ITN_USE | 前一夜在 ITN 下睡眠的人口比例 | % | 14 |
| MALARIA_IRS_COVERAGE | IRS 保护人数 | 人 | 11 |
| MALARIA_EST_INCIDENCE | 估计疟疾发病率 | 每 1,000 风险人口 | 14 |

例如，Tanzania 2024 年 ITN access 返回约 65.97%，ITN use 为 57.4%，IRS 为 93,664 人。Benin 2024 年估计发病率为每 1,000 风险人口 354.25，区间 227.86–527.48。这些值用于展示 API 可用性和字段类型，单个年份无法支持某项干预效果的因果推断。[WHO API 说明](https://www.who.int/data/gho/info/gho-odata-api) [本轮 WHO 请求日志](PATH_Visualize2_调研核验记录/external_api_requests.jsonl)

WHO 元数据说明 ITN 指标使用调查、蚊帐交付和分发数据进行建模。原材料中的 `use = 0.8133 × access + 0.0026` 确实出现在官方方法说明中，但当前返回值不应据此统一重算。例如，将本轮 Tanzania access 以 proportion 代入后约得 53.92%，与实际 use 57.4% 有差异，需保留各指标版本和来源。[ITN use 元数据](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/malaria---number-of-reported-deaths)

WHO 数据中 Low/High 为 null 时保留缺失。Benin 的 IRS 记录在部分年份缺失，缺失人数与零人需要分别显示。country-year 指标与某个村庄儿童试验的结果，地理和人群尺度不同。

### 8.3 MAP 与 MalariaGEN 的适用范围

| 数据源 | 可补充什么 | 本轮核验状态 | 取舍建议 |
|---|---|---|---|
| MAP | 年度、国家及 admin1 的负担、流行率和干预覆盖估计 | 官方开放政策及下载入口已核查，未下载全量数据 | 有余力时补充地图或背景趋势 |
| MalariaGEN Pf7 | 寄生虫基因组与耐药标记分布 | 已核查官方发布，20,864 样本、33 国，采样 1984–2018 | 作为探索性扩展，先审查时间与地理匹配 |
| PubMed / Europe PMC | 标题、日期、摘要、全文和原文核验 | 本轮已用于核心文献核查 | 核心依赖 |
| OpenAlex | 论文元数据及开放获取连接 | 为主办方建议的补充来源，本轮未运行其接口 | PubMed/Europe PMC 无法补齐时使用 |

MalariaGEN 的 DHFR、DHPS 等标记描述的是寄生虫对药物的耐受相关性。蚊子对杀虫剂的耐药属于另一类生物学信息。SMC 通常涉及 SP+AQ，因此 marker 的选择应对应这些药物，K13 的青蒿素相关信息不能直接作为 SMC 效果的替代变量。基因样本也需检查采样选择、地点和年代。[MalariaGEN 官方发布](https://malariagen.net/article/pf7-released/) [Pf7 标记说明](https://apps.malariagen.net/apps/pf7/documentation/) [MAP 开放政策](https://malariaatlas.org/open-access-policy/)

## 9. 首版范围、必须完成项与补充优先级

### 9.1 页面应帮助用户完成的判断

用户进入后应能识别，当前结果来自哪类干预、相对于哪个对照、适用哪些人群与地点、随访多久，以及数据是否已完成原文核验。

建议保留四个主要视图。

1. **证据索引**。按蚊帐、SMC、疫苗组织研究卡片，提供国家、结局和随访期筛选。优先从筛选版候选中选取记录，显示实际覆盖论文数、独立试验数和已核验结果数。
2. **同类比较森林图**。先以 Benin 已完成三方核验的结果跑通流程，再加入 Tanzania 24 与 36 个月随访。每点展示原始统计类型、区间和明确对照。
3. **跨环境与时间面板**。展示 Tanzania 与 Benin 各自的随访结果，结局标签始终可见。提供疫苗与 SMC 组合试验作为另一组明确比较。
4. **来源抽屉**。显示 API 原始记录、核对后的比较组、论文链接和修改说明。补充文献数据有独立的 origin 标记。

首版围绕三类核心干预和少量经核验试验，环境维度先保留国家、人群、结局和随访期。筛选、图表与导出应读取同一份审核后的结果集，来源详情保留原始抽取与修改依据。前端实现可参考第 12 节已读代码。

### 9.2 更稳妥的显示规则

| 情况 | 页面显示 |
|---|---|
| 本次检索无匹配记录 | 在当前查询范围内没有取得记录 |
| 论文存在但 API 关联为空 | 论文已定位，图谱关联缺失 |
| 原文已确认，数据来自补充文献 | 文献补充，附来源 |
| API 标签与原文不符 | 待核对，或显示已审核修正记录 |
| 区间跨 1 | 展示区间及估计方向，并提示不确定性 |
| 对照组或时间点不明确 | 待补上下文 |
| 不同结局或不同 effect measure | 分面展示 |

原始数据层保留 API 值。人工修正写入审核后的展示层，保留修改记录。Graph 主展示层优先使用在已固定版本 CSV 中存在、且比较条件已审核的记录。17 条未匹配 API 样本保留在审计层。若用它们的原始论文补充证据，重新核对并标记为文献补充，保留清晰来源。

### 9.3 当前必须完成的交付清单

以下都是待完成项，建议的文件名是交付目标，并不表示文件已经生成。

| 优先级 | 必须完成的工作 | 具体要做什么 | 完成标志 |
|---|---|---|---|
| P0-1 | 冻结首版范围 | 三类入口保留蚊帐、SMC、疫苗；主故事选少量有明确比较与随访的试验 | 一页范围说明，能说清用户进来要判断什么 |
| P0-2 | 补充候选研究信息 | 为入选候选补题名、摘要、DOI、study_type；批量处理现有 277 个 PMID，记录未返回与失败记录 | 有可检索的文献索引，失败记录不被静默丢弃 |
| P0-3 | 形成审核后的结果表 | 从 497 条候选中筛临床预防比较，优先深核约 10–20 条展示结果；补国家、人群、对照、结局、随访、统计定义和出处 | `evidence_verified.csv/json` 中每条展示结果可回到原文位置；数量是计划目标，不是现有已审核数量 |
| P0-4 | 识别独立试验与多篇报告 | 建立试验家族、论文、结果三层 ID；关联主报告、不同随访和二次分析 | 同一试验多篇论文不会增加独立试验计数 |
| P0-5 | 做展示前检查 | 保留 HR/OR/RR/IRR 类型；检查区间、时间、单位、比较组与标签修正；缺失值有状态 | 进入图表的数据有明确审核状态，异常记录有说明 |
| P0-6 | 做出首版看板 | 研究筛选、同类比较森林图、来源详情、筛选结果导出；先跑通贝宁已核验记录 | 能连续完成选择研究、看结果、查论文、导出 |
| P0-7 | 测试并部署 | 检查筛选和图表一致、空结果、缺区间、试验去重、论文链接、手机显示、导出；保留本地固定数据供演示 | 可运行链接、演示截图和检查记录 |
| P0-8 | 准备比赛提交 | 填官方 README，完成三分钟讲述、代码与来源说明、AI 工具披露，提交 PR 并在 Devpost 填链接 | PR、Devpost 和演示材料均可打开 |

你和队友需要定下队名、成员职责及最终讲述主线。这些信息不会阻碍先整理数据与开发首个案例。现有报告中的若干关键论文结果已核验，但尚未整理成上述统一结果表。

### 9.4 值得补充的内容

| 优先级 | 补充项 | 为什么值得做 | 前提 |
|---|---|---|---|
| P1 | 结果旁的来源与修正记录 | 让用户理解标签怎么核对、比较组怎么恢复，也能清楚展示 Graph 的作用 | 每条结果有原始 association ID、原始标签、审核标签和原文位置 |
| P1 | 同一试验的随访切换 | 最贴近“over time”题意，能形成连贯演示 | 随访时间、结局及分析人群已核对；按具体研究解释，不凭显著与否推断时间交互 |
| P1 | 数据覆盖和审核进度 | 让候选、论文、独立试验、已审核结果分别可见 | 明确每个计数的单位及查询范围 |
| P1 | 贝宁和坦桑尼亚的 WHO 背景小面板 | 已有两国四类指标共 53 条，可用较少工作增加环境语境 | 保留模型值、单位和缺年状态，不把全国背景当作试验效应的因果解释 |
| P1 | 预设演示按钮与导出 | 稳定重现已选的国家、干预和随访组合，方便三分钟讲述 | 基础筛选已经稳定 |
| P2 | 国家地图 | 研究分布有帮助 | 国家或站点来源可核实；缺坐标的研究单列未定位列表 |
| P2 | 耐药与气候背景 | 能扩展“setting”的解释线索 | 另行取得并匹配地点、时间与测量方法，不能直接用国家标签替代 |
| P2 | 更多干预类别 | 扩大后续价值 | 三类核心干预的数据与交互已完成 |

首版暂不把大规模全球栅格、多跳机制网络、自动共识评分、合并效应量、LLM 聊天入口列为交付前提。新增 skill 的价值应对应具体待办，现有 frontend-design、vercel-react-best-practices 可以继续用于页面开发。

## 10. 数据核验门槛与可复查记录

建议对每个进入展示层的结果检查六件事。

1. Graph 记录已核对其在固定版本 CSV 中的成员状态，intervention 与 comparator 已从原文确认。
2. outcome、统计类型和比较方向明确。
3. followup 与 publication year 分开保存。
4. 点估计、区间、p 值及其符号按来源记录，布尔值与异常值有错误标记。
5. 文献已与 trial family 关联，重复随访有标注。
6. 每条结果显示 API / 文献补充来源，以及核验状态。

对于需绘制对数轴的比值，点估计和区间必须适合该轴。零值可出现在某些估计情形中，但需要适当的方法与显示处理；负的风险比标签则应触发来源检查。ci_lower 大于 ci_upper、区间与点估计明显矛盾、单位丢失等情况均需查原文。

本轮日志保存时间、HTTP 方法、完整查询地址、返回条数、原始文件名与 SHA-256。研究目录中的 evidence 文件均为无认证值的数据和文献证据。

- [System 请求日志](PATH_Visualize2_调研核验记录/api_requests.jsonl)
- [WHO 指标请求日志](PATH_Visualize2_调研核验记录/external_api_requests.jsonl)
- [核心论文元数据](PATH_Visualize2_调研核验记录/literature_metadata.json)
- [新增试验元数据](PATH_Visualize2_调研核验记录/literature_extra.json)
- [由图谱线索发现的文献](PATH_Visualize2_调研核验记录/literature_discovered.json)
- [Dataverse 成员核验摘要](PATH_Visualize2_调研核验记录/dataverse_membership_summary.json)
- [18 条样本逐条对照](PATH_Visualize2_调研核验记录/dataverse_membership_details.json)
- [目标文献在筛选快照中的全部匹配记录](PATH_Visualize2_调研核验记录/dataverse_target_study_records.json)
- [筛选快照词法覆盖与候选样本](PATH_Visualize2_调研核验记录/dataverse_keyword_coverage.json)

## 11. 数据许可与筛选快照核验

Harvard Dataverse 页面显示数据集 Version 2.1，许可为 CC BY-NC 4.0。页面上的 studies 表为 844,435 行，variables 为 1,774,551 行，concepts 为 45,721 行。association CSV 大小约 422 MB。这些是特定下载版本的页面元数据，不能与商业全图谱或其他日期的指数直接合并。[Dataverse 数据集](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/7V6JDO)

官方 data-provenance 文档说明，下载版本进行了 grounding 和抽取准确性等筛选，Beta API 与下载版本的范围存在差异。当前 API 中实际仍可取得 concept_id 缺失的变量，所以应按使用的数据渠道记录覆盖口径。[System 数据来源说明](https://docs.system.com/system/public/data-provenance)

### 11.1 已完成下载和全文件扫描

用户于 11 月 14 日授权接受 CC BY-NC 4.0 数据许可。本地已取得文件并完成 CSV 解析及全文件扫描。核验以 association 的 `system_id` 为匹配键，并检查了目标文献的 PMID。文件保存在本机下载目录。

| 项目 | 本次结果 |
|---|---|
| 数据集版本 | Dataverse 2.1 |
| Dataverse file ID | 14061020 |
| 文件 | system-public-graph-v1-associations.csv |
| 字节数 | 442,463,948 |
| 全文件扫描数据行数 | 1,999,877，排除表头 |
| 自计算 MD5 | c884dd1132957f69ffea45404f29db61 |
| 自计算 SHA-256 | a9c8ba3db760efec0d08c65c17c36f0066073062d8e1ff8ea40cc71679daddf9 |
| 原有 API 样本 | 18 条唯一 system_id |
| 在该 CSV 找到 | 1 条 |
| 在该 CSV 未找到 | 17 条 |

这些校验值记录本次读取文件的身份。下载路径与扫描时间同时保存在核验摘要中，便于后续重跑。[核验摘要](PATH_Visualize2_调研核验记录/dataverse_membership_summary.json)

### 11.2 原有 18 条 API 样本的成员结果

| 原有 API 样本对应文献 | PMID | API 样本数 | 这些样本在筛选 CSV 中的匹配数 |
|---|---|---:|---:|
| Tanzania 24 个月 | 35339225 | 3 | 0 |
| Tanzania 36 个月 | 37776879 | 3 | 0 |
| Benin 前两年 | 36706778 | 2 | 1 |
| ACCESS-SMC | 33278936 | 2 | 0 |
| RTS,S 与 SMC 随机试验 | 34432975 | 1 | 0 |
| Senegal SMC | 27875528 | 2 | 0 |
| Mali 第五轮 SMC | 36704118 | 2 | 0 |
| RTS,S 抗体反应 | 34894221 | 1 | 0 |
| South Sudan SMC | 38267985 | 1 | 0 |
| Uganda IRS | 28558701 | 1 | 0 |

唯一匹配的是 Benin chlorfenapyr 记录 `5uTwNLWhey`，HR 0.54，区间 0.42–0.70。API 与 CSV 的干预名称、点估计、区间及 PMID 一致，CSV 的 ci_level 为 0.95，API 的同字段为 0。原论文确认该区间为 95%，比较组为标准 pyrethroid 蚊帐。

此前发现标签错配的 Tanzania 36 个月三条记录，以及抗体分组被写为疫苗效果的 `owr0kFL1O8`，均未匹配到本版 CSV。17 条缺失的原因还涉及 grounding、关系参与情况和准确性筛选，无法仅凭成员缺失确定每一条的移除原因。本次保留比例也受定向样本影响，不能外推为全图谱错误率。[逐条核验明细](PATH_Visualize2_调研核验记录/dataverse_membership_details.json) [筛选范围说明](https://docs.system.com/system/public/data-provenance)

按这些目标文献的 PMID 扫描，CSV 另外保留了 Uganda 论文的 4 条关联，原先 API 样本中的那一条未保留。4 条涉及不同年龄组、时间比较或统计量，共用同一篇描述性研究，使用时仍需补齐上下文。[目标文献快照记录](PATH_Visualize2_调研核验记录/dataverse_target_study_records.json)

### 11.3 三类候选已完成全量导出

| 类别 | 词法候选关联数 | 不同 PMID 数 | 两个区间端点均为数值 | 导出行数 |
|---|---:|---:|---:|---:|
| 蚊帐 | 436 | 251 | 353 | 436 |
| SMC | 35 | 13 | 30 | 35 |
| 疫苗 | 28 | 14 | 23 | 28 |
| 三类去重合计 | 497 | 277 | 404 | 497 |

匹配针对 CSV 两端变量名，使用蚊帐名称及常见产品、SMC 全称与药物组合、RTS,S / R21 与 malaria vaccine 等关键词。本次复用原有规则重新读取完整文件并导出全部候选。三类计数存在重叠，按 association system_id 去重后为 497 条。497 条均有数值型点估计，404 条有两个数值型区间端点，396 条有数值型 ci_level。这些完整性检查不等于临床结果审核。

候选包括利用行为、接种意愿、免疫学指标及其他关联，命中范围之外也可能存在相关研究。此前的覆盖 JSON 保留最初的抽样记录，本版候选 CSV 与 inventory 记录完整导出情况。[原始匹配规则与候选样本](PATH_Visualize2_调研核验记录/dataverse_keyword_coverage.json) [最新数据清单](PATH_Visualize2_GitHub与数据核查/data_inventory.json)

- [全部 497 条候选](PATH_Visualize2_GitHub与数据核查/candidates_all.csv)
- [蚊帐候选](PATH_Visualize2_GitHub与数据核查/candidates_nets.csv)
- [SMC 候选](PATH_Visualize2_GitHub与数据核查/candidates_smc.csv)
- [疫苗候选](PATH_Visualize2_GitHub与数据核查/candidates_vaccines.csv)

这一结果支持调整接入顺序，先在固定 CSV 上发现候选，再用 API 与文献元数据补充上下文。已核对的 Benin 记录可作为首个端到端示例，其他核心试验作为文献补充，并保留与 Graph 来源的区分。

### 11.4 数据完整性与当前缺口

| 数据层 | 已完成 | 尚需完成 |
|---|---|---|
| 原始关联 | 固定版本 association CSV 与全文件核验 | 本次下载目录未发现 studies、variables、concepts 配套 CSV；首版可按入选研究补元数据 |
| 候选队列 | 497 条去重关联，277 个 PMID，已全部导出 | 判定哪些是临床预防比较，保留排除理由 |
| 研究信息 | 关键论文已有部分 metadata、API study 与原文核验 | 国家、对照、人群、结局、随访、试验家族仍需统一整理 |
| WHO 背景 | Benin、Tanzania，2018–2024 年四类指标，共 53 条 | IRS 存在缺年，其他国家背景尚未完整获取 |
| 地理与耐药 | 已核查 MAP、MalariaGEN 等数据源的适用范围 | 本次文件清单没有相应栅格、耐药或完整站点地理数据；按 P2 范围决定是否加入 |
| 展示数据 | 核心数值分散在报告和证据文件 | 统一审核表、试验去重映射、可运行看板与提交包仍待完成 |

association CSV 不直接提供 `country`、`comparator`、`followup_months`、`trial_family_id`、`title`、`doi`、`population`。补充 study 与论文信息是当前主要工作。

277 个候选 PMID 与本次扫描的三份既有文献元数据缓存仅匹配 2 个，与已保存 `study_pmid_*.json` 匹配 1 个。这只是候选与特定缓存的重叠，不能解释为此前只核验过两篇论文。首版可先深核约 10–20 条展示结果，其余保持候选状态；该数量是计划目标。数据量、元数据覆盖和原文核验完成度分别记录。[字段与缓存检查](PATH_Visualize2_GitHub与数据核查/data_inventory.json)

### 11.5 仍有的研究限制

其他尚存限制如下。

- 本轮是锚点驱动和关键词抽样，检索完整性仍有限。
- 原材料中的 Open Variable Index 固定计数本轮缺少可复现来源。
- PATH 专用附加 CSV 的提供情况仍需现场确认。
- 单克隆抗体、ATSB、幼虫控制等扩展主题的全部数值与最新进展未在本轮逐项重查。
- 文献中耐久性、覆盖率、抗体和环境变量的相关性，需要在相应设计内解释。
- 原始论文核验可提升关键记录的可解释性，完整证据质量评价仍涉及偏倚风险、选择性报告、样本独立性和分析方法。

## 12. GitHub 项目源码审阅与借鉴方案

本轮完整阅读四个项目的 28 个自有运行源码文件，共 7,831 行。第三方压缩依赖、图片、原始数据、依赖引导库和生成文档不计入该口径。另阅读 LSYS 全部测试及五份 notebook 的代码单元，PATH 教程代码按与主程序的差异审阅。[逐文件阅读审计](/Users/xh_qian/Desktop/PATH_源码阅读审计_2026-11-14.md) [文件哈希与阅读范围](/Users/xh_qian/Desktop/第一个项目/output/system-public-challenge-research/source-review/source_review_coverage.json)

本轮没有执行四个完整应用或上游整套测试。已对森林图参考线、MIT 论文去重、PubMed 元数据解析做三项本地隔离行为核验，输入均为合成样例，没有网络与凭据访问。改造成本是基于代码结构的工程判断。[验证结果](/Users/xh_qian/Desktop/第一个项目/output/system-public-challenge-research/source-review/review_probes.json)

### 12.1 PATH AMMnet：借鉴统一筛选数据与图表联动

[仓库](https://github.com/PATH-Global-Health/ammnet-training-20215)，固定 commit `7df4ffb970633321e7aade71e5e4eac040fcd191`。

已完整阅读自有运行脚本和入口，共 4 个文件、845 行。教程中的 R 代码按与主程序的差异审阅，压缩包的两个脚本与工作树版本内容相同，仅换行不同。

可借鉴：`filtered_data` 把筛选逻辑集中为一个响应式数据入口，多个图表读取它；条件 UI 提示用户补选择；界面和下载功能形成清晰闭环。[筛选入口](https://github.com/PATH-Global-Health/ammnet-training-20215/blob/7df4ffb970633321e7aade71e5e4eac040fcd191/lesson-materials/app-walkthrough.R#L143)、[导出逻辑](https://github.com/PATH-Global-Health/ammnet-training-20215/blob/7df4ffb970633321e7aade71e5e4eac040fcd191/lesson-materials/app-walkthrough.R#L603)

落实到本项目：所有图表与下载读取同一份筛选后的审核结果；顶部显示论文数、独立试验数和审核结果数。病例、检测总数及 TPR 的计算不能直接移植为试验效应综合。代码中平均月度 TPR 的定义也提醒我们保留分母与聚合方法。未发现明确仓库许可，优先借鉴结构与交互，自行实现。改造成本中等。

### 12.2 EviAtlas：借鉴证据分布与来源浏览

[仓库](https://github.com/ESHackathon/eviatlas)，固定 commit `b71a399914b5faa5a93fb1fc9d5d74cecdfdac63`。

已完整阅读 10 个 R 文件及 UI/server，共 12 个运行源码文件、1,775 行。

可借鉴：二维分类热图、数据表筛选、论文链接弹窗、图片与交互文件导出。[热图实现](https://github.com/ESHackathon/eviatlas/blob/b71a399914b5faa5a93fb1fc9d5d74cecdfdac63/R/GenHeatMap.R#L17)、[来源弹窗](https://github.com/ESHackathon/eviatlas/blob/b71a399914b5faa5a93fb1fc9d5d74cecdfdac63/inst/shiny-examples/eviatlas/server.R#L696)

必须调整：热图直接统计行数，我们应按试验家族和比较定义计算研究计数；它能把缺坐标记录放到预设海域，我们应采用单独的未定位列表。[缺坐标处理](https://github.com/ESHackathon/eviatlas/blob/b71a399914b5faa5a93fb1fc9d5d74cecdfdac63/inst/shiny-examples/eviatlas/server.R#L738)

UI/server 还有 PhantomJS 安装与旧外部脚本依赖，因此不建议把完整应用当作比赛首版基础。GPL ≥3 的代码复用应按其许可安排；可优先自行实现相应交互。结构借鉴成本低至中等，整体迁移成本较高。

### 12.3 MIT Evidence Gap Map：借鉴矩阵到文献列表的下钻

[仓库](https://github.com/MIT-GovLab/Evidence-Gap-Map)，固定 commit `f0b65142c897d9865b60e6a750fcfb7e03531908`。

已完整阅读自有 HTML、CSS 和业务 JavaScript，共 3 个运行源码文件、1,764 行。第三方库、国家字典、国家距离数据和编码图片不计作自有业务源码。

可借鉴：`filterCsvData` 先筛选、`formatCsvData` 再计算矩阵、点选后提供文献详情及导出。[筛选与聚合](https://github.com/MIT-GovLab/Evidence-Gap-Map/blob/f0b65142c897d9865b60e6a750fcfb7e03531908/js/viz.js#L718)

必须调整：原代码按 studyname 去重。同标题重复行会合并，同试验不同标题仍记为两篇，已用隔离样例复现。我们的计数应使用 trial_family_id，结果详情继续保留各论文与时点。气泡半径由数量线性增加，移植时应明确面积与研究数的映射；国家相似度基于治理指标，不能移植为疟疾环境相似度。

代码未发现明确仓库许可，且依赖栈较旧。建议借鉴“矩阵—文献—导出”的操作流程，自行实现。改造成本中等。

### 12.4 LSYS forestplot：最适合直接采用的绘图包

[仓库](https://github.com/LSYS/forestplot)，固定 commit `b7591e3be7004f9962fd7cd7f91aa4cac91c45fc`。

已完整阅读 9 个运行 Python 文件、3,447 行，另外阅读全部 9 个测试文件、5 个 notebook 的代码单元及安装、示例和文档配置代码。MIT 许可。

可采用：不对称区间绘制、分组标题、左右文字列、多个时点并列标记。它适合生成审阅图、演示备用图或嵌入后端生成的静态图。[区间绘制](https://github.com/LSYS/forestplot/blob/b7591e3be7004f9962fd7cd7f91aa4cac91c45fc/forestplot/graph_utils.py#L13)

必须配置：比值图使用对数轴并显式设参考线为 1；默认参考线为 0，已隔离验证。校验器主要检查类型与注释配置，需要我们增加比较条件、区间顺序和比值适用性的检查。p 值默认按小数位四舍五入，会把 0.0001 显示为 0.0，原始小于号也需要我们保留。[默认参考线](https://github.com/LSYS/forestplot/blob/b7591e3be7004f9962fd7cd7f91aa4cac91c45fc/forestplot/graph_utils.py#L103)、[p 值格式化](https://github.com/LSYS/forestplot/blob/b7591e3be7004f9962fd7cd7f91aa4cac91c45fc/forestplot/text_utils.py#L71)

绘图包不负责判断研究可比性或执行系统证据综合。首版按相同结局和统计类型分面，独立保留人群、对照与时点。静态图接入成本低，交互网页仍需自己的状态与来源组件。

### 12.5 最小借鉴组合

| 项目部分 | 建议采用的做法 | 对应待办 |
|---|---|---|
| 候选与文献索引 | PubMed skill 的批量获取、限速和落盘方式，补足解析与审计字段 | P0-2 |
| 审核结果表 | scientific-critical-thinking 的问题与分析单位固定流程，保留原文位置和判断理由 | P0-3、P0-4、P0-5 |
| 前端状态 | PATH 的共享筛选数据入口；表格、图表和导出复用同一结果集 | P0-6 |
| 证据总览 | EviAtlas/MIT 的二维索引与文献下钻，计数改用明确的独立单位 | P0-6、P1 |
| 效果图 | LSYS 的区间与注释组织，使用正确尺度和参考线 | P0-6 |
| 页面验收 | webapp-testing 的观察、操作、日志和截图流程，增加业务状态断言 | P0-7 |
| 提交 | 官方比赛 README 模板，PR 链接进入 Devpost | P0-8 |

第一项实际交付建议仍然是审核结果表和贝宁首个可点击案例。随后扩展坦桑尼亚随访、SMC 与疫苗，保持每条结果的来源和比较条件可见。

## 13. 相关 Skill 的审阅与接入建议

检索使用了 skills.sh 目录、Skills CLI 和 GitHub 原始文件；安装量与仓库 stars 是核查时的热度指标，不是科学有效性的证明。

### 13.1 scientific-critical-thinking：优先用于结果审核

来源：[K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/scientific-critical-thinking)。检索时约 2.6K installs，仓库约 57.2K stars，MIT。

已完整阅读 235 行 SKILL.md 和证据层级附录；包内没有可执行脚本。其他参考资料的阅读状态单列在审计中。

最适合借鉴的是它在评判前先固定人群、干预、对照、结局、时点、统计量和独立分析单位的流程，并把每个判断关联到原文位置与理由。可落实为我们的结果审核表和来源详情。它强调按具体结果判断偏倚、按结局与比较判断证据确定性，适合防止把“论文属于 RCT”直接变成高质量标签。[工作流程](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-critical-thinking/SKILL.md#L30)

建议采用其审核流程；首版使用“原文已核对/待补上下文”等状态。正式 RoB 2 或 GRADE 评价仍需相应工具和完整判断依据，不能自动从 API 字段生成。分析流程无需另一个模型 API；生成示意图是包中另外列出的可选能力。

### 13.2 pubmed-database：优先用于批量补全元数据

来源：[google-deepmind/science-skills](https://github.com/google-deepmind/science-skills/tree/main/skills/pubmed_database)。检索时约 2.9K installs，仓库约 3.5K stars，Apache-2.0。

已完整阅读 187 行 SKILL.md、715 行唯一脚本及批量获取、内容解析两份说明。核心可借鉴部分是带限速的请求、PMID 批量获取、结构化摘要解析、History Server 与文件化输出，适合为现有候选补题名和摘要。[批量获取函数](https://github.com/google-deepmind/science-skills/blob/main/skills/pubmed_database/scripts/pubmed_api.py#L179)

完整代码审阅后发现三项适配工作：

1. 标题使用 `findtext`，在含内嵌标签的合成 XML 中只返回前段文字，应改为收集完整文本。
2. DOI 只从 Article 内的 ELocationID 读取，在合成样例中未从 PubmedData 的 ArticleIdList 回填，应增加回退解析。
3. 搜索函数返回的是受 max_results 限制的一批 PMID，没有完整分页审计流程；输出也需要补上请求时间、来源、失败与未返回 ID。

前两项已经用隔离函数和合成 XML 复现，未调用真实 NCBI 服务。该 skill 可以补文献索引，国家、对照和随访定义仍需要从 study 与论文进一步确认。它的原始说明还依赖 uv、polite-http 和凭据管理约定，接入时应适配现有项目环境。

### 13.3 webapp-testing：用于交付前的功能验证

来源：[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/webapp-testing)。CLI 检索时约 204.9K installs，目录页面随后约 205.0K；仓库约 194K stars，该 skill 自带 Apache-2.0 许可。

已完整阅读 SKILL.md、106 行服务器辅助脚本和三份示例。可借鉴服务器启动、页面观察、控件发现、截图和日志收集。[服务器辅助脚本](https://github.com/anthropics/skills/blob/main/skills/webapp-testing/scripts/with_server.py)

改造成本较低，但脚本只确认端口已监听，业务测试还要等待数据和关键控件出现；示例中的固定路径、页面文字和固定等待不能直接照用。我们的验收应覆盖筛选与图表一致、同试验去重、来源链接、缺失状态及导出结果。

### 安装入口

以下为经来源核对的安装入口，本轮只审阅，没有安装。

```bash
npx skills add https://github.com/K-Dense-AI/scientific-agent-skills --skill scientific-critical-thinking
npx skills add https://github.com/google-deepmind/science-skills --skill pubmed-database
npx skills add https://github.com/anthropics/skills --skill webapp-testing
```

## 14. 留给主办方或 PATH 的具体问题

1. 当前 API 的组别错配是否有修正版或现成 correction mapping？可提供 PMID 37776879 的三个 association ID 作为可复现例子。
2. R21 PMID 38310910 与 Benin 第三年 PMID 38401551 的 study 已存在、associations 为空，是提取覆盖还是发布过滤导致？
3. 本次 API 的 ci_level=0 应如何解释，是否有可信的区间级别或 source sentence 字段？
4. PATH 是否有优先国家、SMC 药物耐药 marker 或额外整理数据，能支持挑战文档中的探索方向？
5. API 的 include_total 是否计算过滤后的匹配总数？当前空检索返回了较大的 total。

这些问题来自已经完成的查询，可帮助主办方快速定位，也能为比赛当日的数据范围做决定。

## 15. 展示叙事建议

三分钟演示可以先打开 Benin 已完成三方核验的结果，让用户看到比较组、区间和论文来源；随后进入 Tanzania 的随访记录，展示结果如何随研究环境和时间组织，并提示两国结局和随访窗的差异。再展示疫苗与 SMC 的组合比较，最后点开来源抽屉，让评委看到图谱记录、原文与修正依据。

建议使用的英文核心表述是 *Malaria prevention evidence depends on the comparison, setting and follow-up period.* 这句话表达本产品的研究组织方式。每个具体科学结论仍由其研究记录支撑。

本方案对四项评分的贡献分别是，Public Graph 提供发现与连接入口，核验后的比较条件支持洞察，数据与来源联动体现技术执行，分面图和三分钟路径支持清晰沟通。

## 16. 主要来源

### 主办方与图谱

- [PATH 等机构的官方挑战文档](https://docs.google.com/document/d/1PZon0PcNrHA3gYPsYsRGbOJk0SqUY9Nq70vCYNLwK6s/edit)
- [参赛者指南](https://docs.google.com/document/d/1jEDJKLsi2k-vmUmzkABaJGLVNNA-fHbwRWhYqdGmoxs/edit)
- [比赛规则](https://system-public-challenge.devpost.com/rules)
- [Public Graph v1 API](https://docs.system.com/system/public/v1.0-api-documentation)
- [Data Provenance](https://docs.system.com/system/public/data-provenance)
- [Limitations and Known Biases](https://docs.system.com/system/public/limitations-and-known-biases)
- [Variable Grounding Logic](https://docs.system.com/system/public/variable-grounding-logic)
- [Harvard Dataverse V2.1](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/7V6JDO)

### 原始试验与综述

- [Mosha 等，Tanzania 24 个月，2022](https://pubmed.ncbi.nlm.nih.gov/35339225/)
- [Mosha 等，Tanzania 36 个月随访，2023](https://pubmed.ncbi.nlm.nih.gov/37776879/)
- [Accrombessi 等，Benin 前两年，2023](https://pubmed.ncbi.nlm.nih.gov/36706778/)
- [Accrombessi 等，Benin 第三年，2024](https://pubmed.ncbi.nlm.nih.gov/38401551/)
- [Datoo 等，R21 三期，2024](https://pubmed.ncbi.nlm.nih.gov/38310910/)
- [ACCESS-SMC Partnership，2020](https://pubmed.ncbi.nlm.nih.gov/33278936/)
- [RTS,S 与 SMC 随机试验，2021](https://pubmed.ncbi.nlm.nih.gov/34432975/)
- [Senegal SMC 阶梯楔形试验，2016](https://pubmed.ncbi.nlm.nih.gov/27875528/)
- [Mali 第五轮 SMC，2023](https://pubmed.ncbi.nlm.nih.gov/36704118/)
- [RTS,S 抗体反应研究](https://pubmed.ncbi.nlm.nih.gov/34894221/)
- [South Sudan SMC 准实验研究](https://pubmed.ncbi.nlm.nih.gov/38267985/)
- [Uganda IRS 描述性研究](https://pubmed.ncbi.nlm.nih.gov/28558701/)
- [标准 ITN Cochrane 综述](https://pubmed.ncbi.nlm.nih.gov/30398672/)
- [PBO Cochrane 综述](https://www.cochrane.org/evidence/CD012776_pyrethroid-pbo-nets-prevent-malaria)
- [IRS Cochrane 综述](https://www.cochrane.org/evidence/CD012688_adding-indoor-residual-spraying-communities-using-insecticide-treated-nets-prevention-malaria)
- [Tanzania 织物耐久性二次分析](https://pmc.ncbi.nlm.nih.gov/articles/PMC11212245/)
- [含负 RR 文本异常的综述](https://pmc.ncbi.nlm.nih.gov/articles/PMC12294781/)

### 外部数据与方法

- [WHO World malaria report 2025](https://www.who.int/teams/global-malaria-programme/reports/world-malaria-report-2025/)
- [WHO Subnational tailoring 手册](https://www.who.int/publications/i/item/9789240115712)
- [WHO GHO OData API](https://www.who.int/data/gho/info/gho-odata-api)
- [WHO ITN use 元数据](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/malaria---number-of-reported-deaths)
- [Malaria Atlas Project 开放政策](https://malariaatlas.org/open-access-policy/)
- [MalariaGEN Pf7 发布](https://malariagen.net/article/pf7-released/)
- [PATH Visualize No Malaria](https://www.path.org/visualize-no-malaria/)
- [Cochrane 综合与展示方法](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-12)


### GitHub、Skill 与本地核查材料

- [System Public Challenge 提交仓库](https://github.com/SystemPublic/system-public-challenge-2026)
- [PATH AMMnet 看板教程](https://github.com/PATH-Global-Health/ammnet-training-20215)
- [EviAtlas](https://github.com/ESHackathon/eviatlas)
- [MIT Evidence Gap Map](https://github.com/MIT-GovLab/Evidence-Gap-Map)
- [LSYS forestplot](https://github.com/LSYS/forestplot)
- [scientific-critical-thinking](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/scientific-critical-thinking)
- [pubmed-database](https://github.com/google-deepmind/science-skills/tree/main/skills/pubmed_database)
- [webapp-testing](https://github.com/anthropics/skills/tree/main/skills/webapp-testing)
- [源码阅读审计](/Users/xh_qian/Desktop/PATH_源码阅读审计_2026-11-14.md)
- [逐文件哈希与阅读范围](/Users/xh_qian/Desktop/第一个项目/output/system-public-challenge-research/source-review/source_review_coverage.json)
- [三项隔离行为核验](/Users/xh_qian/Desktop/第一个项目/output/system-public-challenge-research/source-review/review_probes.json)

本版 GitHub 与 Skill 研究没有新增 System API 请求，复用了本地快照与既有研究证据。候选导出与代码审阅已完成，Skill 安装、代码接入、统一审核表和产品实现尚待执行。
