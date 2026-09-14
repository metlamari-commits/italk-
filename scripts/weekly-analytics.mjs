#!/usr/bin/env node
// Weekly analytics report for i-talk.gr via Cloudflare Web Analytics GraphQL API.
// Reads token/account/site from .env, prints markdown to stdout, and writes it to
// Documents/italk-analytics/YYYY-WW.md.

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { homedir } from 'node:os';
import { spawn } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = join(__dirname, '..', '.env');
const env = Object.fromEntries(
  readFileSync(envPath, 'utf8')
    .split(/\r?\n/)
    .filter(l => l && !l.startsWith('#') && l.includes('='))
    .map(l => {
      const i = l.indexOf('=');
      return [l.slice(0, i).trim(), l.slice(i + 1).trim()];
    })
);

const TOKEN = env.CLOUDFLARE_API_TOKEN;
const ACCOUNT = env.CLOUDFLARE_ACCOUNT_ID;
const SITE_TAG = env.ITALK_SITE_TAG;
if (!TOKEN || !ACCOUNT || !SITE_TAG) {
  console.error('Missing env: CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID / ITALK_SITE_TAG');
  process.exit(1);
}

const ymd = d => d.toISOString().slice(0, 10);
const daysAgo = n => { const d = new Date(); d.setUTCDate(d.getUTCDate() - n); return d; };

const now = new Date();
const thisWeekStart = ymd(daysAgo(7));
const thisWeekEnd = ymd(now);
const prevWeekStart = ymd(daysAgo(14));
const prevWeekEnd = ymd(daysAgo(8));

async function gql(query) {
  const res = await fetch('https://api.cloudflare.com/client/v4/graphql', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  const json = await res.json();
  if (json.errors) throw new Error(JSON.stringify(json.errors));
  return json.data.viewer.accounts[0];
}

const filter = (start, end) =>
  `{siteTag: "${SITE_TAG}", date_geq: "${start}", date_leq: "${end}"}`;

async function totals(start, end) {
  const q = `query { viewer { accounts(filter: {accountTag: "${ACCOUNT}"}) {
    rumPageloadEventsAdaptiveGroups(limit: 1, filter: ${filter(start, end)}) {
      count sum { visits }
    }
  } } }`;
  const r = await gql(q);
  const g = r.rumPageloadEventsAdaptiveGroups[0];
  return { pageviews: g?.count ?? 0, visits: g?.sum?.visits ?? 0 };
}

async function topBy(dimension, start, end, limit = 5) {
  const q = `query { viewer { accounts(filter: {accountTag: "${ACCOUNT}"}) {
    rumPageloadEventsAdaptiveGroups(limit: ${limit}, filter: ${filter(start, end)}, orderBy: [count_DESC]) {
      count sum { visits } dimensions { ${dimension} }
    }
  } } }`;
  const r = await gql(q);
  return r.rumPageloadEventsAdaptiveGroups.map(g => ({
    label: g.dimensions[dimension] || '(unknown)',
    count: g.count,
    visits: g.sum.visits,
  }));
}

async function webVitals(start, end) {
  const q = `query { viewer { accounts(filter: {accountTag: "${ACCOUNT}"}) {
    rumWebVitalsEventsAdaptiveGroups(limit: 1, filter: ${filter(start, end)}) {
      count
      quantiles {
        largestContentfulPaintP75
        interactionToNextPaintP75
        cumulativeLayoutShiftP75
        firstContentfulPaintP75
        timeToFirstByteP75
      }
    }
  } } }`;
  try {
    const r = await gql(q);
    const g = r.rumWebVitalsEventsAdaptiveGroups[0];
    if (!g) return null;
    return { count: g.count, ...g.quantiles };
  } catch { return null; }
}

const pct = (a, b) => b === 0 ? '—' : `${((a / b) * 100).toFixed(0)}%`;
const delta = (curr, prev) => {
  if (prev === 0) return curr > 0 ? '↑ νέο' : '—';
  const d = ((curr - prev) / prev) * 100;
  return `${d >= 0 ? '↑' : '↓'} ${Math.abs(d).toFixed(0)}%`;
};

(async () => {
  const [nowTotals, prevTotals, pages, countries, refs, browsers, devices, vitals] = await Promise.all([
    totals(thisWeekStart, thisWeekEnd),
    totals(prevWeekStart, prevWeekEnd),
    topBy('requestPath', thisWeekStart, thisWeekEnd),
    topBy('countryName', thisWeekStart, thisWeekEnd),
    topBy('refererHost', thisWeekStart, thisWeekEnd),
    topBy('userAgentBrowser', thisWeekStart, thisWeekEnd),
    topBy('deviceType', thisWeekStart, thisWeekEnd),
    webVitals(thisWeekStart, thisWeekEnd),
  ]);

  const md = [];
  md.push(`# i-talk.gr — Weekly Analytics (${thisWeekStart} → ${thisWeekEnd})`);
  md.push('');
  md.push(`## Επισκεψιμότητα`);
  md.push(`| Metric | Αυτή η εβδομάδα | Προηγούμενη | Μεταβολή |`);
  md.push(`|---|---|---|---|`);
  md.push(`| Pageviews | ${nowTotals.pageviews} | ${prevTotals.pageviews} | ${delta(nowTotals.pageviews, prevTotals.pageviews)} |`);
  md.push(`| Visits | ${nowTotals.visits} | ${prevTotals.visits} | ${delta(nowTotals.visits, prevTotals.visits)} |`);
  md.push('');

  const section = (title, rows, labelHeader = 'Label') => {
    md.push(`## ${title}`);
    if (rows.length === 0) { md.push('_Χωρίς δεδομένα_', ''); return; }
    md.push(`| ${labelHeader} | Pageviews | Visits |`);
    md.push(`|---|---|---|`);
    for (const r of rows) md.push(`| ${r.label} | ${r.count} | ${r.visits} |`);
    md.push('');
  };

  section('Top Pages', pages, 'Path');
  section('Top Χώρες', countries, 'Country');
  section('Top Referrers', refs, 'Host');
  section('Browsers', browsers, 'Browser');
  section('Devices', devices, 'Device');

  md.push(`## Core Web Vitals (P75, ${vitals?.count ?? 0} samples)`);
  if (!vitals) {
    md.push('_Δεν επιστράφηκαν δεδομένα Web Vitals._');
  } else {
    // Cloudflare returns time metrics in microseconds; convert to ms for Google's thresholds.
    const toMs = v => v == null ? null : v / 1000;
    const rate = (v, good, poor) => v == null ? '—' : v <= good ? '🟢 Good' : v <= poor ? '🟡 NI' : '🔴 Poor';
    const ms = v => v == null ? '—' : `${Math.round(toMs(v))}ms`;
    const num = v => v == null ? '—' : v.toFixed(3);
    const rateMs = (v, good, poor) => rate(toMs(v), good, poor);
    md.push(`| Metric | P75 | Rating (Google) |`);
    md.push(`|---|---|---|`);
    md.push(`| LCP (Largest Contentful Paint) | ${ms(vitals.largestContentfulPaintP75)} | ${rateMs(vitals.largestContentfulPaintP75, 2500, 4000)} |`);
    md.push(`| INP (Interaction to Next Paint) | ${ms(vitals.interactionToNextPaintP75)} | ${rateMs(vitals.interactionToNextPaintP75, 200, 500)} |`);
    md.push(`| CLS (Cumulative Layout Shift) | ${num(vitals.cumulativeLayoutShiftP75)} | ${rate(vitals.cumulativeLayoutShiftP75, 0.1, 0.25)} |`);
    md.push(`| FCP (First Contentful Paint) | ${ms(vitals.firstContentfulPaintP75)} | ${rateMs(vitals.firstContentfulPaintP75, 1800, 3000)} |`);
    md.push(`| TTFB (Time to First Byte) | ${ms(vitals.timeToFirstByteP75)} | ${rateMs(vitals.timeToFirstByteP75, 800, 1800)} |`);
  }
  md.push('');
  md.push(`---`);
  md.push(`_Generated ${now.toISOString()} · deploy version: check sw.js CACHE_VERSION_`);

  const output = md.join('\n');
  console.log(output);

  const outDir = join(homedir(), 'Documents', 'italk-analytics');
  if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true });
  const year = now.getUTCFullYear();
  const week = Math.ceil(((now - new Date(Date.UTC(year, 0, 1))) / 86400000 + new Date(Date.UTC(year, 0, 1)).getUTCDay() + 1) / 7);
  const stem = `${year}-W${String(week).padStart(2, '0')}`;
  const mdFile = join(outDir, `${stem}.md`);
  const htmlFile = join(outDir, `${stem}.html`);
  writeFileSync(mdFile, output, 'utf8');
  writeFileSync(htmlFile, mdToHtml(output, stem), 'utf8');
  console.error(`\n✓ Saved MD:   ${mdFile}`);
  console.error(`✓ Saved HTML: ${htmlFile}`);

  if (process.argv.includes('--open')) {
    spawn('cmd', ['/c', 'start', '', htmlFile], { detached: true, stdio: 'ignore' }).unref();
    console.error(`✓ Opened in default browser`);
  }
})().catch(e => { console.error('ERROR:', e.message); process.exit(1); });

function mdToHtml(md, title) {
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const lines = md.split('\n');
  const out = [];
  let inTable = false;
  const flushTable = () => { if (inTable) { out.push('</tbody></table>'); inTable = false; } };
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (/^\|.+\|$/.test(l)) {
      const cells = l.slice(1, -1).split('|').map(c => c.trim());
      const next = lines[i + 1] || '';
      const isHeaderSep = /^\|[\s\-|]+\|$/.test(next);
      if (isHeaderSep && !inTable) {
        out.push('<table><thead><tr>' + cells.map(c => `<th>${esc(c)}</th>`).join('') + '</tr></thead><tbody>');
        inTable = true;
        i++;
        continue;
      }
      if (inTable) {
        out.push('<tr>' + cells.map(c => `<td>${esc(c)}</td>`).join('') + '</tr>');
        continue;
      }
    }
    flushTable();
    if (/^# /.test(l)) out.push(`<h1>${esc(l.slice(2))}</h1>`);
    else if (/^## /.test(l)) out.push(`<h2>${esc(l.slice(3))}</h2>`);
    else if (/^### /.test(l)) out.push(`<h3>${esc(l.slice(4))}</h3>`);
    else if (/^---$/.test(l)) out.push('<hr>');
    else if (/^_(.+)_$/.test(l)) out.push(`<p><em>${esc(l.slice(1, -1))}</em></p>`);
    else if (l.trim() === '') out.push('');
    else out.push(`<p>${esc(l)}</p>`);
  }
  flushTable();
  return `<!doctype html><html lang="el"><head><meta charset="utf-8"><title>i-talk.gr Analytics — ${esc(title)}</title>
<style>
  body{font-family:system-ui,Segoe UI,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#0a0e13;line-height:1.5;background:#f5f7fb}
  h1{border-bottom:3px solid #114277;padding-bottom:.5rem;color:#114277}
  h2{margin-top:2rem;color:#114277;border-bottom:1px solid #cbd5e1;padding-bottom:.3rem}
  table{border-collapse:collapse;width:100%;background:#fff;margin:.5rem 0 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.06);border-radius:6px;overflow:hidden}
  th,td{padding:.6rem .8rem;text-align:left;border-bottom:1px solid #eef2f8}
  th{background:#114277;color:#fff;font-weight:600}
  tr:last-child td{border-bottom:none}
  tr:nth-child(even){background:#fafbfd}
  hr{border:none;border-top:1px solid #cbd5e1;margin:2rem 0}
  em{color:#64748b;font-size:.9rem}
  p{margin:.5rem 0}
</style></head><body>
${out.join('\n')}
</body></html>`;
}
