import { GRAPH_SNAPSHOT_DATE, GRAPH_VERSION } from "@/lib/stats";

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto max-w-6xl px-4 py-10 text-sm text-muted sm:px-6 grid gap-4 md:grid-cols-2">
        <p>
          A hackathon prototype. Evidence comes from a frozen snapshot of the System
          Public Graph (v{String(GRAPH_VERSION.value)},{" "}
          {String(GRAPH_SNAPSHOT_DATE.value)}), CC BY-NC 4.0. The alert demo
          replays real publication history; it is not live surveillance.
        </p>
        <p className="md:text-right">
          Not clinical guidance. Not affiliated with or endorsed by WHO. A marker
          association does not establish treatment failure for any patient.
        </p>
      </div>
    </footer>
  );
}
