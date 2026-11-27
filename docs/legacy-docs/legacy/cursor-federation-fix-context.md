# Cursor Context: Federation Fix & Tarnover Cleanup
# Date: 2026-03-06
# Purpose: Update golden docs with federation root cause analysis and routing lessons
# Author: Agent0-1 (on g2s)

---

## 1. What Happened

After migrating agent0-1 from tarnover to g2s, federation from Synapse (matrix.v-site.net)
to agent0-1-mhs failed with `ResponseNeverReceived` and `tls: bad record MAC` errors.
Agent0-2 and agent0-3 federation worked perfectly. After an extensive debugging session
(~3 hours), TWO routing issues were identified and resolved.

---

## 2. Root Cause Analysis

### Root Cause #1 — DD-WRT Stale Routes (kama router, 172.23.1.1)

**Problem:** The DD-WRT startup script still routed agent0-1 traffic to tarnover:
```
ip route add 172.23.88.1/32 via 172.23.0.103   # agent0-1 → tarnover (WRONG)
ip route add 172.23.89.1/32 via 172.23.0.103   # agent0-1-mhs → tarnover (WRONG)
```

**Fix:** Updated to point to g2s:
```
ip route add 172.23.88.1/32 via 172.23.100.121  # agent0-1 → g2s (CORRECT)
ip route add 172.23.89.1/32 via 172.23.100.121  # agent0-1-mhs → g2s (CORRECT)
```

**Location:** DD-WRT (kama) → Administration → Commands → Startup

### Root Cause #2 — g2s Missing mac0 Route for .89.x Subnet

**Problem:** g2s had `172.23.88.0/24 dev mac0 scope link` for agent containers
but was MISSING `172.23.89.0/24 dev mac0 scope link` for homeserver containers.
VPN traffic arrived at g2s but matched `172.23.0.0/16 dev eno1` instead of going
through mac0, so it couldn't reach the macvlan Dendrite containers.

**Fix:** `ip route add 172.23.89.0/24 dev mac0 scope link`

**Note:** The `agent-bridge.service` on g2s already had this route in its ExecStart,
but the service hadn't been reloaded after being updated. The route was added manually
and will persist via the service on next reboot.

---

## 3. Why Local Tests Passed But VPN Federation Failed

| Traffic Source | Path | Uses DD-WRT? | Uses g2s mac0 route? | Result |
|---|---|---|---|---|
| g2s `curl --interface mac0` | Local bridge → container | No | No (direct) | ✅ Works |
| LAN laptop browser | ARP → macvlan MAC directly | No | No | ✅ Works |
| Synapse via VPN tunnel | VPN → DD-WRT → g2s → mac0 → container | **Yes** | **Yes** | ❌ Failed |

Macvlan containers appear as real hosts on the LAN with their own MAC addresses.
Local network devices reach them directly via ARP (Layer 2). Only traffic that
crosses a router (like VPN traffic) needs Layer 3 routing.

---

## 4. Red Herrings During Debugging

The following were investigated but were NOT the cause:
- TLS certificate content, chain, or bundling
- Key/cert mismatch (pubkeys matched)
- EC curve type (both prime256v1)
- File corruption during SCP (sizes matched exactly)
- Docker volume mount caching
- Element client caching
- Synapse destination backoff (symptom, not cause)
- Dendrite --https-bind-address flag
- dendrite.yaml TLS paths

**Key lesson:** `bad record MAC` was caused by VPN traffic hitting tarnover's
old/dead TLS endpoint, not by any certificate issue on g2s.

---

## 5. Tarnover Cleanup Completed

After migration, the following orphaned infrastructure was removed from tarnover:
- ✅ mac0 bridge interface removed (`ip link del mac0`)
- ✅ macvlan routes removed (.88.0/24 and .89.0/24 via mac0)
- ✅ Promiscuous mode disabled on enp36s0
- ✅ No agent0 Docker containers were running
- ⬜ /opt/agent-zero/usr/ directory remains (can be archived/removed)

Tarnover retains its roles: Step-CA, kubectl, general administration.

---

## 6. Fleet Status (Verified 2026-03-06)

| Instance | Host | Agent IP | MHS IP | Matrix ID | Federation | Status |
|---|---|---|---|---|---|---|
| agent0-1 | g2s | 172.23.88.1 | 172.23.89.1 | @agent0-1:agent0-1-mhs.cybertribe.com | ✅ Verified | Sovereign |
| agent0-2 | g2s | 172.23.88.2 | 172.23.89.2 | @agent0-2:agent0-2-mhs.cybertribe.com | ✅ Verified | Sovereign |
| agent0-3 | g2s | 172.23.88.3 | 172.23.89.3 | @agent0-3:agent0-3-mhs.cybertribe.com | ✅ Verified | Sovereign |
| agent0-4 | g2s | 172.23.88.4 | 172.23.89.4 | — | Pre-wired | Available |
| agent0-5 | g2s | 172.23.88.5 | 172.23.89.5 | — | Pre-wired | Available |

---

## 7. New Gotcha #14 — Migration Routing Checklist

When migrating an agent instance between hosts, update ALL THREE routing layers:

1. **DD-WRT /32 routes** — Update `kama` startup script to point agent IPs to new host
2. **Destination host mac0 routes** — Verify BOTH .88.0/24 and .89.0/24 are routed via mac0
3. **Source host cleanup** — Remove mac0 bridge, routes, and promiscuous mode from old host

Verify with end-to-end test from VPN sidecar:
```bash
kubectl exec -n matrix <synapse-pod> -c openvpn -- \
  wget -O- --timeout=5 --no-check-certificate \
  https://<agent-mhs-hostname>:8448/_matrix/key/v2/server 2>&1
```

---

## 8. DD-WRT Startup Script (Current Correct State)

```bash
# Container host routes — all agents on g2s (172.23.100.121)
ip route add 172.23.88.1/32 via 172.23.100.121 # agent0-1 (g2s)
ip route add 172.23.89.1/32 via 172.23.100.121 # agent0-1-mhs (g2s)
ip route add 172.23.88.2/32 via 172.23.100.121 # agent0-2 (g2s)
ip route add 172.23.89.2/32 via 172.23.100.121 # agent0-2-mhs (g2s)
ip route add 172.23.88.3/32 via 172.23.100.121 # agent0-3 (g2s)
ip route add 172.23.89.3/32 via 172.23.100.121 # agent0-3-mhs (g2s)
# Add new lines here as new containers are deployed
```

---

## 9. g2s agent-bridge.service (Current Correct State)

```ini
[Unit]
Description=Agent-Matrix Host Bridge (mac0)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/bash -c "\
  ip link set eno1 promisc on && \
  ip link add mac0 link eno1 type macvlan mode bridge || true && \
  ip addr add 172.23.88.254/32 dev mac0 || true && \
  ip link set mac0 up && \
  ip route add 172.23.88.0/24 dev mac0 || true && \
  ip route add 172.23.89.0/24 dev mac0 || true"

[Install]
WantedBy=multi-user.target
```

---

## 10. Documents Requiring Updates

| Document | What to Update |
|---|---|
| **multi-instance-guide.md** | Add Section: "Migration Routing Checklist" (Gotcha #14); Add networking traffic path diagram; Update DD-WRT script reference |
| **Migration.md** | Add mandatory step: update DD-WRT /32 routes; Add step: verify mac0 routes on destination host; Add VPN end-to-end verification test |
| **operations-manual.md** | Update fleet status table; Add tarnover role change (no longer hosts agents); Add DD-WRT route management section |
| **theory-of-operations.md** | Add section on macvlan traffic paths (local ARP vs routed VPN); Document why local tests can pass while VPN fails |
| **agent-matrix-design.md** | Update tarnover description to "Step-CA + kubectl only"; Confirm all agents on g2s |

---

## 11. Interesting Discovery: Agent0-2 Certificate CN

During debugging, we discovered agent0-2's TLS certificate has:
```
subject=CN = agent0-N-mhs.cybertribe.com
```
This is the UNSUBSTITUTED template placeholder. Despite this, federation works because
Synapse validates against the Step-CA root CA via `federation_custom_ca_list` and the
hostname check likely uses SANs. This should be fixed by regenerating agent0-2's cert
with the correct CN, but is non-blocking.

