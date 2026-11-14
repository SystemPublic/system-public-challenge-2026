# 前端单文件交付说明

**只需加载 `what-works-where/site/data/frontend-data.json`。** 不需要解析CSV、再合并两个人的输出或请求外部API。

schema_version: `1.0.0`。输入来自已整合的 evidence-pipeline 分支；源文件和SHA-256记录在JSON的 `meta.inputs`。

## 文件内容

| 顶层字段 | 内容 |
|---|---|
| `summary` | 由实际数组计算的覆盖和质量计数 |
| `countries` | 11个整理过的国家分组，加候选记录中其余国家代码；未整理的国家名称回退为代码，`showcase=index_only` |
| `filters` | 干预类别、结局、统计量和国家筛选选项 |
| `results` | 20条论文锚点 + 33条摘要核验记录，共53条。52条满足当前展示规则，1条已排除 |
| `candidates` | 481条待核验图谱关联；保留QC标记，并连接已有核验结果ID |
| `context.country_year` | WHO/MAP国家背景，721条，来源/单位/版本分开 |
| `context.pf8_sp` | SP相关药物分类背景，332条 |
| `context.pf8_aq_markers` | 原始crt/mdr1变异携带背景，166条，不是AQ耐药率 |
| `graph_context` | 疟疾与干预概念网络及锚点覆盖 |
| `possible_result_overlaps` | 同论文、数值、区间和随访相同的潜在重复，需比较定义后处理，不静默合并 |
| `meta`, `frontend_rules` | 来源、许可、解释边界和接入规则 |

## 最小接入示例

```js
const data = await fetch('./data/frontend-data.json').then(r => {
  if (!r.ok) throw new Error(`Data load failed: ${r.status}`);
  return r.json();
});

// 效果图只取核验结果，并保留各自的核验层级。
const results = data.results.filter(r => r.display.plot_eligible);
const tanzania = results.filter(r => r.iso3.includes('TZA'));
const nets = tanzania.filter(r => r.intervention_class === 'nets');

// 背景图显式选择来源、指标、国家，不按论文发表年自动连接。
const trend = data.context.country_year.filter(r =>
  r.iso3 === 'TZA' && r.source === 'MAP' && r.indicator === 'ITN_use-rate'
).sort((a, b) => a.year - b.year);
```

`results[*].iso3` 和 `candidates[*].iso3` 始终是数组。多国结果只保留一个ID，不复制成多项独立研究。背景表的 `iso3` 是单个国家字符串。`country` 保留原文描述供展示。

## 绘图与来源详情

- `estimate/ci_lower/ci_upper/ci_level` 为数值；缺失统一为 `null`。不要把null变0。
- 效果图使用 `results` 中 `display.plot_eligible=true` 的记录。该标记表示当前证据/数值规则允许展示，不代表统一研究质量或因果强度。
- 按 `display.panel_key` 分面，保留对照组、结局、统计量、人群和时间。不同统计量不能直接排序或汇总。
- `display.verification_level` 区分 `full_text`、`paper_reported`、`abstract`。综述汇总另有 `evidence_kind=systematic_review_summary`，不能当新增独立试验。
- `candidates` 仅用于搜索、证据索引与来源详情。`numeric_plot_eligible` 只表示数值形式可画，所有候选的 `effect_display_eligible` 都是false；应通过 `linked_result_ids` 查找核验结果。
- 来源详情可直接显示已有 `source_url`、`source_location/source_quote`、`verification_note` 和 `fulltext_check`。
- R21两条及ACCESS-SMC的历史全文核验曾标记上下文不符。历史标记保留，但 `current_resolution=resolved_in_current_evidence`，表示当前证据已修正。ACCESS-SMC的五国代码从全文病例对照部分恢复，溯源说明在 `provenance` 中。
- WHO百分比与MAP比例单位保持不同。IRS是保护人数。Pf8是采样病例背景，BFA只有2008年。
- `results`、`candidates`、综述及同试验不同随访存在重叠，不能相加当作独立研究数量。

## 复跑

```sh
python3 scripts/build_frontend_bundle.py
python3 scripts/validate_frontend_bundle.py
```

Python标准库即可。生成器不修改任何来源证据表和原始数据。其他已有site/data文件保留，前端迁移为一次fetch即可。
