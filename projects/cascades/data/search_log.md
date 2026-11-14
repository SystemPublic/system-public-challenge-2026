# Search log

Run: 2026-11-14T16:10

Source: System Public Graph, Harvard Dataverse v2.1 (doi:10.7910/DVN/7V6JDO), curated associations CSV.
Matching: case-insensitive regex on both variable names; clinical false matches excluded. Keyword search is not exhaustive; counts describe coverage, not evidence strength.

## Moisture & mould remediation
- intervention terms: `(mou?ld|damp\w*|moisture|water[- ]damage)\w* \w* ?remediat\w*|remediat\w* (of )?(mou?ld|damp\w*|moisture|water damage)|\bleak repair|repair\w* (of )?leaks?\b|\bdehumidif\w*|mou?ld removal|moisture control|damp[- ]proof\w*`
- exposure terms: `\bdamp\w*|\bmou?ld(s|y|iness)?\b|visible mou?ld|water[- ]damage|condensation|indoor fung\w*|household fung\w*|home moisture|moisture (in|damage)`

## Building fabric (insulation, airtightness)
- intervention terms: `(home|house|housing|dwelling|loft|wall|roof|floor|cavity|building|thermal)\w* insulat\w*|insulat\w* (of|in) (the )?(home|house|dwelling|building|walls?|roofs?|lofts?)|insulated (home|house|dwelling)s?|\bretrofit\w*|weatheri[sz]\w*|(home|house|dwelling|building)\w* airtight\w*|air[- ]tightness of|draught[- ]?proof\w*|draft[- ]?proof\w*|double[- ]glaz\w*|energy[- ]efficien\w* (home|hous|dwelling|retrofit|upgrade|improvement)\w*|home energy (upgrade|improvement)|energy upgrade`
- exposure terms: `(home|house|dwelling|building) (air )?leakage`

## Ventilation & source capture
- intervention terms: `extractor fan|exhaust fan|range hood|cooker hood|heat[- ]recovery ventilation|\bmvhr\b|trickle vent|(building|home|house|dwelling|school|classroom|office)\w* ventilation system|ventilation system\w* (in|of) (the )?(home|house|dwelling|building|school|classroom|office)|(house|household|dwelling|building|school|classroom|kitchen|bathroom|bedroom|office|living)\w* \w* ?ventilat\w*`
- exposure terms: `poor ventilation|inadequate ventilation|natural ventilation|ventilation (in|of) (the )?(home|house|household|dwelling|building|kitchen|room|classroom)|air exchange|air change rate|window opening|open(ing)? windows?`

## Particle filtration
- intervention terms: `air purifier\w*|air cleaner\w*|\bair filt\w*|\bhepa\b|portable (air )?filt\w*|indoor air filtration`
- exposure terms: `indoor (pm\S*|particulate\w*|particle\w*|fine particle\w*)|household (pm\S*|particulate\w*)`

## Clean cooking
- intervention terms: `induction (hob|stove|cook\w*|range)|electric (stove|cook\w*|hob)|clean(er)? (cooking )?fuel\w*|improved (cook)?stove\w*|cookstove intervention|\blpg\b|liquefied petroleum gas|stove (replacement|intervention|exchange)`
- exposure terms: `gas (cook\w*|stove\w*|hob\w*|range)|cooking fuel\w*|solid fuel\w*|biomass fuel\w*|biomass smoke|biomass (use|exposure|burning|cooking)|(household|domestic|indoor) cooking|cooking with (wood|coal|biomass|gas|kerosene|charcoal|dung)|charcoal|animal dung|crop residue|kerosene|household air pollution|indoor (no2|nitrogen dioxide|air pollution)|cooking (smoke|fume\w*)|unvented|unflued|wood ?stove\w*|wood burning|coal (stove|heating|use)`

## Indoor temperature (heating & cooling)
- intervention terms: `central heating|heating system\w*|heating type|type of heating|heating (fuel|source|method|equipment|appliance)\w*|home heating|space heat\w*|heat pumps?|electric heat\w*|floor heating|\bheaters?\b|thermostat\w*|warm homes?|winter fuel|fuel payment|air[- ]condition(er|ers|ing)\b|\bshading\b|\bshutters\b|cool roof\w*|green roof\w*|\bfan use|electric fans?`
- exposure terms: `cold homes?|cold housing|cold (indoor|house)|indoor temperature\w*|bedroom temperature|living[- ]room temperature|overheat\w*|indoor heat|thermal comfort|excess cold|indoor cold|fuel poverty|energy poverty|energy insecurity`

## Radon mitigation
- intervention terms: `radon (mitigation|remediation|reduction|sump|test\w*|control)`
- exposure terms: `\bradon\b`

## Allergen & pest control (household)
- intervention terms: `integrated pest management|(home|household|residential)\w* pest (control|management)|mattress (cover|encas\w*)|(bedding|pillow) encas\w*|impermeable cover\w*|allergen (avoidance|reduction|control|remov\w*)|home[- ]based (asthma|environmental)|asthma home visit\w*|home environmental (intervention|assessment)|environmental asthma intervention|carpet removal`
- exposure terms: `dust mite\w*|house dust|cockroach\w*|mouse allergen\w*|rodent (infestation|allergen)\w*|pet allergen\w*|indoor allergen\w*|household allergen\w*|(house|home|household|indoor|mattress|airborne|dust|bedding)\w* endotoxin\w*|endotoxin\w* (in|from) (the )?(house|home|dust|mattress|bedding)`

## Exclusions
`antifung|aspergill|mou?ld-active|ventilator|non-?invasive|diffusing capacity|\bdlco\b|\btlco\b|ventilation[- ]perfusion|minute ventilation|alveolar ventilation|ventilatory|endotracheal|intensive care|\bicu\b|fio2|hypoxic|hyperoxic|oxygenation|insulin|nasoalveolar|health-enhancing|asbestos|insulator|perioperative|intraoperative|surgical|anesthe|anaesthe|labou?r induction|induction of (labou?r|anesthesia|remission)|therapeutic hypotherm|cooling (therapy|cap|vest|blanket)|cryo|warming system|\bmurine\b|\bin vitro\b|cell culture|culture medium|mou?ld (of|in) (the )?(teeth|dental)|hepatic|wound|orthodont|denture|prosthe|cognitive remediation|remediation (for|of) (professionalism|skills)|soil moisture|soil remediation|face mask|mechanical ventilation|hypercapni|kyphoscoli|round window|cochlear|hemofiltration|ultrafiltration|hemodia|filtration rate|glomerular|cascade|hematolog|transplant|operating (room|theat)|scrot|microneedle|\bleads?\b|endotoxin[- ](treated|infusion|challenge)|lipopolysacch|\blps\b|swine|room air condition|feline|canine|legionella|zika|dengue|virus|hospital room|laminar|controlled environ|glaucoma|water filtration|daycare`
