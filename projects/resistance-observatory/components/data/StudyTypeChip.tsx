import { Chip } from "@/components/Chip";

/**
 * A finding's study type, exactly as the graph's Studies table records it.
 * When the graph records none, it says so; it never guesses.
 */
export function StudyTypeChip({ studyType }: { studyType: string | null }) {
  return studyType ? (
    <Chip tone="drug" glyph="square" title="Study type as recorded in the System Public Graph">
      Study type: {studyType}
    </Chip>
  ) : (
    <Chip tone="neutral" title="The System Public Graph records no study type for this finding's study">
      Study type: type not recorded
    </Chip>
  );
}
