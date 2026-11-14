// Plain-language definitions of every metric and label used in the app.
import { AnimatePresence, motion } from 'motion/react'
import { create } from 'zustand'

export const TERMS: { id: string; term: string; group: string; def: string; example?: string }[] = [
  { id: 'ratio', group: 'Reading the numbers', term: 'Ratios in general', def: 'Compare how often something happened to people on the drug (or with a risk factor) with people without it. 1 means no difference; above 1 means more often; below 1 means less often.', example: '2.0 ≈ twice as likely; 0.5 ≈ half as likely; 1.38 ≈ 38% more likely.' },
  { id: 'OR', group: 'Reading the numbers', term: 'OR (odds ratio)', def: 'How the odds of an outcome compare between two groups, e.g. people on a drug versus not. Used in case-control studies.', example: 'OR 6.0: about six times the odds of hospital admission for heat illness.' },
  { id: 'aOR', group: 'Reading the numbers', term: 'aOR (adjusted odds ratio)', def: 'An odds ratio after the study accounted for other differences between the groups, such as age, sex or other illnesses. Usually more trustworthy than an unadjusted OR.', example: 'aOR 2.09: about twice the odds of dying in the heat wave, after adjusting for other factors.' },
  { id: 'HR', group: 'Reading the numbers', term: 'HR (hazard ratio)', def: 'How fast an outcome happens over time in one group compared with another. Read like an odds ratio.', example: 'HR 2.17: about twice the risk of dying during the hospital stay.' },
  { id: 'RR', group: 'Reading the numbers', term: 'RR / IRR (risk or rate ratio)', def: 'How the risk, or the rate of events, compares between groups or periods. Read like an odds ratio.', example: 'IRR 0.76: about a quarter fewer deaths.' },
  { id: 'CI', group: 'Reading the numbers', term: '95% CI (confidence interval)', def: 'The range the true value very likely lies in. Shown in brackets and as the bar in the plots. If the whole range is above 1, the raised risk is real; if it crosses 1, the study cannot tell it apart from no effect. A wide range means a small or imprecise study.', example: '2.09 (1.89–2.35) is precise; 26 (2–350) is very imprecise.' },
  { id: 'p', group: 'Reading the numbers', term: 'p-value', def: 'How likely a result this large would be by chance if there were no real effect. Below 0.05 is conventionally called significant.', example: 'p = 0.08: not significant.' },
  { id: 'forest', group: 'Reading the numbers', term: 'Forest plot', def: 'One row per study: the square is the result, the bar is its 95% interval, the dashed line is 1 (no difference). Rows to the right mean higher risk.' },
  { id: 'guidance-docs', group: 'Kinds of evidence', term: 'Heat-health guidance', def: 'Official advice for clinicians from public-health agencies about medicines and heat. We read eight: CDC (2025), NYC Health (provider page and 2026 health alert), Health Canada (2011 technical guide and 2024 pharmacist guide), UK Health Security Agency (2024), France\'s medicines agency ANSM (2023 summary) and Victoria, Australia (2024). Each card lists which ones name the effect; hover a name for the full title.' },
  { id: 'measured', group: 'Kinds of evidence', term: 'Direct evidence', def: 'A study looked at people taking this drug during hot weather or a heat wave, and measured what happened to them. The strongest kind of evidence here.' },
  { id: 'group', group: 'Kinds of evidence', term: 'Direct evidence, drug group', def: 'The study looked at a group of drugs together (e.g. "blood-pressure medicines"), not this class alone.' },
  { id: 'null', group: 'Kinds of evidence', term: 'Studied in heat, no clear effect', def: 'It was studied in heat, but the result could not be told apart from no effect. Not proof of safety.' },
  { id: 'shared', group: 'Kinds of evidence', term: 'Indirect evidence', def: 'Some studies link the drug to a body effect (e.g. kidney injury) and separate studies link heat to the same effect. It suggests the two could add up, but nobody has studied them together in the same people.' },
  { id: 'guidance', group: 'Kinds of evidence', term: 'No studies', def: 'One or more heat-health guidance documents mention this link, but we found no study for it in the graph. The card names the documents.' },
  { id: 'drugside', group: 'Kinds of evidence', term: 'Drug side / heat side', def: 'Drug side: studies of the drug and a body effect, with the share showing raised (orange) or lowered (green) risk. Heat side: studies of heat and the same effect.' },
  { id: 'strength', group: 'Kinds of evidence', term: 'Circle size (evidence strength)', def: 'Our 0–5 rating of how strong the heat evidence is for a class: direct > direct (drug group) > indirect > no studies, adjusted for vetting and consistency. It is about evidence, not about how dangerous the drug is.' },
  { id: 'vetted', group: 'Trust labels', term: 'Vetted / unvetted', def: 'Vetted rows are in the System Public Graph\'s quality-filtered release. Unvetted rows exist only in the live graph, where the provider estimates about 20% are extracted wrongly. Unvetted results are dashed and labelled.' },
  { id: 'checked', group: 'Trust labels', term: 'Abstract-checked', def: 'We read the paper\'s abstract and confirmed the number and what it refers to.' },
  { id: 'corrected', group: 'Trust labels', term: 'Corrected by us', def: 'The graph had the right number with the wrong label (or direction); we show the corrected reading from the abstract.' },
  { id: 'casecontrol', group: 'Study types', term: 'Case-control study', def: 'Compares people who had the outcome (e.g. died in the heat wave) with similar people who did not, and looks back at differences such as medicines. Gives odds ratios.' },
  { id: 'cohort', group: 'Study types', term: 'Cohort or case-crossover study', def: 'Follows a group over time, or compares the same people on hot days and normal days.' },
  { id: 'ecological', group: 'Study types', term: 'Ecological study', def: 'Compares areas or populations, not individuals. Weaker for saying what happens to one person.' },
  { id: 'hvi', group: 'Heat check', term: 'Heat vulnerability index (HVI)', def: 'NYC\'s 1–5 score for how vulnerable a neighbourhood is to heat, based on surface temperature, green space, air-conditioning access, income and race. 5 = most vulnerable.' },
  { id: 'alerts', group: 'Heat check', term: 'Heat advisory / extreme heat warning', def: 'National Weather Service alerts. An advisory means dangerous heat is expected; a warning means extreme heat. NYC issues advisories when the heat index is forecast to reach about 95–100 °F or more.' },
  { id: 'points', group: 'Heat check', term: 'Risk band and points', def: 'Our transparent rule, not a validated score: each factor adds points (guided by the size of its effect in studies), protective factors subtract, and the total sets Low, Elevated, High or Very high.' },
]

export const useGlossary = create<{ open: boolean; focus: string | null; show: (id?: string) => void; hide: () => void }>(set => ({
  open: false, focus: null, show: id => set({ open: true, focus: id ?? null }), hide: () => set({ open: false }),
}))

/** A metric abbreviation with a dotted underline; hover for the definition, click to open the glossary. */
export function Term({ id, children }: { id: string; children: React.ReactNode }) {
  const t = TERMS.find(x => x.id === id)
  const show = useGlossary(s => s.show)
  return (
    <button type="button" title={t ? `${t.term}: ${t.def}` : undefined} onClick={e => { e.stopPropagation(); show(id) }}
      className="cursor-help underline decoration-dotted decoration-1 underline-offset-2">{children}</button>
  )
}

export function GlossaryPanel() {
  const { open, focus, hide } = useGlossary()
  const groups = [...new Set(TERMS.map(t => t.group))]
  return (
    <AnimatePresence>
      {open && (
        <motion.div className="fixed inset-0 z-50 flex justify-end bg-black/30" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={hide}>
          <motion.aside className="h-full w-full max-w-md overflow-y-auto bg-panel p-6 shadow-2xl" initial={{ x: 40 }} animate={{ x: 0 }} exit={{ x: 40 }} onClick={e => e.stopPropagation()}
            role="dialog" aria-label="Glossary">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-[22px] font-bold">How to read the numbers</h2>
              <button onClick={hide} className="text-[13px] text-ink-3 hover:text-ink">Close</button>
            </div>
            {groups.map(g => (
              <section key={g} className="mt-5">
                <h3 className="eyebrow mb-2">{g}</h3>
                <dl className="flex flex-col gap-3">
                  {TERMS.filter(t => t.group === g).map(t => (
                    <div key={t.id} ref={el => { if (el && focus === t.id) el.scrollIntoView({ block: 'center' }) }}
                      className={`rounded-md p-2 ${focus === t.id ? 'bg-heat-soft' : ''}`}>
                      <dt className="text-[14px] font-bold">{t.term}</dt>
                      <dd className="text-[13px] leading-relaxed text-ink-2">{t.def}{t.example && <span className="mt-0.5 block text-ink-3">Example: {t.example}</span>}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            ))}
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
