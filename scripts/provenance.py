"""Evidence labels, not a new probability model or an official verification claim.

Hotspawn is first-party evidence for its own listing. Leaguepedia is community
reporting. Neither an HTTP 200 nor an organizer homepage verifies an outcome,
a model estimate, or all results used to train that estimate.
"""
from urllib.parse import urlparse


def source_kind(url):
    host = (urlparse(url or "").hostname or "").lower()
    def on(domain):
        return host == domain or host.endswith("." + domain)
    if on("hotspawn.com"):
        return "fixture_provider"
    if any(on(d) for d in ("lol.fandom.com", "liquipedia.net")):
        return "community_reference"
    if any(on(d) for d in ("pinnacle.com", "bovada.lv", "polymarket.com", "kambicdn.com",
                            "unibet.com", "unibet.com.au")):
        return "market_publisher"
    return "unclassified_reference"


def annotate_matches(matches):
    """Add machine-readable provenance without changing estimates or input facts."""
    for m in matches:
        for s in m.get("sources") or []:
            s["source_kind"] = source_kind(s.get("url"))
        unresolved = m.get("method") == "UNRESOLVED"
        market = bool(m.get("market"))
        m["verification"] = {
            "probability_kind": "unavailable" if unresolved else "market_derived" if market else "model_estimate",
            # Deliberately blank: no primary-organizer, result-by-result audit is
            # implemented. A generic organizer link must never fill this field.
            "official_results_confirmed": None,
            "official_results_source": None,
            "status": "unverified_official_results" if not market else "market_reference_only",
            "limitation": (
                "No supported probability or recommendation. Internal 50/50 values are placeholders only."
                if unresolved else
                "De-vigged external prices are estimates, not verified outcomes or guaranteed win chances."
                if market else
                "Own estimate from community-reported Leaguepedia results/standings; underlying results have not been independently confirmed against primary organizer records."
            ),
        }
    return matches


def market_arithmetic_errors(matches):
    """Recompute no-vig/consensus arithmetic from the saved source values only.

    Does NOT prove the provider still quotes those prices or verify team identity.
    Decimal fields are nullable for prediction markets; never synthesize them.
    Tolerance allows the stored four-decimal rounding of odds/probabilities.
    """
    from statistics import median
    weights = {"pinnacle": 1.0, "unibet": .85, "bovada": .8, "polymarket": .7}
    errors = []
    for m in matches:
        market = m.get("market") or {}
        records = market.get("sources") or []
        for r in records:
            a, b = r.get("decimal_team1"), r.get("decimal_team2")
            if a is None or b is None:
                continue  # cannot confirm an absent value; leave it blank
            try:
                if a <= 1 or b <= 1:
                    raise ValueError("decimal odds must exceed 1")
                expected = (1 / a) / (1 / a + 1 / b)
                if abs(expected - r["prob_team1"]) > .0003:
                    raise ValueError("recorded no-vig probability disagrees with decimal odds")
            except (KeyError, TypeError, ValueError) as e:
                errors.append(f"{m.get('id')}/{r.get('source')}: {e}")
        if records and all(isinstance(r.get("prob_team1"), (int, float)) for r in records):
            ps = [r["prob_team1"] for r in records]
            ws = [weights.get(r.get("source_key"), .6) for r in records]
            expected = median(ps) if len(ps) >= 3 else sum(p*w for p, w in zip(ps, ws))/sum(ws)
            observed = market.get("consensus_team1")
            if not isinstance(observed, (int, float)) or abs(observed - expected) > .00015:
                errors.append(f"{m.get('id')}: consensus disagrees with recorded source probabilities")
    return errors
