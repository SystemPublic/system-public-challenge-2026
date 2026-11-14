import type { Metadata } from "next";
import { Suspense } from "react";
import { Conversation } from "@/components/messages/Conversation";

export const metadata: Metadata = { title: "Conversation · Cool-Aid" };

// One patient's conversation with the clinic. The id is read on the client (useParams).
export default function ConversationPage() {
  return (
    <Suspense fallback={<div className="p-6 text-ink-muted">Loading conversation…</div>}>
      <Conversation />
    </Suspense>
  );
}
