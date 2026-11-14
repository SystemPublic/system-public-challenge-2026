// One guidance quote. French/German quotes show the English first, with a
// "Translated from …" note and the original one click away.

import { translateQuote } from "./translations";

export function GuidanceQuote({ sourceId, quote }: { sourceId: string; quote: string }) {
  const t = translateQuote(sourceId, quote);
  if (!t) return <q className="text-ink-muted">{quote}</q>;
  if (!t.english)
    return (
      <span className="text-ink-muted">
        <q lang={t.language === "French" ? "fr" : "de"}>{quote}</q>{" "}
        <span className="text-xs">(in {t.language}; no English translation yet)</span>
      </span>
    );
  return (
    <span className="text-ink-muted">
      <q>{t.english}</q>
      <details className="mt-0.5 text-xs">
        <summary className="cursor-pointer select-none underline decoration-dotted underline-offset-2">
          Translated from {t.language} · show original
        </summary>
        <q lang={t.language === "French" ? "fr" : "de"} className="mt-1 block italic">
          {quote}
        </q>
      </details>
    </span>
  );
}
