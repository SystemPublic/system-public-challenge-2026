import { fmtRho } from "@/lib/format";

/** ρ value as a bordered pill; ⚠ marks checks that used a modeled measure. */
export function RhoPill({
  rho,
  mod,
  digits = 2,
}: {
  rho: number | null | undefined;
  mod?: boolean;
  digits?: number;
}) {
  if (rho === null || rho === undefined) {
    return <span className="badge-gray">citywide-only</span>;
  }
  return (
    <>
      <span className={`rho-pill ${rho >= 0 ? "pos" : "neg"}`}>{fmtRho(rho, digits)}</span>
      {mod && (
        <span
          className="rho-pill warn"
          title="this check used a modeled burden measure: treat as neighborhood structure, not observed outcome"
        >
          ρ⚠
        </span>
      )}
    </>
  );
}
