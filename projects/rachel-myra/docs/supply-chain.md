# Heat-safe delivery: the supply-chain piece

**Prompted by the judge:** mail-order medications can sit on a hot doorstep for hours. This doc proposes a **software layer** over the existing pharmacy → carrier → patient chain, plus one small hardware demo.

Compiled 13 Nov 2026 from web searches. Several numbers come from news or vendor summaries (marked), so verify them before using them on slides.

---

## 1. What the evidence says

| Finding | Source | Confidence |
|---|---|---|
| All 48 mail-order packages with temperature loggers went outside 68–77°F at some point. Time out of range: 27–54% in summer, 68–87% in winter. | ASHP-presented study, 2020 ([ASHP News](https://news.ashp.org/news/ashp-news/2020/12/09/mail-order-medications-often-exposed-to-unsafe-temperatures-study-shows); [EurekAlert](https://www.eurekalert.org/news-releases/841330)) | Conference study |
| Packages were out of range for most of transit regardless of carrier, method or season. **Summer 3-day shipping: 43.1% out of range vs. 13.6% for next-day.** | JAPhA 2023, evaluation against USP <659> ([PDF](https://opha.com/wp-content/uploads/2023/05/JAPhA-2023-Temperature-Excursions.pdf)) | Peer-reviewed; PMID not yet confirmed |
| About 40% of mailbox readings were outside 59–86°F | University of Arizona ([repository](https://repository.arizona.edu/handle/10150/624736)) | Not a drug-stability study |
| Simulated summer shipping didn't reduce insulin potency | Chandler et al., AJHP 2008 (PMID 18463345) | Peer-reviewed |
| Insulin pens kept at 37°C (99°F) for 21 days worked the same as refrigerated pens (randomized trial) | PMID 36585035 | Strong. Insulin is sturdier than its label says. |
| **Heat-fragile items:** epinephrine auto-injectors (dose loss after prolonged extreme heat), glucose test strips (20–30% reading errors), insulin pump reservoirs, EMS drugs (lorazepam, succinylcholine) | See `report/Prescribed drug heat risks.md` | Lab and field studies |
| **No federal rule requires temperature monitoring for mailed prescriptions.** Missouri revised its mail-order rule in 2025 to address temperature. Drugs stored at room temperature have no shipping-temperature requirements. | [NC Health News](https://www.northcarolinahealthnews.org/2024/08/22/extreme-heat-mail-order-medicine-temperature-tracking/); [KCUR](https://www.kcur.org/health/2025-01-20/a-new-missouri-rule-tries-to-protect-your-mail-order-medications-from-extreme-cold-and-heat) | News reporting |
| Mail-order's share of US pharmacy volume is estimated at **8–25%** depending on the measure, and higher for specialty drugs | Various; estimates conflict | Low |
| **No study measured temperatures on porches specifically** | Search came up empty | **Gap.** This is something we could measure ourselves. |

**The standard we can use:** USP controlled room temperature is 20–25°C, with brief excursions to 15–30°C allowed. **Mean kinetic temperature (MKT)** is the industry formula that turns a fluctuating temperature history into one equivalent temperature for drug degradation. It's an established pharmaceutical metric, not something we invented.

---

## 2. The product: Heat-Safe Delivery

The idea: **check the weather before shipping, alert the patient at the doorstep, and estimate exposure after delivery.**

### A. Before shipping: a risk check at the pharmacy
- **Inputs:**
  - the drug's **heat-tolerance profile**, taken from our knowledge base and calibrated to evidence rather than the label (e.g., epinephrine and glucose strips sensitive; insulin pens tolerant to 37°C)
  - the National Weather Service forecast for the destination zip code over the delivery window
  - shipping speed (3-day vs. next-day)
  - the Heat Vulnerability Index for the destination
- **Output:** a risk tier and one recommended action:
  - ship as-is
  - **upgrade to next-day** (summer time out of range falls from 43% to 14%)
  - add insulated packaging or a cold pack
  - **reroute** to a local pharmacy or indoor locker for pickup
  - request a morning delivery window or require a signature
  - **hold until the heat passes,** if the patient has enough supply on hand

### B. At the door: alert the patient
- The carrier's "delivered" event triggers a text: *"Your epinephrine was delivered at 1:12 PM. It's 94°F outside. Please bring it inside within 30 minutes."*
- If the patient doesn't confirm, it **escalates** to a caregiver.

### C. After delivery: estimate exposure and advise
- Hourly NOAA temperatures from delivery until the patient confirms it's inside, plus a sun/shade factor, give an **estimated MKT and peak temperature**.
- Matched against the drug's profile, the result is:
  - **use as normal**
  - **check with your pharmacist**
  - **request a replacement** (pre-filled)
- It's deliberately cautious and labeled as an estimate. The porch sun factor is the weakest assumption, and the hardware demo (§3) is how we'd measure it.

### D. Pharmacy and health-system dashboard
- Today's heat-risk shipments on a map, with **the SBH catchment as the demo**.
- Which heat-vulnerable zip codes get the most heat-sensitive mail-order medicines.
- An audit log of each shipment's exposure, which is useful for states adding rules like Missouri's.

### How it scales
- It's an API that sits between a pharmacy's dispensing system and the carrier's tracking events.
- Every input it needs is a national dataset: NWS, NOAA, RxNorm, and our drug profiles.
- No new logistics infrastructure is required.

---

## 3. Hardware (doable in 2 days)

| Option | Effort | Demo value |
|---|---|---|
| **Package logger:** ESP32 + SHT31 or DHT22 sensor in a pill-bottle box, sending readings over Wi-Fi to the dashboard, which computes MKT live | About 3–5 hours if one of you has done Arduino/ESP32 before | **High.** Warm the box with a hair dryer or heat lamp ("it's sitting on the porch"). The dashboard's MKT climbs, the advice flips to "check with pharmacist," and the text alert fires. |
| **Temperature-indicator sticker** (thermochromic or irreversible) on the package | Buy only | Medium. A visible "this package got hot" mark. |
| **Measure a real porch:** leave the logger outside at someone's home before the demo | Overnight in November isn't representative | Low this time of year. Mention it as a pilot study you'd run next summer. |

**Rule:** build the software first. Add the hardware only once the dashboard works.

---

## 4. Talking point: what we quantify and what we don't

> "We quantify what can be measured: **the drug in the box.** Mean kinetic temperature is a pharmaceutical industry standard, and a $10 sensor can measure it. We don't quantify what can't: **the drug in the body.** No validated data exists to compute a safe dose at a given temperature, so the Heat Dose Compass shows direction, mechanism and what to monitor instead."

This answers the judge's dosing idea, shows judgment about where the evidence runs out, and ties both features together.
