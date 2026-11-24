/* Tool-X GUI frontend
   No frameworks, no CDN — works fully offline once the page is loaded. */

const ICONS = {
  all: '<path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/>',
  default: '<rect x="4" y="7" width="16" height="13" rx="1"/><path d="M4 7l8-4 8 4"/>',
  information_gathering: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M20 20l-5-5"/>',
  vulnerability_scanner: '<path d="M12 3v3M12 18v3M4.2 7l2.4 1.4M17.4 15.6l2.4 1.4M4.2 17l2.4-1.4M17.4 8.4l2.4-1.4"/><rect x="8" y="8" width="8" height="10" rx="4"/><path d="M8 12H4M20 12h-4"/>',
  exploitation_tools: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
  wireless_testing: '<path d="M4 9a13 13 0 0 1 16 0M7 12.5a8.5 8.5 0 0 1 10 0M10.3 16a4 4 0 0 1 3.4 0"/><circle cx="12" cy="19" r="1"/>',
  forensics_tools: '<path d="M12 3a5 5 0 0 0-5 5v3a9 9 0 0 0 4 7.5M12 3a5 5 0 0 1 5 5v3a9 9 0 0 1-2 5.6M9 10v2a3 3 0 0 0 1.4 2.5M15 10v2a7 7 0 0 1-1 3.6"/>',
  web_hacking: '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.2 2.3 3.3 5.3 3.3 8.5s-1.1 6.2-3.3 8.5c-2.2-2.3-3.3-5.3-3.3-8.5S9.8 5.8 12 3.5z"/>',
  stress_testing: '<path d="M4 15a8 8 0 1 1 16 0"/><path d="M12 15l4-5"/><circle cx="12" cy="15" r="1"/>',
  sniffing_spoofing: '<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z"/><circle cx="12" cy="12" r="2.6"/>',
  password_attack: '<circle cx="8" cy="12" r="4"/><path d="M12 12h9M17 12v3M20 12v3"/>',
  maintaining_access: '<rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  ip_tracking: '<path d="M12 21s7-6.3 7-11.5A7 7 0 1 0 5 9.5C5 14.7 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.4"/>',
  programming_language: '<path d="M9 7 4 12l5 5M15 7l5 5-5 5"/>',
  ddos: '<path d="M13 2 4 14h6l-1 8 9-12h-6z"/>',
  web_server: '<rect x="4" y="4" width="16" height="6" rx="1"/><rect x="4" y="14" width="16" height="6" rx="1"/><circle cx="8" cy="7" r="0.8" fill="currentColor"/><circle cx="8" cy="17" r="0.8" fill="currentColor"/>',
  termux_os: '<rect x="3" y="4" width="18" height="16" rx="1.5"/><path d="M7 9l3 3-3 3M13 15h4"/>',
};

function iconSvg(key) {
  const inner = ICONS[key] || ICONS.default;
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${inner}</svg>`;
}

const state = {
  tools: [],
  categories: {},
  activeCat: "__all__",
  query: "",
};

const grid = document.getElementById("grid");
const catList = document.getElementById("catList");
const searchInput = document.getElementById("search");
const resultCount = document.getElementById("resultCount");
const emptyState = document.getElementById("emptyState");
const statInstalled = document.getElementById("statInstalled");
const statPending = document.getElementById("statPending");
const logDrawer = document.getElementById("logDrawer");
const logTitle = document.getElementById("logTitle");
const logBody = document.getElementById("logBody");
const logClose = document.getElementById("logClose");

logClose.addEventListener("click", () => { logDrawer.hidden = true; });

async function loadData() {
  const res = await fetch("/api/data");
  const payload = await res.json();
  state.tools = payload.tools;
  state.categories = payload.categories;
  buildSidebar();
  render();
}

function buildSidebar() {
  document.getElementById("countAll").textContent = state.tools.length;
  Object.entries(state.categories).forEach(([key, label]) => {
    const count = state.tools.filter((t) => t.category.includes(key)).length;
    const btn = document.createElement("button");
    btn.className = "cat-item";
    btn.dataset.cat = key;
    btn.innerHTML = `
      <span class="cat-icon">${iconSvg(key)}</span>
      <span class="cat-label">${label}</span>
      <span class="cat-count">${count}</span>`;
    btn.addEventListener("click", () => setActiveCat(key));
    catList.appendChild(btn);
  });
  catList.querySelector('[data-cat="__all__"]').innerHTML = `
    <span class="cat-icon">${iconSvg("all")}</span>
    <span class="cat-label">All tools</span>
    <span class="cat-count" id="countAll">${state.tools.length}</span>`;
  catList.querySelector('[data-cat="__all__"]').addEventListener("click", () => setActiveCat("__all__"));
}

function setActiveCat(key) {
  state.activeCat = key;
  document.querySelectorAll(".cat-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.cat === key);
  });
  render();
}

searchInput.addEventListener("input", (e) => {
  state.query = e.target.value.trim().toLowerCase();
  render();
});

function filteredTools() {
  return state.tools.filter((t) => {
    const inCat = state.activeCat === "__all__" || t.category.includes(state.activeCat);
    const inSearch = !state.query || t.name.toLowerCase().includes(state.query);
    return inCat && inSearch;
  });
}

function render() {
  const list = filteredTools();
  resultCount.textContent = `${list.length} tool${list.length === 1 ? "" : "s"}`;
  grid.innerHTML = "";
  emptyState.hidden = list.length !== 0;

  let installed = 0;
  state.tools.forEach((t) => { if (t.state === "installed") installed += 1; });
  statInstalled.textContent = installed;
  statPending.textContent = state.tools.length - installed;

  const frag = document.createDocumentFragment();
  list.forEach((tool) => frag.appendChild(renderCard(tool)));
  grid.appendChild(frag);
}

function renderCard(tool) {
  const el = document.createElement("div");
  el.className = "card";
  el.dataset.name = tool.name;

  const primaryCat = tool.category[0];
  const catPills = tool.category
    .map((c) => `<span class="pill">${state.categories[c] || c}</span>`)
    .join("");

  el.innerHTML = `
    <div class="card-top">
      <div class="card-icon">${iconSvg(primaryCat)}</div>
      <div>
        <div class="card-name">${tool.name}</div>
        <div class="card-meta">${tool.package_manager}</div>
      </div>
    </div>
    <div class="card-cats">${catPills}</div>
    <div class="card-action">
      <button class="btn ${btnClass(tool.state)}">${btnLabel(tool.state)}</button>
    </div>
  `;

  const btn = el.querySelector(".btn");
  btn.addEventListener("click", () => handleInstallClick(tool, btn));
  if (tool.state === "installing") pollStatus(tool.name, btn);

  return el;
}

function btnClass(s) {
  if (s === "installed") return "state-installed";
  if (s === "installing") return "state-installing";
  if (s === "failed") return "state-failed";
  if (s === "needs_root") return "state-needs_root";
  return "";
}

function btnLabel(s) {
  if (s === "installed") return "Installed";
  if (s === "installing") return "Installing…";
  if (s === "failed") return "Retry install";
  if (s === "needs_root") return "Needs sudo (see log)";
  return "Install";
}

async function handleInstallClick(tool, btn) {
  if (tool.state === "installed") {
    openLog(tool.name, [`'${tool.name}' is already installed.`]);
    return;
  }
  if (tool.state === "installing") {
    openLog(tool.name, []);
    return;
  }
  btn.disabled = true;
  btn.textContent = "Installing…";
  btn.className = "btn state-installing";
  openLog(tool.name, [`Starting install of ${tool.name}…`]);

  await fetch(`/api/install/${encodeURIComponent(tool.name)}`, { method: "POST" });
  pollStatus(tool.name, btn);
}

function pollStatus(name, btn) {
  const timer = setInterval(async () => {
    const res = await fetch(`/api/status/${encodeURIComponent(name)}`);
    const data = await res.json();

    if (!logDrawer.hidden && logTitle.dataset.tool === name) {
      logBody.textContent = data.log.join("\n");
      logBody.scrollTop = logBody.scrollHeight;
    }

    if (data.state !== "installing") {
      clearInterval(timer);
      btn.disabled = false;
      btn.className = `btn ${btnClass(data.state)}`;
      btn.textContent = btnLabel(data.state);
      const toolRef = state.tools.find((t) => t.name === name);
      if (toolRef) toolRef.state = data.state;
      render();
    }
  }, 1000);
}

function openLog(name, initialLines) {
  logDrawer.hidden = false;
  logTitle.textContent = name;
  logTitle.dataset.tool = name;
  logBody.textContent = initialLines.join("\n");
}

loadData();
