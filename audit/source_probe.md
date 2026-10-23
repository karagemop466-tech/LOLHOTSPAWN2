# External source probe (read-only)

Generated: 2026-10-23T15:43:45.830680Z · 36 endpoints probed against 117 team names on the current Hotspawn fixture list.

A source is marked **usable** only when it returns HTTP 200, is machine-readable or names a current Hotspawn team, and carries a League-of-Legends/price token. No probability is taken from any row here; this is an evidence log for manual review.

| Group | Source | HTTP | Bytes | LoL token | Current teams named | Low-tier leagues named | Price tokens | Usable | Link |
|---|---|---|---|---|---|---|---|---|---|
| established book | Pinnacle (control) | 200 | 14407 | no | 0 | no | yes | no | https://www.pinnacle.com/en/esports/league-of-legends |
| established book | Bovada (control) | 200 | 2 | no | 0 | no | no | no | https://www.bovada.lv/sports/esports/league-of-legends |
| established book | Betano LoL | 200 | 29842 | no | 1 | no | no | no | https://www.betano.com/sport/esports/league-of-legends/ |
| established book | Betsson LoL | 202 | 2597 | no | 0 | no | no | no | https://www.betsson.com/en/sportsbook/esports/league-of-legends |
| established book | Marathonbet esports | 403 | 5850 | no | 0 | no | no | no | https://www.marathonbet.com/en/betting/e-Sports |
| established book | Unibet LoL | 503 | 190 | no | 0 | no | no | no | https://www.unibet.com/betting/sports/filter/esports/league_of_legends |
| established book | DraftKings LoL | 404 | 257729 | no | 0 | no | yes | no | https://sportsbook.draftkings.com/leagues/esports/league-of-legends |
| established book | FanDuel esports | 200 | 11177 | no | 0 | no | yes | no | https://sportsbook.fanduel.com/navigation/esports |
| established book | BetMGM esports | 403 | 9887 | no | 0 | no | no | no | https://www.betmgm.com/en/sports |
| established book | Betway esports | 404 | 9 | no | 0 | no | no | no | https://www.betway.com/en/esports/league-of-legends |
| established book | 1xBet line feed | 203 | 2646 | no | 0 | no | no | no | https://1xbet.com/en/line/esports/ |
| established book | 1xBet LoL 1x2 | 203 | 2646 | no | 0 | no | no | no | https://1xbet.com/en/line/esports/ |
| established book | BetOnline esports | 200 | 365926 | no | 0 | no | yes | no | https://www.betonline.ag/sportsbook/esports |
| established book | BetUS esports | 403 | 5773 | no | 0 | no | no | no | https://www.betus.com.pa/sportsbook/esports/ |
| esportsbook | Rivalry LoL | 503 | 1591 | no | 0 | no | no | no | https://www.rivalry.com/lol |
| esportsbook | Thunderpick LoL | 403 | 5789 | no | 0 | no | no | no | https://thunderpick.io/esports/league-of-legends |
| esportsbook | GG.Bet LoL | 403 | 126 | no | 0 | no | no | no | https://gg.bet/en/esports/lol |
| esportsbook | Midnite LoL | 200 | 33881 | no | 0 | no | yes | no | https://www.midnite.com/esports/league-of-legends |
| esportsbook | LOOT.BET LoL | 0 | 0 | no | 0 | no | no | no | https://loot.bet/esports/league-of-legends |
| esportsbook | EsportsBet.io LoL | 404 | 149342 | no | 1 | no | yes | no | https://esportsbet.io/ |
| esportsbook | Betify esports | 403 | 4546 | no | 0 | no | no | no | https://www.betify.com/en/esports |
| odds aggregator | Oddspedia LoL | 410 | 340010 | yes | 0 | rivals | yes | no | https://oddspedia.com/esports/league-of-legends |
| odds aggregator | Oddspedia API (leagues) | 404 | 0 | no | 0 | no | no | no | https://oddspedia.com/esports/league-of-legends |
| odds aggregator | BetExplorer LoL | 404 | 0 | no | 0 | no | no | no | https://www.betexplorer.com/lol/ |
| odds aggregator | BetExplorer esports | 404 | 0 | no | 0 | no | no | no | https://www.betexplorer.com/esports/ |
| odds aggregator | OddsPortal LoL | 503 | 0 | no | 0 | no | no | no | https://www.oddsportal.com/lol/ |
| odds aggregator | OddsPortal esports | 200 | 335342 | yes | 1 | no | yes | no | https://www.oddsportal.com/esports/league-of-legends/ |
| odds aggregator | Oddspedia LoL (short path) | 404 | 339879 | yes | 0 | rivals | yes | no | https://oddspedia.com/lol |
| odds aggregator | The Odds API sports | 401 | 152 | no | 0 | no | no | no | https://the-odds-api.com/liveapi/guides/v4/ |
| prediction market | Polymarket (control) | 200 | 1382453 | yes | 12 | no | yes | **yes** | https://polymarket.com/markets/esports |
| prediction market | Kalshi esports series | 200 | 16 | no | 0 | no | no | no | https://kalshi.com/markets |
| prediction market | Manifold LoL | 200 | 8575 | yes | 0 | no | yes | **yes** | https://manifold.markets/ |
| data provider | PandaScore (no key) | 403 | 28 | no | 0 | no | no | no | https://developers.pandascore.co/docs |
| data provider | Abios (no key) | 0 | 0 | no | 0 | no | no | no | https://abiosgaming.com/ |
| data provider | SofaScore esports schedule | 403 | 48 | no | 0 | no | no | no | https://www.sofascore.com/esports |
| data provider | SofaScore LoL rankings | 403 | 48 | no | 0 | no | no | no | https://www.sofascore.com/tournament/league-of-legends/world-championship/325 |

## Observed responses

### Pinnacle (control)
- Endpoint: https://guest.api.arcadia.pinnacle.com/0.1/sports
- Observed: HTTP 200 · 14407 bytes · 0.13 s
- Body starts: `[ { "featureOrder": -1, "id": 1, "isFeatured": false, "isHidden": false, "isSticky": false, "matchupCount": 0, "matchupCountSE": 0, "name": "Badminton", "primaryMarketType": "moneyline" }, { "featureOrder": -1, "id": 2, `

### Bovada (control)
- Endpoint: https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends?marketFilterId=def&lang=en
- Observed: HTTP 200 · 2 bytes · 1.46 s
- Body starts: `{}`

### Betano LoL
- Endpoint: https://www.betano.com/sport/esports/league-of-legends/
- Observed: HTTP 200 · 29842 bytes · 0.37 s
- Current Hotspawn teams found in the body: geng
- Body starts: `<!DOCTYPE html> <html> <head> <meta charset="utf-8" /> <meta http-equiv="x-ua-compatible" content="ie=edge" /> <title>Online Betting - Great Odds and Live Betting | Betano</title> <meta name="description" content="Visit `

### Betsson LoL
- Endpoint: https://www.betsson.com/en/sportsbook/esports/league-of-legends
- Observed: HTTP 202 · 2597 bytes · 0.08 s
- Body starts: `<!DOCTYPE html> <html lang="en"> <head> <meta charset="utf-8"> <meta name="viewport" content="width=device-width, initial-scale=1"> <title></title> <style> body { font-family: "Arial"; } </style> <script type="text/javas`

### Marathonbet esports
- Endpoint: https://www.marathonbet.com/en/betting/e-Sports/League+of+Legends
- Observed: HTTP 403 · 5850 bytes · 0.19 s
- Body starts: `<!DOCTYPE html> <!--[if lt IE 7]> <html class="no-js ie6 oldie" lang="en-US"> <![endif]--> <!--[if IE 7]> <html class="no-js ie7 oldie" lang="en-US"> <![endif]--> <!--[if IE 8]> <html class="no-js ie8 oldie" lang="en-US"`

### Unibet LoL
- Endpoint: https://www.unibet.com/betting/sports/filter/esports/league_of_legends
- Observed: HTTP 503 · 190 bytes · 2.02 s
- Body starts: `<html> <head><title>503 Service Temporarily Unavailable</title></head> <body> <center><h1>503 Service Temporarily Unavailable</h1></center> <hr><center>nginx</center> </body> </html> `

### DraftKings LoL
- Endpoint: https://sportsbook.draftkings.com/leagues/esports/league-of-legends
- Observed: HTTP 404 · 257729 bytes · 0.96 s
- Body starts: `<!doctype html> <html lang="en"> <head> <meta charset="utf-8"> <meta http-equiv="X-UA-Compatible" content="IE=edge"> <meta name="viewport" content="width=device-width, initial-scale=1"> <title>404 Not Found | DraftKings `

### FanDuel esports
- Endpoint: https://sportsbook.fanduel.com/navigation/esports
- Observed: HTTP 200 · 11177 bytes · 0.24 s
- Body starts: `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,shrink-to-fit=no"><title>FanDuel Sportsbook</title><link rel="icon shortcut" href="https://spor`

### BetMGM esports
- Endpoint: https://www.betmgm.com/en/sports/esports-10
- Observed: HTTP 403 · 9887 bytes · 0.2 s
- Body starts: `<!DOCTYPE html> <html lang="en"> <head> <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> <meta content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=3.0, user-scalable=yes" n`

### Betway esports
- Endpoint: https://www.betway.com/en/esports/league-of-legends
- Observed: HTTP 404 · 9 bytes · 0.44 s
- Body starts: `Not found`

### 1xBet line feed
- Endpoint: https://1xbet.com/LineFeed/GetSportsShortZip?sports=all&lng=en&country=1&partner=51
- Observed: HTTP 203 · 2646 bytes · 0.71 s
- Body starts: `<!DOCTYPE html><html data-capo=""><head><meta charset="utf-8"> <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"> <link rel="stylesheet" href="/sys-static/shared-assets/Desktop/__sha`

### 1xBet LoL 1x2
- Endpoint: https://1xbet.com/LineFeed/Get1x2_VZip?sports=92&count=50&lng=en&mode=4&country=1&partner=51
- Observed: HTTP 203 · 2646 bytes · 0.6 s
- Body starts: `<!DOCTYPE html><html data-capo=""><head><meta charset="utf-8"> <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"> <link rel="stylesheet" href="/sys-static/shared-assets/Desktop/__sha`

### BetOnline esports
- Endpoint: https://www.betonline.ag/sportsbook/esports
- Observed: HTTP 200 · 365926 bytes · 1.44 s
- Body starts: `<!DOCTYPE html><script>(function(){const webAppConfig = {"FEATURE_UBS_LIVE_PARLAY":"true","FEATURE_STRAPI_PROMO_BANNERS":"true","FEATURE_HUB_OUTRIGHTS_ALL_TAB":"true","CHASHOUT_API_URL":"https://cashoutapi.betonline.ag/a`

### BetUS esports
- Endpoint: https://www.betus.com.pa/sportsbook/esports/
- Observed: HTTP 403 · 5773 bytes · 0.6 s
- Body starts: `<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=Edge"><meta name="robots" content="`

### Rivalry LoL
- Endpoint: https://www.rivalry.com/lol
- Observed: HTTP 503 · 1591 bytes · 3.28 s
- Body starts: `<!DOCTYPE html> <html> <head> <title>503 Backend fetch failed</title> </head> <body> <h1>Error 503 Backend fetch failed</h1> <p>Backend fetch failed</p> <h3>Guru Meditation:</h3> <p>XID: 679774019</p> <hr> <p>Varnish cac`

### Thunderpick LoL
- Endpoint: https://thunderpick.io/esports/league-of-legends
- Observed: HTTP 403 · 5789 bytes · 0.1 s
- Body starts: `<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=Edge"><meta name="robots" content="`

### GG.Bet LoL
- Endpoint: https://gg.bet/en/esports/lol
- Observed: HTTP 403 · 126 bytes · 0.08 s
- Body starts: `This internet site is not accepting visitors from your region. If you have any questions please address them to support@gg.bet`

### Midnite LoL
- Endpoint: https://www.midnite.com/esports/league-of-legends
- Observed: HTTP 200 · 33881 bytes · 0.34 s
- Body starts: `<!DOCTYPE html><html><head><meta charset="utf-8" /> <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no" /> <base href="/" /> <title>Sports Betting, Casino Games, &amp; Live`

### LOOT.BET LoL
- Endpoint: https://loot.bet/esports/league-of-legends
- Observed: HTTP 0 · 0 bytes · 2.04 s

### EsportsBet.io LoL
- Endpoint: https://esportsbet.io/sport/league-of-legends
- Observed: HTTP 404 · 149342 bytes · 0.69 s
- Current Hotspawn teams found in the body: lyon
- Body starts: `<!DOCTYPE html><html lang="en"><head><meta charSet="utf-8"/><link rel="icon" href="/favicon.png"/><meta property="og:site_name" content="EsportsBet.io"/><meta property="og:locale" content="en_US"/><meta name="application`

### Betify esports
- Endpoint: https://www.betify.com/en/esports/league-of-legends
- Observed: HTTP 403 · 4546 bytes · 0.11 s
- Body starts: `<!DOCTYPE html> <!--[if lt IE 7]> <html class="no-js ie6 oldie" lang="en-US"> <![endif]--> <!--[if IE 7]> <html class="no-js ie7 oldie" lang="en-US"> <![endif]--> <!--[if IE 8]> <html class="no-js ie8 oldie" lang="en-US"`

### Oddspedia LoL
- Endpoint: https://oddspedia.com/esports/league-of-legends
- Observed: HTTP 410 · 340010 bytes · 2.81 s
- Body starts: `<!doctype html><html data-n-head-ssr><head ><meta data-n-head="ssr" charset="utf-8"><meta data-n-head="ssr" name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover"><meta data-n-`

### Oddspedia API (leagues)
- Endpoint: https://oddspedia.com/api/v1/getSportLeagues?sport=league-of-legends&limit=5
- Observed: HTTP 404 · 0 bytes · 0.16 s

### BetExplorer LoL
- Endpoint: https://www.betexplorer.com/lol/
- Observed: HTTP 404 · 0 bytes · 1.39 s

### BetExplorer esports
- Endpoint: https://www.betexplorer.com/esports/
- Observed: HTTP 404 · 0 bytes · 0.42 s

### OddsPortal LoL
- Endpoint: https://www.oddsportal.com/lol/
- Observed: HTTP 503 · 0 bytes · 2.3 s

### OddsPortal esports
- Endpoint: https://www.oddsportal.com/esports/league-of-legends/
- Observed: HTTP 200 · 335342 bytes · 2.07 s
- Current Hotspawn teams found in the body: lyon
- Body starts: `<!DOCTYPE html><html lang="en" class="opensans_aaadb7a3-module__b9fGUa__variable montserrat_5d237d23-module__hkFSxG__variable"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale`

### Oddspedia LoL (short path)
- Endpoint: https://oddspedia.com/lol
- Observed: HTTP 404 · 339879 bytes · 1.1 s
- Body starts: `<!doctype html><html data-n-head-ssr><head ><meta data-n-head="ssr" charset="utf-8"><meta data-n-head="ssr" name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover"><meta data-n-`

### The Odds API sports
- Endpoint: https://api.the-odds-api.com/v4/sports/?apiKey=
- Observed: HTTP 401 · 152 bytes · 0.23 s
- Body starts: `{"message":"API key is missing","error_code":"MISSING_KEY","details_url":"https://the-odds-api.com/liveapi/guides/v4/api-error-codes.html#missing-key"} `

### Polymarket (control)
- Endpoint: https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=20
- Observed: HTTP 200 · 1382453 bytes · 3.99 s
- Current Hotspawn teams found in the body: anyoneslegend, bilibiligaming, dpluskia, g2esports, geng, hanwhalifeesports, invictusgaming, karminecorp
- Body starts: `[{"id":"131447","ticker":"lol-worlds-2026-winning-region-226","slug":"lol-worlds-2026-winning-region-226","title":"Worlds 2026 Winning Region","description":"This market will resolve according to the region or country of`

### Kalshi esports series
- Endpoint: https://api.elections.kalshi.com/trade-api/v2/series?category=Esports
- Observed: HTTP 200 · 16 bytes · 0.11 s
- Body starts: `{"series":null} `

### Manifold LoL
- Endpoint: https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=10
- Observed: HTTP 200 · 8575 bytes · 0.26 s
- Body starts: `[{"id":"sC6cPEn0dZ","creatorId":"mQAyH9lcrrXmk0gVstjVtBU6Lhr1","creatorUsername":"Zeolite","creatorName":"Zeolite","createdTime":1791212192210,"creatorAvatarUrl":"https://firebasestorage.googleapis.com/v0/b/mantic-market`

### PandaScore (no key)
- Endpoint: https://api.pandascore.co/lol/matches/upcoming
- Observed: HTTP 403 · 28 bytes · 0.39 s
- Body starts: `{"error":"Token is missing"}`

### Abios (no key)
- Endpoint: https://api.abiosgaming.com/v2/series
- Observed: HTTP 0 · 0 bytes · 1.55 s

### SofaScore esports schedule
- Endpoint: https://api.sofascore.com/api/v1/sport/esports/scheduled-events/2026-10-23
- Observed: HTTP 403 · 48 bytes · 0.1 s
- Body starts: `{"error": {"code": 403, "reason": "Forbidden" }}`

### SofaScore LoL rankings
- Endpoint: https://api.sofascore.com/api/v1/unique-tournament/325/rankings
- Observed: HTTP 403 · 48 bytes · 0.03 s
- Body starts: `{"error": {"code": 403, "reason": "Forbidden" }}`

