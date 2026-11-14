import type { Metadata } from "next";
import { Suspense } from "react";
import { Inbox } from "@/components/messages/Inbox";

export const metadata: Metadata = { title: "Messages · Cool-Aid" };

// Clinician inbox: every patient conversation, newest activity first.
export default function MessagesPage() {
  return (
    <Suspense fallback={<div className="p-6 text-ink-muted">Loading messages…</div>}>
      <Inbox />
    </Suspense>
  );
}
