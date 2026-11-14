// English renderings of the non-English guidance quotes in
// data/kb/knowledge_base.json (drugs[].guidance.by_source[].quote, coded from
// data/processed/guidance_matrix.csv). The original stays one click away.
// Keyed by the exact original quote (whitespace-normalised).

export type QuoteLanguage = "French" | "German";

/** Which guidance sources publish in which language. */
export const SOURCE_LANGUAGE: Record<string, QuoteLanguage> = {
  ANSM: "French",
  GER_BMG: "German",
  GER_HEID: "German",
};

const T: Record<string, string> = {
  // ANSM (France)
  "Sels de lithium Profil cinétique affecté par la déshydratation":
    "Lithium salts: dehydration changes how the body handles the drug.",
  "en cas de prescription d’un diurétique, vérifier que les apports hydriques et sodés sont adaptés":
    "When a diuretic is prescribed, check that fluid and salt intake are adequate.",
  "certains antispasmodiques, en particulier ceux à visée urinaire (oxybutynine, toltérodine,":
    "certain antispasmodics, especially those used for the bladder (oxybutynin, tolterodine,",
  "les inhibiteurs de l’enzyme de conversion de l’angiotensine, les antidépresseurs sérotoninergiques, les inhibiteurs de la pompe à proton, la digoxine, les benzodiazépines, les hypoglycémiants oraux, les sartans, les antagonistes calciques et les β-bloquants10":
    "ACE inhibitors, serotonergic antidepressants, proton pump inhibitors, digoxin, benzodiazepines, oral glucose-lowering drugs, sartans (ARBs), calcium channel blockers and beta blockers [ref. 10]",
  "les hypoglycémiants oraux": "oral glucose-lowering drugs",
  "Médicaments biologiques (insuline, somatropine...) en présentation multidose qui se conservent hors du réfrigérateur après ouverture à des températures ne dépassant pas 25°C ou 30°C En cas d'exposition à des températures supérieures, il est recommandé de se rapprocher, éventuellement avec l'aide d'un pharmacien, du laboratoire":
    "Biological medicines (insulin, somatropin...) in multi-dose form that, once opened, are kept out of the fridge at no more than 25°C or 30°C. If exposed to higher temperatures, contact the manufacturer, if needed with a pharmacist's help.",
  "Biguanides et sulfamides hypoglycémiants Profil cinétique affecté par la déshydratation":
    "Biguanides and sulfonylureas (glucose-lowering drugs): dehydration changes how the body handles the drug.",
  "la prise d’un psychotrope, en particulier antidépresseur ou neuroleptique, est associée à une augmentation du risque de décès chez le sujet âgé pendant une vague de chaleur":
    "taking a psychiatric medicine, especially an antidepressant or antipsychotic, is linked to a higher risk of death in older people during a heat wave",
  "les antidépresseurs sérotoninergiques": "serotonergic antidepressants",
  "Anti-épileptiques Profil cinétique affecté par la déshydratation":
    "Anti-epileptic drugs: dehydration changes how the body handles the drug.",
  "l’usage de certaines drogues, en particulier les substances amphétaminiques et la cocaïne":
    "use of certain drugs, especially amphetamine-type substances and cocaine",
  "les antagonistes calciques et les β-bloquants10": "calcium channel blockers and beta blockers [ref. 10]",
  "la pharmacocinétique des dispositifs transdermiques peut être modifiée en raison de la vasodilatation sous-cutanée, et de l’hypersudation susceptible d’entrainer un décollement.":
    "how skin patches release the drug can change because blood vessels under the skin widen, and heavy sweating can make the patch come off.",
  // Heidelberg table (Germany)
  "Lithium Spiegelkontrolle. Besondere Vorsicht bei Polyurie / Diabetes insipidus":
    "Lithium: check blood levels. Take special care with heavy urination / diabetes insipidus.",
  "Diuretika Gewichtsmonitoring, ausreichende Flüssigkeits- und ggf. Elektrolytzufuhr":
    "Diuretics: monitor weight; enough fluids and, if needed, electrolytes.",
  "Urologische anticholinerge Spasmolytika (z. B. Oxybutynin, Solifenacin, Tolterodin) Therapiewechsel auf weniger anticholinerge Vertreter erwägen":
    "Bladder anticholinergic antispasmodics (e.g. oxybutynin, solifenacin, tolterodine): consider switching to a less anticholinergic option.",
  "ACE-Hemmer, AT1-Rezeptor-Antagonisten Trinkprotokoll führen um adäquate Flüssigkeitszufuhr zu überwachen.":
    "ACE inhibitors, AT1 receptor blockers (ARBs): keep a drinking log to make sure fluid intake is adequate.",
  "Subcutan applizierte Arzneimittel (schnell wirksames Insulin) Intensivierte Überwachung, ggf. Dosisanpassung":
    "Medicines injected under the skin (fast-acting insulin): closer monitoring; adjust the dose if needed.",
  "Enges UAW-Monitoring und ggf. Dosisanpassung": "Close monitoring for side effects; adjust the dose if needed.",
  "SSRI, SNRI (insb. auch in Kombination mit Lithium), NDRI (Bupropion)":
    "SSRIs, SNRIs (especially when combined with lithium), NDRIs (bupropion)",
  "Topiramat, Zonisamid 11-14": "Topiramate, zonisamide [refs. 11–14]",
  "Sympathomimetika, zentral wirkend (z. B. Methylphenidat, Modafinil) Enges UAW-Monitoring":
    "Centrally acting stimulants (e.g. methylphenidate, modafinil): close monitoring for side effects.",
  "Betablocker 4, 58, 59": "Beta blockers [refs. 4, 58, 59]",
  "Opioide als transdermale therapeutische Systeme (Pflaster) Enges UAW-Monitoring und ggf. Dosisanpassung":
    "Opioids as skin patches: close monitoring for side effects; adjust the dose if needed.",
};

const norm = (s: string) => s.replace(/\s+/g, " ").trim();
const TABLE = new Map(Object.entries(T).map(([k, v]) => [norm(k), v]));

export function translateQuote(sourceId: string, quote: string): { language: QuoteLanguage; english: string | null } | null {
  const language = SOURCE_LANGUAGE[sourceId];
  if (!language) return null;
  return { language, english: TABLE.get(norm(quote)) ?? null };
}
