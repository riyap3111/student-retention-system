// Written by /env.js (app/env.js/route.ts) at request time; read by
// lib/api.ts. Absent in local `npm run dev` (no container), where api.ts
// falls back to NEXT_PUBLIC_API_BASE_URL / its own default.
interface Window {
  __ENV__?: { API_BASE_URL?: string };
}
