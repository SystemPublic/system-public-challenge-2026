import { Suspense } from "react";
import type { Metadata } from "next";
import { getBundle, getDistricts } from "@/lib/bundle";
import ContestedApp from "@/components/contested-app";

export const metadata: Metadata = { title: "contested" };

export default function ContestedPage() {
  const b = getBundle();
  const d = getDistricts();
  return (
    <div className="mx-auto w-full max-w-[72rem] px-6 sm:px-10">
      <div className="mt-12 max-w-[62rem]">
        <h1 className="text-[clamp(1.8rem,4vw,2.6rem)] leading-tight font-normal">
          Where the city and the research{" "}
          <em>point apart</em>
        </h1>
      </div>
      <Suspense fallback={null}>
        <ContestedApp
          confirmations={b.confirmations}
          concepts={b.concepts}
          measures={b.measures}
          egos={b.egos}
          districts={d.districts}
          values={d.values}
        />
      </Suspense>
    </div>
  );
}
