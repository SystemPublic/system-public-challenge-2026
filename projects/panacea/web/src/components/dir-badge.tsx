// SPG expected-direction pill: what the majority of the pair's signable
// published effects imply for the city correlation (port of the dashboard
// branch's dirBadge). Rendered in the confirmations/contested tables and the
// row-popup evidence.

import type { ConfirmationRow } from "@/lib/bundle";

export function DirBadge({ dir, nsigns }: { dir: number | null; nsigns: number }) {
  if (dir === 1) {
    return (
      <span
        className="dir-pill up"
        title={`majority of the ${nsigns} signable effects imply positive dependence between the two variables`}
      >
        SPG: ↑ positive
      </span>
    );
  }
  if (dir === -1) {
    return (
      <span
        className="dir-pill down"
        title={`majority of the ${nsigns} signable effects imply negative (protective) dependence between the two variables`}
      >
        SPG: ↓ negative
      </span>
    );
  }
  return (
    <span
      className="badge-gray"
      title="fewer than 3 signable effects or mixed signs: direction ambiguous"
    >
      direction ambiguous
    </span>
  );
}

/** How the city ρ compares to the SPG direction (used in the row popup). */
export function AgreeBadge({ agree }: { agree: ConfirmationRow["agree"] }) {
  if (agree === "same") {
    return <span className="dir-pill up">same direction</span>;
  }
  if (agree === "opposite") {
    return <span className="dir-pill down">opposite direction</span>;
  }
  return null;
}
