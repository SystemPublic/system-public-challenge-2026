/**
 * Link to the real paper behind a finding. CLAUDE.md: every finding keeps its
 * system_id, pubmed_id and doi end to end, and a user must always be able to
 * click through. DOI is preferred; PubMed is the fallback; if neither exists we
 * say so plainly rather than hiding the finding's provenance.
 */
type Props = {
  systemId: string;
  pubmedId?: string | null;
  doi?: string | null;
  /** Visible link text. Defaults to "Read the paper". */
  children?: React.ReactNode;
  className?: string;
};

export function paperUrl(pubmedId?: string | null, doi?: string | null): string | null {
  if (doi) return `https://doi.org/${doi.replace(/^https?:\/\/(dx\.)?doi\.org\//, "")}`;
  if (pubmedId) return `https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(pubmedId)}/`;
  return null;
}

export function EvidenceLink({ systemId, pubmedId, doi, children, className = "" }: Props) {
  const href = paperUrl(pubmedId, doi);
  const ids = (
    <span className="font-mono text-[0.72rem] text-muted">
      system_id {systemId}
      {pubmedId ? ` · PMID ${pubmedId}` : ""}
      {doi ? ` · doi ${doi}` : ""}
    </span>
  );
  if (!href) {
    return (
      <span className={`inline-flex flex-col gap-0.5 ${className}`}>
        <span className="text-gap">No PubMed ID or DOI on this finding</span>
        {ids}
      </span>
    );
  }
  return (
    <span className={`inline-flex flex-col gap-0.5 ${className}`}>
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 font-medium text-drug underline decoration-drug/40 underline-offset-4 hover:decoration-drug"
      >
        {children ?? "Read the paper"}
        <span aria-hidden>↗</span>
        <span className="sr-only">(opens in a new tab)</span>
      </a>
      {ids}
    </span>
  );
}
