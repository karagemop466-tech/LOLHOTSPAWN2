/* Hotspawn LoL Picks — data-driven mobile-first dashboard (vanilla JS, zero build step) */
(() => {
  "use strict";
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const pct = (x) => (x == null ? "—" : `${Math.round(x * 100)}%`);
  const pct1 = (x) => (x == null ? "—" : `${(x * 100).toFixed(1)}%`);
  const slugify = (s) => String(s || "league").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  const METHOD = {
    MARKET_CONSENSUS: { label: "Market consensus", cls: "green", ico: "💰" },
    MARKET_SINGLE: { label: "Single book line", cls: "green", ico: "💰" },
    MODEL_ELO: { label: "Own Elo model", cls: "blue", ico: "🧮" },
    MODEL_ELO_THIN: { label: "Elo (thin history)", cls: "amber", ico: "🧮" },
    MODEL_STANDINGS: { label: "Split standings", cls: "blue", ico: "📊" },
    MODEL_LEAGUE_PRIOR: { label: "League prior", cls: "amber", ico: "📐" },
    UNRESOLVED: { label: "Unresolved 50/50", cls: "red", ico: "⚠️" },
  };
  const CONF = { High: "green", Medium: "blue", Low: "amber", None: "red" };
  const CONF_RANK = { High: 3, Medium: 2, Low: 1, None: 0 };
  const METHOD_RANK = {
    MARKET_CONSENSUS: 6, MARKET_SINGLE: 5, MODEL_ELO: 4,
    MODEL_STANDINGS: 3, MODEL_ELO_THIN: 2, MODEL_LEAGUE_PRIOR: 1, UNRESOLVED: 0,
  };
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
  function pickPill(m) {
    const tone = m.method === "UNRESOLVED" ? "red" : (m.confidence === "Low" ? "amber" : "");
    const prefix = m.method === "UNRESOLVED" ? "⚠️ 50/50:" : "✅ PICK:";
    return `<span class="pick-pill ${tone}">${prefix} ${esc(m.pick)} · ${pct1(m.pick_prob)}</span>`;
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
      <div class="pickline">${pickPill(m)}<span class="chip ${CONF[m.confidence] || ""}">${esc(m.confidence || "—")} confidence</span></div>
      <div class="evidence">${esc(m.evidence || "")}</div>
      ${sourcesInline(m, opts.sources || 3)}
    </article>`;
  }

  function row(m) {
    const t = whenLocal(m.start_utc);
    const mi = methodInfo(m);
    const cls = matchClass(m);
    const srcCount = (m.sources || []).filter((s) => s.url).length;
    const srcLinks = (m.sources || []).filter((s) => s.url).slice(0, 3)
      .map((s) => `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)} ↗</a>`).join(" ");
    return `<tr class="${cls}">
      <td data-label="Start" title="${esc(t.title)}"><b>${esc(t.text)}</b><span class="sub">${esc(whenUTC(m.start_utc))}</span><span class="sub">${esc(relative(m.start_utc))}</span></td>
      <td class="teams-cell" data-label="Match"><a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team1)}</a> <span class="vs">vs</span> <a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team2)}</a><span class="sub">${esc(m.tournament || "")}${m.best_of ? ` · Bo${esc(m.best_of)}` : ""}${m.tier && !/^WAITING/i.test(m.tier) ? ` · Tier ${esc(m.tier)}` : ""}</span></td>
      <td class="probcell" data-label="Win probability"><span class="p1">${esc(m.team1)} ${pct1(m.prob_team1)}</span><span class="sub"><span class="p2">${esc(m.team2)} ${pct1(m.prob_team2)}</span></span><div class="bar" aria-hidden="true"><i style="width:${pct(m.prob_team1)}"></i><b style="width:${pct(m.prob_team2)}"></b></div></td>
      <td class="pickcell" data-label="Pick">${pickPill(m)}</td>
      <td data-label="Method"><span class="chip ${mi.cls}">${mi.ico} ${esc(mi.label)}</span><span class="sub"><span class="chip ${CONF[m.confidence] || ""}">${esc(m.confidence || "—")}</span></span></td>
      <td data-label="Sources"><span class="sub">${srcCount} verified link${srcCount === 1 ? "" : "s"}</span><div class="src-links">${srcLinks}</div></td>
    </tr>`;
  }

  function computeLeagueBreakdown(d) {
    if (Array.isArray(d.league_breakdown) && d.league_breakdown.length) return d.league_breakdown;
    const byTour = new Map();
    (d.matches || []).forEach((m) => {
      const k = m.tournament || "Unknown competition";
      if (!byTour.has(k)) byTour.set(k, []);
      byTour.get(k).push(m);
    });
    return Array.from(byTour.entries()).sort((a, b) => b[1].length - a[1].length).map(([tour, ms]) => {
      const lpUrl = (ms.find((x) => x.leaguepedia_url) || {}).leaguepedia_url || "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule";
      const mkt = ms.filter((x) => x.market).length;
      const elo = ms.filter((x) => x.method === "MODEL_ELO" || x.method === "MODEL_ELO_THIN").length;
      const st = ms.filter((x) => x.method === "MODEL_STANDINGS").length;
      const prior = ms.filter((x) => x.method === "MODEL_LEAGUE_PRIOR").length;
      const unres = ms.filter((x) => x.method === "UNRESOLVED").length;
      const t = tour.toLowerCase();
      const cat = /worlds|msi|lck|lpl|lec|lcs|lta/.test(t)
        ? "Tier 1 — International & Major Leagues"
        : /emea masters|promotion|lgc rising|2nd division/.test(t)
          ? "Tier 2 — Regional Challenger & Promotion"
          : "Tier 3 — National & Amateur Divisions";
      return {
        tournament: tour, category: cat, fixtures: ms.length, market: mkt, elo, standings: st,
        league_prior: prior, unresolved: unres, leaguepedia_url: lpUrl,
        limitation: mkt ? "Priced by external bookmaker/prediction-market consensus." : "No external sportsbook line; priced via Leaguepedia recorded results & split standings.",
      };
    });
  }

  function leagueSourceLinks(lb) {
    const links = [];
    if (lb.leaguepedia_url) links.push(`<a href="${esc(lb.leaguepedia_url)}" target="_blank" rel="noopener">Leaguepedia ↗</a>`);
    if (lb.organizer_url) links.push(`<a href="${esc(lb.organizer_url)}" target="_blank" rel="noopener">${esc(lb.organizer_name || "Organizer")} ↗</a>`);
    if (!links.length) links.push(`<a href="https://play.hotspawn.com/lol-pickems" target="_blank" rel="noopener">Hotspawn lobby ↗</a>`);
    return `<div class="src-links">${links.join(" ")}</div>`;
  }

  function setHeader(d) {
    const upd = $("#updated");
    const fresh = $("#freshness");
    const t = whenLocal(d.generated_at);
    if (upd) upd.innerHTML = `<b>Updated</b> ${esc(t.text)} <span class="small">your local time</span>`;
    const fu = $("#footer-updated");
    if (fu) fu.textContent = `Data generated ${whenUTC(d.generated_at)} · automatic refresh every 6 hours.`;
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

    const rb = $("#recon-body");
    if (rb) {
      const r = d.coverage_reconciliation || {};
      const ex = (d.excluded_fixtures || []).length;
      if (r.lobby_upcoming == null) {
        rb.innerHTML = `<p>The Hotspawn lobby could not be read in this run, so coverage is compared with the fixtures feed only: <b>${d.counts?.fixtures ?? 0}</b> upcoming fixtures priced.</p>`;
      } else {
        const missing = (r.lobby_upcoming_missing_from_priced || []).length;
        rb.innerHTML = `<div class="stats-mini">
          <div><b>${r.lobby_upcoming}</b><span>upcoming on the Hotspawn lobby</span></div>
          <div><b>${r.priced}</b><span>with a pick</span></div>
          <div class="${missing ? "bad" : "good"}"><b>${missing}</b><span>missing a pick</span></div>
          <div><b>${ex}</b><span>cancelled, not priced</span></div></div>
          <p>${missing === 0 ? "Every upcoming Hotspawn LoL fixture has a pick." : `${missing} fixture(s) still need a pick — see the flagged page.`}
          Lobby rows that already started (${r.lobby_past_not_priced ?? 0}) are locked, so they are not priced. Rule: ${esc(r.rule || "")}</p>
          <p><a href="flagged.html#excluded">See the ${ex} cancelled fixture(s) that were excluded →</a></p>`;
      }
    }

    const cov = d.coverage || {};
    const stCount = cov.with_standings_model ?? c.standings ?? 0;
    const covText = $("#coverage-text");
    if (covText) covText.innerHTML = `<b>${cov.resolved ?? 0} of ${cov.fixtures ?? 0}</b> fixtures have a verified pick (${cov.resolved_pct ?? 0}%): <b>${cov.with_external_market ?? 0}</b> from external betting lines, <b>${(cov.with_team_specific_model ?? 0) - stCount}</b> from our chronological Elo model, <b>${stCount}</b> from split standings, <b>${cov.with_prior_only ?? 0}</b> from competition priors, and <b>${cov.unresolved ?? 0}</b> explicit 50/50 placeholders. See <a href="picks.html">All picks</a> · <a href="leagues.html">By league</a> · <a href="unresolved.html">Unresolved &amp; limitations</a>.`;
    const covBar = $("#coverage-bar");
    if (covBar) covBar.innerHTML = `<i style="width:${cov.resolved_pct || 0}%"></i><b style="width:${100 - (cov.resolved_pct || 0)}%"></b>`;

    const sortedAll = (d.matches || []).slice().sort((a, b) => (a.start_utc || "").localeCompare(b.start_utc || ""));
    const quickBody = $("#quick-picks-body");
    if (quickBody) {
      const quickRows = sortedAll.slice(0, 12);
      quickBody.innerHTML = quickRows.length ? quickRows.map(row).join("") : `<tr><td colspan="6">No upcoming matches right now.</td></tr>`;
    }

    const lbs = computeLeagueBreakdown(d);
    const sumLeagues = $("#summary-leagues-body");
    if (sumLeagues) {
      sumLeagues.innerHTML = lbs.map((lb) => `<tr>
        <td data-label="Competition"><a class="rowlink" href="leagues.html#league-${esc(slugify(lb.tournament))}"><b>${esc(lb.tournament)}</b></a><span class="sub"><a href="picks.html?tournament=${encodeURIComponent(lb.tournament)}">Filter in All picks →</a></span></td>
        <td data-label="Category"><span class="chip">${esc(lb.category)}</span></td>
        <td data-label="Fixtures"><b>${lb.fixtures}</b></td>
        <td data-label="Pricing breakdown" class="small">💰 ${lb.market} mkt · 🧮 ${lb.elo} Elo · 📊 ${lb.standings || 0} st · 📐 ${lb.league_prior} prior · ⚠️ ${lb.unresolved} unres</td>
        <td data-label="Source links">${leagueSourceLinks(lb)}</td>
      </tr>`).join("");
    }

    const nowMs = Date.now();
    const next = (d.matches || [])
      .filter((m) => new Date(m.start_utc).getTime() >= nowMs - 300000)
      .sort((a, b) => (a.start_utc || "").localeCompare(b.start_utc || ""))
      .slice(0, 6);
    const nextBox = $("#next24");
    if (nextBox) nextBox.innerHTML = next.length ? next.map((m) => matchCard(m, { sources: 3 })).join("") : `<div class="card">No matches locking in the next 24 hours. <a href="picks.html">Browse all upcoming picks →</a></div>`;
    const soonCount = $("#soon-count");
    if (soonCount) {
      const n24 = (d.matches || []).filter((m) => { const t = new Date(m.start_utc).getTime(); return t >= nowMs - 300000 && t <= nowMs + 86400000; }).length;
      soonCount.textContent = n24 ? `${n24} match${n24 === 1 ? "" : "es"} locking in the next 24 hours` : "Next scheduled matches on Hotspawn's list";
    }

    const featured = (d.matches || []).filter((m) => m.market).sort((a, b) => (a.start_utc || "").localeCompare(b.start_utc || "")).slice(0, 10);
    const featBox = $("#featured");
    if (featBox) featBox.innerHTML = featured.length ? featured.map((m) => matchCard(m, { sources: 4 })).join("")
      : `<div class="card">No external market lines are open right now. Every match is priced by our Elo/standings model or flagged unresolved.</div>`;

    const u = d.unresolved || {};
    const allMatches = d.matches || [];
    const noLine = allMatches.filter((m) => !m.market);
    const unresN = allMatches.filter((m) => m.method === "UNRESOLVED").length;
    const lowN = u.low_confidence_count ?? allMatches.filter((m) => m.confidence === "Low").length;
    const priorN = allMatches.filter((m) => m.method === "MODEL_LEAGUE_PRIOR").length;
    const reasons = (u.reasons || []).map((r) => `<li><b>${r.count}</b> — ${esc(r.reason)}</li>`).join("");
    const lims = (u.limitations || []).map((x) => `<li>${esc(x)}</li>`).join("");
    const ubox = $("#unresolved-summary");
    if (ubox) ubox.innerHTML = `<div class="warnbox">
      <h3>${unresN ? "⚠️ Unresolved picks" : "✅ No unresolved placeholders"} · ${noLine.length} of ${allMatches.length} matches have no external betting line</h3>
      <p><b>${noLine.length}</b> fixture${noLine.length === 1 ? "" : "s"} are priced <b>without</b> a sportsbook or prediction-market line, because no book we can reach lists that competition. They still get a pick and both win probabilities, from a documented signal:
      🧮 our Elo model on recorded Leaguepedia results, 📊 current-split standings, or 📐 the competition prior when a side has no recorded games.</p>
      <p><b>${unresN}</b> row${unresN === 1 ? "" : "s"} have no signal at all and are published strictly as an explicit <b>50.0% / 50.0% placeholder</b> (never an edge).
      <b>${lowN}</b> row${lowN === 1 ? "" : "s"} are capped at <b>Low confidence</b> (thin history, no cross-league evidence, or a prior substituted for a side), and <b>${priorN}</b> use a competition prior for a team with no recorded games.
      Hotspawn's crowd percentage is never used.</p>
      ${reasons ? `<p class="small"><b>Breakdown by reason</b></p><ul class="clean small">${reasons}</ul>` : ""}
      <p class="small"><b>Open the rows behind these numbers</b></p>
      <div class="hero-actions">
        <a class="btn" href="picks.html?filter=model">🧮 ${allMatches.filter((m) => m.model && !m.market).length} model-priced matches →</a>
        <a class="btn" href="picks.html?filter=low">⚠️ ${lowN} low-confidence matches →</a>
        <a class="btn warn" href="unresolved.html">⚠️ Unresolved &amp; limitations →</a>
      </div>
      ${lims ? `<details><summary class="small"><b>Key limitations for generating these picks</b></summary><ul class="clean small">${lims}</ul></details>` : ""}
    </div>`;

    const ulBody = $("#unresolved-league-body");
    if (ulBody) {
      const lbs = (u.by_league && u.by_league.length) ? u.by_league : computeLeagueBreakdown(d);
      ulBody.innerHTML = lbs.length ? lbs.map((lb) => {
        const elo = lb.elo ?? 0, st = lb.standings ?? 0, prior = lb.prior_only ?? lb.league_prior ?? 0;
        const unres = lb.unresolved ?? 0, mkt = lb.market ?? 0;
        const q = `picks.html?tournament=${encodeURIComponent(lb.tournament)}`;
        const href = unres ? `${q}&filter=unresolved` : q;
        return `<tr>
          <td data-label="Competition"><a class="rowlink" href="${esc(href)}"><b>${esc(lb.tournament)}</b></a>${lb.best_signal ? `<span class="sub small">${esc(lb.best_signal)}</span>` : ""}</td>
          <td data-label="Fixtures"><b>${lb.fixtures ?? 0}</b></td>
          <td data-label="Signal mix" class="small">💰 ${mkt} market · 🧮 ${elo} Elo · 📊 ${st} standings · 📐 ${prior} prior · ⚠️ ${unres} unresolved</td>
          <td data-label="Limitation" class="small">${esc(lb.limitation || (mkt === (lb.fixtures ?? 0) ? "Priced from external bookmaker lines." : "No external sportsbook prices this competition; picks come from recorded results and split standings."))}</td>
          <td data-label="Open the picks"><a class="btn" style="min-height:40px;padding:8px 12px" href="${esc(href)}">${lb.fixtures ?? 0} rows →</a></td>
        </tr>`;
      }).join("") : `<tr><td colspan="5">No competitions in this snapshot.</td></tr>`;
    }

    const ss = $("#sources-strip");
    if (ss) ss.innerHTML = (d.sources_status || []).map((s) => `<span class="chip ${s.status === "ok" ? "green" : "amber"}" title="${esc(s.note || "")}">${esc(s.name)} · ${esc(s.status)}${s.count != null ? ` · ${s.count}` : ""}</span>`).join(" ");
  }

  function renderLeagues(d) {
    const lbs = computeLeagueBreakdown(d);
    const jump = $("#league-jump-links");
    if (jump) {
      jump.innerHTML = lbs.map((lb) => `<a class="chipbtn" href="#league-${esc(slugify(lb.tournament))}">${esc(lb.tournament)} <span class="n">${lb.fixtures}</span></a>`).join("");
    }
    const sumBody = $("#leagues-summary-body");
    if (sumBody) {
      sumBody.innerHTML = lbs.map((lb) => `<tr>
        <td data-label="Competition"><a class="rowlink" href="#league-${esc(slugify(lb.tournament))}"><b>${esc(lb.tournament)}</b></a></td>
        <td data-label="Category"><span class="chip">${esc(lb.category)}</span></td>
        <td data-label="Fixtures"><b>${lb.fixtures}</b></td>
        <td data-label="Pricing breakdown" class="small">💰 ${lb.market} market · 🧮 ${lb.elo} Elo · 📊 ${lb.standings || 0} standings · 📐 ${lb.league_prior} prior · ⚠️ ${lb.unresolved} unresolved</td>
        <td data-label="Limitation" class="small">${esc(lb.limitation || "")}</td>
        <td data-label="Sources">${leagueSourceLinks(lb)}</td>
      </tr>`).join("");
    }
    const container = $("#leagues-sections");
    if (container) {
      const byTour = new Map();
      (d.matches || []).forEach((m) => {
        const k = m.tournament || "Unknown competition";
        if (!byTour.has(k)) byTour.set(k, []);
        byTour.get(k).push(m);
      });
      container.innerHTML = lbs.map((lb) => {
        const ms = (byTour.get(lb.tournament) || []).slice().sort((a, b) => (a.start_utc || "").localeCompare(b.start_utc || ""));
        return `<section class="cat-section" id="league-${esc(slugify(lb.tournament))}">
          <h2>${esc(lb.tournament)} <span class="chip">${esc(lb.category)}</span></h2>
          <p class="small">${esc(lb.limitation || "")}</p>
          ${leagueSourceLinks(lb)}
          <div class="table-wrap" style="margin-top:10px">
            <table>
              <thead><tr><th>Start (UTC)</th><th>Match</th><th>Win probability</th><th>Pick</th><th>Method</th><th>Sources</th></tr></thead>
              <tbody>${ms.map(row).join("")}</tbody>
            </table>
          </div>
        </section>`;
      }).join("");
    }
  }

  function applyFilter(m) {
    const now = Date.now();
    if (state.filter === "next24") {
      const t = new Date(m.start_utc).getTime();
      if (!(t >= now - 300000 && t <= now + 86400000)) return false;
    }
    if (state.filter === "market" && !m.market) return false;
    if (state.filter === "model" && !(m.model && !m.market)) return false;
    if (state.filter === "standings" && m.method !== "MODEL_STANDINGS") return false;
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
      standings: all.filter((m) => m.method === "MODEL_STANDINGS").length,
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
    if (state.tournament) url.searchParams.set("tournament", state.tournament); else url.searchParams.delete("tournament");
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
    if (ub) ub.innerHTML = un.length ? un.map((m) => matchCard(m, { sources: 3 })).join("") : `<div class="okbox">0 unresolved placeholders right now — every listed fixture has either external bookmaker odds, recorded Leaguepedia match history, or split standings.</div>`;
    const lb = $("#lowconf-body");
    if (lb) lb.innerHTML = low.length ? low.map((m) => matchCard(m, { sources: 3 })).join("") : `<div class="card">No low-confidence rows.</div>`;
    const limBody = $("#league-limitations-body");
    if (limBody) {
      const lbs = computeLeagueBreakdown(d);
      limBody.innerHTML = lbs.map((x) => {
        const q = `picks.html?tournament=${encodeURIComponent(x.tournament)}`;
        const href = x.unresolved ? `${q}&filter=unresolved` : q;
        return `<tr>
        <td data-label="Competition"><a class="rowlink" href="leagues.html#league-${esc(slugify(x.tournament))}"><b>${esc(x.tournament)}</b></a></td>
        <td data-label="Fixtures"><a class="rowlink" href="${esc(href)}"><b>${x.fixtures}</b> row(s) →</a></td>
        <td data-label="Breakdown" class="small">💰 ${x.market} · 🧮 ${x.elo} · 📊 ${x.standings || 0} · 📐 ${x.league_prior} · ⚠️ ${x.unresolved}</td>
        <td data-label="Limitation" class="small">${esc(x.limitation || "")}</td>
        <td data-label="Sources">${leagueSourceLinks(x)}</td>
      </tr>`;
      }).join("");
    }
    const reasons = (d.unresolved?.reasons || []).map((r) => `<li><b>${r.count}</b> — ${esc(r.reason)}</li>`).join("");
    const rbox = $("#reasons");
    if (rbox) rbox.innerHTML = reasons || "<li>None.</li>";
    const lim = (d.unresolved?.limitations || []).map((x) => `<li>${esc(x)}</li>`).join("");
    const lbox = $("#limitations");
    if (lbox) lbox.innerHTML = lim;
    const stat = $("#unresolved-counts");
    if (stat) stat.innerHTML = `<b>${un.length}</b> unresolved placeholders · <b>${low.length}</b> low-confidence model rows · <b>${(d.counts?.market ?? 0)}</b> external market rows`;
  }

  function flagLabel(f) {
    const map = {
      HOTSPAWN_NAME_COLLISION: "Upstream Hotspawn tag collision mapped to verified split entrant",
      HOTSPAWN_ENTITY_MISMATCH: "Upstream Hotspawn tag collision resolved via Leaguepedia UTC schedule",
      NAME_BRIDGED_VIA_SCHEDULE: "Team name bridged via 2+ exact UTC schedule slots",
      LEAGUEPEDIA_TIME_TBD: "Leaguepedia match timestamp still TBD (Hotspawn governs lock)",
      GENERIC_RESULTS_SOURCE: "General Leaguepedia table link (no fixture-specific split page matched)",
      NO_EXTERNAL_MARKET: "No external market line",
      NO_TEAM_HISTORY: "No recorded team history",
      ONE_TEAM_NO_HISTORY: "One team has no history (competition prior used)",
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
    if (gb) gb.innerHTML = order.length ? order.map((f) => {
      const sampleSrc = groups[f][0]?.sources?.[0]?.url || "https://play.hotspawn.com/lol-pickems";
      return `<tr><td><span class="flag">${esc(f)}</span><span class="sub">${esc(flagLabel(f))}</span></td><td><b>${groups[f].length}</b></td><td><a href="picks.html?filter=${f === "NO_VERIFIED_SIGNAL" ? "unresolved" : "all"}">picks →</a> · <a href="${esc(sampleSrc)}" target="_blank" rel="noopener">source ↗</a></td></tr>`;
    }).join("") : `<tr><td colspan="3">No flags.</td></tr>`;

    const eb = $("#excluded-body");
    if (eb) {
      const ex = d.excluded_fixtures || [];
      eb.innerHTML = ex.length ? ex.map((x) => `<tr><td data-label="Start"><b>${esc(whenLocal(x.start_utc).text)}</b><span class="sub">${esc(whenUTC(x.start_utc))}</span></td><td class="teams-cell" data-label="Match">${esc(x.team1)} vs ${esc(x.team2)}<span class="sub">${esc(x.tournament || "")} · fixture ${esc(x.id)}</span></td><td data-label="Status"><span class="chip amber">${esc(x.status || "")}</span></td><td class="small" data-label="Why not priced">${esc(x.reason || "")}<span class="sub"><a href="${esc(x.source || "https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures")}" target="_blank" rel="noopener">Hotspawn fixtures API ↗</a></span></td></tr>`).join("")
        : `<tr><td colspan="4">No excluded fixtures in this run.</td></tr>`;
    }

    const bridgesBody = $("#bridges-body");
    if (bridgesBody) {
      const explicit = d.model?.schedule_bridges || [];
      let bridges = explicit.slice();
      if (!bridges.length) {
        const seenB = new Map();
        (d.matches || []).forEach((m) => {
          const md = m.model || {};
          const page = m.leaguepedia_page || md.tournament_page || m.tournament || "";
          [[m.team1, md.canonical_team1 || md.resolved_team1], [m.team2, md.canonical_team2 || md.resolved_team2]].forEach(([hs, lp]) => {
            if (hs && lp && hs !== lp) {
              const key = `${page}::${hs}::${lp}`;
              const cur = seenB.get(key) || { overview: page, hotspawn_name: hs, leaguepedia_name: lp, exact_slot_matches: 0, entity_mismatch: (m.flags || []).includes("HOTSPAWN_NAME_COLLISION") };
              cur.exact_slot_matches += 1;
              seenB.set(key, cur);
            }
          });
        });
        bridges = Array.from(seenB.values());
      }
      bridgesBody.innerHTML = bridges.length ? bridges.map((b) => {
        const wiki = "https://lol.fandom.com/wiki/" + String(b.overview || "").replace(/ /g, "_");
        return `<tr>
          <td data-label="Competition">${esc(b.overview)}</td>
          <td data-label="Hotspawn name"><b>${esc(b.hotspawn_name)}</b>${b.entity_mismatch ? ` <span class="chip amber">tag collision</span>` : ""}</td>
          <td data-label="Leaguepedia team"><b>${esc(b.leaguepedia_name)}</b></td>
          <td data-label="Fixtures">${b.exact_slot_matches} verified fixture${b.exact_slot_matches === 1 ? "" : "s"}</td>
          <td data-label="Source link"><a href="${esc(wiki)}" target="_blank" rel="noopener">Leaguepedia split ↗</a></td>
        </tr>`;
      }).join("") : `<tr><td colspan="5">No schedule-bridged team names required in this snapshot (<a href="https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule" target="_blank" rel="noopener">Leaguepedia MatchSchedule ↗</a>).</td></tr>`;
    }

    const flagged = (d.matches || []).filter((m) => (m.flags || []).length).sort((a, b) => (a.start_utc || "").localeCompare(b.start_utc || ""));
    const body = $("#flagged-body");
    if (body) body.innerHTML = flagged.map((m) => `<tr class="${matchClass(m)}">
      <td data-label="Start"><b>${esc(whenLocal(m.start_utc).text)}</b><span class="sub">${esc(whenUTC(m.start_utc))}</span></td>
      <td class="teams-cell" data-label="Match"><a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team1)} vs ${esc(m.team2)}</a><span class="sub">${esc(m.tournament || "")}</span></td>
      <td data-label="Flags">${(m.flags || []).map((f) => `<span class="chip amber flag" title="${esc(flagLabel(f))}">${esc(f)}</span>`).join(" ")}</td>
      <td data-label="Pick">${pickPill(m)}</td>
      <td data-label="Sources">${sourcesInline(m, 3)}</td>
    </tr>`).join("");

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
        <div class="match-top"><span class="chip ${mi.cls}">${mi.ico} ${esc(mi.label)}</span><span class="chip ${CONF[m.confidence] || ""}">${esc(m.confidence || "—")} confidence</span>${m.best_of ? `<span class="chip">Bo${esc(m.best_of)}</span>` : ""}${m.tier ? `<span class="chip">${/^WAITING/i.test(m.tier) ? "Tier not published" : `Tier ${esc(m.tier)}`}</span>` : ""}</div>
        <h1>${esc(m.team1)} <span style="color:var(--muted);font-weight:600;font-size:.6em">vs</span> ${esc(m.team2)}</h1>
        <p class="small">${esc(m.tournament || "")} · ${esc(t.text)} <span title="${esc(t.title)}">· ${esc(whenUTC(m.start_utc))}</span> · ${esc(relative(m.start_utc))}</p>
        <div class="bar" aria-hidden="true"><i style="width:${pct(m.prob_team1)}"></i><b style="width:${pct(m.prob_team2)}"></b></div>
        <div class="probrow"><span>${esc(m.team1)} <b>${pct1(m.prob_team1)}</b></span><span style="margin-left:auto">${esc(m.team2)} <b>${pct1(m.prob_team2)}</b></span></div>
        <div class="pickline">${pickPill(m)}</div>
        <p class="small">${esc(m.evidence || "")}</p>
      </div>
      <div class="two-col">
        <div>
          <div class="card"><h3>${m.market ? "External betting lines" : "No external betting line"}</h3>
            ${m.market ? `<p class="small">Consensus: <b>${pct1(m.market.consensus_team1)}</b> ${esc(m.team1)} · <b>${pct1(1 - m.market.consensus_team1)}</b> ${esc(m.team2)}. Dispersion ${pct1(m.market.dispersion)} across ${m.market.distinct_books ?? m.market.source_count} book(s).${m.market.model_team1 != null ? ` Model: ${pct1(m.market.model_team1)} (edge ${(m.market.model_edge_team1 * 100 >= 0 ? "+" : "")}${(m.market.model_edge_team1 * 100).toFixed(1)} pts).` : ""}</p>
            <div class="table-wrap"><table><thead><tr><th>Source</th><th>${esc(m.team1)}</th><th>${esc(m.team2)}</th><th>Decimal</th><th>Link</th></tr></thead><tbody>${marketRows}</tbody></table></div>`
            : `<p>No bookmaker or prediction-market line was found for this fixture at the time of the update. The pick comes from ${m.model ? esc(mi.label) : "an explicit 50/50 placeholder"}.</p>`}
          </div>
          <div class="card"><h3>Our model &amp; standings inputs</h3>
            ${m.model ? `<dl class="kv">
              <dt>Resolved teams</dt><dd>${esc(model.canonical_team1 || model.resolved_team1 || m.team1)} vs ${esc(model.canonical_team2 || model.resolved_team2 || m.team2)}</dd>
              ${model.standings ? `<dt>Standings record</dt><dd>${esc(m.team1)} <b>${model.standings.team1_wins}–${model.standings.team1_losses}</b> · ${esc(m.team2)} <b>${model.standings.team2_wins}–${model.standings.team2_losses}</b> <span class="small">(${esc(model.standings.kind)} in ${esc(model.standings.page)})</span></dd>` : (model.standings_team1 || model.standings_team2) ? `<dt>Split standings</dt><dd>${typeof model.standings_team1 === "object" ? `${esc(m.team1)} <b>${model.standings_team1.win_series ?? "—"}–${model.standings_team1.loss_series ?? "—"}</b> series` : esc(model.standings_team1 || "—")} · ${typeof model.standings_team2 === "object" ? `${esc(m.team2)} <b>${model.standings_team2.win_series ?? "—"}–${model.standings_team2.loss_series ?? "—"}</b> series` : esc(model.standings_team2 || "—")}</dd>` : ""}
              <dt>Elo (team 1)</dt><dd>${model.elo_team1 ?? "—"} <span class="small">${model.games_team1_365d != null ? `(${model.games_team1_365d} games in 365d)` : ""}</span></dd>
              <dt>Elo (team 2)</dt><dd>${model.elo_team2 ?? "—"} <span class="small">${model.games_team2_365d != null ? `(${model.games_team2_365d} games in 365d)` : ""}</span></dd>
              <dt>Prior used</dt><dd>${esc(model.prior_used || "—")}</dd>
              <dt>Head-to-head</dt><dd>${h2h}</dd>
              <dt>Tournament page</dt><dd>${m.leaguepedia_url ? `<a href="${esc(m.leaguepedia_url)}" target="_blank" rel="noopener">Leaguepedia ↗</a>` : "—"}</dd>
            </dl>` : `<p>No rated team history or standings record was available. Published as an explicit 50/50 placeholder.</p>`}
          </div>
        </div>
        <div>
          <div class="card"><h3>Flags</h3>${(m.flags || []).length ? `<ul class="clean small">${m.flags.map((f) => `<li><span class="flag">${esc(f)}</span> — ${esc(flagLabel(f))}</li>`).join("")}</ul>` : `<p class="small">No flags.</p>`}</div>
          <div class="card"><h3>Sources &amp; verification</h3><ul class="clean small">${(m.sources || []).map((s) => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)} ↗</a> — ${esc(s.claim)}</li>`).join("")}</ul>
          <p class="tiny">Crowd context (never used in probability): ${m.crowd?.team1_pct != null ? `${esc(m.crowd.team1_pct)}% picked ${esc(m.team1)} / ${esc(m.crowd.team2_pct)}% picked ${esc(m.team2)}` : "not published"}.</p></div>
        </div>
      </div>
      <p><a class="btn" href="picks.html">← All picks</a> <a class="btn" href="leagues.html">By league →</a></p>`;
  }

  function renderMethodology(d) {
    const ss = $("#sources-status");
    if (ss) ss.innerHTML = (d.sources_status || []).map((s) => `<tr><td><b>${esc(s.name)}</b><span class="sub"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a></span></td><td><span class="chip ${s.status === "ok" ? "green" : "amber"}">${esc(s.status)}</span></td><td>${s.count ?? "—"}</td><td class="small">${esc(s.note || "")}</td></tr>`).join("");
    const cu = $("#checked-unavailable");
    if (cu) cu.innerHTML = (d.checked_unavailable || []).map((s) => `<tr><td><b>${esc(s.name)}</b><span class="sub"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a></span></td><td class="small">${esc(s.observed)}</td><td class="small">${esc(s.consequence)}</td></tr>`).join("");
    const lims = (d.unresolved?.limitations || []).map((x) => `<li>${esc(x)}</li>`).join("");
    const lbox = $("#limitations");
    if (lbox && lims) lbox.innerHTML = lims;
    const m = $("#model-info");
    if (m && d.model) m.innerHTML = `<dl class="kv">
      <dt>Results used</dt><dd>${d.model.matches_used}</dd>
      <dt>Teams rated</dt><dd>${d.model.teams_rated}</dd>
      <dt>Teams with 365d games</dt><dd>${d.model.teams_with_recent_games}</dd>
      <dt>Schedule bridges</dt><dd>${(d.model.schedule_bridges || []).length} verified upstream tag mappings</dd>
      <dt>Elo K</dt><dd>${d.model.k_base} (scaled by BestOf and score margin)</dd>
      <dt>Inactivity half-life</dt><dd>${d.model.half_life_days} days</dd>
      <dt>Competition priors</dt><dd>${d.model.competitions_with_prior} leagues mapped to strength tiers</dd>
      ${d.model.standings_rows != null ? `<dt>Standings records</dt><dd>${d.model.standings_rows} team rows across ${d.model.standings_pages} competitions (fallback when Elo cannot rate a side)</dd>` : ""}
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
    if (params.get("tournament")) state.tournament = params.get("tournament");
  }

  async function main() {
    setActiveNav();
    try {
      DATA = await load();
      setHeader(DATA);
      if (PAGE === "summary") renderIndex(DATA);
      if (PAGE === "leagues") renderLeagues(DATA);
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
