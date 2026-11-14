"use client";

// Right-hand citation panel: resolves a PMID against OpenAlex and shows the
// study with its abstract and one-click links. Publisher sites block PDF
// embedding (X-Frame-Options), so instead of a frame that "refuses to
// connect", the panel surfaces the abstract and hands off to the OA copy.

import { useEffect, useState } from "react";

type Work = {
  display_name?: string;
  publication_year?: number;
  authorships?: { author?: { display_name?: string } }[];
  primary_location?: { source?: { display_name?: string | null } | null };
  doi?: string | null;
  best_oa_location?: { pdf_url?: string | null; landing_page_url?: string | null } | null;
  open_access?: { oa_status?: string; is_oa?: boolean };
  abstract_inverted_index?: Record<string, number[]> | null;
};

type State =
  | { kind: "loading" }
  | { kind: "ready"; work: Work }
  | { kind: "error"; message: string };

const MAILTO = "mrigsksum@gmail.com";

/** OpenAlex stores abstracts as word→positions maps; rebuild the sentence. */
function abstractFromInv(
  inv: Record<string, number[]> | null | undefined,
): string | null {
  if (!inv) return null;
  const words: string[] = [];
  for (const [word, positions] of Object.entries(inv)) {
    for (const p of positions) words[p] = word;
  }
  const text = words
    .filter((w) => w !== undefined && w !== null)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
  return text.length > 40 ? text : null;
}

export function CitationSidebar({
  pmid,
  onClose,
}: {
  pmid: string;
  onClose: () => void;
}) {
  // state initializes to loading; the parent remounts us per PMID (via key),
  // so no synchronous setState in the effect
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const ctrl = new AbortController();
    fetch(
      `https://api.openalex.org/works/pmid:https://pubmed.ncbi.nlm.nih.gov/${pmid}/?mailto=${MAILTO}`,
      { signal: ctrl.signal, headers: { Accept: "application/json" } },
    )
      .then((r) => {
        if (!r.ok) throw new Error(`OpenAlex returned ${r.status}`);
        return r.json() as Promise<Work>;
      })
      .then((work) => setState({ kind: "ready", work }))
      .catch((e: unknown) => {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setState({
          kind: "error",
          message: e instanceof Error ? e.message : "lookup failed",
        });
      });
    return () => ctrl.abort();
  }, [pmid]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const authors = (state.kind === "ready" ? state.work.authorships ?? [] : [])
    .map((a) => a.author?.display_name)
    .filter((n): n is string => Boolean(n));
  const authorsLabel =
    authors.length > 3 ? `${authors.slice(0, 3).join(", ")} et al.` : authors.join(", ");
  const venue = state.kind === "ready" ? state.work.primary_location?.source?.display_name : null;
  const oa = state.kind === "ready" ? state.work.best_oa_location : undefined;
  const doi = state.kind === "ready" ? state.work.doi?.replace("https://doi.org/", "") : null;
  const abstract =
    state.kind === "ready" ? abstractFromInv(state.work.abstract_inverted_index) : null;

  return (
    <div className="fixed inset-0 z-40" role="dialog" aria-label={`Citation PMID ${pmid}`}>
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <aside className="absolute right-0 top-0 flex h-full w-full max-w-[520px] flex-col overflow-y-auto border-l border-rule bg-paper shadow-2xl">
        <header className="flex items-baseline justify-between border-b border-rule px-5 py-3">
          <span className="label">citation · PMID {pmid}</span>
          <button
            onClick={onClose}
            aria-label="Close citation panel"
            className="font-sans text-[0.9rem] text-muted hover:text-ink"
          >
            ✕
          </button>
        </header>

        <div className="px-5 py-4">
          {state.kind === "loading" && (
            <p className="font-sans text-[0.8rem] text-muted">looking the study up on OpenAlex…</p>
          )}
          {state.kind === "error" && (
            <p className="font-sans text-[0.8rem] text-muted">
              couldn&apos;t reach OpenAlex ({state.message}).{" "}
              <a href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}/`} target="_blank" rel="noreferrer">
                open PubMed ↗
              </a>
            </p>
          )}
          {state.kind === "ready" && (
            <>
              <h3 className="text-[1.15rem] leading-snug font-medium">
                {state.work.display_name || `PMID ${pmid}`}
              </h3>
              <p className="mt-1.5 font-sans text-[0.75rem] text-muted">
                {authorsLabel}
                {venue ? ` · ${venue}` : ""}
                {state.work.publication_year ? ` · ${state.work.publication_year}` : ""}
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 font-sans text-[0.8rem]">
                {oa?.pdf_url && (
                  <a
                    href={oa.pdf_url}
                    target="_blank"
                    rel="noreferrer"
                    className="underline underline-offset-4 decoration-1 hover:decoration-2"
                  >
                    read the PDF ↗
                  </a>
                )}
                {doi && (
                  <a href={`https://doi.org/${doi}`} target="_blank" rel="noreferrer">
                    doi.org ↗
                  </a>
                )}
                <a href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}/`} target="_blank" rel="noreferrer">
                  PubMed ↗
                </a>
                {state.work.open_access?.oa_status && (
                  <span className="badge-gray">{state.work.open_access.oa_status}</span>
                )}
              </div>
              <div className="mt-4 border-t border-rule pt-4">
                <span className="label">abstract</span>
                {abstract ? (
                  <p className="mt-2 text-[0.92rem] leading-relaxed text-[color:var(--chart-ink-2)]">
                    {abstract}
                  </p>
                ) : (
                  <p className="mt-2 font-sans text-[0.8rem] text-muted">
                    No abstract in the OpenAlex record — the links above lead to
                    the full text (publishers don&apos;t allow their PDFs to be
                    embedded here).
                  </p>
                )}
              </div>
            </>
          )}
        </div>
      </aside>
    </div>
  );
}
