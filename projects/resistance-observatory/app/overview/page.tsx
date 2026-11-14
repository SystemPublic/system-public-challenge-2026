"use client";

import { useSelection } from "@/lib/selection";
import { Hero } from "@/components/home/Hero";
import { Scale } from "@/components/home/Scale";
import { StepScene } from "@/components/home/StepScene";
import { ParasiteScene } from "@/components/home/ParasiteScene";
import { Gap } from "@/components/home/Gap";
import { TabCards } from "@/components/home/TabCards";

export default function OverviewPage() {
  const { hrefWithSelection } = useSelection();
  return (
    <>
      <Hero learnHref={hrefWithSelection("/learn")} />
      <Scale />
      <StepScene
        id="works"
        eyebrow="The drug works"
        tone="drug"
        heading="A drug finds the parasite."
        steps={[
          "Malaria is caused by Plasmodium parasites, most dangerously P. falciparum.",
          "An antimalarial drug reaches the parasite.",
          "The drug works, and the parasite is cleared.",
        ]}
        visual={(s) => <ParasiteScene step={s} mutant={false} title="Schematic: drug acting on a parasite" />}
      />
      <StepScene
        id="mutation"
        eyebrow="The turn"
        tone="signal"
        heading={
          <>
            Same drug. <span className="text-signal">One mutation.</span>
          </>
        }
        steps={[
          "The same parasite — now carrying a specific mutation in one of its genes.",
          "The same drug reaches it.",
          "Specific mutations reduce how well particular drugs work. Those mutations are tracked as resistance markers.",
        ]}
        note="This illustrates how resistance mutations work in general. It is not the mechanism of K540E specifically."
        visual={(s) => <ParasiteScene step={s} mutant title="Schematic: drug reaching a parasite that carries a mutation" />}
      />
      <Gap />
      <TabCards />
    </>
  );
}
