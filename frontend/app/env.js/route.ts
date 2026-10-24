// Serves /env.js, read by lib/api.ts's window.__ENV__ check. Unlike
// NEXT_PUBLIC_* vars (inlined into the client bundle at BUILD time), a
// server-side process.env read can happen at REQUEST time — so one built
// Docker image can be pointed at any backend via the API_BASE_URL
// container env var without rebuilding, the same problem the sibling
// Vite frontend solved with a shell-script-generated env.js; this is the
// Next.js-native way to get the same result.
//
// Without connection(), Cache Components treats this handler as static and
// bakes in whatever API_BASE_URL happens to be set at BUILD time — verified
// this the hard way: built with one value, started the server with a
// different one, and /env.js kept serving the build-time value.
// connection() is the documented way to force a route that doesn't use its
// own Request-time APIs (cookies/headers) to still wait for a real request
// before running, exactly this case.
import { connection } from "next/server";

export async function GET() {
  await connection();
  const apiBaseUrl = process.env.API_BASE_URL ?? "";
  const body = `window.__ENV__ = { API_BASE_URL: ${JSON.stringify(apiBaseUrl)} };`;
  return new Response(body, { headers: { "Content-Type": "application/javascript" } });
}
