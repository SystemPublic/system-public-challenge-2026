import { redirect } from "next/navigation";

/**
 * The landing experience is the standalone scrollytelling intro in
 * public/story.html. The scroll sections that used to live here are at
 * /overview.
 */
export default function HomePage() {
  redirect("/story.html");
}
