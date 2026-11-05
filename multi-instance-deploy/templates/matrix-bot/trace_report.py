#!/usr/bin/env python3
"""
trace_report.py — Pipeline latency timeline analyzer for matrix-bot traces
=========================================================================
Reads the structured JSONL trace file written by matrix_bot.py (trace.jsonl)
and reconstructs a per-message timeline of each stage of the journey.

Bot-side stages (trace.jsonl):

    origin_server_ts   stamped by the sender's homeserver (Synapse gateway)
      |
      |  federation (8448) + conduwuite + /sync delivery
      v
    bot_received       matrix-bot on_message handler fired
      |
      |  trigger check / prefix strip / typing notice
      v
    a0_request_start   HTTP POST to Agent Zero /api_message
      |
      |  Agent Zero reasoning + LLM time
      v
    a0_request_done    bot received A0 response
      |
      |  markdown render + room_send
      v
    reply_sent         last chunk accepted by conduwuite

With --synapse synapse_trace.jsonl (from synapse_trace_extract.py) two more
gateway-side points are merged in:

    client PUT start (gateway)   Element's send request reached Synapse
    ... (bot stages) ...
    reply at gateway (fed recv)  reply transaction arrived back at Synapse

Usage:
    python3 trace_report.py [trace.jsonl] [--synapse synapse_trace.jsonl]
                            [--last N] [--stats]
"""

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

STAGE_ORDER = ["bot_received", "a0_request_start", "a0_request_done", "reply_sent"]

STAGE_LABELS = {
    "bot_received":     "bot received (sync)",
    "a0_request_start": "A0 request sent",
    "a0_request_done":  "A0 response received",
    "reply_sent":       "reply sent to room",
}

# Human-readable meaning of the gap *before* each stage
GAP_LABELS = {
    "bot_received":     "federation+sync (origin HS -> bot)",
    "a0_request_start": "bot processing",
    "a0_request_done":  "Agent Zero / LLM",
    "reply_sent":       "send path (conduwuite accept)",
}

# Match windows for synapse-side records
CLIENT_SEND_WINDOW_MS = 10000   # PUT completion within +/-10s of origin_server_ts
FED_RECV_AFTER_MS     = 500     # fed recv may complete slightly before reply_sent logs
FED_RECV_WINDOW_MS    = 15000   # ... and up to 15s after


def fmt_ts(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000)
    return dt.strftime("%H:%M:%S") + f".{ms % 1000:03d}"


def load_traces(path: Path) -> dict:
    """Group bot trace records by event_id, preserving insertion order."""
    events = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.setdefault(rec.get("event_id", "?"), []).append(rec)
    for recs in events.values():
        recs.sort(key=lambda r: r.get("ts", 0))
    return events


def load_synapse(path: Path) -> dict:
    """Load synapse-side records, split by stage."""
    recs = {"synapse_client_send": [], "synapse_fed_recv": [],
            "synapse_fed_send": [], "synapse_pdu": []}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("stage") in recs:
                recs[rec["stage"]].append(rec)
    return recs


def measure_event(recs: list, syn: dict | None, mhs: str | None = None):
    """Build the ordered timeline rows for one message.

    Returns (rows, total_ms) where rows = [(label, ts_ms, gap_ms, note), ...]
    and total_ms spans the widest known journey (client PUT -> last point).
    """
    by_stage = {r["stage"]: r for r in recs}
    recv = by_stage.get("bot_received")
    origin_ts = recv.get("origin_server_ts") if recv else None
    room = recv.get("room_id") if recv else None

    # --- match synapse-side points ---
    cs = fr = None
    if syn and origin_ts and room:
        cands = [
            r for r in syn["synapse_client_send"]
            if r.get("room") == room
            and r["start_ts"] - 2000 <= origin_ts <= r["ts"] + CLIENT_SEND_WINDOW_MS
        ]
        if cands:
            cs = min(cands, key=lambda r: abs(r["ts"] - origin_ts))
    if syn and "reply_sent" in by_stage:
        sent_ts = by_stage["reply_sent"]["ts"]
        cands = [
            r for r in syn["synapse_fed_recv"]
            if sent_ts - FED_RECV_AFTER_MS <= r["ts"] <= sent_ts + FED_RECV_WINDOW_MS
        ]
        if mhs:  # burst-safe: match the txn from THIS agent's homeserver
            exact = [r for r in cands if r.get("origin") == mhs]
            if exact:
                cands = exact
        if cands:
            fr = min(cands, key=lambda r: r["ts"])

    # --- build ordered rows ---
    rows = []
    prev = None
    if cs:
        rows.append(("client PUT start (gateway)", cs["start_ts"], None,
                     f"req={cs['req']} user={cs.get('user', '?')}"))
        prev = cs["start_ts"]
    if origin_ts:
        gap = origin_ts - prev if prev is not None else None
        note = "element->gateway transit+proc" if gap is not None else "origin HS clock"
        rows.append(("event created (origin_server_ts)", origin_ts, gap, note))
        prev = origin_ts
    # outbound federation transmit (gateway -> agent MHS), splits the fed+sync leg
    fs = None
    if syn and origin_ts and "bot_received" in by_stage:
        recv_ts = by_stage["bot_received"]["ts"]
        if mhs:  # burst-safe: match the txn destined to THIS agent's homeserver
            exact = [
                r for r in syn["synapse_fed_send"]
                if r.get("dest") == mhs
                and origin_ts - 2000 <= r["start_ts"] <= recv_ts + 5000
            ]
            if exact:
                fs = min(exact, key=lambda r: r["start_ts"])
        if fs is None:
            cands = [
                r for r in syn["synapse_fed_send"]
                if r["start_ts"] >= origin_ts - 2000 and r["ts"] <= recv_ts + 3000
            ]
            if cands:
                fs = min(cands, key=lambda r: abs(r["ts"] - recv_ts))
    if fs:
        rows.append(("federation transmit (gw->MHS)", fs["start_ts"],
                     fs["start_ts"] - prev if prev is not None else None,
                     f"synapse fed queue ->{fs['dest']} [flight {fs['dur_ms']}ms]"))
        prev = fs["start_ts"]
    for stage in STAGE_ORDER:
        r = by_stage.get(stage)
        if not r:
            continue
        gap = r["ts"] - prev if prev is not None else None
        note = GAP_LABELS[stage]
        if stage == "a0_request_done" and "a0_latency_ms" in r:
            note += f"  [reply_len={r.get('reply_len', '?')}]"
        if stage == "reply_sent":
            note += "  [built-in, no LLM]" if r.get("builtin") \
                else f"  [{r.get('chunks', '?')} chunk(s)]"
        rows.append((STAGE_LABELS[stage], r["ts"], gap, note))
        prev = r["ts"]
    if fr:
        note = f"conduwuite->synapse federation from={fr.get('origin', '?')}"
        if syn and room:
            pdus = [p for p in syn["synapse_pdu"]
                    if p.get("room") == room and abs(p["ts"] - fr["ts"]) <= 2000]
            if pdus:
                nearest = min(pdus, key=lambda p: abs(p["ts"] - fr["ts"]))
                note += f" [reply_event={nearest['pdu_event_id']}]"
        rows.append(("reply at gateway (fed recv)", fr["ts"],
                     fr["ts"] - prev if prev is not None else None, note))
        prev = fr["ts"]

    start = cs["start_ts"] if cs else origin_ts
    total = (prev - start) if (prev is not None and start) else None
    return rows, total


def render_event(event_id: str, recs: list, syn: dict | None, mhs: str | None = None) -> None:
    recv = next((r for r in recs if r["stage"] == "bot_received"), {})
    print(f"\n=== {event_id} ===")
    if recv:
        print(f"  sender: {recv.get('sender', '?')}   room: {recv.get('room_id', '?')}")

    rows, total = measure_event(recs, syn, mhs)
    for label, ts, gap, note in rows:
        gap_s = f"+{gap:>6} ms  {note}" if gap is not None else f" {note}"
        print(f"  {label:<30}: {fmt_ts(ts)}  {gap_s}")
    if total is not None:
        print(f"  {'TOTAL':<30}: {total:>6} ms")


def render_stats(events: dict, syn: dict | None, mhs: str | None = None) -> None:
    gaps = {}
    totals = []
    for recs in events.values():
        rows, total = measure_event(recs, syn, mhs)
        for label, _ts, gap, _note in rows:
            if gap is not None:
                gaps.setdefault(label, []).append(gap)
        if total is not None:
            totals.append(total)

    def pct(vals, p):
        vals = sorted(vals)
        k = max(0, min(len(vals) - 1, int(round((p / 100) * (len(vals) - 1)))))
        return vals[k]

    print("\n=== Aggregate stage latencies (ms) ===")
    print(f"  {'stage':<34}{'n':>5}{'p50':>8}{'p95':>8}{'max':>8}")
    for label in ["event created (origin_server_ts)", "federation transmit (gw->MHS)"] + [STAGE_LABELS[s] for s in STAGE_ORDER] + ["reply at gateway (fed recv)"]:
        vals = gaps.get(label)
        if not vals:
            continue
        print(f"  {label:<34}{len(vals):>5}"
              f"{int(statistics.median(vals)):>8}{pct(vals, 95):>8}{max(vals):>8}")
    if totals:
        print(f"  {'TOTAL':<34}{len(totals):>5}"
              f"{int(statistics.median(totals)):>8}{pct(totals, 95):>8}{max(totals):>8}")
    print("\n  NOTE: origin_server_ts and synapse log times use the gateway clock (UTC);")
    print("        bot stages use the instance host clock. Cross-host deltas include")
    print("        clock skew -- keep NTP/chrony tight on all hosts.")
    print("        Synapse-side matching is by room+time window (no event_id in access")
    print("        logs) -- reliable at lab traffic levels, ambiguous under bursts.")


def main() -> int:
    ap = argparse.ArgumentParser(description="matrix-bot pipeline trace analyzer")
    ap.add_argument("tracefile", nargs="?", default="trace.jsonl")
    ap.add_argument("--synapse", metavar="FILE",
                    help="synapse_trace_extract.py JSONL output to merge in")
    ap.add_argument("--mhs", metavar="SERVER",
                    help="this agent's homeserver (e.g. agent0-1-mhs.cybertribe.com) "
                         "for burst-safe federation txn matching")
    ap.add_argument("--last", type=int, default=20, help="show last N events (default 20)")
    ap.add_argument("--stats", action="store_true", help="print aggregate stats only")
    args = ap.parse_args()

    path = Path(args.tracefile)
    if not path.exists():
        print(f"trace file not found: {path}", file=sys.stderr)
        return 1

    syn = None
    if args.synapse:
        spath = Path(args.synapse)
        if not spath.exists():
            print(f"synapse trace file not found: {spath}", file=sys.stderr)
            return 1
        syn = load_synapse(spath)
        print(f"[synapse merge: {len(syn['synapse_client_send'])} client sends, "
              f"{len(syn['synapse_fed_recv'])} federation receives]")

    events = load_traces(path)
    if not events:
        print("no trace records found")
        return 0

    if not args.stats:
        items = list(events.items())[-args.last:]
        for event_id, recs in items:
            render_event(event_id, recs, syn, args.mhs)

    render_stats(events, syn, args.mhs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
