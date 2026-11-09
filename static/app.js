/* msksweb — the workspaces page (issue #02) over the scaffold's
   proxy (issue #01). Vanilla JS, no build step.

   Cell logic mirrors the CLI: status_with_mounts, image_column's
   middle clip, created_date's date cut — see
   msks/client/workspaces.py. */

"use strict";

const state = {
  workspaces: [],
  health: null,
  error: null,
  query: "",
  jsonView: false,
  loading: true,
  lastFetch: null,
  timer: null,
  tickTimer: null,
};

const $ = (id) => document.getElementById(id);

/* --- API with the UI-token gate ------------------------------------- */

function apiHeaders() {
  const headers = {};
  const token = localStorage.getItem("msksweb.token");
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function api(path) {
  const res = await fetch(path, { headers: apiHeaders() });
  if (res.status === 401) {
    openTokenDialog();
    throw new Error("ui token required");
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.detail || `${res.status} ${res.statusText}`);
  }
  return body;
}

/* --- Token dialog ----------------------------------------------------- */

function openTokenDialog() {
  const dlg = $("token-dialog");
  if (dlg.open) return;
  $("token-error").textContent = "";
  $("token-input").value = "";
  dlg.showModal();
  $("token-input").focus();
}

$("token-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const value = $("token-input").value.trim();
  localStorage.setItem("msksweb.token", value);
  $("token-dialog").close();
  refresh();
});

/* --- Rendering: health ------------------------------------------------ */

function renderHealth() {
  const pill = $("health-pill");
  const text = $("health-text");
  const h = state.health;
  if (!h) {
    pill.className = "health-pill";
    text.textContent = "probing…";
    return;
  }
  if (h.status === "ok") {
    pill.className = "health-pill ok";
    const v = h.daemon?.version ? `msksd v${h.daemon.version}` : "daemon";
    text.textContent = `${v} · ${h.daemon_address || ""}`;
    pill.title = `daemon ${h.daemon_address}\nversion ${h.daemon?.version ?? "?"} · ${h.daemon?.machine ?? "?"} · fastapi ${h.daemon?.fastapi ?? "?"}`;
  } else if (h.status === "unconfigured") {
    pill.className = "health-pill";
    text.textContent = "no daemon configured";
  } else {
    pill.className = "health-pill bad";
    text.textContent = `unreachable · ${h.daemon_address || ""}`;
  }
}

function renderBanners() {
  const host = $("banners");
  host.innerHTML = "";
  const h = state.health;

  const add = (cls, title, detail, retry) => {
    const el = document.createElement("div");
    el.className = `banner ${cls}`;
    const icon = cls === "error"
      ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v4m0 4h.01"/></svg>`
      : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4m0 4h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>`;
    el.innerHTML = `${icon}<div><div>${title}</div>${detail ? `<div class="detail"></div>` : ""}</div>`;
    if (detail) el.querySelector(".detail").textContent = detail;
    if (retry) {
      const btn = document.createElement("button");
      btn.className = "ghost-btn retry";
      btn.textContent = "Retry";
      btn.onclick = refresh;
      el.appendChild(btn);
    }
    host.appendChild(el);
  };

  if (h && h.status === "unconfigured") {
    add("warn", "No daemon configured",
        "set MSKSWEB_DAEMON_URL (or MSKSC_URL) for a remote daemon, or MSKSWEB_DAEMON_SOCKET / MSKSC_SOCKET for the local listener");
  } else if (h && h.status === "unreachable") {
    add("error", "Cannot reach the daemon",
        String(h.daemon_address || ""), true);
  }
  if (h && h.skew_notice) {
    add("warn", "Version skew", h.skew_notice);
  }
  if (state.error) {
    add("error", "The listing failed", state.error, true);
  }
}

/* --- Rendering: the table -------------------------------------------- */

/* The listing's image column width (#523): the CLI's own budget. */
const IMAGE_COLUMN_W = 16;

function clipMiddle(text, width) {
  if (text.length <= width) return text;
  const head = Math.ceil((width - 1) / 2);
  const tail = width - 1 - head;
  return `${text.slice(0, head)}…${text.slice(-tail)}`;
}

function imageCell(row) {
  const ref = row.image_ref || row.image_hash || "-";
  const clipped = clipMiddle(ref, IMAGE_COLUMN_W);
  const cell = document.createElement("span");
  cell.className = "mono";
  cell.textContent = clipped;
  if (clipped !== ref) cell.title = ref;
  return cell;
}

function createdDate(raw) {
  return raw ? raw.slice(0, 10) : "-";
}

/* status_with_mounts: the mounts' standing marker beside the pill. */
function statusWithMounts(row) {
  const issues = row.mount_issues || [];
  if (!issues.length) return { status: row.status, note: "" };
  const kinds = [...new Set(issues.map((i) => i.kind))].sort();
  const label = issues.length > 1
    ? `mounts ${kinds.join("/")}`
    : `mount ${issues[0].kind}`;
  return { status: row.status, note: `${issues.length} ${label}` };
}

function modeBadge(mode) {
  const el = document.createElement("span");
  const m = mode || "allow";
  el.className = `mode ${m}`;
  el.textContent = m;
  return el;
}

function esc(s) {
  return String(s ?? "");
}

function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove("show"), 1600);
}

function copyText(text) {
  navigator.clipboard?.writeText(text).then(
    () => toast(`copied ${text}`),
    () => {},
  );
}

function filtered() {
  const q = state.query.trim().toLowerCase();
  if (!q) return state.workspaces;
  return state.workspaces.filter((w) =>
    [w.name, w.id, w.image_ref, w.image_hash, w.host, w.status]
      .some((v) => esc(v).toLowerCase().includes(q)));
}

function skeletonRows() {
  const area = $("table-area");
  const table = document.createElement("table");
  table.className = "ws";
  table.innerHTML =
    `<thead><tr>${["name", "status", "egress", "created", "image", "host"]
      .map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>` +
    [0, 1, 2].map(() =>
      `<tr class="skel">${"<td><div class='bar'></div></td>".repeat(6)}</tr>`
    ).join("") + "</tbody>";
  area.innerHTML = "";
  area.appendChild(table);
}

function emptyState(filteredOut) {
  const area = $("table-area");
  const div = document.createElement("div");
  div.className = "empty";
  if (filteredOut) {
    div.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
      <h3>No match</h3>
      <div>Nothing matches “${state.query}”.</div>`;
  } else {
    div.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="6" rx="1.5"/><rect x="3" y="14" width="18" height="6" rx="1.5"/></svg>
      <h3>No workspaces yet</h3>
      <div>Create one from the CLI — the create dialog arrives with <a href="https://github.com/mcdonc/msksweb/issues/3" target="_blank" rel="noopener">issue #3</a>:</div>
      <div><code>msks create my-workspace</code></div>`;
  }
  area.innerHTML = "";
  area.appendChild(div);
}

function renderTable() {
  const rows = filtered();
  const area = $("table-area");

  if (state.loading) { skeletonRows(); return; }
  if (!state.workspaces.length) { emptyState(false); return; }
  if (!rows.length) { emptyState(true); return; }

  const table = document.createElement("table");
  table.className = "ws";

  const head = document.createElement("thead");
  head.innerHTML = `<tr>
    <th>name</th><th>status</th><th>egress</th>
    <th>created</th><th>image</th><th>host</th>
  </tr>`;
  table.appendChild(head);

  const body = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");

    const nameTd = document.createElement("td");
    const label = row.name || row.id;
    nameTd.innerHTML =
      `<div class="ws-name"></div><div class="ws-sub" title="click to copy the id"></div>`;
    nameTd.querySelector(".ws-name").textContent = label;
    const sub = nameTd.querySelector(".ws-sub");
    sub.textContent = row.id;
    sub.onclick = () => copyText(row.id);
    if (!row.name || row.name === row.id) sub.style.visibility = "hidden";
    tr.appendChild(nameTd);

    const { status, note } = statusWithMounts(row);
    const statusTd = document.createElement("td");
    const pill = document.createElement("span");
    pill.className = `pill ${status}`;
    pill.textContent = status;
    statusTd.appendChild(pill);
    if (note) {
      const n = document.createElement("span");
      n.className = "pill-note";
      n.textContent = note;
      n.title = (row.mount_issues || [])
        .map((i) => `${i.host || "?"} ${i.kind} (${i.detail})`).join("; ");
      statusTd.appendChild(n);
    }
    tr.appendChild(statusTd);

    const egTd = document.createElement("td");
    if (row.egress === false) {
      const off = document.createElement("span");
      off.className = "mode off";
      off.textContent = "off";
      egTd.appendChild(off);
    } else {
      egTd.appendChild(modeBadge(row.egress_mode));
    }
    tr.appendChild(egTd);

    const createdTd = document.createElement("td");
    createdTd.className = "dim";
    createdTd.textContent = createdDate(row.created_at);
    tr.appendChild(createdTd);

    const imageTd = document.createElement("td");
    imageTd.appendChild(imageCell(row));
    tr.appendChild(imageTd);

    const hostTd = document.createElement("td");
    hostTd.className = "mono dimmer";
    hostTd.textContent = row.host || "-";
    tr.appendChild(hostTd);

    body.appendChild(tr);
  }
  table.appendChild(body);
  area.innerHTML = "";
  area.appendChild(table);
}

function renderStats() {
  const host = $("stats");
  host.innerHTML = "";
  if (state.loading || !state.workspaces.length) return;
  const running = state.workspaces.filter((w) => w.status === "running").length;
  const inFlight = state.workspaces.filter((w) =>
    ["starting", "stopping"].includes(w.status)).length;
  const chip = (html) => {
    const el = document.createElement("span");
    el.className = "chip";
    el.innerHTML = html;
    host.appendChild(el);
  };
  chip(`<b>${state.workspaces.length}</b> workspace${state.workspaces.length === 1 ? "" : "s"}`);
  if (running) chip(`<span class="dot"></span><b>${running}</b> running`);
  if (inFlight) chip(`<b>${inFlight}</b> in transition`);
}

function renderJson() {
  const card = $("json-card");
  $("workspaces-card").hidden = state.jsonView;
  card.hidden = !state.jsonView;
  if (state.jsonView) {
    $("json-doc").textContent = JSON.stringify(state.workspaces, null, 2);
  }
  $("json-toggle").classList.toggle("on", state.jsonView);
}

function renderUpdated() {
  const el = $("updated-line");
  if (!state.lastFetch) { el.innerHTML = ""; return; }
  const secs = Math.max(0, Math.round((Date.now() - state.lastFetch) / 1000));
  el.innerHTML = `<span class="live-dot"></span> live · updated ${secs === 0 ? "just now" : `${secs}s ago`}`;
}

/* --- Data cycle -------------------------------------------------------- */

async function refresh() {
  try {
    state.health = await api("/api/health");
  } catch {
    /* the token dialog already opened, or a transient miss —
       the banner speaks from what we have */
  }
  state.error = null;
  try {
    state.workspaces = await api("/api/workspaces");
  } catch (e) {
    state.error = e.message;
  }
  state.loading = false;
  state.lastFetch = Date.now();
  renderHealth();
  renderBanners();
  renderStats();
  renderTable();
  renderJson();
  renderUpdated();
}

/* --- Wiring ------------------------------------------------------------- */

$("refresh-btn").addEventListener("click", () => {
  const icon = $("refresh-btn").querySelector("svg");
  icon.style.transition = "transform 0.5s";
  icon.style.transform = "rotate(360deg)";
  setTimeout(() => { icon.style.transition = ""; icon.style.transform = ""; }, 500);
  refresh();
});

$("json-toggle").addEventListener("click", () => {
  state.jsonView = !state.jsonView;
  renderJson();
});

$("search").addEventListener("input", (ev) => {
  state.query = ev.target.value;
  renderTable();
});

document.addEventListener("keydown", (ev) => {
  if (ev.key === "/" && document.activeElement !== $("search")
      && !ev.target.closest("input, textarea, dialog")) {
    ev.preventDefault();
    $("search").focus();
  }
});

/* The theme toggle: dark default, light opt-in, remembered. */
const savedTheme = localStorage.getItem("msksweb.theme");
if (savedTheme) document.documentElement.dataset.theme = savedTheme;

$("theme-toggle").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("msksweb.theme", next);
});

/* Poll a few seconds while the tab is visible — boots and stops
   animate through their transitions (the CLI's watch posture). */
const POLL_MS = 3000;

function schedule() {
  clearInterval(state.timer);
  state.timer = setInterval(() => {
    if (!document.hidden) refresh();
  }, POLL_MS);
}

setInterval(renderUpdated, 1000);

refresh();
schedule();
