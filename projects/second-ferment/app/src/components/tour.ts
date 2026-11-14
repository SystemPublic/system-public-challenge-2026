// The guided tour on atlas screen 1 = the five headline findings. Every number comes from the bundle
// (F15, F20-F21, F31-F32, F42; teammate's 20104062 checked against its abstract).
export interface Stop { caption: string; select?: string; hub?: string }

export const TOUR: Stop[] = [
  { select: 'antipsychotics', caption: 'The strongest signal is in psychiatric medicines. In the 2003 French heat wave, people over 70 taking antipsychotics had about twice the odds of dying (aOR 2.09); antidepressants 1.71.' },
  { hub: 'kidney', caption: 'The measured evidence runs through the kidneys and sodium. Diuretics, ACE inhibitors/ARBs and NSAIDs each have dozens of kidney-injury studies, and heat raises kidney injury too. Almost no study links a drug to reduced sweating, the mechanism guidance cites most.' },
  { select: 'insulin', caption: 'Under-recognised: older insulin users had more serious hypoglycaemia on hot days (OR 1.38 on the hottest). Most guidance treats insulin only as a storage problem.' },
  { select: 'lithium', caption: 'Over-warned: every guidance source flags lithium, yet the two studies of lithium levels in heat found no clear effect.' },
  { select: 'antipsychotics', caption: 'Who needs to hear this: nurse practitioners write 34% of antipsychotic claims in Medicare and are in the top three prescribers for every class. No guidance document we read addresses them.' },
]
