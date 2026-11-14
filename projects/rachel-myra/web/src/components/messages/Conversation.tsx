"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { GroupChip, type RiskGroup } from "./groups";

interface Header {
  id: string;
  name: string;
  age: number;
  zip: string;
  language: string;
  group: RiskGroup;
  why: string[];
  optIn: boolean | null;
  phone: string | null;
  contacts: { id: string; name: string; relationship: string }[];
  templates: { kind: string; label: string; text: string }[];
}
interface Item {
  id: string;
  at: string;
  kind: "out" | "in" | "contact" | "clinic";
  channel: string;
  body: string;
  note: string | null;
  who: string;
}

const TIME = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit" });
const LANG: Record<string, string> = { en: "English", es: "Spanish" };

export function Conversation() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? "";
  const [header, setHeader] = useState<Header | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement | null>(null);
  const count = useRef(0);

  const load = useCallback(() => {
    if (!id) return;
    fetch(`/api/messages/${encodeURIComponent(id)}`, { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        if (!d.ok) return setError(d.error ?? "Not found");
        setHeader(d.header);
        setItems(d.items);
      })
      .catch(() => {});
  }, [id]);

  useEffect(() => {
    load();
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
  }, [load]);

  useEffect(() => {
    if (items.length !== count.current) {
      count.current = items.length;
      bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [items.length]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    setBusy(true);
    const r = await fetch(`/api/messages/${encodeURIComponent(id)}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ body: text }),
    }).then((x) => x.json()).catch(() => ({ ok: false }));
    setBusy(false);
    if (r.ok) {
      setDraft("");
      load();
    }
  }

  async function sendAlert() {
    setBusy(true);
    await fetch("/api/loop/alerts", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ patientIds: [id] }),
    }).catch(() => {});
    setBusy(false);
    load();
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-6">
        <Link href="/messages" className="text-sm underline">← All messages</Link>
        <p className="mt-4">Couldn&apos;t find patient {id}.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col px-4 py-4" style={{ minHeight: "calc(100vh - 140px)" }}>
      <Link href="/messages" className="text-sm text-ink-muted hover:underline">← All messages</Link>

      {/* Who you're talking to */}
      <header className="mt-2 rounded-tile border border-line bg-page p-4">
        {header ? (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold">{header.name}</h1>
              <GroupChip group={header.group} />
              <span className="text-sm text-ink-muted">
                {header.age} · ZIP {header.zip} · {LANG[header.language] ?? header.language} · synthetic patient
              </span>
            </div>
            {header.why.length > 0 && (
              <p className="mt-2 text-sm">
                <span className="font-semibold">Why: </span>
                {header.why.join(" · ")}
              </p>
            )}
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-muted">
              {header.phone && <span>Phone {header.phone}</span>}
              {header.contacts.length > 0 && (
                <span>Contact: {header.contacts.map((c) => `${c.name} (${c.relationship})`).join(", ")}</span>
              )}
              <Link href={`/phone/${header.id}`} className="underline">See their phone</Link>
            </div>
            {header.optIn === false && (
              <p className="mt-2 rounded-tile bg-[#fbe3d6] px-3 py-2 text-sm font-semibold text-[#a0410a]">
                Not signed up for heat texts. Call instead.
              </p>
            )}
          </>
        ) : (
          <p className="text-ink-muted">Loading…</p>
        )}
      </header>

      {/* Thread */}
      <div className="mt-3 flex flex-1 flex-col gap-2 rounded-tile bg-surface p-3" aria-live="polite">
        {items.length === 0 && <p className="m-auto py-8 text-center text-ink-muted">No messages yet. Send a text or a heat safety alert below.</p>}
        {items.map((m) => {
          if (m.kind === "clinic") {
            return (
              <div key={m.id} className="mx-auto max-w-[90%] rounded-full border border-line bg-page px-3 py-1 text-center text-xs text-ink-muted">
                {TIME.format(new Date(m.at))} · {m.body}
              </div>
            );
          }
          const mine = m.kind === "out" || m.kind === "contact";
          return (
            <div key={m.id} className={`flex flex-col ${mine ? "items-end" : "items-start"}`}>
              <div
                className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-[15px] leading-snug ${
                  m.kind === "out"
                    ? "bg-[#0e7c86] text-white"
                    : m.kind === "contact"
                      ? "border-2 border-[#0e7c86] bg-page"
                      : "border border-line bg-page"
                }`}
              >
                {m.body}
              </div>
              <span className="mt-0.5 text-[11px] text-ink-muted">
                {m.kind === "contact" ? `${m.who} · ` : m.kind === "in" ? "Patient tapped · " : ""}
                {m.channel} · {TIME.format(new Date(m.at))}
                {m.note && m.kind === "out" && m.note !== "clinician message" ? ` · ${m.note}` : ""} · simulated
              </span>
            </div>
          );
        })}
        <div ref={bottom} />
      </div>

      {/* Compose */}
      <div className="sticky bottom-0 mt-3 rounded-tile border border-line bg-page p-3">
        {header && header.templates.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {header.templates.map((t) => (
              <button
                key={t.kind}
                type="button"
                onClick={() => setDraft(t.text)}
                className="rounded-full border border-line-strong px-3 py-1 text-xs hover:bg-surface"
              >
                {t.label}
              </button>
            ))}
            <button
              type="button"
              onClick={sendAlert}
              disabled={busy}
              className="rounded-full border-2 border-[#a0410a] bg-[#fbe3d6] px-3 py-1 text-xs font-semibold text-[#a0410a] hover:opacity-90"
            >
              Send heat safety alert
            </button>
          </div>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(draft);
          }}
          className="flex gap-2"
        >
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(draft);
              }
            }}
            rows={2}
            placeholder={header ? `Text ${header.name.split(" ")[0]}…` : "Write a message…"}
            className="min-w-0 flex-1 resize-none rounded-tile border border-line-strong px-3 py-2 text-[15px]"
            aria-label="Message"
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            className="self-end rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-40"
          >
            Send
          </button>
        </form>
        <p className="mt-1 text-[11px] text-ink-muted">Simulated text. It also shows on the patient&apos;s demo phone. No dose advice by text.</p>
      </div>
    </div>
  );
}
