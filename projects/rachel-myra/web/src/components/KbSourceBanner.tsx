import type { KbSource } from "@/lib/kb";

/** Tells the viewer when they are not looking at the real knowledge base. */
export function KbSourceBanner({ source, file }: { source: KbSource; file: string | null }) {
  if (source === "knowledge_base") return null;
  const text =
    source === "mock_knowledge_base"
      ? `Showing mock data (${file}) for layout work. Not evidence.`
      : "Knowledge base not built yet: showing a one-drug layout placeholder. Not evidence.";
  return (
    <p role="status" className="rounded border border-verify-conflict-fg bg-verify-conflict-bg px-3 py-2 text-sm text-verify-conflict-fg">
      {text}
    </p>
  );
}
