// GET: every patient's conversation summary (latest activity first on the client).
import { connection } from "next/server";
import { conversations } from "@/lib/conversation";
import { boardState } from "@/lib/loop";

export async function GET() {
  await connection();
  boardState(); // runs any due escalation steps so the list is current
  return Response.json({ conversations: conversations() });
}
