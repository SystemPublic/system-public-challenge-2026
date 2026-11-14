# Provenance: what the record shows about prediction before data

The method of this project rests on one order: each hypothesis is registered before the city data that test it are queried. This note sets out what the repository can show about that order, and what it cannot. The audit is `analyses/provenance/audit.py`. Its results are in `data/derived/provenance/registrations.csv` (one row per claim) and `summary.json`. It was run on 12 November 2026 at 23:11 UTC, at commit d7eb381.

## Three kinds of evidence

The repository holds three records of time, and they differ in who can check them.

1. **The registration's own time and hash.** Each registration stores `registered_at` and a SHA-256 hash of its content. The hash shows that a file has not been changed since it was hashed. It does not show when it was hashed, because the machine that wrote the file also wrote the time.
2. **Git commit times and order.** Commit order shows that a registration was committed before the outcome built on it. Commit times are also written by the committer's machine, and local history can be rewritten. Commit order is evidence for the team, not for an outside reader.
3. **GitHub push times.** GitHub records the time at which it received each push (`data/derived/provenance/github_pushes.json`, from the repository's activity API). These times are written by a third party. A commit that GitHub received at a given time existed at that time.

## Results

All 28 registration hashes match their content. No registration file was changed by any commit after the one that added it.

For each of the 27 claims with an outcome, the commit that added the registration is an ancestor of the commit that added the outcome. The interval between the two commits ranged from 3.9 to 28.3 minutes, with a median of 19.6 minutes. Eighteen outcomes were later revised after criticism, and the revisions are recorded in each outcome's `history` field.

Twenty-one outcomes give fetch times for their city sources. Seven of them cite at least one source fetched before the claim was registered. None of these early fetches is the outcome measure of the claim that cites it:

| Claim | Fetched before registration | Role in the test |
|---|---|---|
| heat-shootings, heat-ed-syndromic | NOAA GHCN-Daily, 12.9 min | the temperature series, which is the exposure; it holds no outcome |
| bridge-heat-shootings-ems, bridge-shot-ems-link | shootings (5ucz-vwe8, 833y-fsy8) and NOAA, 43 to 58 min | the data of the heat-shootings link, reused by design; the endpoint, EMS dispatches (76xm-jjuj), was fetched 3.8 min after registration |
| bridge-crz-injury-crashes | MTA zone geofence (srxy-5nxn), 3.5 min | the zone's boundary; the endpoint, crashes (h9gi-nx95), was fetched afterwards |
| construction2-rows-per-job-legacy-2000s | DOB permits (ipu4-2q9a), 32.7 min | the table fetched by the first round; the registration names it and lists what had been seen of it |
| construction2-rows-per-job-dobnow | DOB NOW filings (w9ak-ipjd), 38.0 min | as above; the permit rows that decide the claim (rbx6-tga4) were a new query |

Six outcomes give no fetch time for any city source, and the four first-round construction outcomes give the NOAA fetch date without a time. For these, only commit order supports the claim that the prediction came first.

## What the push times show

GitHub received three pushes on 12 November 2026:

| Push (UTC) | Head | Contents |
|---|---|---|
| 20:14:12 | 07b24a4 | the clients and the initial commits; no registrations |
| 23:06:47 | 8cba89c | all 27 earlier registrations and all 27 outcomes, together |
| 23:10:27 | d7eb381 | the registration of construction-2022-rush-units-2027 |

The 27 earlier claims reached GitHub in a single push, together with their outcomes. GitHub's record therefore shows that they existed by 23:06 UTC, but not that any registration came before its outcome. For these claims the order rests on commit order and fetch times, which an outside reader must take on trust.

The registration of construction-2022-rush-units-2027 is different. GitHub received it at 23:10:27 UTC on 12 November 2026. The data it names, a Housing Database release covering 30 June 2027, do not exist yet. Its order is checkable by anyone who can read the repository.

## Limits

The repository is private. The push record can be checked only by people with access to it. Making the repository public, or timestamping the registration hashes with a public service such as OpenTimestamps, would let anyone check the record. The OpenTimestamps calendars could not be reached from the environment in which this audit ran. The registration hashes are listed in `claims/registered/*.json`, so they can be timestamped later. A later timestamp proves only that a hash existed by that time.

The audit does not read the local cache (`data/cache/`), which is not in git. The cache's file times could extend the fetch-time check to the six outcomes that do not record fetch times. Those times are written by the local machine.

## Re-running

```bash
gh api "repos/jvnickerson/nyc-concordance/activity?per_page=100" \
  --jq '[.[] | select(.activity_type=="push") | {timestamp, ref, before, after}] | sort_by(.timestamp)' \
  > data/derived/provenance/github_pushes.json
python analyses/provenance/audit.py
```

The audit needs the full git history, not a shallow clone.
