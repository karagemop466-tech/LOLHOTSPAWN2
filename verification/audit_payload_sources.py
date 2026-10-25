#!/usr/bin/env python3
"""
audit_payload_sources.py — CI gate around scripts/source_audit.py.

The audit itself lives in `scripts/source_audit.py` because the pipeline calls it
on every refresh and publishes the result as `payload["source_audit"]`. This
wrapper runs the same code over the committed payload and fails the build if any
row has an arithmetic/provenance defect, so the JSON and the site can never
disagree about what was checked.

Outputs:
  verification/payload-audit.json  full per-row record (id, teams, verdict, links)
  verification/payload-audit.md    one line per row + the flags
Exit code 1 on a hard failure.

Usage: python3 verification/audit_payload_sources.py [--diag data/diag]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from source_audit import audit, day_of, find_pair, load_snapshots  # noqa: E402

PAYLOAD = os.path.join(ROOT, "docs", "data", "picks.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diag", default=os.path.join(ROOT, "data", "diag"))
    ap.add_argument("--json-out", default=os.path.join(ROOT, "verification", "payload-audit.json"))
    ap.add_argument("--md-out", default=os.path.join(ROOT, "verification", "payload-audit.md"))
    args = ap.parse_args()

    payload = json.load(open(PAYLOAD, encoding="utf-8"))
    matches = payload["matches"]
    out = audit(matches, args.diag)

    snaps = load_snapshots(args.diag)
    flags_by_id = {f["id"]: f for f in out["flags"]}
    rows = []
    for m in matches:
        hits = find_pair(snaps, m.get("team1", ""), m.get("team2", ""))
        same_day = [h for h in hits if day_of(h.get("DateTime UTC")) == day_of(m.get("start_utc"))]
        src = next((s.get("url") for s in (m.get("sources") or []) if isinstance(s, dict)), None)
        rows.append({
            "id": m.get("id"),
            "teams": f"{m.get('team1')} vs {m.get('team2')}",
            "competition": m.get("tournament"),
            "start_utc": m.get("start_utc"),
            "method": m.get("method"),
            "pick": m.get("pick"),
            "pick_prob": m.get("pick_prob"),
            "leaguepedia_url": m.get("leaguepedia_url"),
            "match_url": f"match.html?id={m.get('id')}",
            "re_matched_same_day": bool(same_day),
            "flag": flags_by_id.get(str(m.get("id"))),
            "source": src,
        })

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "payload_generated_at": payload.get("generated_at"),
        "payload_audit_block": payload.get("source_audit"),
        **{k: out[k] for k in ("rows", "snapshot_rows", "verified", "no_snapshot", "flagged", "failed", "verdict")},
        "failures": out["failures"],
        "flags": out["flags"],
        "detail": rows,
    }
    json.dump(result, open(args.json_out, "w", encoding="utf-8"), indent=1)

    lines = [
        "# Line-by-line payload audit",
        "",
        f"_generated {result['generated_at']} · payload {result['payload_generated_at']}_",
        "",
        f"**{out['verdict']}** — {out['rows']} published rows · {out['verified']} independently re-matched to a",
        f"Leaguepedia MatchSchedule row ({out['snapshot_rows']} snapshot rows in `data/diag/ms_*.json`) ·",
        f"{out['flagged']} flagged for manual review · {out['no_snapshot']} in competitions with no snapshot ·",
        f"{out['failed']} arithmetic/source failures.",
        "",
        "| # | Fixture | Competition | Start (UTC) | Method | Pick | P | Re-matched | Source |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        mark = "yes" if r["re_matched_same_day"] else ("flagged" if r["flag"] else "no snapshot")
        lines.append(
            f"| {i} | [{r['teams']}]({r['match_url']}) | {r['competition']} | {r['start_utc']} | {r['method']} | "
            f"{r['pick']} | {round(r['pick_prob'], 4) if isinstance(r['pick_prob'], (int, float)) else ''} | "
            f"{mark} | [source]({r['source'] or r['leaguepedia_url'] or '#'}) |"
        )
    lines += ["", "## Failures (wrong data)", ""]
    lines += [f"- {p}" for p in out["failures"]] or ["None."]
    lines += ["", "## Flags for manual review (unverified, not wrong)", ""]
    for f in out["flags"]:
        extra = f" — snapshot has the pair on {f['snapshot_time']}" if f.get("snapshot_time") else ""
        lines.append(f"- `{f['id']}` {f['teams']} ({f['competition']}, {f['start_utc']}): "
                     f"{f['verdict']}{extra}. [Leaguepedia]({f.get('leaguepedia_url') or '#'})")
    if not out["flags"]:
        lines.append("None.")
    open(args.md_out, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print(f"rows={out['rows']} snapshot_rows={out['snapshot_rows']} re-matched={out['verified']} "
          f"flags={out['flagged']} no_snapshot={out['no_snapshot']} failures={out['failed']} "
          f"-> {out['verdict']}")
    if out["failed"]:
        print("\n".join(out["failures"][:20]))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
