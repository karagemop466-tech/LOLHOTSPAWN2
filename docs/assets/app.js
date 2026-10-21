async function load(){const r=await fetch('data/picks.json',{cache:'no-store'});return r.json()}
const pct=x=>Math.round(x*100)+'%';
const badge=m=>({MARKET_BOOKS:'💰 Esportsbook line',MARKET_POLYMARKET:'💰 Polymarket',MODEL_ELO:'🧮 Our Elo model',UNRESOLVED:'⚠️ Unresolved'})[m]||m;
function card(m){const P1=Math.round(m.prob_team1*100),P2=100-P1;return `<article class="card ${m.method=='UNRESOLVED'?'unres':m.method.startsWith('MARKET')?'market':''} pick">
<div class="meta">${m.start_utc?new Date(m.start_utc).toLocaleString():m.start_raw} · ${m.tournament||''} · Tier ${m.tier||'?'} ${m.points?('· '+m.points+' pts'):''}</div>
<div class="teams">${m.team1} <span class="vs">vs</span> ${m.team2}</div>
<div class="bar"><i style="width:${P1+'%'}"></i><b style="width:${P2+'%'}"></b></div>
<div>${m.team1}: <b>${P1+'%'}</b> &nbsp;·&nbsp; ${m.team2}: <b>${P2+'%'}</b></div>
<div class="pct">✅ PICK: ${m.pick} (${pct(m.pick_prob)})</div>
<div><span class="badge">${badge(m.method)}</span><span class="badge">${m.confidence||''}</span></div>
<div class="meta">Evidence: ${m.evidence||''} ${m.market_url?`· <a href="${m.market_url}" target="_blank" rel="noopener">market source ↗</a>`:''} ${m.source_url?`· <a href="${m.source_url}" target="_blank" rel="noopener">source ↗</a>`:''} ${m.hotspawn_url?`· <a href="${m.hotspawn_url}" target="_blank" rel="noopener">Hotspawn match ↗</a>`:''}</div></article>`}
