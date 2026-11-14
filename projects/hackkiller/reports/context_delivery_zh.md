# AI-2 背景数据与全文核验交付

## 完成范围

在 context-data 分支完成 B1–B5、C1 和可选 B6，仅修改 AI-2 负责的目录与协调记录。原始数据不覆盖，所有新增下载均加入 SHA-256 清单。没有修改队友的 evidence_*.csv、pipeline、site 或 docs。

| 交付文件（what-works-where/data/ 下） | 数据行数 | 用途 |
|---|---:|---|
| context/countries.csv | 11 | 核心/支持国家、粗粒度环境分组及实际数据可用性 |
| context/context_country_year.csv | 721 | 五国 WHO 331 条 + MAP 390 条，保留原单位 |
| context/pf8_sp_country_year.csv | 332 | 八国四类 SP 相关药物分类及有效分母 |
| verified/fulltext_checks.csv | 11 | 逐条原始 XML 数值与上下文核验 |
| context/pf8_aq_markers_country_year.csv | 166 | crt K76T、mdr1 N86Y 的原始标记携带比例 |

WHO/MAP 核心五国：坦桑尼亚、贝宁、布基纳法索、马里、尼日利亚。MAP 固定版本 202608，2000–2025 年。新增 31 份原始返回（MAP 27，WHO 4），没有分页遗漏。

## 全文核验结果

11 条结果的点估计及置信区间均可在原始 XML 对应表格或段落中找到；R21 和 ACCESS-SMC 按原文 VE/PE 定义反推并检查了区间端点。发现的是三条上下文问题，数值没有差异：

1. **R21-SEAS**：季节性站点只有布基纳法索 Nanoro、马里 Bougouni，国家应为 BFA;MLI。
2. **R21-STD**：常年/标准站点为布基纳法索 Dande、肯尼亚 Kilifi、坦桑尼亚 Bagamoyo，国家应为 BFA;KEN;TZA。
3. **ACCESS-SMC-CC**：原文 Figure 2A 的对照是过去 42 天未接受 SMC。28 天是服药后保护观察窗。病例对照部分是五国数据，七国是整个实施项目范围。

上述三条 `matches_our_value=N` 表示完整比较上下文需修正；`reports/fulltext_check_audit.json` 单独记录 `numerical_match=true`，避免把上下文问题误报为数值不符。修改请求已写入 COORDINATION.md，未擅自改证据表。

其余 8 条的数值和比较定义按现有材料一致。Cochrane 记录是综述汇总，不是独立新试验；本次核验不等于偏倚风险评价。证据表中没有待补充的 PMID 27875528/34894221 graph-checked 行，因此没有制造对应结果ID。

## 数据适用边界

- 国家季节性分组来自团队约定，仅用于导航，不是所有研究站点的事实。
- Pf8 无 amodiaquine 分类；SP 表只覆盖 SMC 的 SP 部分。
- BFA 的 Pf8 样本仅有 2008 年，不能外推到后续干预试验。
- crt/mdr1 变异携带率不等于 AQ 耐药率，更不等于 SMC 效力。混合调用单列，缺失不进入有效分母。
- WHO/MAP 保持来源与版本分开，不从背景趋势推断因果效果，不将两者当作独立重复证据。

## 验证与复跑

已运行 `clean_data.py`、`validate_processed.py`、`build_context_contracts.py`、`check_context_fulltexts.py`、`build_pf8_aq_marker_context.py`、`validate_context_contracts.py`。检查精确表头、唯一键、单位、五国范围、国家代码、耐药分母、BFA 年份、11 条核验及标记计数。

下一步由证据与前端负责人消费这四份契约文件，修正三条上下文并重建 site/data。AI-2 没有直接修改前端数据。
