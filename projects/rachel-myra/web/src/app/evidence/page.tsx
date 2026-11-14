import type { Metadata } from "next";
import { BucketEvidenceChart, type BucketEvidenceRow } from "@/components/BucketEvidenceChart";
import { Dash } from "@/components/badges";
import { KbSourceBanner } from "@/components/KbSourceBanner";
import { Placeholder } from "@/components/Placeholder";
import { listProcessedFiles, loadKb, primaryBucket, readProcessedJson } from "@/lib/kb";
import { BADGES, BUCKET_ORDER, BUCKETS } from "@/lib/ui";
import type { BadgeCode } from "@lib/types/knowledge-base.ts";

export const metadata: Metadata = { title: "Evidence (nerd stats) · Cool-Aid" };

interface KappaFile {
  method?: string;
  core?: Record<string, { kappa?: number; percent_agreement?: number } | number>;
}

export default function EvidencePage() {
  const { kb, source, file } = loadKb();
  const drugs = kb.drugs;

  const rows: BucketEvidenceRow[] = BUCKET_ORDER.map((b) => {
    const ds = drugs.filter((d) => primaryBucket(d) === b);
    return {
      bucket: BUCKETS[b].label,
      strong: ds.filter((d) => d.evidence?.meter === "strong").length,
      some: ds.filter((d) => d.evidence?.meter === "some").length,
      early: ds.filter((d) => d.evidence?.meter === "early_signs").length,
    };
  });

  const claims = drugs.flatMap((d) => d.claims ?? []);
  const badgeCounts = (Object.keys(BADGES) as BadgeCode[]).map((code) => ({
    code,
    n: claims.filter((c) => c.badge_code === code).length,
  }));

  const kappa = readProcessedJson<KappaFile>("guidance_kappa.json");
  const kappaRows = kappa?.core
    ? Object.entries(kappa.core).filter(
        (e): e is [string, { kappa?: number; percent_agreement?: number }] => typeof e[1] === "object",
      )
    : [];
  const files = listProcessedFiles();

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold">Evidence: methods and receipts</h1>
        <p className="text-ink-muted">For the curious: how every number on this site was found and checked.</p>
      </header>
      <KbSourceBanner source={source} file={file} />

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-tile border border-line p-4">
          <h2 className="text-lg font-bold">Knowledge base</h2>
          <dl className="mt-2 grid grid-cols-2 gap-1 text-sm">
            <dt className="text-ink-muted">File</dt>
            <dd>{file ?? "inline fallback"}</dd>
            <dt className="text-ink-muted">Schema version</dt>
            <dd>{kb.schema_version || <Dash />}</dd>
            <dt className="text-ink-muted">Build id</dt>
            <dd className="truncate">{kb.build_id || <Dash />}</dd>
            <dt className="text-ink-muted">Medicines</dt>
            <dd>{drugs.length}</dd>
            <dt className="text-ink-muted">Claims (all)</dt>
            <dd>{claims.length}</dd>
          </dl>
        </div>
        <div className="min-w-0 rounded-tile border border-line p-4">
          <h2 className="text-lg font-bold">Medicines by action and evidence</h2>
          <div className="max-w-full overflow-x-auto">
            <BucketEvidenceChart rows={rows} />
          </div>
        </div>
      </section>

      <section className="rounded-tile border border-line p-4">
        <h2 className="text-lg font-bold">Verification badges</h2>
        <p className="text-sm text-ink-muted">Automated checks, no human review. &ldquo;?&rdquo; claims are never shown on labels.</p>
        <ul className="mt-2 flex flex-wrap gap-3">
          {badgeCounts.map(({ code, n }) => (
            <li key={code} className={`rounded px-3 py-2 text-sm ${BADGES[code].cls}`}>
              <span className="font-bold">{BADGES[code].symbol}</span> {BADGES[code].label.split(":")[0]}:{" "}
              <span className="font-bold">{claims.length ? n : "—"}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-tile border border-line p-4">
        <h2 className="text-lg font-bold">Guidance coding agreement (Cohen&apos;s kappa)</h2>
        {kappaRows.length === 0 ? (
          <Dash what="data/processed/guidance_kappa.json not found" />
        ) : (
          <>
            <p className="text-sm text-ink-muted">{kappa?.method}</p>
            <table className="mt-2 text-sm">
              <thead>
                <tr className="text-left">
                  <th className="pr-6">Field</th>
                  <th className="pr-6">Kappa</th>
                  <th>Agreement</th>
                </tr>
              </thead>
              <tbody>
                {kappaRows.map(([k, v]) => (
                  <tr key={k}>
                    <td className="pr-6">{k.replace(/_/g, " ")}</td>
                    <td className="pr-6">{v.kappa ?? "—"}</td>
                    <td>{v.percent_agreement != null ? `${v.percent_agreement}%` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-1 text-xs text-ink-muted">Source: data/processed/guidance_kappa.json (core set)</p>
          </>
        )}
      </section>

      <section className="rounded-tile border border-line p-4">
        <h2 className="text-lg font-bold">Scoring formula</h2>
        <p className="text-sm">{kb.evidence_model?.formula || <Dash />}</p>
        <p className="mt-1 text-sm text-ink-muted">{kb.evidence_model?.flag_change_rules}</p>
      </section>

      <div className="grid gap-3 md:grid-cols-2">
        <Placeholder title="Evidence funnel: searched → screened → included" spec="§4.7" />
        <Placeholder title="Graph audit: in System / extracted / correct / mislabeled" spec="§5 #17" />
        <Placeholder title="8-step evidence tiers" spec="§9" />
        <Placeholder title="Live System API status" spec="§8.5a role 6">
          Stub at /api/system-live.
        </Placeholder>
        <Placeholder title="Escalation-timing assumptions" spec="§4.4a" />
        <Placeholder title="Known limitations and confounding" spec="§4.7">
          Includes the do-not-disturb caveat: a web app cannot break through do-not-disturb; that needs a native app
          (iOS Critical Alerts entitlement, Android DND-bypass channel).
        </Placeholder>
      </div>

      <section className="rounded-tile border border-line p-4">
        <h2 className="text-lg font-bold">Data files on disk (data/processed/)</h2>
        {files.length === 0 ? (
          <Dash />
        ) : (
          <ul className="mt-2 columns-1 text-xs sm:columns-2 lg:columns-3">
            {files.map((f) => (
              <li key={f.name}>
                {f.name} <span className="text-ink-muted">({Math.max(1, Math.round(f.bytes / 1024))} KB)</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
