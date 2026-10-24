/* Hotspawn LoL Picks — data-driven mobile-first dashboard (vanilla JS, zero build step) */
(() => {
  "use strict";
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const pct = (x) => (x == null ? "—" : `${Math.round(x * 100)}%`);
  const pct1 = (x) => (x == null ? "—" : `${(x * 100).toFixed(1)}%`);
  // Two-way display that always sums to exactly 100.0%: rounding each side
  // independently can print 68.5% + 31.6% = 100.1% for p=0.6845/0.3155.
  const pctPair = (a) => {
    if (a == null) return ["—", "—"];
    const x = Math.round(a * 1000) / 10;
    const y = Math.round((100 - x) * 10) / 10;
    return [`${x.toFixed(1)}%`, `${y.toFixed(1)}%`];
  };
  const slugify = (s) => String(s || "league").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  const METHOD = {
    MARKET_CONSENSUS: { label: "Market consensus", cls: "green", ico: "💰" },
    MARKET_SINGLE: { label: "Single book line", cls: "green", ico: "💰" },
    MODEL_ELO: { label: "Own Elo model", cls: "blue", ico: "🧮" },
    MODEL_ELO_THIN: { label: "Elo (thin history)", cls: "amber", ico: "🧮" },
    MODEL_ELO_STANDINGS: { label: "Elo + split standings", cls: "blue", ico: "📊" },
    MODEL_STANDINGS: { label: "Split standings", cls: "blue", ico: "📊" },
    MODEL_LEAGUE_PRIOR: { label: "League prior", cls: "amber", ico: "📐" },
    UNRESOLVED: { label: "Unresolved 50/50", cls: "red", ico: "⚠️" },
  };
  const CONF = { High: "green", Medium: "blue", Low: "amber", None: "red" };
  const CONF_RANK = { High: 3, Medium: 2, Low: 1, None: 0 };
  const METHOD_RANK = {
    MARKET_CONSENSUS: 6, MARKET_SINGLE: 5, MODEL_ELO: 4,
    MODEL_STANDINGS: 3, MODEL_ELO_STANDINGS: 3, MODEL_ELO_THIN: 2, MODEL_LEAGUE_PRIOR: 1, UNRESOLVED: 0,
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
    const pair = pctPair(m.prob_team1);
    return `<article class="match ${cls}">
      <div class="match-top"><span class="when" title="${esc(t.title)}">${esc(t.text)}</span><span>·</span><span>${esc(m.tournament || "Tournament TBC")}</span>${m.best_of ? `<span>· Bo${esc(m.best_of)}</span>` : ""}<span class="chip ${cls === "unres" ? "red" : cls === "partial" ? "amber" : cls === "market" ? "green" : "blue"}">${mi.ico} ${esc(mi.label)}</span></div>
      <div class="teams"><a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team1)}</a> <span class="vs">vs</span> <a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team2)}</a></div>
      <div class="bar" aria-hidden="true"><i style="width:${pct(m.prob_team1)}"></i><b style="width:${pct(m.prob_team2)}"></b></div>
      <div class="probrow"><span>${esc(m.team1)} <b>${pair[0]}</b></span><span style="margin-left:auto">${esc(m.team2)} <b>${pair[1]}</b></span></div>
      <div class="pickline">${pickPill(m)}<span class="chip ${CONF[m.confidence] || ""}">${esc(m.confidence || "—")} confidence</span></div>
      <div class="evidence">${esc(m.evidence || "")}</div>
      ${sourcesInline(m, opts.sources || 3)}
    </article>`;
  }

  function row(m) {
    const t = whenLocal(m.start_utc);
    const pair = pctPair(m.prob_team1);
    const mi = methodInfo(m);
    const cls = matchClass(m);
    const srcCount = (m.sources || []).filter((s) => s.url).length;
    const srcLinks = (m.sources || []).filter((s) => s.url).slice(0, 3)
      .map((s) => `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)} ↗</a>`).join(" ");
    return `<tr class="${cls}">
      <td data-label="Start" title="${esc(t.title)}"><b>${esc(t.text)}</b><span class="sub">${esc(whenUTC(m.start_utc))}</span><span class="sub">${esc(relative(m.start_utc))}</span></td>
      <td class="teams-cell" data-label="Match"><a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team1)}</a> <span class="vs">vs</span> <a class="rowlink" href="match.html?id=${encodeURIComponent(m.id)}">${esc(m.team2)}</a><span class="sub">${esc(m.tournament || "")}${m.best_of ? ` · Bo${esc(m.best_of)}` : ""}${m.tier && !/^WAITING/i.test(m.tier) ? ` · Tier ${esc(m.tier)}` : ""}</span></td>
      <td class="probcell" data-label="Win probability"><span class="p1">${esc(m.team1)} ${pair[0]}</span><span class="sub"><span class="p2">${esc(m.team2)} ${pair[1]}</span></span><div class="bar" aria-hidden="true"><i style="width:${pct(m.prob_team1)}"></i><b style="width:${pct(m.prob_team2)}"></b></div></td>
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
      const st = ms.filter((x) => x.method === "MODEL_STANDINGS" || x.method === "MODEL_ELO_STANDINGS").length;
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
        limitation: mkt
          ? "Priced by external bookmaker/prediction-market consensus."
          : ("No external sportsbook line; priced via Leaguepedia recorded results"
             + (st ? " & current-split standings records." : ".")),
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


  function probeBooks(d) {
    const p = d.market_probe || {};
    return Array.isArray(p.books) ? p.books : [];
  }

  function probeSummaryLine(d) {
    const p = d.market_probe || {};
    const s = p.summary || {};
    if (!p.checked_at) return "No external-source probe ran in this refresh.";
    const when = whenUTC(p.checked_at);
    return `<b>${s.checked ?? 0}</b> external sources were requested once on ${esc(when)}: `
      + `<b>${s.reachable ?? 0}</b> answered, <b>${s.structured_json ?? 0}</b> returned structured JSON, `
      + `<b>${s.structured_with_lol ?? 0}</b> contained any League of Legends match market. `
      + `Market sources checked: <b>${s.market_sources_checked ?? 0}</b>, reachable: <b>${s.market_sources_reachable ?? 0}</b>. `
      + `Only Pinnacle, Unibet (Kambi), Bovada and Polymarket can produce a market probability, and only when they publish a full-match line.`;
  }

  function probeRows(d, opts = {}) {
    const books = probeBooks(d);
    if (!books.length) return `<tr><td colspan="4" class="small">No external-source probe ran in this refresh.</td></tr>`;
    return books.map((b) => `<tr>
      <td data-label="Source"><b>${esc(b.name)}</b><span class="sub"><a href="${esc(b.url)}" target="_blank" rel="noopener">${esc(b.url)} ↗</a></span></td>
      <td data-label="Type"><span class="chip">${b.category === "results" ? "Results" : "Market"}</span><span class="sub">${esc(b.kind || "")}</span></td>
      <td data-label="HTTP"><span class="chip ${b.http_status === 200 ? "green" : b.http_status ? "amber" : "red"}">${esc(b.http_status ?? "no response")}</span></td>
      <td data-label="Verdict" class="small">${esc(b.verdict || "")}</td>
    </tr>`).join("");
  }

  function probeStrip(d) {
    const books = probeBooks(d);
    if (!books.length) return `<span class="chip">No probe ran</span>`;
    return books.map((b) => `<span class="chip ${b.http_status === 200 ? "green" : b.http_status ? "amber" : "red"}" title="${esc(b.verdict || "")}" role="listitem">${esc(b.name)} · ${esc(b.http_status ?? "—")}</span>`).join(" ");
  }

  function leagueLimitRows(lbs, withCategory) {
    if (!lbs.length) return `<tr><td colspan="${withCategory ? 6 : 5}">No competitions in this refresh.</td></tr>`;
    return lbs.map((lb) => `<tr>
      <td data-label="Competition"><a class="rowlink" href="leagues.html#league-${esc(slugify(lb.tournament))}"><b>${esc(lb.tournament)}</b></a>${withCategory ? `<span class="sub">${esc(lb.category || "")}</span>` : ""}</td>
      <td data-label="Fixtures"><b>${lb.fixtures}</b></td>
      <td data-label="Pricing mix" class="small">💰 ${lb.market} · 🧮 ${lb.elo} · 📊 ${lb.standings || 0} · 📐 ${lb.league_prior} · ⚠️ ${lb.unresolved}</td>
      <td data-label="Limitation" class="small">${esc(lb.limitation || "")}</td>
      <td data-label="Source">${leagueSourceLinks(lb)}</td>
    </tr>`).join("");
  }

  // One source of truth for "how was each fixture priced" (used by the summary and the
  // unresolved page so the two can never disagree again).
  function pricingMix(d) {
    const rows = d.matches || [];
    const n = (f) => rows.filter(f).length;
    const mix = {
      total: rows.length,
      market: n((m) => !!m.market),
      elo: n((m) => m.method === "MODEL_ELO" || m.method === "MODEL_ELO_THIN"),
      standings: n((m) => m.method === "MODEL_STANDINGS" || m.method === "MODEL_ELO_STANDINGS"),
      prior: n((m) => m.method === "MODEL_LEAGUE_PRIOR"),
      unresolved: n((m) => m.method === "UNRESOLVED"),
    };
    return mix;
  }

  function renderIndex(d) {
    const c = d.counts || {};
    const set = (id, v) => { const el = $(id); if (el) el.textContent = v; };
    set("#stat-fixtures", c.fixtures ?? "—");
    set("#stat-market", c.market ?? "—");
    set("#stat-model", c.model ?? "—");
    set("#stat-unresolved", c.unresolved ?? "—");

    const cov0 = d.coverage || {};
    const all0 = d.matches || [];
    const n24 = all0.filter((m) => { const t = new Date(m.start_utc).getTime(); return t >= Date.now() - 300000 && t <= Date.now() + 86400000; }).length;
    set("#here-all-count", all0.length);
    set("#here-24-count", n24);
    set("#here-leagues-count", computeLeagueBreakdown(d).length);
    set("#here-unresolved-count", cov0.unresolved ?? 0);
    set("#here-low-count", cov0.low_confidence ?? c.low_confidence ?? 0);
    const hs = $("#hero-status");
    if (hs) {
      hs.innerHTML = `<b>Updated ${esc(whenLocal(d.generated_at).text)}</b> (${esc(whenUTC(d.generated_at))}) · `
        + `next refresh ${esc(whenUTC(d.next_update_utc))} · `
        + `<b>${cov0.resolved ?? 0}/${cov0.fixtures ?? 0}</b> listed matches priced `
        + `(${cov0.resolved_pct ?? 0}%) · <a href="picks.html">open the picks →</a>`;
    }

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
    // Count the pricing mix from the rows themselves. The coverage fields are a
    // summary written by the generator and mixing them with method counts produced a
    // breakdown that did not add up to the fixture total (e.g. 9 + 41 + 55 = 105 of 160).
    const mix = pricingMix(d);
    const stCount = mix.standings;
    const covText = $("#coverage-text");
    if (covText) covText.innerHTML = `<b>${cov.resolved ?? 0} of ${cov.fixtures ?? 0}</b> fixtures have a verified pick (${cov.resolved_pct ?? 0}%): <b>${mix.market}</b> from external betting lines, <b>${mix.elo}</b> from our chronological Elo model, <b>${stCount}</b> from split standings, <b>${mix.prior}</b> from competition priors, and <b>${mix.unresolved}</b> explicit 50/50 placeholders (total ${mix.total}). See <a href="picks.html">All picks</a> · <a href="leagues.html">By league</a> · <a href="unresolved.html">Unresolved &amp; limitations</a>.`;
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
    const reasons = (u.reasons || []).map((r) => `<li><b>${r.count}</b> — ${esc(r.reason)}</li>`).join("");
    const lims = (u.limitations || []).slice(0, 4).map((x) => `<li>${esc(x)}</li>`).join("");
    const uCount = u.count ?? 0;
    const lcCount = u.low_confidence_count ?? 0;
    const ubox = $("#unresolved-summary");
    if (ubox) {
      // The headline sentence has to read correctly whether or not anything is
      // currently unresolved: "0 fixtures lack ..." is confusing on its own.
      const headline = uCount > 0
        ? `<b>${uCount}</b> fixture${uCount === 1 ? "" : "s"} lack external lines, recorded team
           matches, and split standings — published strictly as an explicit <b>50.0% / 50.0% placeholder</b>
           (never an edge).`
        : `<b>No fixture is unresolved right now</b> — every upcoming Hotspawn LoL match has a pick from an
           external betting line, our Elo model, or a current-split standings record. Anything that later
           loses its evidence is published here as an explicit <b>50.0% / 50.0% placeholder</b>, never an edge.`;
      // Per-league limitations are part of the executive summary, not only on
      // the separate Unresolved page, so the reader sees which signal prices
      // each competition without leaving this page.
      const bl = d.unresolved?.by_league || [];
      const perLeague = bl.length ? `
        <p class="small"><b>Per-league limitations — which signal prices each competition</b></p>
        <div class="table-wrap"><table>
          <thead><tr><th scope="col">Competition</th><th scope="col">Fixtures</th><th scope="col">Pricing mix</th><th scope="col">Limitation</th></tr></thead>
          <tbody>${bl.map((b) => `<tr>
            <td data-label="Competition"><a class="rowlink" href="leagues.html#league-${esc(slugify(b.tournament))}"><b>${esc(b.tournament)}</b></a></td>
            <td data-label="Fixtures"><b>${b.fixtures}</b></td>
            <td data-label="Pricing mix" class="small">💰 ${b.market ?? 0} mkt · 🧮 ${b.elo ?? 0} Elo · 📊 ${b.standings ?? 0} st · 📐 ${b.prior_only ?? 0} prior · ⚠️ ${b.unresolved ?? 0} unres</td>
            <td data-label="Limitation" class="small">${esc(b.limitation || b.best_signal || "")}</td>
          </tr>`).join("")}</tbody>
        </table></div>` : "";
      ubox.innerHTML = `<div class="warnbox"><h3>⚠️ Unresolved picks (${uCount}) &amp; Low-confidence picks (${lcCount})</h3>
      <p>${headline} <b>${lcCount}</b> additional amateur/promotion row${lcCount === 1 ? "" : "s"} rely on thin history (&lt;8 games), a cross-league comparison, or a single debut side against the competition prior and ${lcCount === 1 ? "is" : "are"} capped at Low confidence. Hotspawn's crowd % is never used.</p>
      ${reasons ? `<p class="small"><b>Breakdown by reason</b></p><ul class="clean small">${reasons}</ul>` : ""}
      ${perLeague}
      <p class="small"><b>Key limitations for generating low-tier picks</b></p><ul class="clean small">${lims}</ul>
      <p><a class="btn warn" href="unresolved.html">Open Unresolved &amp; full per-league limitations page →</a></p></div>`;
    }

    const exLimBody = $("#exec-league-limits-body");
    if (exLimBody) exLimBody.innerHTML = leagueLimitRows(computeLeagueBreakdown(d), false);

    const exProbeStrip = $("#exec-probe-strip");
    if (exProbeStrip) exProbeStrip.innerHTML = probeStrip(d);
    const exProbeSummary = $("#probe-summary");
    if (exProbeSummary) exProbeSummary.innerHTML = probeSummaryLine(d);

    const exLimits = $("#exec-limitations");
    if (exLimits) {
      const list = (u.limitations || []);
      exLimits.innerHTML = list.length ? list.map((x) => `<li>${esc(x)}</li>`).join("")
        : "<li>No limitations recorded in this refresh.</li>";
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
    if (state.filter === "standings" && m.method !== "MODEL_STANDINGS" && m.method !== "MODEL_ELO_STANDINGS") return false;
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
      standings: all.filter((m) => m.method === "MODEL_STANDINGS" || m.method === "MODEL_ELO_STANDINGS").length,
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
      limBody.innerHTML = lbs.map((x) => `<tr>
        <td data-label="Competition"><a class="rowlink" href="leagues.html#league-${esc(slugify(x.tournament))}"><b>${esc(x.tournament)}</b></a></td>
        <td data-label="Fixtures"><b>${x.fixtures}</b></td>
        <td data-label="Breakdown" class="small">💰 ${x.market} · 🧮 ${x.elo} · 📊 ${x.standings || 0} · 📐 ${x.league_prior} · ⚠️ ${x.unresolved}</td>
        <td data-label="Limitation" class="small">${esc(x.limitation || "")}</td>
        <td data-label="Sources">${leagueSourceLinks(x)}</td>
      </tr>`).join("");
    }
    const reasons = (d.unresolved?.reasons || []).map((r) => `<li><b>${r.count}</b> — ${esc(r.reason)}</li>`).join("");
    const rbox = $("#reasons");
    if (rbox) rbox.innerHTML = reasons || "<li>None.</li>";
    const lim = (d.unresolved?.limitations || []).map((x) => `<li>${esc(x)}</li>`).join("");
    const lbox = $("#limitations");
    if (lbox) lbox.innerHTML = lim;
    const mix = $("#resolution-mix");
    if (mix) {
      const cov = d.coverage || {};
      const counts = pricingMix(d);
      mix.innerHTML = `<b>${cov.fixtures ?? 0}</b> scheduled fixtures published · `
        + `<b>${counts.market}</b> priced by external betting lines · `
        + `<b>${counts.elo}</b> by our Elo model · `
        + `<b>${counts.standings}</b> by split standings · `
        + `<b>${counts.prior}</b> by a competition prior · `
        + `<b>${counts.unresolved}</b> explicit 50/50 placeholders (total ${counts.total}). `
        + `Every row still carries its own source link on <a href="picks.html">All picks</a>.`;
    }
    const psum = $("#probe-summary");
    if (psum) psum.innerHTML = probeSummaryLine(d);
    const pbody = $("#probe-body");
    if (pbody) pbody.innerHTML = probeRows(d);
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
      STANDINGS_BLEND_APPLIED: "Current-split standings record blended into the rating",
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
    const pair = pctPair(m.prob_team1);
    const t = whenLocal(m.start_utc);
    const marketRows = (m.market?.sources || []).map((s) => { const p = pctPair(s.prob_team1); return `<tr><td><b>${esc(s.source)}</b></td><td>${p[0]}</td><td>${p[1]}</td><td>${s.decimal_team1 ? esc(s.decimal_team1) : "—"}</td><td><a href="${esc(s.url)}" target="_blank" rel="noopener">open ↗</a></td></tr>`; }).join("");
    const model = m.model || {};
    const h2h = model.h2h ? `${model.h2h.team1_wins}/${model.h2h.games} head-to-head wins for ${esc(m.team1)}` : "No head-to-head sample in the last 24 months.";
    box.innerHTML = `
      <div class="detail-hero">
        <div class="match-top"><span class="chip ${mi.cls}">${mi.ico} ${esc(mi.label)}</span><span class="chip ${CONF[m.confidence] || ""}">${esc(m.confidence || "—")} confidence</span>${m.best_of ? `<span class="chip">Bo${esc(m.best_of)}</span>` : ""}${m.tier ? `<span class="chip">${/^WAITING/i.test(m.tier) ? "Tier not published" : `Tier ${esc(m.tier)}`}</span>` : ""}</div>
        <h1>${esc(m.team1)} <span style="color:var(--muted);font-weight:600;font-size:.6em">vs</span> ${esc(m.team2)}</h1>
        <p class="small">${esc(m.tournament || "")} · ${esc(t.text)} <span title="${esc(t.title)}">· ${esc(whenUTC(m.start_utc))}</span> · ${esc(relative(m.start_utc))}</p>
        <div class="bar" aria-hidden="true"><i style="width:${pct(m.prob_team1)}"></i><b style="width:${pct(m.prob_team2)}"></b></div>
        <div class="probrow"><span>${esc(m.team1)} <b>${pair[0]}</b></span><span style="margin-left:auto">${esc(m.team2)} <b>${pair[1]}</b></span></div>
        <div class="pickline">${pickPill(m)}</div>
        <p class="small">${esc(m.evidence || "")}</p>
      </div>
      <div class="two-col">
        <div>
          <div class="card"><h3>${m.market ? "External betting lines" : "No external betting line"}</h3>
            ${m.market ? `<p class="small">Consensus: <b>${pctPair(m.market.consensus_team1)[0]}</b> ${esc(m.team1)} · <b>${pctPair(m.market.consensus_team1)[1]}</b> ${esc(m.team2)}. Dispersion ${pct1(m.market.dispersion)} across ${m.market.distinct_books ?? m.market.source_count} book(s).${m.market.model_team1 != null ? ` Model: ${pct1(m.market.model_team1)} (edge ${(m.market.model_edge_team1 * 100 >= 0 ? "+" : "")}${(m.market.model_edge_team1 * 100).toFixed(1)} pts).` : ""}</p>
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
    const mProbe = $("#market-probe-body");
    if (mProbe) mProbe.innerHTML = probeRows(d);
    const mProbeSum = $("#probe-summary");
    if (mProbeSum) mProbeSum.innerHTML = probeSummaryLine(d);
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
