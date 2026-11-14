// The medicine's whole journey (spec §6.9, decision C5): the site is organized
// by these 6 stages. Each stage can be viewed as a map, graph or patient view.

export type StageId = "prescribe" | "dispense" | "store" | "take" | "watch" | "after";

export interface Stage {
  id: StageId;
  n: number;
  name: string;
  heat: string;
  clinician: string;
  patient: string;
  /** Main screens that serve this stage. */
  links: { href: string; label: string }[];
}

export const STAGES: Stage[] = [
  {
    id: "prescribe",
    n: 1,
    name: "Prescribe",
    heat: "Some medicines add heat risk.",
    clinician: "Alert in the health record during a heat forecast; review combinations before summer.",
    patient: "—",
    links: [
      { href: "/medicines", label: "Evidence Map" },
      { href: "/api/cds-hooks", label: "EHR alert (CDS Hooks)" },
    ],
  },
  {
    id: "dispense",
    n: 2,
    name: "Dispense / ship",
    heat: "Mail-order packages can get too hot on the way.",
    clinician: "Pharmacy holds heat-sensitive mail orders or ships insulated during heat alerts.",
    patient: "Bring the package in right away.",
    links: [{ href: "/readiness", label: "Heat-Wave Readiness" }],
  },
  {
    id: "store",
    n: 3,
    name: "Store at home",
    heat: "Insulin and epinephrine pens can lose strength; power cuts spoil refrigerated medicines.",
    clinician: "Refill reminders before heat season; power-outage plan.",
    patient: "Too warm? Here's what to do.",
    links: [{ href: "/patient", label: "My Medicine Cabinet" }],
  },
  {
    id: "take",
    n: 4,
    name: "Take it",
    heat: "Some medicines act stronger in heat, some weaker.",
    clinician: "Heat Dose Compass on every Drug Card.",
    patient: "One plain line on the label.",
    links: [{ href: "/medicines", label: "Drug Cards" }],
  },
  {
    id: "watch",
    n: 5,
    name: "Watch for warning signs",
    heat: "Warning signs of heat illness differ by medicine.",
    clinician: "Call list sorted by risk.",
    patient: "\"I feel dizzy\" button that reaches the clinic.",
    links: [
      { href: "/readiness", label: "Call-first list" },
      { href: "/patient", label: "Check-ins" },
    ],
  },
  {
    id: "after",
    n: 6,
    name: "After the heat wave",
    heat: "Refill and emergency-room surges after power cuts.",
    clinician: "Follow-up list; lab checks after the heat wave.",
    patient: "Check levels if your clinician advised it.",
    links: [{ href: "/readiness", label: "Follow-up list" }],
  },
];

export const STAGE_VIEWS = [
  { id: "map", label: "Map view" },
  { id: "graph", label: "Graph view" },
  { id: "patient", label: "Patient view" },
] as const;
