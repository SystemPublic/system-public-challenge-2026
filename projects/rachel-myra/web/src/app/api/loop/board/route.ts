// GET: clinic board state (runs due escalation steps first). Polled every ~2.5 s.
import { connection } from "next/server";
import { boardState } from "@/lib/loop";

export async function GET() {
  await connection();
  return Response.json(boardState());
}
