# 1. Explicit research inputs. These are published estimates, not simulated observations.
import math

GRAPH_EVIDENCE = {
    "salary_mortality": {
        "rr": 1.59,
        "ci": None,  # No verified interval; never replace missing uncertainty with zero.
        "population": "Korean male civil servants, 1992–1996",
        "contrast": "lowest versus highest salary grade",
        "source": "https://pubmed.ncbi.nlm.nih.gov/10746109/",
        "locator": "Abstract; System Graph association 020zZ9sQBg",
    },
    "pay_life_satisfaction": {
        "beta_log_hourly_pay": 0.250,
        "robust_se": 0.010,
        "population": "UK Annual Population Survey; full-time workers aged 18–65",
        "source": "https://onlinelibrary.wiley.com/doi/10.1111/ecca.12516",
        "locator": "Table 1; primary-paper supplement, not matched in snapshot",
    },
    "conditions_physical": {
        "individual_hr_abstract": 1.32,
        "individual_hr_results_text": 1.31,  # Source discrepancy remains unresolved.
        "individual_ci": (1.13, 1.53),
        "work_unit_hr": 1.02,
        "work_unit_ci": (0.88, 1.19),
        "source": "https://www.sjweh.fi/show_abstract.php?abstract_id=3402&fullText=1",
        "locator": "Abstract and Results; Model 2; Graph seed OCkbXWwzaH",
    },
    "conditions_mental": {
        "individual_hr": 1.90,
        "individual_ci": (1.51, 2.40),
        "work_unit_hr": 1.63,
        "work_unit_ci": (1.31, 2.04),
        "source": "https://www.sjweh.fi/show_abstract.php?abstract_id=3402&fullText=1",
        "locator": "Results; Model 2; depression-related disability pension",
    },
    "hours_depression": {
        "main_or": 2.52,
        "main_ci": (1.12, 5.65),
        "sensitivity_or": 1.89,
        "sensitivity_ci": (0.92, 3.86),
        "source": "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0030719",
        "locator": "Table 2 / Results; prior v01 paper check; Graph qtGTRpRBv0",
    },
    "insecurity_depression": {
        "men_or": 2.47,
        "men_ci": (1.37, 4.48),
        "women_or": 1.48,
        "women_ci": (0.88, 2.50),
        "source": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8949946/",
        "locator": "Tables 5–6, separate-indicator models; v02 E01 and E03",
    },
    "insecurity_life_satisfaction": {
        "adjusted_beta": -0.26,
        "se": 0.16,
        "contrast": "worried versus not worried, conditional on permanent employment",
        "source": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5984641/",
        "locator": "Table 3 M2; initial life satisfaction; primary-paper supplement",
    },
}

# 2. Transparent transformations. The papers report coefficients and standard errors.
# Pay: a doubling changes log(hourly pay) by ln(2); scale the coefficient and SE.
pay = GRAPH_EVIDENCE["pay_life_satisfaction"]
pay_difference = pay["beta_log_hourly_pay"] * math.log(2)
pay_margin = 1.96 * pay["robust_se"] * math.log(2)
pay_ci = (pay_difference - pay_margin, pay_difference + pay_margin)

# Insecurity: normal-approximation CI from the rounded published coefficient and SE.
security = GRAPH_EVIDENCE["insecurity_life_satisfaction"]
security_ci = (
    security["adjusted_beta"] - 1.96 * security["se"],
    security["adjusted_beta"] + 1.96 * security["se"],
)

# Labels/colors summarize these selected findings, not the quality of all evidence.
salary = GRAPH_EVIDENCE["salary_mortality"]
physical = GRAPH_EVIDENCE["conditions_physical"]
mental = GRAPH_EVIDENCE["conditions_mental"]
hours = GRAPH_EVIDENCE["hours_depression"]
insecurity = GRAPH_EVIDENCE["insecurity_depression"]
graph_rows = [
    ("Physical health", "Lower salary grade, higher mortality",
     f"RR {salary['rr']:.2f} • confidence interval not verified", "gray", salary["source"]),
    ("Life satisfaction", "Higher hourly pay, higher life satisfaction†",
     f"UK: +{pay_difference:.2f} points per doubling of pay (approx. CI {pay_ci[0]:.2f}–{pay_ci[1]:.2f})",
     "teal", pay["source"]),
    ("Physical health", "Effort–reward imbalance: findings vary",
     f"Musculoskeletal disability: HR {physical['individual_hr_abstract']:.2f}* (individual) / {physical['work_unit_hr']:.2f} (work unit)",
     "amber", physical["source"]),
    ("Mental health", "Greater imbalance, more depression-related disability",
     f"HR {mental['individual_hr']:.2f} (individual measure) / {mental['work_unit_hr']:.2f} (work-unit measure)",
     "teal", mental["source"]),
    ("Mental health", "Long hours associated with depression",
     f"OR {hours['main_or']:.2f}; sensitivity analysis {hours['sensitivity_or']:.2f}, with interval including 1",
     "amber", hours["source"]),
    ("Mental health", "Insecurity–depression findings vary by group",
     f"Men: OR {insecurity['men_or']:.2f}; women: OR {insecurity['women_or']:.2f}, with interval including 1",
     "amber", insecurity["source"]),
    ("Life satisfaction", "Lower satisfaction; adjusted finding uncertain†",
     f"−{abs(security['adjusted_beta']):.2f} points (approx. 95% CI −{abs(security_ci[0]):.2f} to {security_ci[1]:.2f})",
     "amber", security["source"]),
]

# 3. Draw the evidence diagram with Matplotlib; no image-generation service is used.
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
C={'ink':'#17303D','muted':'#607584','teal':'#007D72','amber':'#A36D16','gray':'#6D808D','line':'#D9E5E9','pale':'#EFF7F5'}
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':C['ink'],'svg.fonttype':'none'})
f=plt.figure(figsize=(16,11),facecolor='white');a=f.add_axes([0,0,1,1]);a.set_xlim(0,1);a.set_ylim(0,1);a.axis('off')
def text(x,y,s,size=14,**kw):return a.text(x,y,s,fontsize=size,va='center',**kw)
def box(x,y,w,h,fill,edge):a.add_patch(FancyBboxPatch((x,y-h/2),w,h,boxstyle='round,pad=0,rounding_size=0.012',fc=fill,ec=edge,lw=1.2))
text(.04,.949,'How job quality relates to health and well-being',28,fontweight='bold')
text(.04,.903,'Seven investigated relationships • selected study findings, not causal effects',15,color=C['muted'])
text(.04,.850,'JOB-QUALITY FACTORS',12,fontweight='bold',color=C['muted'])
text(.30,.850,'WHAT THE STUDIES FOUND',12,fontweight='bold',color=C['muted'])
text(.795,.850,'OUTCOMES',12,fontweight='bold',color=C['muted'])
ys=[.785,.700,.595,.510,.405,.300,.215]
for y,label,h in [(.7425,'Wages and\nearnings',.151),(.5525,'Working\nconditions',.151),(.405,'Working hours',.072),(.2575,'Job security',.151)]:
 box(.04,y,.215,h,C['pale'],'#BEDBD5');text(.1475,y,label,20,fontweight='bold',ha='center',linespacing=1.35)
for y,(out,title,detail,col,url) in zip(ys,graph_rows):
 color=C[col]
 a.add_patch(FancyArrowPatch((.258,y),(.787,y),arrowstyle='-|>',mutation_scale=17,lw=2,color=color,linestyle=(0,(4,3)) if col=='gray' else '-'))
 # White label panel preserves the flow while keeping annotations readable.
 a.add_patch(FancyBboxPatch((.288,y-.032),.475,.065,boxstyle='round,pad=0.005,rounding_size=0.006',fc='white',ec='none',zorder=3))
 t=text(.30,y+.013,title,14.5,fontweight='bold',color=color,zorder=4);t.set_url(url)
 text(.30,y-.014,detail,11.4,color=C['muted'],zorder=4)
 box(.79,y,.17,.068,'#F0F5F9','#C7D4DE');text(.875,y,out,17,fontweight='bold',ha='center')
# Legend describes the displayed results, not evidence quality.
a.plot([.04,.96],[.159,.159],color=C['line'],lw=1)
for x,col,label in [(.04,'teal','Association observed'),(.31,'amber','Mixed / uncertain findings'),(.65,'gray','Interval not verified')]:
 a.plot([x,x+.025],[.134,.134],color=C[col],lw=3,ls='--' if col=='gray' else '-')
 text(x+.034,.134,label,12,color=C['muted'])
text(.04,.103,'RR = relative risk; HR = hazard ratio; OR = odds ratio. These measures and populations are not directly comparable.',11,color=C['muted'])
text(.04,.079,'† Life-satisfaction estimates are primary-paper supplements. * Physical-health estimate: abstract 1.32; Results text 1.31.',10.8,color=C['muted'])
text(.04,.055,'Sources: System Graph snapshot + checked papers. Salary is an SES proxy; physical-health outcomes include mortality and disability.',10.8,color=C['muted'])
text(.04,.029,'Colors describe selected findings, not evidence quality. Arrowheads identify the relationship studied. No pooling or attribute ranking.',10.8,color=C['muted'])

# 4. Export the graph for the presentation and show it in the notebook.
GRAPH_OUTPUT = Path("figures")
GRAPH_OUTPUT.mkdir(parents=True, exist_ok=True)
f.savefig(GRAPH_OUTPUT / "job_quality_relationships.png", dpi=200, facecolor="white")
f.savefig(GRAPH_OUTPUT / "job_quality_relationships.svg", facecolor="white")
plt.show()
print("Saved figures/job_quality_relationships.png and .svg")
