/**
 * Send one alert email through Resend. Server-side only: the key never
 * reaches the browser. With no key the route reports "preview only".
 *
 * GET  -> { configured, from }
 * POST { to, subject, text, html? } -> { ok: true, id } | { ok: false, error, status }
 *
 * "Sent" means the provider returned a message id; nothing else counts.
 */
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

/** The key, under any of the names the team has used for it. Never logged, never sent to the browser. */
const resendKey = () => (process.env.RESEND_API_KEY || process.env.resend_api_key || process.env.RESEND_KEY || process.env.resend_key || "").trim();

const FROM = () => process.env.ALERT_FROM_EMAIL || "onboarding@resend.dev";
const EMAIL = /^[^\s@<>,;]+@[^\s@<>,;]+\.[^\s@<>,;]+$/;

export async function GET() {
  return NextResponse.json({ configured: Boolean(resendKey()), from: FROM() });
}

export async function POST(req: Request) {
  const key = resendKey();
  if (!key) {
    return NextResponse.json(
      { ok: false, previewOnly: true, error: "No email key is configured on this server. Preview only." },
      { status: 503 },
    );
  }

  let body: { to?: unknown; subject?: unknown; text?: unknown; html?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Request body was not JSON." }, { status: 400 });
  }
  const to = typeof body.to === "string" ? body.to.trim() : "";
  const subject = typeof body.subject === "string" ? body.subject.slice(0, 300) : "";
  const text = typeof body.text === "string" ? body.text.slice(0, 40000) : "";
  const html = typeof body.html === "string" ? body.html.slice(0, 120000) : undefined;
  if (!EMAIL.test(to)) {
    return NextResponse.json({ ok: false, error: "Enter one plain email address." }, { status: 400 });
  }
  if (!subject || !text) {
    return NextResponse.json({ ok: false, error: "Subject and text are required." }, { status: 400 });
  }

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from: FROM(), to, subject, text, ...(html ? { html } : {}) }),
      signal: AbortSignal.timeout(15000),
    });
    const raw = await res.text();
    let json: { id?: string; message?: string; name?: string } = {};
    try {
      json = JSON.parse(raw);
    } catch {
      /* provider sent non-JSON; fall through with raw text */
    }
    if (res.ok && typeof json.id === "string" && json.id) {
      return NextResponse.json({ ok: true, id: json.id, from: FROM(), to });
    }
    // Provider's own words, verbatim.
    return NextResponse.json(
      { ok: false, error: json.message || raw || `Provider returned HTTP ${res.status}`, status: res.status },
      { status: 502 },
    );
  } catch (e) {
    return NextResponse.json(
      { ok: false, error: `Could not reach the email provider: ${e instanceof Error ? e.message : String(e)}` },
      { status: 502 },
    );
  }
}
