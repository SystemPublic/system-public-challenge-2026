import { Suspense } from "react";
import type { Metadata } from "next";
import { getBundle, getDistricts } from "@/lib/bundle";
import BridgesApp from "@/components/bridges/bridges-app";

export const metadata: Metadata = { title: "bridges" };

export default function BridgesPage() {
  const b = getBundle();
  const d = getDistricts();
  return (
    <div>
      <Suspense fallback={null}>
        <BridgesApp
          bridges={b.bridges}
          concepts={b.concepts}
          measures={b.measures}
          districts={d.districts}
          values={d.values}
        />
      </Suspense>
    </div>
  );
}
