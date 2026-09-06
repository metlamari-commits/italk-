// i-talk.gr — AI translation Cloudflare Worker (with KV persistence)
//
// Endpoints:
//   GET  /              → health check
//   POST /              → translate a term (proxies to Anthropic Claude)
//   GET  /list          → return all saved AI translations from KV
//   POST /save          → save an AI translation to KV (called when user
//                         bookmarks an AI card on the frontend)
//
// Requires:
//   - Secret ANTHROPIC_API_KEY
//   - KV namespace binding named ITALK_KV

const ALLOWED_ORIGINS = new Set([
  'https://i-talk.gr',
  'https://www.i-talk.gr',
  'http://localhost:8765',
  'http://127.0.0.1:8765'
]);

const MODEL = 'claude-haiku-4-5-20251001';
const MAX_TERM_LEN = 200;
const MAX_TOKENS = 600;
const KV_PREFIX = 'term:';

function corsHeaders(origin) {
  const allow = ALLOWED_ORIGINS.has(origin) ? origin : 'https://i-talk.gr';
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
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
3. Classify the term into one of these domains: "status", "procedure", "reception", "vulnerable", "legal", "medical", "detention", "return", "family", "integration", "communication", "documentation", or "general" if none fits.
4. If the term is nonsense, offensive, or clearly outside asylum/humanitarian scope, set "translations" to null and put a short reason in "note".

Return ONLY valid JSON, no markdown, no code fences, no extra text:
{
  "translations": {"el":"...", "en":"...", "ar":"...", "fa":"...", "fr":"..."},
  "definition_el": "...",
  "definition_en": "...",
  "category": "one of the domain slugs above",
  "note": null
}`;
}

async function handleTranslate(request, env, origin) {
  if (!env.ANTHROPIC_API_KEY) {
    return jsonResponse({
      error: 'Worker not configured: missing ANTHROPIC_API_KEY secret',
      env_keys_present: Object.keys(env)
    }, 500, origin);
  }
  let body;
  try { body = await request.json(); }
  catch (e) { return jsonResponse({ error: 'Invalid JSON body' }, 400, origin); }
  const term = String(body.term || '').trim().slice(0, MAX_TERM_LEN);
  const sourceLang = String(body.sourceLang || 'el').slice(0, 5);
  if (!term) return jsonResponse({ error: 'Missing term' }, 400, origin);

  const cacheKey = new Request(
    new URL(request.url).origin + '/__cache?t=' + encodeURIComponent(term.toLowerCase()) + '&s=' + sourceLang,
    { method: 'GET' }
  );
  const cache = caches.default;
  const cached = await cache.match(cacheKey);
  if (cached) {
    const hit = new Response(cached.body, cached);
    const h = corsHeaders(origin);
    Object.entries(h).forEach(([k, v]) => hit.headers.set(k, v));
    hit.headers.set('X-Cache', 'HIT');
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
  try { parsed = JSON.parse(cleaned); }
  catch (e) { return jsonResponse({ error: 'Model returned invalid JSON', raw: cleaned.slice(0, 300) }, 502, origin); }

  parsed.term_input = term;
  parsed.source_lang = sourceLang;
  parsed.model = MODEL;
  parsed.ai_generated = true;

  const finalRes = jsonResponse(parsed, 200, origin);
  finalRes.headers.set('Cache-Control', 'public, max-age=2592000');
  finalRes.headers.set('X-Cache', 'MISS');
  try { await cache.put(cacheKey, finalRes.clone()); } catch(e) {}
  return finalRes;
}

async function handleSave(request, env, origin) {
  if (!env.ITALK_KV) {
    return jsonResponse({ error: 'KV namespace ITALK_KV not bound to this worker' }, 500, origin);
  }
  let body;
  try { body = await request.json(); }
  catch (e) { return jsonResponse({ error: 'Invalid JSON body' }, 400, origin); }

  const t = body.term_input || body.term;
  const src = body.source_lang || body.sourceLang || 'el';
  if (!t || !body.translations) {
    return jsonResponse({ error: 'Missing term_input or translations' }, 400, origin);
  }
  const term = String(t).trim().slice(0, MAX_TERM_LEN);
  const sourceLang = String(src).slice(0, 5);

  const record = {
    term_input: term,
    source_lang: sourceLang,
    translations: body.translations,
    definition_el: body.definition_el || '',
    definition_en: body.definition_en || '',
    category: body.category || 'general',
    model: body.model || MODEL,
    ai_generated: true,
    saved_at: new Date().toISOString()
  };

  const key = KV_PREFIX + sourceLang + ':' + term.toLowerCase();
  try {
    await env.ITALK_KV.put(key, JSON.stringify(record));
    return jsonResponse({ ok: true, key, record }, 200, origin);
  } catch (e) {
    return jsonResponse({ error: 'KV write failed', detail: String(e) }, 500, origin);
  }
}

// One-shot cleanup of the two corrupted test entries that Windows-terminal
// curl POSTed during KV setup on 2026-09-05. Idempotent; safe to leave in.
const CLEANUP_KEYS = [
  'term:en:bunker',
  'term:en:curfew'
];
async function handleCleanup(env, origin) {
  if (!env.ITALK_KV) {
    return jsonResponse({ error: 'KV not bound' }, 500, origin);
  }
  const deleted = [];
  const missing = [];
  for (const key of CLEANUP_KEYS) {
    const existing = await env.ITALK_KV.get(key);
    if (existing === null) {
      missing.push(key);
      continue;
    }
    await env.ITALK_KV.delete(key);
    deleted.push(key);
  }
  return jsonResponse({ ok: true, deleted, already_missing: missing }, 200, origin);
}

async function handleList(env, origin) {
  if (!env.ITALK_KV) {
    return jsonResponse({ terms: [], warning: 'KV not bound', has_kv: false }, 200, origin);
  }
  try {
    const list = await env.ITALK_KV.list({ prefix: KV_PREFIX, limit: 1000 });
    const keys = (list && list.keys) || [];
    const terms = [];
    for (const k of keys) {
      try {
        const v = await env.ITALK_KV.get(k.name);
        if (v) terms.push(JSON.parse(v));
      } catch (e) {}
    }
    const res = jsonResponse({ terms, count: terms.length }, 200, origin);
    res.headers.set('Cache-Control', 'public, max-age=60');
    return res;
  } catch (e) {
    return jsonResponse({ error: 'KV list failed', detail: String(e), stack: (e && e.stack) || null }, 500, origin);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin') || '';
    const path = url.pathname;

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    if (request.method === 'GET' && path === '/list') {
      return handleList(env, origin);
    }
    if (request.method === 'GET' && path === '/cleanup') {
      return handleCleanup(env, origin);
    }
    if (request.method === 'GET' && (path === '/' || path === '')) {
      return jsonResponse({ ok: true, service: 'italk-translate', model: MODEL, has_kv: !!env.ITALK_KV }, 200, origin);
    }
    if (request.method !== 'POST') {
      return jsonResponse({ error: 'Method not allowed' }, 405, origin);
    }
    if (!ALLOWED_ORIGINS.has(origin)) {
      return jsonResponse({ error: 'Origin not allowed', origin }, 403, origin);
    }
    if (path === '/save') {
      return handleSave(request, env, origin);
    }
    // Default POST → translate
    return handleTranslate(request, env, origin);
  }
};
