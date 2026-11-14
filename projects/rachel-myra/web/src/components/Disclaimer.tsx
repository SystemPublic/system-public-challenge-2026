export const DISCLAIMER = "Prototype with synthetic patients. Not medical advice.";

export function Disclaimer({ className = "" }: { className?: string }) {
  return (
    <p role="note" className={`text-ink-muted ${className || "text-sm"}`}>
      {DISCLAIMER}
    </p>
  );
}
