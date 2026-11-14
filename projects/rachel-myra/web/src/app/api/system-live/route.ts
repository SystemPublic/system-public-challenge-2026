// Live System layer (stub). Spec §8.5a role 6: the Drug Card will fetch live
// relationship counts and newest-evidence year from the System API through
// this cached route. No external calls yet.

export function GET() {
  return Response.json({
    status: "stub",
    connected: false,
    note: "System API not wired yet. No external calls are made.",
  });
}
