/**
 * Schematic, original illustration: a parasite inside a red blood cell, drug
 * particles arriving, and the outcome. Not to scale, not a structural model.
 *
 * Encodings are never colour alone: the drug is a diamond shape, the mutation
 * is a triangle with a text label, the cleared parasite is dashed outline +
 * label, the persisting parasite is solid + label.
 */
type Props = { step: number; mutant: boolean; title: string };

const DRUG_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315];

export function ParasiteScene({ step, mutant, title }: Props) {
  const arrived = step >= 1;
  const outcome = step >= 2;
  const cleared = outcome && !mutant;
  const blunted = outcome && mutant;

  return (
    <svg
      viewBox="0 0 400 400"
      role="img"
      aria-labelledby={`${title}-t`}
      className="mx-auto w-full max-w-[460px] overflow-visible"
    >
      <title id={`${title}-t`}>{title}</title>
      {/* red blood cell */}
      <circle cx="200" cy="200" r="150" fill="var(--surface-2)" stroke="var(--line-strong)" strokeWidth="2" />
      <circle cx="200" cy="200" r="104" fill="none" stroke="var(--line)" strokeWidth="1.5" strokeDasharray="2 6" />
      <text x="200" y="38" textAnchor="middle" fontSize="15" fill="var(--muted)" fontFamily="var(--font-sans)">
        red blood cell
      </text>

      {/* parasite */}
      <g
        style={{
          transition: "opacity 700ms ease, transform 700ms ease",
          opacity: cleared ? 0.28 : 1,
          transformOrigin: "200px 200px",
          transform: cleared ? "scale(0.82)" : "none",
        }}
      >
        <circle
          cx="200"
          cy="200"
          r="44"
          fill="none"
          stroke="var(--fg)"
          strokeWidth={cleared ? 3 : 6}
          strokeDasharray={cleared ? "6 7" : undefined}
        />
        <circle cx="222" cy="182" r="10" fill="var(--fg)" />
        {mutant ? (
          <g>
            <path d="M200 140 l12 22 h-24 Z" fill="var(--signal)" stroke="var(--fg)" strokeWidth="1.5" />
            <line x1="212" y1="150" x2="262" y2="118" stroke="var(--signal)" strokeWidth="1.5" />
            <text x="266" y="116" fontSize="15" fontWeight="600" fill="var(--signal)" fontFamily="var(--font-sans)">
              mutation
            </text>
          </g>
        ) : null}
      </g>
      <text x="200" y="272" textAnchor="middle" fontSize="15" fill="var(--muted)" fontFamily="var(--font-sans)">
        parasite
      </text>

      {/* drug particles */}
      {DRUG_ANGLES.map((deg, i) => {
        const rad = (deg * Math.PI) / 180;
        const far = 205;
        const near = cleared ? 46 : blunted ? 92 : 62;
        const r = arrived ? near : far;
        const x = 200 + Math.cos(rad) * r;
        const y = 200 + Math.sin(rad) * r;
        return (
          <g
            key={deg}
            style={{
              transition: `transform 900ms cubic-bezier(.2,.7,.2,1) ${i * 40}ms, opacity 500ms`,
              transform: `translate(${x}px, ${y}px)`,
              opacity: arrived ? 1 : 0.55,
            }}
          >
            <rect x="-7" y="-7" width="14" height="14" transform="rotate(45)" fill="var(--drug)" />
          </g>
        );
      })}

      {/* legend */}
      <g transform="translate(24 372)" fontFamily="var(--font-sans)" fontSize="14" fill="var(--muted)">
        <rect x="0" y="-6" width="10" height="10" transform="rotate(45 5 -1)" fill="var(--drug)" />
        <text x="18" y="3">drug</text>
      </g>

      {/* outcome label */}
      {outcome ? (
        <g fontFamily="var(--font-sans)">
          <rect
            x="110"
            y="300"
            width="180"
            height="34"
            rx="17"
            fill="var(--bg)"
            stroke={cleared ? "var(--drug)" : "var(--signal)"}
            strokeWidth="2"
          />
          <text
            x="200"
            y="322"
            textAnchor="middle"
            fontSize="15"
            fontWeight="600"
            fill={cleared ? "var(--drug)" : "var(--signal)"}
          >
            {cleared ? "✓ parasite cleared" : "▲ drug works less well"}
          </text>
        </g>
      ) : null}
    </svg>
  );
}
