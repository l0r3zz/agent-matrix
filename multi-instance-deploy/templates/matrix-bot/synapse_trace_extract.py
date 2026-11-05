#!/usr/bin/env python3
"""
synapse_trace_extract.py — Extract pipeline timing points from Synapse logs
===========================================================================
Reads raw Synapse (matrix.v-site.net gateway) log text on stdin or from files
and emits JSONL trace records compatible with matrix-bot trace.jsonl, so
trace_report.py can render the full Element<->agent journey.

Stages extracted:

  synapse_client_send  Element client's PUT .../rooms/!ROOM/send/m.room.message
                       completed (access log). start_ts = ts - proc time
                       approximates request arrival; origin_server_ts of the
                       created event falls inside [start_ts, ts].

  synapse_fed_send     OUTBOUND federation transmit completed
                       (synapse.http.matrixfederationclient "{PUT-O-n}
                       [dest] Completed request ... in X secs"). Carries dest
                       server + flight duration. This is the gateway pushing
                       the user's event to the agent's conduwuite.

  synapse_fed_recv     INBOUND federation transaction carrying >=1 PDU
                       (synapse.federation.transport.server "Received txn ...
                       (PDUs: n, EDUs: m)" with n>0). This is the agent's
                       conduwuite delivering the reply back to the gateway.
                       EDU-only txns (typing/presence) are ignored.

  synapse_pdu          "handling received PDU in room ... event_id=$..." line.
                       Carries the reply's exact event_id for correlation.

Correlation notes: Synapse access lines carry no event_id. client_send is
matched by room+window; fed_recv by time window; synapse_pdu carries the true
event_id. Reliable at lab traffic levels, ambiguous under bursts.

Usage:
  ssh g2s 'kubectl logs -n matrix deploy/matrix-synapse -c matrix --since=30m' \
      | python3 synapse_trace_extract.py > synapse_trace.jsonl

  python3 trace_report.py trace.jsonl --synapse synapse_trace.jsonl
"""

import json
import re
import sys
from datetime import datetime, timezone
from urllib.parse import unquote

# Access log: 2026-10-31 00:39:33,337 - synapse.access.http.8008 - 641 - INFO - PUT-235972 - 10.200.0.27 - 8008 - {agent0-1-mhs...} Processed request: 0.069sec/... "PUT /_matrix/... HTTP/1.1" ...
ACCESS_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}),(\d{3}) - synapse\.access\.http\.\d+ - "
    r"\d+ - INFO - (PUT|POST)-(\d+) - ([\d.]+) - \d+ - \{([^}]*)\} "
    r"Processed request: ([\d.]+)sec.*?\"(?:PUT|POST) (\S+) HTTP"
)

CLIENT_SEND_RE = re.compile(r"/_matrix/client/(?:v3|r0)/rooms/([^/]+)/send/m\.room\.message")

# Outbound federation: ... synapse.http.matrixfederationclient - 371 - INFO - federation_transaction_transmission_loop-13718 - {PUT-O-22055} [agent0-1-mhs.cybertribe.com] Completed request: 200 OK in 0.23 secs, got 60 bytes - PUT matrix-federation://agent0-1-mhs.cybertribe.com/_matrix/federation/v1/send/1792411332049
FED_SEND_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}),(\d{3}) - synapse\.http\.matrixfederationclient - "
    r"\d+ - INFO - \S+ - \{(PUT-O-\d+)\} \[(\S+)\] Completed request: \d+ [A-Z]+ "
    r"in ([\d.]+) secs.*- PUT matrix-federation://\S+/_matrix/federation/v1/send/(\S+)"
)

# Inbound federation txn: ... synapse.federation.transport.server.federation - 110 - INFO - PUT-235972 - Received txn tRPqyckUfOYzVIdy--... from agent0-1-mhs.cybertribe.com. (PDUs: 1, EDUs: 0)
TXN_RECV_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}),(\d{3}) - synapse\.federation\.transport\.server\.federation - "
    r"\d+ - INFO - (PUT-\d+) - Received txn (\S+) from (\S+)\. "
    r"\(PDUs: (\d+), EDUs: (\d+)\)"
)

# PDU handling: ... synapse.federation.federation_server - 1292 - INFO - _process_incoming_pdus_in_room_inner-10 - handling received PDU in room !ROOM:server: <FrozenEventV3 event_id=$EVT, type=m.room.message, state_key=None, outlier=False>
PDU_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}),(\d{3}) - synapse\.federation\.federation_server - "
    r"\d+ - INFO - \S+ - handling received PDU in room (\S+): "
    r"<FrozenEvent\S+ event_id=(\S+?), type=(\S+?),"
)


def to_epoch_ms(date_s: str, time_s: str, ms_s: str) -> int:
    dt = datetime.strptime(f"{date_s} {time_s}", "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    return int(dt.timestamp() * 1000) + int(ms_s)


def extract(lines) -> list:
    out = []
    for line in lines:
        m = ACCESS_RE.search(line)
        if m:
            date_s, time_s, ms_s, method, req_n, src_ip, user, proc_s, path = m.groups()
            cm = CLIENT_SEND_RE.search(path)
            if cm:
                ts = to_epoch_ms(date_s, time_s, ms_s)
                proc_ms = int(float(proc_s) * 1000)
                out.append({
                    "ts": ts,
                    "stage": "synapse_client_send",
                    "req": f"{method}-{req_n}",
                    "src_ip": src_ip,
                    "user": user,
                    "room": unquote(cm.group(1)),
                    "proc_ms": proc_ms,
                    "start_ts": ts - proc_ms,
                })
            continue

        m = FED_SEND_RE.search(line)
        if m:
            date_s, time_s, ms_s, req, dest, secs, txn = m.groups()
            ts = to_epoch_ms(date_s, time_s, ms_s)
            dur_ms = int(float(secs) * 1000)
            out.append({
                "ts": ts,
                "stage": "synapse_fed_send",
                "req": req,
                "dest": dest,
                "txn": txn,
                "dur_ms": dur_ms,
                "start_ts": ts - dur_ms,
            })
            continue

        m = TXN_RECV_RE.search(line)
        if m:
            date_s, time_s, ms_s, req, txn, origin, pdus, edus = m.groups()
            if int(pdus) > 0:  # ignore EDU-only txns (typing/presence)
                out.append({
                    "ts": to_epoch_ms(date_s, time_s, ms_s),
                    "stage": "synapse_fed_recv",
                    "req": req,
                    "txn": txn,
                    "origin": origin,
                    "pdus": int(pdus),
                })
            continue

        m = PDU_RE.search(line)
        if m:
            date_s, time_s, ms_s, room, event_id, ev_type = m.groups()
            out.append({
                "ts": to_epoch_ms(date_s, time_s, ms_s),
                "stage": "synapse_pdu",
                "room": room,
                "pdu_event_id": event_id,
                "pdu_type": ev_type,
            })
    return out


def main() -> int:
    if len(sys.argv) > 1:
        lines = []
        for p in sys.argv[1:]:
            with open(p) as f:
                lines.extend(f)
    else:
        lines = sys.stdin
    for rec in extract(lines):
        print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
