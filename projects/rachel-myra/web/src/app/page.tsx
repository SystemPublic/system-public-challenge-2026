import type { Metadata } from "next";
import { Clock, Map as MapIcon, Smartphone } from "lucide-react";
import { Hero195 } from "@/components/ui/hero-195";
import { ClinicianMap } from "@/components/map/ClinicianMap";
import { FILES, loadMapPatients } from "@/components/map/data";
import PatientPlanMap from "@/components/map/PatientPlanMap";
import { Timelapse } from "@/components/replay/Timelapse";
import { loadReplay } from "@/lib/replay";

export const metadata: Metadata = { title: "Cool-Aid" };

// Home: hero with the live clinic map as the default tab, one patient's plan second, and the heat-day time-lapse third.
export default function Home() {
  const patients = loadMapPatients();
  const replay = loadReplay();
  const clinicMap = patients.length ? (
    <div className="bg-white p-2 sm:p-3">
      <ClinicianMap patients={patients} files={{ panel: FILES.panel, patients: FILES.patients }} mapHeight="min(64vh, 620px)" />
    </div>
  ) : (
    <p className="p-4 text-sm">Patients go here: {FILES.panel} and {FILES.patients} (not found).</p>
  );
  return (
    <Hero195
      title="Who is at risk in the heat, and where to cool off"
      description="Each person icon is a patient's home. Click one or a neighborhood."
      className="[&_h1]:text-2xl sm:[&_h1]:text-4xl [&_h1+p]:mt-2 [&_h1+p]:text-base"
      defaultTab="map"
      tabs={[
        { value: "map", label: "Clinic map", icon: <MapIcon className="size-4" aria-hidden />, content: clinicMap },
        { value: "patient", label: "A patient's plan", icon: <Smartphone className="size-4" aria-hidden />, content: <div className="bg-white p-2 sm:p-3"><PatientPlanMap patientId="S01" variant="patient" height={420} /></div> },
        { value: "hours", label: "Hour by hour", icon: <Clock className="size-4" aria-hidden />, content: replay ? <div className="bg-white p-2 sm:p-3"><Timelapse data={replay} embedded /></div> : <p className="p-6 text-sm text-muted-foreground">Hour-by-hour replay needs data/processed/replay_heatwave_hourly.csv.</p> },
      ]}
    />
  );
}
