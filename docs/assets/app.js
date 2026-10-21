/* Hotspawn LoL Picks — data-driven UI (vanilla JS, no build step) */
(() => {
  "use strict";
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const pct = (x) => (x == null ? "—" : `${Math.round(x * 100)}%`);
  const pct1 = (x) => (x == null ? "—" : `${(x * 100).toFixed(1)}%`);
  const METHOD = {
    MARKET_CONSENSUS: { label: "Market consensus", cls: "green", ico: "💰" },
    MARKET_SINGLE: { label: "Single book line", cls: "green", ico: "💰" },
    MODEL_ELO: { label: "Own Elo model", cls: "blue", ico: "🧮" },
    MODEL_ELO_THIN: { label: "Elo (thin history)", cls: "amber", ico: "🧮" },
    MODEL_LEAGUE_PRIOR: { label: "League prior", cls: "amber", ico: "📐" },
    UNRESOLVED: { label: "Unresolved", cls: "red", ico: "⚠️" },
  };
  const CONF = { High: "green", Medium: "blue", Low: "amber", None: "red" };
  const CONF_RANK = { High: 3, Medium: 2, Low: 1, None: 0 };
  const METHOD_RANK = { MARKET_CONSENSUS: 5, MARKET_SINGLE: 4, MODEL_ELO: 3, MODEL_ELO_THIN: 2, MODEL_LEAGUE_PRIOR: 1, UNRESOLVED: 0 };
  const PAGE = document.body.dataset.page || "";
  let DATA = null;

  const state = { filter: "all", q: "", tournament: "", sort: "time" };

  function toastError(err) {
    const box = $("#error-box");
    const msg = `Could not load picks data (${esc(err && err.message ? err.message : err)}). The scheduled GitHub Action may not have run yet.`;
    if (box) { box.className = "dangerbox"; box.innerHTML = `<b>Data unavailable.</b> ${msg}`; }
    $$(".loading").forEach((el) => { el.innerHTML = `<span class="dot bad"></span> ${msg}`; });
    console.error(err);
  }

  async function load() {
    const res = await fetch("data/picks.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function whenLocal(iso) {
    if (!iso) return { text: "Time TBC", title: "" };
    const d = new Date(iso);
    if (isNaN(d)) return { text: iso, title: "" };
    const text = d.toLocaleString(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
    const title = `${d.toLocaleString()} (${d.toUTCString()})`;
    return { text, title };
  }
  function whenUTC(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    return isNaN(d) ? "—" : `${d.toISOString().slice(0, 16).replace("T", " ")} UTC`;
  }
  function relative(iso) {
    if (!iso) return "";
    const ms = new Date(iso) - new Date();
    const abs = Math.abs(ms);
    const mins = Math.round(abs / 60000);
    if (mins < 60) return ms >= 0 ? `in ${mins} min` : `${mins} min ago`;
    const hrs = Math.round(abs / 3600000);
    if (hrs < 36) return ms >= 0 ? `in ${hrs} h` : `${hrs} h ago`;
    return ms >= 0 ? `in ${Math.round(hrs / 24)} d` : `${Math.round(hrs / 24)} d ago`;
  }
  function isFresh(d) {
    if (!d.stale_after_utc) return true;
    return new Date(d.stale_after_utc) > new Date();
  }
  function methodInfo(m) { return METHOD[m.method] || { label: m.method, cls: "", ico: "•" }; }
  function matchClass(m) {
    if (m.method === "UNRESOLVED") return "unres";
    if (m.market) return "market";
    if (m.method === "MODEL_LEAGUE_PRIOR" || m.method === "MODEL_ELO_THIN" || m.confidence === "Low") return "partial";
    return "model";
  }
  function sourcesInline(m, max = 4) {
    const list = (m.sources || []).filter((s) => s.url).slice(0, max);
    if (!list.length) return "";
    return `<div class="src-links">${list.map((s) => `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)} ↗</a>`).join("")}</div>`;
  }

  function matchCard(m, opts = {}) {
    const cls = matchClass(m);
    const t = whenLocal(m.start_utc);
    const mi = methodInfo(m);
    return `<article class="match ${cls}">
      <div class="match-top"><span class="when" title="${esc(t.title)}">${esc(t.text)}</span><span>·</span><span>${esc(m.tournament || "Tournament TBC")}</span>${m.best_of ? `<span>· Bo${esc(m.best_of)}</span>` : ""}<span class="chip ${cls === "unres" ? "red" : cls === "partial" ? "amber" : cls === "market" ? "green" : "blue"}">${mi.ico} ${esc(mi.label)}</span></div>
      <div class="teams"><a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team1)}</a> <span class="vs">vs</span> <a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team2)}</a></div>
      <div class="bar" aria-hidden="true"><i style="width:${pct(m.prob_team1)}"></i><b style="width:${pct(m.prob_team2)}"></b></div>
      <div class="probrow"><span>${esc(m.team1)} <b>${pct1(m.prob_team1)}</b></span><span style="margin-left:auto">${esc(m.team2)} <b>${pct1(m.prob_team2)}</b></span></div>
      <div class="pickline"><span class="pick">✅ ${esc(m.pick)} <span class="p">${pct1(m.pick_prob)}</span></span><span class="chip ${CONF[m.confidence] || ""}">${esc(m.confidence || "—")} confidence</span></div>
      <div class="evidence">${esc(m.evidence || "")}</div>
      ${sourcesInline(m, opts.sources || 3)}
    </article>`;
  }

  function row(m) {
    const t = whenLocal(m.start_utc);
    const mi = methodInfo(m);
    const cls = matchClass(m);
    const srcCount = (m.sources || []).filter((s) => s.url).length;
    const srcLinks = (m.sources || []).filter((s) => s.url).slice(0, 2)
      .map((s) => `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)} ↗</a>`).join(" ");
    return `<tr class="${cls}">
      <td data-label="Start" title="${esc(t.title)}"><b>${esc(t.text)}</b><span class="sub">${esc(whenUTC(m.start_utc))}</span><span class="sub">${esc(relative(m.start_utc))}</span></td>
      <td class="teams-cell" data-label="Match"><a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team1)}</a> <span class="vs">vs</span> <a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team2)}</a><span class="sub">${esc(m.tournament || "")}${m.best_of ? ` · Bo${esc(m.best_of)}` : ""}${m.tier ? ` · Tier ${esc(m.tier)}` : ""}</span></td>
      <td class="probcell" data-label="Win probability"><span class="p1">${esc(m.team1)} ${pct1(m.prob_team1)}</span><span class="sub"><span class="p2">${esc(m.team2)} ${pct1(m.prob_team2)}</span></span><div class="bar" aria-hidden="true"><i style="width:${pct(m.prob_team1)}"></i><b style="width:${pct(m.prob_team2)}"></b></div></td>
      <td class="pickcell" data-label="Pick">${esc(m.pick)}<span class="p">${pct1(m.pick_prob)}</span></td>
      <td data-label="Method"><span class="chip ${mi.cls}">${mi.ico} ${esc(mi.label)}</span><span class="sub"><span class="chip ${CONF[m.confidence] || ""}">${esc(m.confidence || "—")}</span></span></td>
      <td data-label="Sources"><span class="sub">${srcCount} link${srcCount === 1 ? "" : "s"}</span><div class="src-links">${srcLinks}</div></td>
    </tr>`;
  }

  function setHeader(d) {
    const upd = $("#updated");
    const fresh = $("#freshness");
    const t = whenLocal(d.generated_at);
    if (upd) upd.innerHTML = `<b>Updated</b> ${esc(t.text)}`;
    const fu = $("#footer-updated");
    if (fu) fu.textContent = `Data generated ${whenUTC(d.generated_at)} · every 6 hours.`;
    if (fresh) {
      const ok = isFresh(d);
      fresh.innerHTML = `<span class="dot ${ok ? "" : "stale"}"></span>${ok ? "Live data" : "Stale — check the scheduled update"}`;
      fresh.title = `Next scheduled update: ${whenUTC(d.next_update_utc)}`;
    }
    const warn = $("#freshness-warning");
    if (warn && !isFresh(d)) {
      warn.className = "warnbox";
      warn.innerHTML = `<b>This data is older than expected.</b> Last update ${esc(t.text)}; next expected ${esc(whenUTC(d.next_update_utc))}. The 6-hour GitHub Action may have failed — check the repository Actions tab.`;
    }
    document.title = document.title.replace("Hotspawn LoL", "Hotspawn LoL");
  }

  function setActiveNav() {
    $$("[data-nav]").forEach((a) => {
      if (a.getAttribute("data-nav") === PAGE) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  }

  function renderIndex(d) {
    const c = d.counts || {};
    const set = (id, v) => { const el = $(id); if (el) el.textContent = v; };
    set("#stat-fixtures", c.fixtures ?? "—");
    set("#stat-market", c.market ?? "—");
    set("#stat-model", c.model ?? "—");
    set("#stat-unresolved", c.unresolved ?? "—");
    const cov = d.coverage || {};
    const covText = $("#coverage-text");
    if (covText) covText.innerHTML = `<b>${cov.resolved ?? 0} of ${cov.fixtures ?? 0}</b> fixtures have a pick with verified inputs (${cov.resolved_pct ?? 0}%). ${cov.unresolved ?? 0} are published as explicit 50/50 placeholders and listed on the <a href="unresolved.html">Unresolved page</a>.`;
    const covBar = $("#coverage-bar");
    if (covBar) covBar.innerHTML = `<i style="width:${cov.resolved_pct || 0}%"></i><b style="width:${100 - (cov.resolved_pct || 0)}%"></b>`;

    const byId = new Map((d.matches || []).map((m) => [m.id, m]));
    const next = (d.next_24h || []).map((id) => byId.get(id)).filter(Boolean).slice(0, 6);
    const nextBox = $("#next24");
    if (nextBox) nextBox.innerHTML = next.length ? next.map((m) => matchCard(m, { sources: 2 })).join("") : `<div class="card">No matches in the next 24 hours.</div>`;

    const featured = (d.matches || []).filter((m) => m.market).sort((a, b) => (a.start_utc || "").localeCompare(b.start_utc || "")).slice(0, 8);
    const featBox = $("#featured");
    if (featBox) featBox.innerHTML = featured.length ? featured.map((m) => matchCard(m, { sources: 4 })).join("")
      : `<div class="card">No external market lines are available right now. Every match below is priced by our own model or marked unresolved.</div>`;

    const u = d.unresolved || {};
    const reasons = (u.reasons || []).map((r) => `<li><b>${r.count}</b> — ${esc(r.reason)}</li>`).join("");
    const lims = (u.limitations || []).slice(0, 3).map((x) => `<li>${esc(x)}</li>`).join("");
    const ubox = $("#unresolved-summary");
    if (ubox) ubox.innerHTML = `<div class="warnbox"><h3>⚠️ Unresolved picks — ${u.count ?? 0} match${(u.count ?? 0) === 1 ? "" : "es"}</h3>
      <p>${u.count ?? 0} fixture${(u.count ?? 0) === 1 ? "" : "s"} have no external betting line and no usable team history, so the published pick is an explicit 50/50 placeholder — <b>not an edge</b>. ${u.low_confidence_count ?? 0} more use a low-confidence league prior. Hotspawn's crowd percentage is never used.</p>
      ${reasons ? `<p class="small"><b>Reasons</b></p><ul class="clean small">${reasons}</ul>` : ""}
      <p class="small"><b>Key limitations</b></p><ul class="clean small">${lims}</ul>
      <p><a class="btn warn" href="unresolved.html">See every unresolved pick and all limitations →</a></p></div>`;

    const ss = $("#sources-strip");
    if (ss) ss.innerHTML = (d.sources_status || []).map((s) => `<span class="chip ${s.status === "ok" ? "green" : "amber"}" title="${esc(s.note || "")}">${esc(s.name)} · ${esc(s.status)}${s.count != null ? ` · ${s.count}` : ""}</span>`).join(" ");
  }

  function applyFilter(m) {
    const now = Date.now();
    if (state.filter === "next24") {
      const t = new Date(m.start_utc).getTime();
      if (!(t >= now - 300000 && t <= now + 86400000)) return false;
    }
    if (state.filter === "market" && !m.market) return false;
    if (state.filter === "model" && !(m.model && !m.market)) return false;
    if (state.filter === "low" && !(m.method === "MODEL_ELO_THIN" || m.method === "MODEL_LEAGUE_PRIOR" || m.confidence === "Low")) return false;
    if (state.filter === "unresolved" && m.method !== "UNRESOLVED") return false;
    if (state.tournament && m.tournament !== state.tournament) return false;
    if (state.q) {
      const hay = `${m.team1} ${m.team2} ${m.tournament} ${m.pick}`.toLowerCase();
      if (!hay.includes(state.q)) return false;
    }
    return true;
  }

  function sortMatches(list) {
    const arr = list.slice();
    if (state.sort === "time") arr.sort((a, b) => (a.start_utc || "").localeCompare(b.start_utc || ""));
    if (state.sort === "pick") arr.sort((a, b) => (b.pick_prob || 0) - (a.pick_prob || 0));
    if (state.sort === "confidence") arr.sort((a, b) => (CONF_RANK[b.confidence] || 0) - (CONF_RANK[a.confidence] || 0) || (METHOD_RANK[b.method] || 0) - (METHOD_RANK[a.method] || 0) || (a.start_utc || "").localeCompare(b.start_utc || ""));
    if (state.sort === "tournament") arr.sort((a, b) => (a.tournament || "").localeCompare(b.tournament || "") || (a.start_utc || "").localeCompare(b.start_utc || ""));
    return arr;
  }

  function renderPicks(d) {
    const tbody = $("#picks-body");
    if (!tbody) return;
    const all = d.matches || [];
    const tournaments = Array.from(new Set(all.map((m) => m.tournament).filter(Boolean))).sort();
    const sel = $("#tournament");
    if (sel && !sel.dataset.ready) {
      sel.innerHTML = `<option value="">All tournaments (${tournaments.length})</option>` + tournaments.map((t) => `<option value="${esc(t)}">${esc(t)}</option>`).join("");
      sel.dataset.ready = "1";
      sel.value = state.tournament;
    }
    const rows = sortMatches(all.filter(applyFilter));
    tbody.innerHTML = rows.length ? rows.map(row).join("") : `<tr><td colspan="6"><div class="card">No matches match these filters. <button class="chipbtn" onclick="document.getElementById('reset').click()">Reset filters</button></div></td></tr>`;
    const count = $("#countline");
    if (count) count.textContent = `Showing ${rows.length} of ${all.length} fixtures · ${all.filter((m) => m.market).length} with external lines · ${all.filter((m) => m.method === "UNRESOLVED").length} unresolved`;
    const counts = {
      all: all.length,
      next24: all.filter((m) => applyFilterWith(m, "next24")).length,
      market: all.filter((m) => m.market).length,
      model: all.filter((m) => m.model && !m.market).length,
      low: all.filter((m) => m.method === "MODEL_ELO_THIN" || m.method === "MODEL_LEAGUE_PRIOR" || m.confidence === "Low").length,
      unresolved: all.filter((m) => m.method === "UNRESOLVED").length,
    };
    $$("[data-filter]").forEach((b) => {
      b.setAttribute("aria-pressed", b.dataset.filter === state.filter ? "true" : "false");
      const n = $(".n", b);
      if (n) n.textContent = counts[b.dataset.filter] ?? "";
    });
    const url = new URL(location.href);
    if (state.filter !== "all") url.searchParams.set("filter", state.filter); else url.searchParams.delete("filter");
    history.replaceState(null, "", url.toString());
  }

  function applyFilterWith(m, f) {
    const saved = state.filter;
    state.filter = f;
    const ok = applyFilter(m);
    state.filter = saved;
    return ok;
  }

  function renderUnresolved(d) {
    const all = (d.matches || []).slice().sort((a, b) => (a.start_utc || "").localeCompare(b.start_utc || ""));
    const un = all.filter((m) => m.method === "UNRESOLVED");
    const low = all.filter((m) => m.method !== "UNRESOLVED" && (m.method === "MODEL_ELO_THIN" || m.method === "MODEL_LEAGUE_PRIOR" || m.confidence === "Low"));
    const ub = $("#unresolved-body");
    if (ub) ub.innerHTML = un.length ? un.map((m) => matchCard(m, { sources: 3 })).join("") : `<div class="okbox">None right now — every fixture has either an external market line or usable team history.</div>`;
    const lb = $("#lowconf-body");
    if (lb) lb.innerHTML = low.length ? low.map((m) => matchCard(m, { sources: 3 })).join("") : `<div class="card">No low-confidence rows.</div>`;
    const reasons = (d.unresolved?.reasons || []).map((r) => `<li><b>${r.count}</b> — ${esc(r.reason)}</li>`).join("");
    const rbox = $("#reasons");
    if (rbox) rbox.innerHTML = reasons || "<li>None.</li>";
    const lim = (d.unresolved?.limitations || []).map((x) => `<li>${esc(x)}</li>`).join("");
    const lbox = $("#limitations");
    if (lbox) lbox.innerHTML = lim;
    const stat = $("#unresolved-counts");
    if (stat) stat.innerHTML = `<b>${un.length}</b> unresolved · <b>${low.length}</b> low-confidence · <b>${(d.counts?.market ?? 0)}</b> with external market lines`;
  }

  function flagLabel(f) {
    const map = {
      NO_EXTERNAL_MARKET: "No external market line",
      NO_TEAM_HISTORY: "No recorded team history",
      ONE_TEAM_NO_HISTORY: "One team has no history (prior used)",
      THIN_HISTORY: "Thin history (<5 games)",
      NO_VERIFIED_SIGNAL: "No verified signal",
      MODEL_DISAGREES_WITH_MARKET: "Model disagrees with market (≥8 pts)",
      MARKET_DISAGREEMENT: "Sources disagree (>10 pts)",
      NO_HOTSPAWN_MATCH_PAGE: "Hotspawn match page not published",
      TIER_UNVERIFIED: "Hotspawn tier unverified",
      START_TIME_MISMATCH: "Start time differs from Leaguepedia (>30 min)",
      START_TIME_DISAGREES_WITH_BOOKS: "Bookmaker start time differs from Hotspawn (>1.5 h)",
      CROSS_LEAGUE_MODEL: "Teams' recent competitions differ (model capped at Low)",
    };
    return map[f] || f;
  }

  function renderFlagged(d) {
    const groups = {};
    (d.matches || []).forEach((m) => (m.flags || []).forEach((f) => { (groups[f] = groups[f] || []).push(m); }));
    const order = Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length);
    const gb = $("#flag-groups");
    if (gb) gb.innerHTML = order.length ? order.map((f) => `<tr><td><span class="flag">${esc(f)}</span><span class="sub">${esc(flagLabel(f))}</span></td><td><b>${groups[f].length}</b></td><td><a href="picks.html?filter=${f === "NO_EXTERNAL_MARKET" || f === "NO_VERIFIED_SIGNAL" ? "unresolved" : "all"}">view</a></td></tr>`).join("") : `<tr><td colspan="3">No flags.</td></tr>`;
    const flagged = (d.matches || []).filter((m) => (m.flags || []).length).sort((a, b) => (a.start_utc || "").localeCompare(b.start_utc || ""));
    const body = $("#flagged-body");
    if (body) body.innerHTML = flagged.map((m) => `<tr class="${matchClass(m)}"><td data-label="Start"><b>${esc(whenLocal(m.start_utc).text)}</b></td><td class="teams-cell" data-label="Match"><a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team1)} vs ${esc(m.team2)}</a><span class="sub">${esc(m.tournament || "")}</span></td><td data-label="Flags">${(m.flags || []).map((f) => `<span class="chip amber flag" title="${esc(flagLabel(f))}">${esc(f)}</span>`).join(" ")}</td><td data-label="Pick">${esc(m.pick)} <span class="sub">${pct1(m.pick_prob)}</span></td></tr>`).join("");
    const ss = $("#sources-status");
    if (ss) ss.innerHTML = (d.sources_status || []).map((s) => `<tr><td><b>${esc(s.name)}</b>${s.url ? `<span class="sub"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a></span>` : ""}</td><td><span class="chip ${s.status === "ok" ? "green" : "amber"}">${esc(s.status)}</span></td><td>${s.count ?? "—"}</td><td class="small">${esc(s.note || "")}</td></tr>`).join("");
    const cu = $("#checked-unavailable");
    if (cu) cu.innerHTML = (d.checked_unavailable || []).map((s) => `<tr><td><b>${esc(s.name)}</b><span class="sub"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a></span></td><td class="small">${esc(s.observed)}</td><td class="small">${esc(s.consequence)}</td></tr>`).join("");
  }

  function renderMatch(d) {
    const box = $("#match-detail");
    if (!box) return;
    const id = new URLSearchParams(location.search).get("id");
    const m = (d.matches || []).find((x) => String(x.id) === String(id));
    if (!m) {
      box.innerHTML = `<div class="dangerbox"><b>Match not found.</b> It may have locked or dropped off the Hotspawn fixture list. <a href="picks.html">See all current picks →</a></div>`;
      return;
    }
    const mi = methodInfo(m);
    const t = whenLocal(m.start_utc);
    const marketRows = (m.market?.sources || []).map((s) => `<tr><td><b>${esc(s.source)}</b></td><td>${pct1(s.prob_team1)}</td><td>${pct1(s.prob_team2)}</td><td>${s.decimal_team1 ? esc(s.decimal_team1) : "—"}</td><td><a href="${esc(s.url)}" target="_blank" rel="noopener">open ↗</a></td></tr>`).join("");
    const model = m.model || {};
    const h2h = model.h2h ? `${model.h2h.team1_wins}/${model.h2h.games} head-to-head wins for ${esc(m.team1)}` : "No head-to-head sample in the last 24 months.";
    box.innerHTML = `
      <div class="detail-hero">
        <div class="match-top"><span class="chip ${mi.cls}">${mi.ico} ${esc(mi.label)}</span><span class="chip ${CONF[m.confidence] || ""}">${esc(m.confidence || "—")} confidence</span>${m.best_of ? `<span class="chip">Bo${esc(m.best_of)}</span>` : ""}${m.tier ? `<span class="chip">Tier ${esc(m.tier)}</span>` : ""}</div>
        <h1>${esc(m.team1)} <span style="color:var(--muted);font-weight:600;font-size:.6em">vs</span> ${esc(m.team2)}</h1>
        <p class="small">${esc(m.tournament || "")} · ${esc(t.text)} <span title="${esc(t.title)}">· ${esc(whenUTC(m.start_utc))}</span> · ${esc(relative(m.start_utc))}</p>
        <div class="bar" aria-hidden="true"><i style="width:${pct(m.prob_team1)}"></i><b style="width:${pct(m.prob_team2)}"></b></div>
        <div class="probrow"><span>${esc(m.team1)} <b>${pct1(m.prob_team1)}</b></span><span style="margin-left:auto">${esc(m.team2)} <b>${pct1(m.prob_team2)}</b></span></div>
        <div class="pickline"><span class="pick">✅ PICK: ${esc(m.pick)} <span class="p">${pct1(m.pick_prob)}</span></span></div>
        <p class="small">${esc(m.evidence || "")}</p>
      </div>
      <div class="two-col">
        <div>
          <div class="card"><h3>${m.market ? "External betting lines" : "No external betting line"}</h3>
            ${m.market ? `<p class="small">Consensus: <b>${pct1(m.market.consensus_team1)}</b> ${esc(m.team1)} · <b>${pct1(1 - m.market.consensus_team1)}</b> ${esc(m.team2)}. Dispersion ${pct1(m.market.dispersion)} across ${m.market.source_count} source(s).${m.market.model_team1 != null ? ` Model: ${pct1(m.market.model_team1)} (edge ${(m.market.model_edge_team1 * 100 >= 0 ? "+" : "")}${(m.market.model_edge_team1 * 100).toFixed(1)} pts).` : ""}</p>
            <div class="table-wrap"><table><thead><tr><th>Source</th><th>${esc(m.team1)}</th><th>${esc(m.team2)}</th><th>Decimal</th><th></th></tr></thead><tbody>${marketRows}</tbody></table></div>`
            : `<p>No bookmaker or prediction-market line was found for this fixture at the time of the update. The pick comes from ${m.model ? "our own Elo model" : "an explicit 50/50 placeholder"}.</p>`}
          </div>
          <div class="card"><h3>Our model</h3>
            ${m.model ? `<dl class="kv">
              <dt>Elo (team 1)</dt><dd>${model.elo_team1 ?? "—"} <span class="small">${model.games_team1_365d != null ? `(${model.games_team1_365d} games in 365d)` : ""}</span></dd>
              <dt>Elo (team 2)</dt><dd>${model.elo_team2 ?? "—"} <span class="small">${model.games_team2_365d != null ? `(${model.games_team2_365d} games in 365d)` : ""}</span></dd>
              <dt>Prior used</dt><dd>${esc(model.prior_used || "—")}</dd>
              <dt>Head-to-head</dt><dd>${h2h}</dd>
              <dt>Tournament page</dt><dd>${m.leaguepedia_url ? `<a href="${esc(m.leaguepedia_url)}" target="_blank" rel="noopener">Leaguepedia ↗</a>` : "—"}</dd>
            </dl>` : `<p>No rated team history was available. The row is an explicit 50/50 placeholder.</p>`}
          </div>
        </div>
        <div>
          <div class="card"><h3>Flags</h3>${(m.flags || []).length ? `<ul class="clean small">${m.flags.map((f) => `<li><span class="flag">${esc(f)}</span> — ${esc(flagLabel(f))}</li>`).join("")}</ul>` : `<p class="small">No flags.</p>`}</div>
          <div class="card"><h3>Sources & verification</h3><ul class="clean small">${(m.sources || []).map((s) => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)} ↗</a> — ${esc(s.claim)}</li>`).join("")}</ul>
          <p class="tiny">Crowd context (not used in the probability): ${m.crowd?.team1_pct != null ? `${esc(m.crowd.team1_pct)}% picked ${esc(m.team1)} / ${esc(m.crowd.team2_pct)}% picked ${esc(m.team2)}` : "not published"}.</p></div>
        </div>
      </div>
      <p><a class="btn" href="picks.html">← All picks</a></p>`;
  }

  function renderMethodology(d) {
    const ss = $("#sources-status");
    if (ss) ss.innerHTML = (d.sources_status || []).map((s) => `<tr><td><b>${esc(s.name)}</b><span class="sub"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a></span></td><td><span class="chip ${s.status === "ok" ? "green" : "amber"}">${esc(s.status)}</span></td><td>${s.count ?? "—"}</td><td class="small">${esc(s.note || "")}</td></tr>`).join("");
    const cu = $("#checked-unavailable");
    if (cu) cu.innerHTML = (d.checked_unavailable || []).map((s) => `<tr><td><b>${esc(s.name)}</b><span class="sub"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a></span></td><td class="small">${esc(s.observed)}</td><td class="small">${esc(s.consequence)}</td></tr>`).join("");
    const m = $("#model-info");
    if (m && d.model) m.innerHTML = `<dl class="kv">
      <dt>Results used</dt><dd>${d.model.matches_used}</dd>
      <dt>Teams rated</dt><dd>${d.model.teams_rated}</dd>
      <dt>Teams with 365d games</dt><dd>${d.model.teams_with_recent_games}</dd>
      <dt>Elo K</dt><dd>${d.model.k_base} (scaled by BestOf and score margin)</dd>
      <dt>Inactivity half-life</dt><dd>${d.model.half_life_days} days</dd>
      <dt>Competition priors</dt><dd>${d.model.competitions_with_prior} leagues mapped to strength tiers</dd>
      <dt>Global prior</dt><dd>${d.model.global_prior}</dd>
    </dl>`;
    const g = $("#generated");
    if (g) g.textContent = `${whenLocal(d.generated_at).text} · next update ${whenUTC(d.next_update_utc)}`;
    const ft = $("#backtest");
    const b = d.model && d.model.backtest;
    if (ft) ft.innerHTML = b ? `<dl class="kv">
        <dt>Test window</dt><dd>Last ${b.window_days} days (${b.n} matches)</dd>
        <dt>Log-loss</dt><dd><b>${b.log_loss}</b> <span class="small">(coin-flip baseline ${b.baseline_log_loss})</span></dd>
        <dt>Brier score</dt><dd><b>${b.brier}</b> <span class="small">(baseline ${b.baseline_brier})</span></dd>
        <dt>Accuracy</dt><dd>${(b.accuracy * 100).toFixed(1)}%</dd>
      </dl><p class="tiny">Out-of-sample: ratings fitted before the window and frozen; only matches where both teams were already rated are scored.</p>`
      : `<p>No backtest available for this run.</p>`;
  }

  function wirePicks() {
    const q = $("#q");
    const sel = $("#tournament");
    const sort = $("#sort");
    const reset = $("#reset");
    if (q) q.addEventListener("input", () => { clearTimeout(q._t); q._t = setTimeout(() => { state.q = q.value.trim().toLowerCase(); renderPicks(DATA); }, 120); });
    if (sel) sel.addEventListener("change", () => { state.tournament = sel.value; renderPicks(DATA); });
    if (sort) sort.addEventListener("change", () => { state.sort = sort.value; renderPicks(DATA); });
    if (reset) reset.addEventListener("click", () => {
      state.filter = "all"; state.q = ""; state.tournament = ""; state.sort = "time";
      if (q) q.value = ""; if (sel) sel.value = ""; if (sort) sort.value = "time";
      renderPicks(DATA);
    });
    $$("[data-filter]").forEach((b) => b.addEventListener("click", () => { state.filter = b.dataset.filter; renderPicks(DATA); }));
    const params = new URLSearchParams(location.search);
    if (params.get("filter")) state.filter = params.get("filter");
  }

  async function main() {
    setActiveNav();
    try {
      DATA = await load();
      setHeader(DATA);
      if (PAGE === "summary") renderIndex(DATA);
      if (PAGE === "picks") { wirePicks(); renderPicks(DATA); }
      if (PAGE === "unresolved") renderUnresolved(DATA);
      if (PAGE === "flagged") renderFlagged(DATA);
      if (PAGE === "match") renderMatch(DATA);
      if (PAGE === "methodology") renderMethodology(DATA);
      $$(".loading").forEach((el) => el.classList.add("hidden"));
    } catch (e) {
      toastError(e);
    }
  }

  document.addEventListener("DOMContentLoaded", main);
})();
