import { Suspense } from "react";
import type { Metadata } from "next";
import { getBundle, getDistricts } from "@/lib/bundle";
import ConfirmationsApp from "@/components/confirmations-app";

export const metadata: Metadata = { title: "confirmations" };

export default function Home() {
  const b = getBundle();
  const d = getDistricts();
  return (
    <div className="mx-auto w-full max-w-[72rem] px-6 sm:px-10">
      <div className="mt-12 max-w-[62rem]">
        <h1 className="text-[clamp(1.8rem,4vw,2.6rem)] leading-tight font-normal">
          What research and the data <em>confirm</em>, <em>contest</em>,
          or <em>bridge</em>
        </h1>
      </div>
      <Suspense fallback={null}>
        <ConfirmationsApp
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
