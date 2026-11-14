"use client";

import { useCallback, useEffect, useState } from "react";

type Message = { id: number; channel: string; body: string; created_at: string };
type Inbox = { demo_time: string; messages: Message[]; alert: { status: string } | null };

const POLL_MS = 2500;

// UI labels only; all message content comes from the server (panel_scores).
const L = {
  en: { push: "Simulated push notification", sms: "Simulated text messages", ok: "I'm OK", unwell: "I feel unwell", noAc: "No AC", sent: "Sent. Your clinic can see this.", none: "No messages yet.", from: "Your clinic" },
  es: { push: "Notificación simulada", sms: "Mensajes de texto simulados", ok: "Estoy bien", unwell: "Me siento mal", noAc: "No tengo aire acondicionado", sent: "Enviado. Su clínica puede verlo.", none: "Todavía no hay mensajes.", from: "Su clínica" },
};

const t = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export function Phone({ patientId, firstName, language, children, checkInNote, footer, badge }: {
  patientId: string; firstName: string; language: "en" | "es"; children?: React.ReactNode;
  /** One line above the check-in buttons (e.g. "We will check in with you today."). */
  checkInNote?: string | null;
  /** Rendered last: "Talk to your doctor or pharmacist." and the "More" disclosure. */
  footer?: React.ReactNode;
  /** Small label next to the name (e.g. "Synthetic patient"). */
  badge?: string;
}) {
  const l = L[language];
  const [inbox, setInbox] = useState<Inbox | null>(null);
  const [dismissed, setDismissed] = useState<number | null>(null);
  const [tapped, setTapped] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const r = await fetch(`/api/loop/inbox/${patientId}?lang=${language}`, { cache: "no-store" });
      setInbox(await r.json());
    } catch { /* keep last state; phone may be briefly off Wi-Fi */ }
  }, [patientId, language]);

  useEffect(() => {
    const first = setTimeout(refresh, 0);
    const id = setInterval(refresh, POLL_MS);
    return () => { clearTimeout(first); clearInterval(id); };
  }, [refresh]);

  const pushes = inbox?.messages.filter((m) => m.channel === "push") ?? [];
  const sms = inbox?.messages.filter((m) => m.channel === "sms") ?? [];
  const latestPush = pushes.at(-1);
  const showBanner = latestPush && latestPush.id !== dismissed;

  const tap = async (status: "ok" | "unwell" | "no_ac") => {
    await fetch("/api/loop/checkin", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ patientId, status }) });
    setTapped(status);
    refresh();
  };

  return (
    // Full-screen so the clinician header is hidden on the demo phone.
    <div className="fixed inset-0 z-50 overflow-auto bg-page text-patient-base leading-relaxed">
      <div className="mx-auto flex min-h-full max-w-md flex-col gap-5 px-4 py-5">
        <header>
          <div className="flex items-baseline justify-between gap-3">
            <h1 className="text-patient-lg font-semibold tracking-tight">{firstName}</h1>
            <span className="shrink-0 font-mono text-base text-muted-foreground">{inbox ? t(inbox.demo_time) : "—"}</span>
          </div>
          {badge && <p className="text-base text-muted-foreground">{badge}</p>}
        </header>

        {showBanner && (
          <button
            onClick={() => setDismissed(latestPush.id)}
            className="rounded-lg border border-border bg-card p-3 text-left shadow-md"
          >
            <div className="flex justify-between text-base font-semibold text-muted-foreground">
              <span>{l.push}</span>
              <span>{t(latestPush.created_at)}</span>
            </div>
            <p className="mt-1 line-clamp-2 font-semibold">{latestPush.body}</p>
          </button>
        )}

        {children}

        <section aria-label={l.sms} className="space-y-3">
          <h2 className="text-base font-semibold text-muted-foreground">{l.sms} · {l.from}</h2>
          {!sms.length && <p className="text-muted-foreground">{l.none}</p>}
          {sms.map((m) => (
            <div key={m.id} className="max-w-[90%] rounded-lg rounded-bl-sm border border-border bg-card p-3">
              <p>{m.body}</p>
              <span className="mt-1 block text-right text-sm text-muted-foreground">{t(m.created_at)}</span>
            </div>
          ))}
        </section>

        <section className="space-y-3 rounded-lg border border-border bg-card p-4">
          {checkInNote && <p>{checkInNote}</p>}
          {tapped && <p className="text-center font-semibold">{l.sent}</p>}
          <button onClick={() => tap("ok")} className="min-h-tap w-full rounded-lg bg-primary text-patient-lg font-semibold text-primary-foreground hover:bg-primary/90">
            {l.ok}
          </button>
          <div className="grid grid-cols-2 gap-3">
            <button onClick={() => tap("unwell")} className="min-h-tap rounded-lg border border-input bg-background px-2 font-semibold hover:bg-accent">
              {l.unwell}
            </button>
            <button onClick={() => tap("no_ac")} className="min-h-tap rounded-lg border border-input bg-background px-2 font-semibold hover:bg-accent">
              {l.noAc}
            </button>
          </div>
        </section>

        {footer}
      </div>
    </div>
  );
}
