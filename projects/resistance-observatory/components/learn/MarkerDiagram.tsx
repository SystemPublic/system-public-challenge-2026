import type { BeforeAfterDiagram, Diagram, LadderDiagram } from "@/content/markers";

/**
 * Original SVG diagrams, built from a config object in content/markers.ts.
 * All labels are real <text>. Colour is never the only encoding: new vs
 * inherited alterations differ by fill AND border style AND a "+" prefix; the
 * altered element carries a triangle glyph and a text label.
 */
export function MarkerDiagram({ diagram }: { diagram: Diagram }) {
  return diagram.kind === "ladder" ? <Ladder d={diagram} /> : <BeforeAfter d={diagram} />;
}

const FONT = "var(--font-sans)";
const CHAR_W = 13.4; // approx px per char at fontSize 21 (bold)

function Ladder({ d }: { d: LadderDiagram }) {
  const W = 1110;
  const rungGap = 130;
  const top = 70;
  const n = d.rungs.length;
  const H = top + 60 + (n - 1) * rungGap + 70;
  const barX = 240;
  const barW = 640;
  const hasCarried = d.rungs.some((r) => r.alterations.some((a) => !a.isNew));
  const effX = barX + barW + 24;

  return (
    <figure>
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="ladder-t ladder-d" className="w-full min-w-[780px] xl:min-w-0">
          <title id="ladder-t">{d.title}</title>
          <desc id="ladder-d">
            {d.rungs
              .map(
                (r) =>
                  `${r.name}: ${r.alterations.map((a) => `${a.gene} ${a.codon}`).join(", ")}${r.residueChange ? ` (${r.residueChange.caption})` : ""}`,
              )
              .join(". ")}
            . Earlier rungs sit lower.
            {d.bracket ? ` ${d.bracket.lines.join(" ")}.` : ""}
          </desc>

          {/* rails */}
          <line x1={barX - 12} y1={top - 20} x2={barX - 12} y2={H - 30} stroke="var(--line-strong)" strokeWidth="4" />
          <line x1={barX + barW + 12} y1={top - 20} x2={barX + barW + 12} y2={H - 30} stroke="var(--line-strong)" strokeWidth="4" />

          {/* "accumulates" arrow */}
          <g>
            <line x1="40" y1={H - 40} x2="40" y2={top} stroke="var(--fg)" strokeWidth="3" />
            <path d={`M40 ${top - 14} l10 18 h-20 Z`} fill="var(--fg)" />
            <text
              x="0"
              y="0"
              transform={`translate(28 ${(H + top) / 2}) rotate(-90)`}
              textAnchor="middle"
              fontSize="18"
              fontFamily={FONT}
              fill="var(--muted)"
              letterSpacing="2"
            >
              ACCUMULATES
            </text>
          </g>

          {[...d.rungs].map((rung, idx) => {
            // idx 0 = first rung = lowest on screen
            const y = top + 60 + (n - 1 - idx) * rungGap;
            let cx = barX + 16;
            return (
              <g key={rung.name}>
                {/* rung bar */}
                <rect
                  x={barX - 12}
                  y={y - 36}
                  width={barW + 24}
                  height="72"
                  rx="10"
                  fill="var(--surface-2)"
                  stroke={rung.highlight ? "var(--signal)" : "var(--line-strong)"}
                  strokeWidth={rung.highlight ? 5 : 2}
                />
                {rung.highlight ? (
                  <text x="72" y={y + 46} fontSize="17" fontWeight="700" fontFamily={FONT} fill="var(--signal)">
                    ▶ this marker
                  </text>
                ) : null}
                {/* step number + name */}
                <text x="72" y={y - 6} fontSize="26" fontWeight="700" fontFamily={FONT} fill="var(--fg)">
                  {rung.name}
                </text>
                <text x="72" y={y + 22} fontSize="17" fontFamily={FONT} fill="var(--muted)">
                  rung {idx + 1} of {d.rungs.length}
                </text>
                {/* alteration chips */}
                {rung.alterations.map((a) => {
                  const label = `${a.isNew ? "+ " : ""}${a.gene} ${a.codon}`;
                  const w = label.length * CHAR_W + 26;
                  const x = cx;
                  cx += w + 10;
                  return (
                    <g key={label}>
                      <rect
                        x={x}
                        y={y - 22}
                        width={w}
                        height="44"
                        rx="22"
                        fill={a.isNew ? "var(--drug)" : "var(--bg)"}
                        stroke={a.isNew ? "var(--drug)" : "var(--line-strong)"}
                        strokeWidth="2"
                        strokeDasharray={a.isNew ? undefined : "5 5"}
                      />
                      <text
                        x={x + w / 2}
                        y={y + 7}
                        textAnchor="middle"
                        fontSize="21"
                        fontWeight={a.isNew ? 700 : 500}
                        fontFamily={FONT}
                        fill={a.isNew ? "var(--bg)" : "var(--muted)"}
                      >
                        {label}
                      </text>
                    </g>
                  );
                })}
                {/* amino-acid change: schematic residue glyphs only, no structure */}
                {rung.residueChange ? (
                  <g fontFamily={FONT}>
                    {(() => {
                      const rc = rung.residueChange;
                      const gy = y + 62;
                      const gx = barX + 30;
                      return (
                        <>
                          {/* from: circle */}
                          <circle cx={gx} cy={gy} r="15" fill="var(--bg)" stroke="var(--fg)" strokeWidth="2" />
                          <text x={gx} y={gy + 6} textAnchor="middle" fontSize="17" fontWeight="700" fill="var(--fg)">
                            {rc.from.letter}
                          </text>
                          <text x={gx + 19} y={gy - 6} fontSize="18" fontWeight="700" fill="var(--fg)">
                            {rc.from.charge}
                          </text>
                          {/* arrow */}
                          <line x1={gx + 40} y1={gy} x2={gx + 72} y2={gy} stroke="var(--fg)" strokeWidth="2" />
                          <path d={`M${gx + 80} ${gy} l-10 -6 v12 Z`} fill="var(--fg)" />
                          {/* to: square, so the two glyphs differ by shape as well as letter and sign */}
                          <rect x={gx + 92} y={gy - 15} width="30" height="30" rx="4" fill="var(--bg)" stroke="var(--fg)" strokeWidth="2" strokeDasharray="5 3" />
                          <text x={gx + 107} y={gy + 6} textAnchor="middle" fontSize="17" fontWeight="700" fill="var(--fg)">
                            {rc.to.letter}
                          </text>
                          <text x={gx + 127} y={gy - 6} fontSize="18" fontWeight="700" fill="var(--fg)">
                            {rc.to.charge}
                          </text>
                          <text x={gx + 156} y={gy + 6} fontSize="17" fill="var(--muted)">
                            {rc.caption}
                          </text>
                        </>
                      );
                    })()}
                  </g>
                ) : null}
                {/* effect on the drug */}
                {rung.effect ? (
                  // Sits inside the bar, after the chips.
                  <text x={cx + 8} y={y + 7} fontSize="19" fontFamily={FONT} fill="var(--fg)">
                    {rung.effect}
                  </text>
                ) : (
                  <g>
                    <text x={effX} y={y - 4} fontSize="16" fontFamily={FONT} fill="var(--gap)" fontWeight="600">
                      Effect on drug:
                    </text>
                    <text x={effX} y={y + 18} fontSize="16" fontFamily={FONT} fill="var(--gap)">
                      pending review
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* named combination spanning rungs: bracket + text label */}
          {d.bracket
            ? (() => {
                const yOf = (idx: number) => top + 60 + (n - 1 - idx) * rungGap;
                const yTop = yOf(d.bracket.to) - 36;
                const yBot = yOf(d.bracket.from) + 36;
                const bx = barX + barW + 26;
                const mid = (yTop + yBot) / 2;
                return (
                  <g>
                    <path
                      d={`M${bx} ${yTop} h14 V${yBot} h-14`}
                      fill="none"
                      stroke="var(--fg)"
                      strokeWidth="3"
                    />
                    {d.bracket.lines.map((line, i) => (
                      <text
                        key={line}
                        x={bx + 28}
                        y={mid - (d.bracket!.lines.length - 1) * 11 + i * 22 + 6}
                        fontSize={i === 0 ? 19 : 16}
                        fontWeight={i === 0 ? 700 : 400}
                        fontFamily={FONT}
                        fill={i === 0 ? "var(--fg)" : "var(--muted)"}
                      >
                        {line}
                      </text>
                    ))}
                  </g>
                );
              })()
            : null}

          {/* legend */}
          <g transform={`translate(${barX} 26)`} fontFamily={FONT} fontSize="16" fill="var(--muted)">
            <rect x="0" y="-14" width="44" height="22" rx="11" fill="var(--drug)" />
            <text x="22" y="2" textAnchor="middle" fontSize="13" fontWeight="700" fill="var(--bg)">+</text>
            <text x="54" y="2">new at this rung</text>
            {hasCarried ? (
              <>
                <rect x="210" y="-14" width="44" height="22" rx="11" fill="var(--bg)" stroke="var(--line-strong)" strokeWidth="2" strokeDasharray="5 5" />
                <text x="264" y="2">carried from the rung below</text>
              </>
            ) : null}
          </g>
        </svg>
      </div>
      <figcaption className="mt-4 max-w-3xl text-sm text-muted">{d.caption}</figcaption>
    </figure>
  );
}

function BeforeAfter({ d }: { d: BeforeAfterDiagram }) {
  const panel = (x: number, altered: boolean) => {
    const heading = altered ? d.after.heading : d.before.heading;
    const note = altered ? d.after.note : d.before.note;
    const cx = x + 230;
    const cy = 250;
    const drugs = altered
      ? [
          [-150, -60],
          [-170, 40],
          [150, -90],
          [160, 60],
          [-120, 120],
        ]
      : [
          [-62, -30],
          [-58, 34],
          [60, -36],
          [64, 30],
          [0, -68],
        ];
    return (
      <g>
        <rect x={x} y="20" width="460" height="440" rx="18" fill="var(--surface)" stroke="var(--line)" strokeWidth="2" />
        <text x={x + 28} y="66" fontSize="28" fontWeight="700" fontFamily={FONT} fill="var(--fg)">
          {altered ? "▲ " : "✓ "}
          {heading}
        </text>
        <text x={x + 28} y="96" fontSize="18" fontFamily={FONT} fill="var(--muted)">
          {note}
        </text>
        {/* protein element — highlighted in both panels */}
        <rect
          x={cx - 70}
          y={cy - 50}
          width="140"
          height="100"
          rx="40"
          fill={altered ? "url(#hatch)" : "var(--surface-2)"}
          stroke="var(--fg)"
          strokeWidth="4"
        />
        <rect x={cx - 82} y={cy - 62} width="164" height="124" rx="50" fill="none" stroke="var(--gap)" strokeWidth="3" strokeDasharray="8 6" />
        <text x={cx} y={cy + 92} textAnchor="middle" fontSize="20" fontWeight="600" fontFamily={FONT} fill="var(--fg)">
          {d.element}
        </text>
        {altered ? (
          <g>
            <path d={`M${cx + 70} ${cy - 70} l16 28 h-32 Z`} fill="var(--signal)" stroke="var(--fg)" strokeWidth="2" />
            <text x={cx + 94} y={cy - 46} fontSize="20" fontWeight="700" fontFamily={FONT} fill="var(--signal)">
              altered
            </text>
          </g>
        ) : null}
        {drugs.map(([dx, dy], i) => (
          <rect
            key={i}
            x={cx + dx - 11}
            y={cy + dy - 11}
            width="22"
            height="22"
            transform={`rotate(45 ${cx + dx} ${cy + dy})`}
            fill={altered ? "none" : "var(--drug)"}
            stroke="var(--drug)"
            strokeWidth="3"
          />
        ))}
        <text x={x + 28} y="430" fontSize="18" fontFamily={FONT} fill="var(--muted)">
          {altered ? "◇ drug effect blunted (schematic)" : "◆ drug effect intact (schematic)"}
        </text>
      </g>
    );
  };

  return (
    <figure>
      <div className="overflow-x-auto">
        <svg viewBox="0 0 960 480" role="img" aria-labelledby="ba-t" className="w-full min-w-[640px]">
          <title id="ba-t">{d.title}</title>
          <defs>
            <pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width="10" height="10" fill="var(--signal-soft)" />
              <line x1="0" y1="0" x2="0" y2="10" stroke="var(--signal)" strokeWidth="4" />
            </pattern>
          </defs>
          {panel(0, false)}
          {panel(500, true)}
        </svg>
      </div>
      <figcaption className="mt-4 max-w-3xl text-sm text-muted">{d.caption}</figcaption>
    </figure>
  );
}
