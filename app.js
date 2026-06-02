const LANGS = ["el", "en", "ar", "fa", "fr"];
const LANG_LABELS = { el: "Ελληνικά", en: "English", ar: "العربية", fa: "فارسی", fr: "Français" };
const RTL_LANGS = new Set(["ar", "fa"]);

const state = {
  data: null,
  uiLang: "el",
  activeCategory: "all",
  query: "",
  view: "cards"
};

const VIEW_LABELS = {
  el: { cards: "Καρτέλες", table: "Πίνακας" },
  en: { cards: "Cards", table: "Table" }
};

async function loadData() {
  const res = await fetch("data/terms.json");
  if (!res.ok) throw new Error("Failed to load terms.json: " + res.status);
  state.data = await res.json();
}

function readUrlState() {
  const params = new URLSearchParams(window.location.search);
  const q = params.get("q");
  const cat = params.get("cat");
  if (q) state.query = q.toLowerCase();
  if (cat) state.activeCategory = cat;
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.query) params.set("q", state.query);
  if (state.activeCategory && state.activeCategory !== "all") {
    params.set("cat", state.activeCategory);
  }
  const qs = params.toString();
  const newUrl = window.location.pathname + (qs ? "?" + qs : "");
  history.replaceState(null, "", newUrl);
}

function setUiLang(lang) {
  state.uiLang = lang;
  document.querySelectorAll(".lang-toggle button").forEach(b => {
    b.classList.toggle("active", b.dataset.lang === lang);
  });
  render();
}

function setCategory(catId) {
  state.activeCategory = catId;
  document.querySelectorAll(".cat-chip").forEach(c => {
    c.classList.toggle("active", c.dataset.cat === catId);
  });
  render();
  syncUrl();
}

function setQuery(q) {
  state.query = q.trim().toLowerCase();
  render();
  syncUrl();
}

function setView(view) {
  state.view = view;
  document.querySelectorAll(".view-toggle button").forEach(b => {
    b.classList.toggle("active", b.dataset.view === view);
  });
  render();
}

function buildViewToggle() {
  const wrap = document.getElementById("view-toggle");
  wrap.innerHTML = "";
  ["cards", "table"].forEach(v => {
    const btn = document.createElement("button");
    btn.dataset.view = v;
    btn.textContent = (VIEW_LABELS[state.uiLang] || VIEW_LABELS.en)[v];
    btn.classList.toggle("active", v === state.view);
    btn.addEventListener("click", () => setView(v));
    wrap.appendChild(btn);
  });
}

let toastTimer = null;
function showCopyToast(text) {
  const toast = document.getElementById("copy-toast");
  if (!toast) return;
  const msg = state.uiLang === "el" ? "Αντιγράφηκε" : "Copied";
  toast.textContent = msg + ": " + text;
  toast.hidden = false;
  toast.classList.add("show");
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => { toast.hidden = true; }, 200);
  }, 1400);
}

function copyToClipboard(text) {
  if (!text) return;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(
      () => showCopyToast(text),
      () => fallbackCopy(text)
    );
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "absolute";
  ta.style.left = "-9999px";
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand("copy"); showCopyToast(text); } catch (e) {}
  document.body.removeChild(ta);
}

function filterTerms() {
  const { data, activeCategory, query } = state;
  let terms = data.terms;
  if (activeCategory !== "all") {
    terms = terms.filter(t => t.category === activeCategory);
  }
  if (query) {
    terms = terms.filter(t => {
      const haystack = [
        t.id,
        t.translations.el || "",
        t.translations.en || "",
        t.translations.ar || "",
        t.translations.fa || "",
        t.translations.fr || "",
        t.definition_el || "",
        t.definition_en || ""
      ].join(" ").toLowerCase();
      return haystack.includes(query);
    });
  }
  return terms;
}

function categoryLabel(catId) {
  const c = state.data.categories.find(x => x.id === catId);
  if (!c) return catId;
  return c[state.uiLang] || c.en || c.id;
}

function buildCategoryBar() {
  const bar = document.getElementById("category-bar");
  bar.innerHTML = "";
  const all = document.createElement("button");
  all.className = "cat-chip" + (state.activeCategory === "all" ? " active" : "");
  all.dataset.cat = "all";
  all.textContent = state.uiLang === "el" ? "Όλες" : "All";
  all.addEventListener("click", () => setCategory("all"));
  bar.appendChild(all);
  state.data.categories.forEach(cat => {
    const chip = document.createElement("button");
    chip.className = "cat-chip" + (state.activeCategory === cat.id ? " active" : "");
    chip.dataset.cat = cat.id;
    chip.textContent = cat[state.uiLang] || cat.en;
    chip.addEventListener("click", () => setCategory(cat.id));
    bar.appendChild(chip);
  });
}

function buildLangToggle() {
  const wrap = document.getElementById("lang-toggle");
  wrap.innerHTML = "";
  LANGS.forEach(l => {
    const btn = document.createElement("button");
    btn.dataset.lang = l;
    btn.textContent = LANG_LABELS[l];
    btn.classList.toggle("active", l === state.uiLang);
    btn.addEventListener("click", () => setUiLang(l));
    wrap.appendChild(btn);
  });
}

function renderTermCard(term) {
  const card = document.createElement("div");
  card.className = "term-card";

  const head = document.createElement("div");
  head.className = "term-head";

  const titleWrap = document.createElement("div");
  const title = document.createElement("div");
  title.className = "term-title";
  const primary = term.translations[state.uiLang] || term.translations.en || term.id;
  title.textContent = primary;
  if (RTL_LANGS.has(state.uiLang)) {
    title.style.direction = "rtl";
    title.style.textAlign = "right";
  }
  titleWrap.appendChild(title);

  const secondaryLang = state.uiLang === "el" ? "en" : "el";
  const secondary = term.translations[secondaryLang];
  if (secondary) {
    const sub = document.createElement("div");
    sub.className = "term-subtitle";
    sub.textContent = secondary;
    titleWrap.appendChild(sub);
  }
  head.appendChild(titleWrap);

  const cat = document.createElement("span");
  cat.className = "term-cat";
  cat.textContent = categoryLabel(term.category);
  head.appendChild(cat);
  card.appendChild(head);

  const body = document.createElement("div");
  body.className = "term-body";

  const trans = document.createElement("div");
  trans.className = "translations";
  LANGS.forEach(l => {
    const item = document.createElement("div");
    item.className = "trans-item";
    const lab = document.createElement("div");
    lab.className = "trans-lang";
    lab.textContent = LANG_LABELS[l];
    item.appendChild(lab);
    const txt = document.createElement("div");
    const val = term.translations[l];
    if (val) {
      txt.className = "trans-text" + (RTL_LANGS.has(l) ? " rtl" : "");
      txt.textContent = val;
    } else {
      txt.className = "trans-pending";
      txt.textContent = "— pending —";
    }
    item.appendChild(txt);
    trans.appendChild(item);
  });
  body.appendChild(trans);

  const defs = document.createElement("div");
  defs.className = "definitions";
  ["el", "en"].forEach(l => {
    const key = "definition_" + l;
    if (term[key]) {
      const block = document.createElement("div");
      block.className = "def-block";
      const lab = document.createElement("div");
      lab.className = "def-lang";
      lab.textContent = LANG_LABELS[l];
      block.appendChild(lab);
      const txt = document.createElement("div");
      txt.className = "def-text";
      txt.textContent = term[key];
      block.appendChild(txt);
      defs.appendChild(block);
    }
  });
  body.appendChild(defs);

  if (term.sources && term.sources.length) {
    const srcs = document.createElement("div");
    srcs.className = "sources";
    const lab = document.createElement("strong");
    lab.textContent = state.uiLang === "el" ? "Πηγές: " : "Sources: ";
    srcs.appendChild(lab);
    srcs.appendChild(document.createTextNode(term.sources.join(" | ")));
    body.appendChild(srcs);
  }

  card.appendChild(body);

  card.addEventListener("click", () => {
    card.classList.toggle("open");
  });

  return card;
}

function sourceShort(src) {
  if (!src) return "";
  if (/^UNHCR/i.test(src)) return "UNHCR";
  if (/^EUAA/i.test(src)) return "EUAA";
  if (/^IATE/i.test(src)) return "IATE";
  if (/^IOM/i.test(src)) return "IOM";
  if (/Geneva Convention/i.test(src)) return "Geneva 1951";
  if (/Qualification Directive/i.test(src)) return "EU Qual. Dir.";
  if (/Reception Conditions/i.test(src)) return "EU RCD";
  if (/Asylum Procedures/i.test(src)) return "EU APD";
  if (/Dublin/i.test(src)) return "Dublin III";
  if (/Statelessness/i.test(src)) return "1954 Conv.";
  const law = src.match(/^(Ν\.?\s*\d+\/\d+|Π\.?Δ\.?\s*\d+\/\d+|ΦΕΚ\s*\S+)/i);
  if (law) return law[1].replace(/\s+/g, " ");
  return src.length > 18 ? src.slice(0, 16) + "…" : src;
}

function renderTable(terms) {
  const wrap = document.getElementById("term-table-wrap");
  wrap.innerHTML = "";

  const table = document.createElement("table");
  table.className = "term-table";

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  const headers = [
    { key: "el", label: "EL" },
    { key: "en", label: "EN" },
    { key: "ar", label: "AR" },
    { key: "fa", label: "FA" },
    { key: "fr", label: "FR" },
    { key: "cat", label: state.uiLang === "el" ? "Κατηγορία" : "Category" },
    { key: "src", label: state.uiLang === "el" ? "Πηγή" : "Source" }
  ];
  headers.forEach(h => {
    const th = document.createElement("th");
    th.textContent = h.label;
    th.dataset.col = h.key;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  terms.forEach(term => {
    const tr = document.createElement("tr");
    LANGS.forEach(l => {
      const td = document.createElement("td");
      const val = term.translations[l];
      if (val) {
        td.textContent = val;
        td.classList.add("copyable");
        if (RTL_LANGS.has(l)) td.classList.add("rtl");
        td.title = state.uiLang === "el" ? "Κλικ για αντιγραφή" : "Click to copy";
        td.addEventListener("click", () => copyToClipboard(val));
      } else {
        td.textContent = "—";
        td.classList.add("pending");
      }
      tr.appendChild(td);
    });

    const catTd = document.createElement("td");
    catTd.className = "cat-cell";
    catTd.textContent = categoryLabel(term.category);
    tr.appendChild(catTd);

    const srcTd = document.createElement("td");
    srcTd.className = "src-cell";
    if (term.sources && term.sources.length) {
      srcTd.textContent = term.sources.map(sourceShort).join(" · ");
      srcTd.title = term.sources.join("\n");
    } else {
      srcTd.textContent = "—";
      srcTd.classList.add("pending");
    }
    tr.appendChild(srcTd);

    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
}

function render() {
  const list = document.getElementById("term-list");
  const tableWrap = document.getElementById("term-table-wrap");
  const stats = document.getElementById("stats");
  list.innerHTML = "";
  tableWrap.innerHTML = "";

  const terms = filterTerms();
  stats.textContent = state.uiLang === "el"
    ? terms.length + " όροι"
    : terms.length + " terms";

  const showTable = state.view === "table";
  list.hidden = showTable;
  tableWrap.hidden = !showTable;

  if (terms.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = state.uiLang === "el"
      ? "Δεν βρέθηκαν όροι."
      : "No terms found.";
    (showTable ? tableWrap : list).appendChild(empty);
    return;
  }

  const sorted = terms.slice().sort((a, b) => {
    const al = (a.translations[state.uiLang] || a.translations.en || "").toLowerCase();
    const bl = (b.translations[state.uiLang] || b.translations.en || "").toLowerCase();
    return al.localeCompare(bl);
  });

  if (showTable) {
    renderTable(sorted);
  } else {
    sorted.forEach(t => list.appendChild(renderTermCard(t)));
  }

  document.querySelectorAll(".cat-chip").forEach(c => {
    if (c.dataset.cat === "all") {
      c.textContent = state.uiLang === "el" ? "Όλες" : "All";
    } else {
      const cat = state.data.categories.find(x => x.id === c.dataset.cat);
      if (cat) c.textContent = cat[state.uiLang] || cat.en;
    }
  });

  document.querySelectorAll(".view-toggle button").forEach(b => {
    b.textContent = (VIEW_LABELS[state.uiLang] || VIEW_LABELS.en)[b.dataset.view];
  });
}

async function init() {
  try {
    await loadData();
  } catch (e) {
    document.getElementById("term-list").innerHTML =
      '<div class="empty">Error loading data: ' + e.message + "</div>";
    return;
  }
  readUrlState();
  buildLangToggle();
  buildViewToggle();
  buildCategoryBar();
  const searchInput = document.getElementById("search");
  searchInput.value = state.query;
  searchInput.addEventListener("input", e => setQuery(e.target.value));
  render();
}

document.addEventListener("DOMContentLoaded", init);
