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
