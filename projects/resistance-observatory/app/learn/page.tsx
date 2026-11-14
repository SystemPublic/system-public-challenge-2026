import { LearnView } from "@/components/learn/LearnView";
import { StructureFigure } from "@/components/learn/StructureFigure";

/**
 * Learn. The page body is a client component (it reads the shared selection);
 * the structural figure is rendered on the server and passed in, because it
 * checks at build time that its image files exist.
 */
export default function LearnPage() {
  return <LearnView structureFigure={<StructureFigure />} />;
}
