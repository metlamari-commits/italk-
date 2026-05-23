const LANGS = ["el", "en", "ar", "fa", "fr"];
const LANG_LABELS = { el: "Ελληνικά", en: "English", ar: "العربية", fa: "فارسی", fr: "Français" };
const RTL_LANGS = new Set(["ar", "fa"]);

const state = {
  data: null,
  uiLang: "el",
  activeCategory: "all",
  query: ""
};

async function loadData() {
  const res = await fetch("data/terms.json");
  if (!res.ok) throw new Error("Failed to load terms.json: " + res.status);
  state.data = await res.json();
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
}

function setQuery(q) {
  state.query = q.trim().toLowerCase();
  render();
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
  all.className = "cat-chip active";
  all.dataset.cat = "all";
  all.textContent = state.uiLang === "el" ? "Όλες" : "All";
  all.addEventListener("click", () => setCategory("all"));
  bar.appendChild(all);
  state.data.categories.forEach(cat => {
    const chip = document.createElement("button");
    chip.className = "cat-chip";
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

function render() {
  const list = document.getElementById("term-list");
  const stats = document.getElementById("stats");
  list.innerHTML = "";

  const terms = filterTerms();
  stats.textContent = state.uiLang === "el"
    ? terms.length + " όροι"
    : terms.length + " terms";

  if (terms.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = state.uiLang === "el"
      ? "Δεν βρέθηκαν όροι."
      : "No terms found.";
    list.appendChild(empty);
    return;
  }

  terms
    .slice()
    .sort((a, b) => {
      const al = (a.translations[state.uiLang] || a.translations.en || "").toLowerCase();
      const bl = (b.translations[state.uiLang] || b.translations.en || "").toLowerCase();
      return al.localeCompare(bl);
    })
    .forEach(t => list.appendChild(renderTermCard(t)));

  document.querySelectorAll(".cat-chip").forEach(c => {
    if (c.dataset.cat === "all") {
      c.textContent = state.uiLang === "el" ? "Όλες" : "All";
    } else {
      const cat = state.data.categories.find(x => x.id === c.dataset.cat);
      if (cat) c.textContent = cat[state.uiLang] || cat.en;
    }
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
  buildLangToggle();
  buildCategoryBar();
  document.getElementById("search").addEventListener("input", e => setQuery(e.target.value));
  render();
}

document.addEventListener("DOMContentLoaded", init);
