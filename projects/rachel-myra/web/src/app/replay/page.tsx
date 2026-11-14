import { redirect } from "next/navigation";

// The heat-day time-lapse now lives on the Map page as its second view.
export default function ReplayPage() {
  redirect("/map?view=hours");
}
