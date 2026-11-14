# Manual setup: what Rachel and Myra do by hand

Everything else is scripted. Put every key in `.env` (gitignored) and **never paste keys into chat**.

## What's needed (updated Sat 14 Nov)
- **Required:** only `SYSTEM_API_KEY` (have it).
- **Optional, already have:** `OPENFDA_API_KEY`, `ORS_API_KEY`. Both services also work without a key at our volume.
- **Not needed any more:**
  - **Twilio:** the demo SMS is simulated on the demo phone.
  - **Web Push / VAPID keys / HTTPS tunnel:** the demo push notification is simulated too (a labeled mock banner in the patient app).
  - **Supabase:** the app uses a local SQLite database; the clinic board polls every 2–3 seconds.
  - **Vercel:** the demo runs from a laptop; Devpost links the GitHub repo plus a video.
  - **Anthropic/Claude API:** Claude Code does extraction in-session.
  - **NYC Open Data token**, NWS, NOAA history, System Dataverse, CDS Hooks sandbox: no key or account.

## Installs on Rachel's machine
- Node 24, npm, Git and Python 3.14 are already installed.
- **Java is too old** (1.8, checked Sat morning). Synthea needs Java 17. Run:

```bash
winget install EclipseAdoptium.Temurin.17.JDK
```

Then open a new terminal and check that `java -version` says 17.

## Demo phone
- The phone opens the app from the laptop: run the dev server on the local network and visit `http://<laptop-ip>:3000/patient` on the phone.
- Phone and laptop must be on the **same Wi-Fi**. Venue Wi-Fi often blocks device-to-device traffic, so **have a phone hotspot ready** and connect the laptop to it.
- Windows may ask to allow Node through the firewall the first time; allow it on private networks.

## Decisions only you two can make
- Confirm the **15 drugs** (spec §8.7).
- Pick the **second demo city / health system** for the switcher (e.g. Phoenix or Houston).
- Pick the **demo phone**.
- Pick **one real past NYC heat wave** to replay. Claude can suggest dates from NOAA data.

## Checklist
- [x] System API key
- [x] openFDA key (optional)
- [x] OpenRouteService key (optional)
- [ ] Java 17 installed
- [ ] Demo phone picked and tested on the venue Wi-Fi (hotspot backup)
- [ ] 15 drugs confirmed; second city picked; heat wave picked
