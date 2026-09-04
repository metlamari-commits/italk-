// i-talk.gr — AI translation Cloudflare Worker
//
// Called from https://i-talk.gr/ when a user asks for a term
// that is not in the static glossary. Proxies to Anthropic Claude
// so the API key never leaves Cloudflare.
//
// Deploy: paste this file into a Cloudflare Worker named
// "italk-translate", add ANTHROPIC_API_KEY as an encrypted secret,
// then update the WORKER_URL constant in index.html.

const ALLOWED_ORIGINS = new Set([
  'https://i-talk.gr',
  'https://www.i-talk.gr',
  'http://localhost:8765',
  'http://127.0.0.1:8765'
]);

const MODEL = 'claude-haiku-4-5-20251001';
const MAX_TERM_LEN = 200;
const MAX_TOKENS = 600;

function corsHeaders(origin) {
  const allow = ALLOWED_ORIGINS.has(origin) ? origin : 'https://i-talk.gr';
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400'
  };
}

function jsonResponse(obj, status, origin) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...corsHeaders(origin)
    }
  });
}

function buildPrompt(term, sourceLang) {
  return `You translate refugee/asylum/humanitarian interpretation terminology used by interpreters in Greek reception centres, asylum offices, and medical/legal contexts.

Input term (source language: ${sourceLang}): "${term}"

Task:
1. Translate the term into all 5 languages: Greek (el), English (en), Arabic (ar, proper script), Farsi/Persian (fa, proper script), French (fr).
2. Provide a short one-sentence definition in Greek AND in English.
3. Classify the term into one of these domains: "status" (legal status), "procedure" (asylum procedure), "reception" (reception & identification), "vulnerable" (vulnerability), "legal" (general legal), "medical", "detention", "return", "family", "integration", "communication" (interpretation/communication), "documentation", or "general" if none fits.
4. If the term is nonsense, offensive, or clearly outside asylum/humanitarian scope, set "translations" to null and put a short reason in "note".

Return ONLY valid JSON, no markdown, no code fences, no extra text:
{
  "translations": {
    "el": "...",
    "en": "...",
    "ar": "...",
    "fa": "...",
    "fr": "..."
  },
  "definition_el": "...",
  "definition_en": "...",
  "category": "one of the domain slugs above",
  "note": null
}`;
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (request.method === 'GET') {
      return jsonResponse({ ok: true, service: 'italk-translate', model: MODEL }, 200, origin);
    }
    if (request.method !== 'POST') {
      return jsonResponse({ error: 'Method not allowed' }, 405, origin);
    }
    if (!ALLOWED_ORIGINS.has(origin)) {
      return jsonResponse({ error: 'Origin not allowed', origin }, 403, origin);
    }
    if (!env.ANTHROPIC_API_KEY) {
      return jsonResponse({ error: 'Worker not configured: missing ANTHROPIC_API_KEY secret' }, 500, origin);
    }

    let body;
    try {
      body = await request.json();
    } catch (e) {
      return jsonResponse({ error: 'Invalid JSON body' }, 400, origin);
    }

    const term = String(body.term || '').trim().slice(0, MAX_TERM_LEN);
    const sourceLang = String(body.sourceLang || 'el').slice(0, 5);
    if (!term) {
      return jsonResponse({ error: 'Missing term' }, 400, origin);
    }

    // Optional caching by term+source
    const cacheKey = new Request(
      new URL(request.url).origin + '/__cache?t=' + encodeURIComponent(term.toLowerCase()) + '&s=' + sourceLang,
      { method: 'GET' }
    );
    const cache = caches.default;
    const cached = await cache.match(cacheKey);
    if (cached) {
      const hit = new Response(cached.body, cached);
      hit.headers.set('X-Cache', 'HIT');
      // Fix CORS in case cached origin differs
      const h = corsHeaders(origin);
      Object.entries(h).forEach(([k, v]) => hit.headers.set(k, v));
      return hit;
    }

    let apiRes;
    try {
      apiRes = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': env.ANTHROPIC_API_KEY,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: MAX_TOKENS,
          messages: [{ role: 'user', content: buildPrompt(term, sourceLang) }]
        })
      });
    } catch (e) {
      return jsonResponse({ error: 'Upstream fetch failed', detail: String(e) }, 502, origin);
    }

    if (!apiRes.ok) {
      const errText = await apiRes.text();
      return jsonResponse({ error: 'Anthropic API error', status: apiRes.status, detail: errText }, 502, origin);
    }

    const data = await apiRes.json();
    const raw = data?.content?.[0]?.text || '';
    const cleaned = raw.replace(/```json\s*|\s*```/g, '').trim();
    let parsed;
    try {
      parsed = JSON.parse(cleaned);
    } catch (e) {
      return jsonResponse({ error: 'Model returned invalid JSON', raw: cleaned.slice(0, 300) }, 502, origin);
    }

    parsed.term_input = term;
    parsed.source_lang = sourceLang;
    parsed.model = MODEL;
    parsed.ai_generated = true;

    const finalRes = jsonResponse(parsed, 200, origin);
    // Cache for 30 days (per-term, cheap)
    finalRes.headers.set('Cache-Control', 'public, max-age=2592000');
    finalRes.headers.set('X-Cache', 'MISS');
    // Only cache successful responses
    try { await cache.put(cacheKey, finalRes.clone()); } catch(e) {}
    return finalRes;
  }
};
