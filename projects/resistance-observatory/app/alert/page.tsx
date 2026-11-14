import type { Metadata } from "next";
import { loadPack, toClientPack } from "@/lib/alert/loadPack";
import { AlertTab } from "@/components/alert/AlertTab";

export const metadata: Metadata = { title: "Alert" };

/**
 * Alert: a researcher says where they care about the marker, and the tab
 * shows every moment the evidence moved. The data pack is read on the server
 * (at build time for the prerendered page) and handed to the client.
 */
export default async function AlertPage() {
  const pack = await loadPack();
  if (!pack) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 sm:px-6">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted">Alert</p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">The data pack is not installed</h1>
        <p className="mt-4 text-muted">
          This tab reads <code className="font-mono text-sm">k540e-data-pack/</code> at the repository root (genome counts, papers, graph findings, thresholds). It was not found
          when this page was built, so nothing is shown: no number here is ever invented.
        </p>
      </div>
    );
  }
  return <AlertTab pack={toClientPack(pack)} />;
}
