# LOLHOTSPAWN2 — Hotspawn LoL Pick'em picks for EVERY match
Mobile-first dashboard: **Executive Summary → docs/index.html** (published via GitHub Pages).
Every LoL match on https://play.hotspawn.com/lol-pickems gets a pick + win probability from
external esportsbook/prediction-market lines, or our own Leaguepedia-Elo model for low-tier
matches no book prices, or an explicitly flagged 50/50 unresolved row. Updated automatically
every 6 hours by `.github/workflows/update-picks.yml` (script: `scripts/update_picks.py`).
See `COORDINATION.md` and the site's Method & Sources page. Not betting advice.
Optional: add a free `ODDSPAPI_KEY` repo secret to enable Pinnacle/bet365-network lines.
