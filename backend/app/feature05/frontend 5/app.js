"use strict";

const API = "/simulations";

const state = {
  caseId: "case_002",
  sessionId: "",
  catalog: [],
  patient: null,
  orders: {},
  exams: {},
  na: {},
  events: [],
  selected: new Set(),
  busy: false,
  gen: 0,
  fetching: {},
};

const $ = (id) => document.getElementById(id);
const enc = encodeURIComponent;

function esc(v) {
  return String(v ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function label(s) {
  return String(s || "").replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
}

function newSession() {
  const id = (window.crypto && crypto.randomUUID)
    ? crypto.randomUUID().replaceAll("-", "")
    : Date.now() + Math.random().toString(16).slice(2);
  return "f05_" + id;
}

const isExam = (i) => i.category === "general" || i.category === "system";
const nameOf = (id) => (state.catalog.find((x) => x.id === id) || {}).name || id;

function secs(iso) {
  const s = Math.max(0, Math.ceil((Date.parse(iso) - Date.now()) / 1000));
  return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
}

function showError(m) {
  $("error").textContent = m || "";
  $("error").hidden = !m;
}

function notice(m) {
  $("notice").textContent = m || "";
}

async function request(path, options = {}) {
  const response = await fetch(API + path, {
    ...options,
    headers: options.body ? { "Content-Type": "application/json" } : {},
    cache: "no-store",
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("Unexpected response (" + response.status + ")");
  }

  if (!response.ok || data.status === "error") {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : data.message || "Request failed (" + response.status + ")"
    );
  }
  return data;
}

/* ---------- status ---------- */

function statusOf(id) {
  const o = state.orders[id];
  if (!o) return { k: "", t: "Not ordered" };
  if (o.status === "pending") return { k: "pending", t: "Pending " + secs(o.ready_at) };
  return { k: "released", t: o.count > 1 ? "Released, repeated" : "Released" };
}

/* ---------- renderers ---------- */

function renderCase() {
  const d = state.patient;
  if (!d) return;
  const p = d.patient || {};
  $("title").textContent = d.title || "Clinical case";
  $("pt").textContent =
    "Age " + (p.age ?? "n/a") + ", " + (p.sex ?? "n/a") + ", " +
    (p.weight_kg != null ? p.weight_kg + " kg" : "weight n/a");
  $("complaint").textContent = d.chief_complaint || "";
  const hist = [
    d.present_history ? "Present history: " + d.present_history : "",
    d.medical_history && d.medical_history !== d.present_history
      ? "Medical history: " + d.medical_history : "",
  ].filter(Boolean).join("\n\n");
  $("history").textContent = hist || "Not documented.";
}

function renderCategories() {
  const cats = [...new Set(state.catalog.filter((i) => !isExam(i)).map((i) => i.category))];
  $("cat").innerHTML = '<option value="">All categories</option>' +
    cats.map((c) => '<option value="' + esc(c) + '">' + esc(label(c)) + "</option>").join("");
}

function renderCatalog() {
  const box = $("catalog");
  const top = box.scrollTop;
  const q = $("q").value.trim().toLowerCase();
  const cat = $("cat").value;
  const items = state.catalog.filter((i) =>
    !isExam(i) &&
    (!cat || i.category === cat) &&
    (!q || (i.id + " " + i.name + " " + (i.description || "") + " " + (i.subcategory || "")).toLowerCase().includes(q))
  );
  const groups = {};
  items.forEach((i) => (groups[i.category] = groups[i.category] || []).push(i));

  box.innerHTML = Object.keys(groups).map((c) =>
    '<div class="cat">' + esc(label(c)) + "</div>" +
    groups[c].map((i) => {
      const s = statusOf(i.id);
      return '<div class="item"><input type="checkbox" id="c_' + esc(i.id) + '" data-c="' + esc(i.id) + '"' +
        (state.selected.has(i.id) ? " checked" : "") + '><label for="c_' + esc(i.id) + '">' + esc(i.name) +
        '</label><span id="s_' + esc(i.id) + '" class="chip ' + s.k + '">' + s.t + "</span></div>";
    }).join("")
  ).join("") || '<p class="empty">No tests match your search.</p>';
  box.scrollTop = top;
}

function updChips() {
  Object.keys(state.orders).forEach((id) => {
    const el = $("s_" + id);
    if (!el) return;
    const s = statusOf(id);
    el.className = "chip " + s.k;
    el.textContent = s.t;
  });
}

function measurementsTable(list) {
  if (!list || !list.length) return "";
  return "<table><tr><th>Test</th><th>Value</th><th>Reference</th></tr>" +
    list.map((m) =>
      "<tr><td>" + esc(m.name) + "</td><td>" + esc(m.value) + (m.unit ? " " + esc(m.unit) : "") +
      "</td><td>" + esc(m.reference_range || "") + "</td></tr>"
    ).join("") + "</table>";
}

function renderResults() {
  const ids = Object.keys(state.orders).reverse();
  $("results").innerHTML = ids.length ? ids.map((id) => {
    const o = state.orders[id];
    const name = esc(o.name || nameOf(id));
    if (o.status === "pending") {
      return '<div class="res"><div class="head"><strong>' + name + '</strong><span class="pill">Pending</span></div>' +
        '<p class="meta">Result not released yet. Available in <span data-cd="' + esc(id) + '">' + secs(o.ready_at) + "</span></p></div>";
    }
    const r = o.result || {};
    const ev = o.evaluation || {};
    return '<div class="res"><div class="head"><strong>' + name + "</strong>" +
      (ev.relevance ? '<span class="pill">' + esc(label(ev.relevance)) + " · penalty " + esc(ev.penalty ?? 0) + "</span>" : "") + "</div>" +
      (r.findings ? '<p class="val">' + esc(r.findings) + "</p>" : "") +
      measurementsTable(r.measurements) +
      (r.reference_range_note ? '<p class="meta">' + esc(r.reference_range_note) + "</p>" : "") +
      (r.note ? '<p class="meta">' + esc(r.note) + "</p>" : "") +
      (r.simulated_normal ? '<p class="meta">Not part of this case. Reported as normal.</p>' : "") +
      (r.image_url
        ? '<button class="thumb" type="button" data-img="' + esc(r.image_url) + '" data-n="' + name + '" aria-label="Open image and zoom"><img alt="' + name + ' image" src="' + esc(r.image_url) + '"></button>'
        : "") + "</div>";
  }).join("") : '<p class="empty">No results yet. Select tests and order them.</p>';
}

function updCountdowns() {
  document.querySelectorAll("[data-cd]").forEach((el) => {
    const o = state.orders[el.dataset.cd];
    if (o && o.ready_at) el.textContent = secs(o.ready_at);
  });
}

function renderExams() {
  const exams = state.catalog.filter(isExam);
  const groups = {};
  exams.forEach((e) => (groups[e.category] = groups[e.category] || []).push(e));
  const order = { general: "General", system: "System-based" };

  $("exams").innerHTML = Object.keys(groups).map((g) =>
    '<div class="exgroup">' + esc(order[g] || label(g)) + '</div><div class="exam">' +
    groups[g].map((e) =>
      '<button type="button" class="ghost' + (state.exams[e.id] ? " done" : "") + (state.na[e.id] ? " na" : "") +
      '" data-e="' + esc(e.id) + '">' + esc(e.name) + "</button>"
    ).join("") + "</div>"
  ).join("");

  const done = Object.values(state.exams);
  $("findings").innerHTML = done.length ? done.map((x) =>
    '<div class="finding"><strong>' + esc(x.examination_name || x.examination_id) + "</strong>" +
    (x.result && x.result.findings ? "<div>" + esc(x.result.findings) + "</div>" : "") +
    measurementsTable(x.result && x.result.measurements) +
    (x.result && x.result.note ? '<div class="meta">' + esc(x.result.note) + "</div>" : "") + "</div>"
  ).join("") : '<p class="empty">Choose an examination to see the finding.</p>';
}

const EVENT_TEXT = {
  pending: "ordered, result pending",
  completed: "done",
  already_ordered: "already ordered, no new result",
  already_performed: "already examined, same finding",
  unavailable: "not available for this case",
};

function renderLog() {
  const ev = [...state.events].reverse();
  $("log").innerHTML = ev.length ? ev.map((e) => {
    const time = new Date(e.timestamp).toLocaleTimeString();
    const rel = e.relevance ? ". Relevance: " + esc(label(e.relevance)) : "";
    const pen = e.penalty ? ". Penalty " + esc(e.penalty) : "";
    return '<div><span class="t">' + esc(time) + "</span> " + esc(nameOf(e.investigation_id)) + ": " +
      esc(EVENT_TEXT[e.status] || e.status) + rel + pen + "</div>";
  }).join("") : '<p class="empty">Empty.</p>';
}

function renderSummary() {
  const o = Object.values(state.orders);
  const penalty = state.events.reduce((a, e) => a + Number(e.penalty || 0), 0);
  const stats = [
    [o.length, "Tests ordered"],
    [o.filter((x) => x.status === "completed").length, "Results ready"],
    [o.filter((x) => x.status === "pending").length, "Pending"],
    [Object.keys(state.exams).length, "Examinations"],
    [penalty, "Penalty points"],
  ];
  $("sum").innerHTML = stats.map((s) => "<div><b>" + s[0] + "</b><span>" + s[1] + "</span></div>").join("");
}

function renderAll() {
  renderCase();
  renderCatalog();
  renderResults();
  renderExams();
  renderLog();
  renderSummary();
}

/* ---------- data ---------- */

async function refreshEvents(gen) {
  const data = await request("/" + enc(state.sessionId) + "/investigation-events");
  if (gen !== state.gen) return;
  state.events = data.events || [];
}

async function fetchResult(id, gen) {
  const data = await request("/" + enc(state.sessionId) + "/investigations/" + enc(id) + "/result");
  if (gen !== state.gen) return;
  const o = state.orders[id];
  if (!o) return;
  if (data.status === "completed") {
    o.status = "completed";
    o.result = data.result;
    o.evaluation = data.evaluation || o.evaluation;
  } else if (data.status === "pending") {
    o.ready_at = data.ready_at || o.ready_at;
  }
}

async function loadCase() {
  const gen = ++state.gen;
  state.sessionId = newSession();
  state.patient = null;
  state.orders = {};
  state.exams = {};
  state.na = {};
  state.events = [];
  state.selected = new Set();
  state.busy = false;
  state.fetching = {};
  notice("");
  showError("");
  $("title").textContent = "Loading case";
  renderAll();

  try {
    const data = await request(
      "/" + enc(state.sessionId) + "/case?case_id=" + enc(state.caseId)
    );
    if (gen !== state.gen) return;
    state.patient = data;
    renderAll();
  } catch (e) {
    if (gen === state.gen) showError(e.message);
  }
}

async function loadCatalog() {
  const data = await request("/investigations/catalog");
  state.catalog = data.investigations || [];
  renderCategories();
  renderAll();
}

async function orderSelected() {
  if (state.busy) return;
  const ids = [...state.selected];
  if (!ids.length) { notice("Select at least one test first."); return; }

  const gen = state.gen;
  const sid = state.sessionId;
  state.busy = true;
  $("order").disabled = true;
  showError("");
  const msgs = [];

  try {
    for (const id of ids) {
      const data = await request("/" + enc(sid) + "/investigations", {
        method: "POST",
        body: JSON.stringify({ case_id: state.caseId, investigation_id: id }),
      });
      if (gen !== state.gen) return;

      if (data.status === "already_ordered") {
        if (state.orders[id]) state.orders[id].count++;
        msgs.push(nameOf(id) + " was already ordered. No new result.");
        continue;
      }

      state.orders[id] = {
        status: data.status,
        name: data.investigation_name || nameOf(id),
        ready_at: data.ready_at,
        evaluation: data.evaluation || {},
        count: 1,
      };

      if (data.status === "completed") await fetchResult(id, gen);
      else msgs.push(nameOf(id) + ": result will be released shortly.");
    }
    state.selected.clear();
    await refreshEvents(gen);
    if (gen === state.gen) notice(msgs.join(" ") || "Results are ready.");
  } catch (e) {
    if (gen === state.gen) showError(e.message);
  } finally {
    if (gen === state.gen) {
      state.busy = false;
      $("order").disabled = false;
      renderAll();
    }
  }
}

async function performExam(id) {
  if (state.busy) return;
  const gen = state.gen;
  const sid = state.sessionId;
  state.busy = true;
  showError("");

  try {
    const data = await request("/" + enc(sid) + "/examinations", {
      method: "POST",
      body: JSON.stringify({ case_id: state.caseId, examination_id: id }),
    });
    if (gen !== state.gen) return;

    if (data.status === "completed") {
      state.exams[id] = data;
      notice("");
    } else if (data.status === "already_performed") {
      notice(nameOf(id) + " was already examined. The finding is unchanged.");
    } else if (data.status === "unavailable") {
      state.na[id] = true;
      notice(nameOf(id) + " is not available for this case.");
    }
    await refreshEvents(gen);
  } catch (e) {
    if (gen === state.gen) showError(e.message);
  } finally {
    if (gen === state.gen) {
      state.busy = false;
      renderAll();
    }
  }
}

async function tick() {
  const gen = state.gen;
  let changed = false;

  for (const [id, o] of Object.entries(state.orders)) {
    if (o.status === "pending" && o.ready_at && Date.now() >= Date.parse(o.ready_at) && !state.fetching[id]) {
      state.fetching[id] = true;
      try {
        await fetchResult(id, gen);
        changed = true;
      } catch (e) {
        console.error(e);
      } finally {
        delete state.fetching[id];
      }
    }
  }

  if (gen !== state.gen) return;

  if (changed) {
    try { await refreshEvents(gen); } catch (e) { console.error(e); }
    renderAll();
  } else {
    updChips();
    updCountdowns();
  }
}

/* ---------- image viewer ---------- */

let zoom = 1;

function setZoom(z) {
  zoom = Math.min(4, Math.max(1, z));
  $("dimg").style.width = zoom * 100 + "%";
}

/* ---------- events ---------- */

$("q").addEventListener("input", renderCatalog);
$("cat").addEventListener("change", renderCatalog);

$("catalog").addEventListener("change", (e) => {
  const c = e.target.dataset.c;
  if (!c) return;
  if (e.target.checked) state.selected.add(c);
  else state.selected.delete(c);
});

$("clear").addEventListener("click", () => {
  state.selected.clear();
  renderCatalog();
});

$("order").addEventListener("click", orderSelected);

$("exams").addEventListener("click", (e) => {
  const b = e.target.closest("[data-e]");
  if (b) performExam(b.dataset.e);
});

$("results").addEventListener("click", (e) => {
  const b = e.target.closest(".thumb");
  if (!b) return;
  zoom = 1;
  $("dimg").src = b.dataset.img;
  $("dimg").style.width = "100%";
  $("dtitle").textContent = b.dataset.n;
  $("dlg").showModal();
});

$("zin").onclick = () => setZoom(zoom + 0.5);
$("zout").onclick = () => setZoom(zoom - 0.5);
$("zreset").onclick = () => setZoom(1);
$("dclose").onclick = () => $("dlg").close();

$("case").addEventListener("change", () => {
  state.caseId = $("case").value;
  loadCase();
});

$("restart").addEventListener("click", loadCase);

$("case").value = state.caseId;

(async function init() {
  try {
    await loadCatalog();
    await loadCase();
  } catch (e) {
    showError(e.message);
  }
  setInterval(tick, 1000);
})();