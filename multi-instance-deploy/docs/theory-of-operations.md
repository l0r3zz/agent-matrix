# Agent-Matrix Theory of Operations

**Version:** 2.0
**Date:** March 2026
**Audience:** SREs, developers implementing the Rust MCP server, deep troubleshooters
**Companion Documents:** [agent-matrix-design.md](agent-matrix-design.md) | [operations-manual.md](operations-manual.md)
**Note:** Updated for Continuwuity v0.5.6 migration (replacing Dendrite v0.15.2)

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Network Deep Dive](#2-network-deep-dive)
3. [Kubernetes Cluster](#3-kubernetes-cluster)
4. [Certificate Management](#4-certificate-management)
5. [Homeserver (Continuwuity)](#5-homeserver-continuwuity)
6. [Agent Zero Container Internals](#6-agent-zero-container-internals)
7. [Federation Walkthrough](#7-federation-walkthrough)
8. [Troubleshooting Reference](#8-troubleshooting-reference)
9. [Current System State](#9-current-system-state)
10. [E2EE Roadmap](#10-e2ee-roadmap)
11. [Appendix A: Configuration File Reference](#appendix-a-configuration-file-reference)
12. [Appendix B: DD-WRT Startup and Firewall Scripts](#appendix-b-dd-wrt-startup-and-firewall-scripts)
13. [Appendix C: Diagnostic Command Cheat Sheet](#appendix-c-diagnostic-command-cheat-sheet)

---

## 1. System Architecture

### Detailed Topology

```
                              ┌──────────────────────────┐
                              │     INTERNET / PUBLIC    │
                              └────────────┬─────────────┘
                                           │ HTTPS :443
                              ┌────────────▼──────────────┐
                              │   Contabo K8s Cluster     │
                              │   MetalLB: 147.93.135.115 │
                              │   Traefik + cert-manager  │
                              │                           │
                              │  matrix namespace:        │
                              │  ┌──────────────────────┐ │
                              │  │ Synapse 1.147.1      │ │
                              │  │ server_name: v-site  │ │
                              │  │ .net                 │ │
                              │  │ + OpenVPN sidecar    │ │
                              │  └──────────┬───────────┘ │
                              │  ┌──────────────────────┐ │
                              │  │ Element Web          │ │
                              │  └──────────────────────┘ │
                              │  ┌──────────────────────┐ │
                              │  │ PostgreSQL           │ │
                              │  └──────────────────────┘ │
                              └────────────┬──────────────┘
                                           │ OpenVPN tunnel
                                           │ 172.23.200.2 ↔ 172.23.200.1
                              ┌────────────▼──────────────┐
                              │  kama (DD-WRT v3)         │
                              │  172.23.1.1               │
                              │  tun2: 172.23.200.1       │
                              │  DHCP + DNS (dnsmasq)     │
                              │  OpenVPN server           │
                              │  Per-container /32 routes │
                              │  step-ca PKI              │
                              └──┬───────────────────┬────┘
                                 │ LAN 172.23.0.0/16 │
                                 │                   │
       ┌─────────────────────────▼──┐  ┌─────────────▼─────────────────┐
       │ tarnover (172.23.0.103)    │  │ g2s (172.23.100.121)          │
       │ step-ca server (:9000)     │  │ Docker rootful (ALL AGENTS)  │
       │ admin workstation          │  │ NIC: eno1, mac0: 172.23.88.254│
       └────────────────────────────┘  │                               │
                                        │ macvlan-172-23 (3 containers │
                                        │ per Continuwuity instance):  │
                                        │                              │
                                        │ agent0-1  172.23.88.1        │
                                        │  agent0-1-continuwuity       │
                                        │    (bridge-local only)       │
                                        │  agent0-1-mhs  172.23.89.1  │
                                        │    (Caddy TLS proxy)         │
                                        │                              │
                                        │ agent0-2  172.23.88.2        │
                                        │  agent0-2-mhs  172.23.89.2  │
                                        │    (Dendrite, pending migr.) │
                                        │                              │
                                        │ agent0-3  172.23.88.3        │
                                        │  agent0-3-mhs  172.23.89.3  │
                                        │    (Dendrite, pending migr.) │
                                        │                              │
                                        │ agent0-4  172.23.88.4        │
                                        │  agent0-4-continuwuity       │
                                        │    (bridge-local only)       │
                                        │  agent0-4-mhs  172.23.89.4  │
                                        │    (Caddy TLS proxy)         │
                                        └──────────────────────────────┘
```

### Host Inventory

| Host | IP | Role | OS | Notes |
|------|----|------|-----|-------|
| kama (DD-WRT) | 172.23.1.1 | Gateway, DHCP, DNS, VPN server | DD-WRT v3 | tun2: 172.23.200.1 |
| tarnover | 172.23.0.103 | step-ca, admin workstation | Pop!_OS, kernel 6.17.9 | No agent containers |
| g2s | 172.23.100.121 | Docker host (all agents) | Pop!_OS 22.04 | NIC: eno1, 128GB RAM |
| agent0-1 | 172.23.88.1 | Agent Zero container #1 | Docker on g2s (agent0ai/agent-zero) | MAC 02:42:AC:17:58:01 |
| agent0-1-continuwuity | — (bridge-local) | Continuwuity homeserver #1 | Docker on g2s (continuwuity:latest) | No macvlan IP |
| agent0-1-mhs | 172.23.89.1 | Caddy TLS proxy #1 | Docker on g2s (caddy:2-alpine) | MAC 02:42:AC:17:59:01 |
| agent0-2 | 172.23.88.2 | Agent Zero container #2 | Docker (agent0ai/agent-zero) | MAC 02:42:AC:17:58:02 |
| agent0-2-mhs | 172.23.89.2 | Dendrite homeserver #2 | Docker (dendrite-monolith:v0.15.2) | MAC 02:42:AC:17:59:02; pending migration |
| agent0-3 | 172.23.88.3 | Agent Zero container #3 | Docker (agent0ai/agent-zero) | MAC 02:42:AC:17:58:03 |
| agent0-3-mhs | 172.23.89.3 | Dendrite homeserver #3 | Docker (dendrite-monolith:v0.15.2) | MAC 02:42:AC:17:59:03; pending migration |
| agent0-4 | 172.23.88.4 | Agent Zero container #4 | Docker on g2s (agent0ai/agent-zero) | MAC 02:42:AC:17:58:04 |
| agent0-4-continuwuity | — (bridge-local) | Continuwuity homeserver #4 | Docker on g2s (continuwuity:latest) | No macvlan IP |
| agent0-4-mhs | 172.23.89.4 | Caddy TLS proxy #4 | Docker on g2s (caddy:2-alpine) | MAC 02:42:AC:17:59:04 |
| mac0 (per host) | 172.23.88.254 | macvlan bridge interface | Virtual | Same IP on all hosts |
| step-ca | 172.23.0.103:9000 | Certificate authority | step-ca on tarnover | CyberTribe CA |
| k8-0 | 144.126.131.105 | K8s control-plane | Ubuntu 24.04 | Contabo |
| k8-1 | 207.244.225.169 | K8s worker | Ubuntu 24.04 | Contabo |
| k8-2 | 207.244.237.219 | K8s worker | Ubuntu 24.04 | Contabo |

### Network Segments

| Segment | CIDR | Purpose |
|---------|------|---------|
| Home LAN | 172.23.0.0/16 | All lab hosts and containers |
| Agent containers | 172.23.88.0/24 | Agent Zero instances |
| Homeserver containers | 172.23.89.0/24 | Caddy TLS proxy instances (Continuwuity on bridge-local) |
| VPN tunnel | 172.23.200.0/24 | Contabo ↔ home lab |
| K8s pod CIDR (k8-0) | 10.200.0.0/24 | Pods on control-plane |
| K8s pod CIDR (k8-1) | 10.200.1.0/24 | Pods on worker 1 |
| K8s pod CIDR (k8-2) | 10.200.2.0/24 | Pods on worker 2 |
| K8s service CIDR | 10.96.0.0/12 | Cluster services |

---

## 2. Network Deep Dive

### 2.1 Docker macvlan Networking

Docker's macvlan driver assigns each container its own MAC address, making it appear as a physical device on the LAN. This avoids port-mapping conflicts when running multiple agents.

**macvlan creation** (one-time per Docker host):
```bash
docker network create --driver macvlan \
  --subnet=172.23.0.0/16 \
  --gateway=172.23.1.1 \
  -o parent=<NIC> \
  macvlan-172-23
```

**Critical requirement:** Docker must run in **rootful** mode. Rootless Docker operates in a user namespace with `slirp4netns`/`pasta` and cannot see host interfaces. The error message `invalid subinterface vlan name` is misleading — the real issue is namespace isolation.

**Dual-network design:** Each agent container connects to two Docker networks:

| Network | Type | Purpose |
|---------|------|---------|
| `macvlan-172-23` | macvlan | LAN-routable IP, federation, inter-host communication |
| `bridge-local` | bridge | localhost port-mapping for host access (Web UI, SSH) |

### 2.2 mac0 Bridge (Host-to-Container Access)

Linux kernel macvlan blocks traffic between a host and its own macvlan containers. The `mac0` bridge interface creates a virtual endpoint into the container subnet:

```bash
ip link add mac0 link <NIC> type macvlan mode bridge
ip addr add 172.23.88.254/32 dev mac0
ip link set mac0 up
ip route add 172.23.88.0/24 dev mac0
ip route add 172.23.89.0/24 dev mac0
```

This is persisted via a systemd service (`mac0-macvlan.service`) on each Docker host. The IP `172.23.88.254` is the same on all hosts (it's a host-local interface, not LAN-routable).

Promiscuous mode must be enabled on the host NIC for macvlan to function: `ip link set <NIC> promisc on`.

### 2.3 Macvlan Traffic Paths: Local vs VPN

Traffic to container IPs (172.23.88.x, 172.23.89.x) can follow two different paths. Confusion between them is a common cause of "federation works from the host but fails from Synapse (VPN)."

| Origin | Path | Why it works or fails |
|--------|------|------------------------|
| **Local (same host)** | Host → mac0 (kernel route 172.23.88.0/24, 172.23.89.0/24 dev mac0) → container | Uses **host routing table only**. No DD-WRT, no VPN. `curl -I http://172.23.89.1:8008` and `ping -I mac0 172.23.89.1` succeed as long as mac0 and the routes exist. |
| **LAN (e.g. kama)** | Client → kama → kama's /32 route (e.g. 172.23.89.1 via g2s) → g2s NIC → mac0 → container | Requires **DD-WRT static routes** to send the packet to the correct Docker host. If the route still points to the old host (e.g. tarnover after migration), traffic never reaches the container. |
| **VPN (Synapse)** | Synapse pod → OpenVPN → kama (tun2) → kama's /32 route → g2s NIC → **mac0** → container | Same as LAN: **DD-WRT routes** must point to g2s. In addition, the **Docker host must have both** `172.23.88.0/24 dev mac0` and `172.23.89.0/24 dev mac0`. If only .88.0/24 exists (e.g. mac0 was set up for agents only), VPN-originated traffic to the Caddy proxy (.89.x) never reaches the container, so federation fails with timeouts or TLS errors while local tests pass. |

**Takeaway:** When federation fails from VPN but local curl/ping from g2s works, check (1) DD-WRT startup script: all agent and MHS /32 routes must point to the current Docker host (g2s); (2) on the Docker host: `ip route show | grep mac0` must include both .88.0/24 and .89.0/24.

### 2.4 DD-WRT Configuration (kama)

#### Static DHCP Leases

Each container gets a DHCP static lease mapping its MAC address to a hostname and IP. Configured via Services > Services > Static Leases in the DD-WRT GUI.

| MAC | Hostname | IP |
|-----|----------|----|
| 02:42:AC:17:58:01 | agent0-1 | 172.23.88.1 |
| 02:42:AC:17:59:01 | agent0-1-mhs | 172.23.89.1 |
| 02:42:AC:17:58:02 | agent0-2 | 172.23.88.2 |
| 02:42:AC:17:59:02 | agent0-2-mhs | 172.23.89.2 |
| 02:42:AC:17:58:03 | agent0-3 | 172.23.88.3 |
| 02:42:AC:17:59:03 | agent0-3-mhs | 172.23.89.3 |
| 02:42:AC:17:58:04 | agent0-4 | 172.23.88.4 |
| 02:42:AC:17:59:04 | agent0-4-mhs | 172.23.89.4 |

These leases also drive dnsmasq hostname resolution — `agent0-1-mhs.cybertribe.com` resolves to `172.23.89.1` for any LAN client using kama as DNS.

#### Per-Container /32 Routes

Each container pair gets two `/32` routes on kama pointing to the Docker host. This is more flexible than per-host /24 — containers on different hosts share the same address space.

```bash
ip route add 172.23.88.1/32 via 172.23.100.121  # agent0-1 (g2s)
ip route add 172.23.89.1/32 via 172.23.100.121  # agent0-1-mhs (g2s)
ip route add 172.23.88.2/32 via 172.23.100.121  # agent0-2 (g2s)
ip route add 172.23.89.2/32 via 172.23.100.121  # agent0-2-mhs via g2s
ip route add 172.23.88.3/32 via 172.23.100.121  # agent0-3 via g2s
ip route add 172.23.89.3/32 via 172.23.100.121  # agent0-3-mhs via g2s
ip route add 172.23.88.4/32 via 172.23.100.121  # agent0-4 via g2s
ip route add 172.23.89.4/32 via 172.23.100.121  # agent0-4-mhs via g2s
```

Saved via Administration > Commands > Save Startup.

#### DHCP Option 121 (VPN Route Push)

```
dhcp-option=br0,121,0.0.0.0/0,172.23.1.1,172.23.200.0/24,172.23.1.1
```

When DHCP Option 121 (Classless Static Routes) is present, most clients (especially `systemd-networkd`) **ignore Option 3** (default gateway). The default route `0.0.0.0/0` **must** be included in Option 121 or clients lose internet connectivity.

### 2.5 OpenVPN Tunnel (kama ↔ Contabo K8s)

The VPN connects the Contabo K8s cluster to the home lab, allowing Synapse to federate with agent homeserver instances on the private LAN.

| Parameter | Value |
|-----------|-------|
| Server | kama (port.nexsys.net:1194 UDP) |
| Server VPN IP | 172.23.200.1 (tun2) |
| Client | OpenVPN sidecar in Synapse pod |
| Client VPN IP | 172.23.200.x (tun0) |
| Tunnel cipher | AES-256-CBC |
| Auth | SHA256 |
| Route pushed | 172.23.0.0/16 via VPN gateway |

**Critical client-side config:** The Synapse sidecar uses `route-nopull` because DD-WRT pushes `redirect-gateway def1`, which would route ALL pod traffic through the VPN and break K8s networking. With `route-nopull`, only `172.23.0.0/16` goes through the tunnel.

#### LAN-to-VPN Routing

By default, LAN hosts cannot reach VPN clients (172.23.200.0/24) due to:

1. **OpenVPN raw table anti-spoof rule:** Auto-generated DROP for traffic to 172.23.200.0/24 from non-tun2 interfaces. Fixed with: `iptables -t raw -I PREROUTING -i br0 -d 172.23.200.0/24 -j ACCEPT`
2. **FORWARD chain:** Must explicitly allow br0↔tun2 traffic.
3. **On-link ARP issue:** LAN hosts with /16 route try ARP for 172.23.200.x. Fixed with DHCP Option 121 pushing a more-specific /24 route.

**DD-WRT GUI "Save Firewall" caveat:** Never use the GUI button for VPN-related iptables rules — it triggers a full firewall + OpenVPN restart that bounces the tunnel. Always use `nvram set rc_firewall` + `nvram commit` from CLI.

---

## 3. Kubernetes Cluster

### 3.1 Cluster Configuration

| Setting | Value |
|---------|-------|
| K8s version | v1.35.1 |
| Nodes | k8-0 (control-plane), k8-1, k8-2 (workers) |
| CNI | Cilium 1.19 (VXLAN tunnel mode) |
| kube-proxy | Running (alongside Cilium) |
| Container runtime | containerd 1.7.28 |
| Node OS | Ubuntu 24.04.4 LTS, kernel 6.8.0 |
| Load balancer | MetalLB (IP: 147.93.135.115) |
| Ingress | Traefik |

### 3.2 Synapse Deployment (matrix namespace)

| Component | Pod Node | Image/Chart |
|-----------|----------|-------------|
| Synapse + OpenVPN sidecar | k8-2 | Helm: matrix-2.9.14, Synapse 1.147.1 |
| Element Web | k8-1 | matrix-synapse-element |
| PostgreSQL | k8-1 | StatefulSet |

**Key Synapse settings:**
- `server_name: v-site.net` (user IDs: `@user:v-site.net`)
- `public_baseurl: https://matrix.v-site.net/`
- Config generated at startup: `/tmp/synapse.yaml` (merged from ConfigMap + PG creds). NOT `/data/homeserver.yaml`.
- Admin user registration: `register_new_matrix_user -c /tmp/synapse.yaml -u admin -p <pw> -a http://localhost:8008`
- Admin API not exposed publicly — use `kubectl port-forward svc/matrix-synapse 8008:80` + `synadm`

### 3.3 TLS and Ingress

cert-manager v1.19.3 with ClusterIssuer `letsencrypt-prod` (HTTP-01 solver via Traefik). Certificates auto-renew ~30 days before expiry.

**Current Ingress paths:**

| Path | PathType | Purpose |
|------|----------|---------|
| `/_matrix/client` | Prefix | Client-Server API |
| `/_matrix/federation` | Prefix | Federation API (for agent homeservers) |
| `/_matrix/key` | Prefix | Signing key exchange |
| `/_synapse/client` | Prefix | Synapse client endpoints |
| `/.well-known/matrix` | Prefix | Client/server discovery |
| `/health` | Exact | Health check |

`/_synapse/admin` is NOT exposed publicly.

### 3.4 Federation Delegation

**.well-known (primary):** Caddy on `v-site.net` (92.243.27.73) serves:
```
https://v-site.net/.well-known/matrix/server → {"m.server":"matrix.v-site.net:443"}
```

**SRV records (fallback):**
```
_matrix._tcp.v-site.net.      3600  IN  SRV  0 0 443 matrix.v-site.net.
_matrix-fed._tcp.v-site.net.  3600  IN  SRV  0 0 443 matrix.v-site.net.
```

`matrix.v-site.net` must be an A record (not CNAME — SRV targets pointing to CNAMEs violate RFC 2782).

### 3.5 OpenVPN Sidecar Pattern

The OpenVPN client runs as a sidecar container in the Synapse pod (Alpine 3.19, `NET_ADMIN` capability). It shares the pod's network namespace — when OpenVPN creates `tun0` and adds routes, they are visible to the Synapse container automatically.

The sidecar mounts the VPN config from K8s Secret `openvpn-client-config` at `/vpn/client.ovpn`.

### 3.6 Synapse Federation Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `federation_domain_whitelist` | `[agent0-1-mhs.cybertribe.com, agent0-2-mhs.cybertribe.com, agent0-3-mhs.cybertribe.com, agent0-4-mhs.cybertribe.com]` | Only federate with listed domains |
| `federation_custom_ca_list` | `/etc/synapse/certs/home-lab-ca.pem` | Trust step-ca for federation TLS |
| `federation_verify_certificates` | `true` | Enforce TLS verification |
| `ip_range_whitelist` | `172.23.0.0/16, 10.8.0.0/24` | Allow RFC 1918 addresses (blocked by default) |
| `allow_public_rooms_over_federation` | `false` | Don't share room directory |
| `allow_profile_lookup_over_federation` | `false` | Don't leak user profiles |

**hostAliases** in the Synapse pod spec provide DNS resolution for agent homeserver domains (which have no public DNS records):

```yaml
hostAliases:
  - ip: "172.23.89.1"
    hostnames: ["agent0-1-mhs.cybertribe.com"]
  - ip: "172.23.89.2"
    hostnames: ["agent0-2-mhs.cybertribe.com"]
  - ip: "172.23.89.3"
    hostnames: ["agent0-3-mhs.cybertribe.com"]
  - ip: "172.23.89.4"
    hostnames: ["agent0-4-mhs.cybertribe.com"]
```

This is the Phase 1 approach. Phase 2 will use CoreDNS conditional forwarding to kama.

### 3.7 Known K8s Issues

#### Cilium UFW Interaction

UFW's `deny (routed)` default drops VXLAN-decapsulated packets in the FORWARD chain. Additionally, UDP 8472 must be explicitly allowed in the INPUT chain — Cilium's nftables ACCEPT rule does NOT override iptables INPUT DROP (both chains evaluate independently).

**Required UFW rules on all K8s nodes:**
```bash
ufw default allow routed
ufw allow 8472/udp
ufw allow 4240/tcp
```

#### Cilium TCX Mode Bug (#44194)

Cilium 1.19 with TCX attachment mode has a bug where BPF programs on `cilium_vxlan` are NOT cleaned up when the agent pod terminates. New pods cannot replace them.

**Detection:** `bpftool net show` — stale programs have lower `prog_id` values than active ones.

**Workaround:** Detach stale links before restarting: `bpftool link detach id <id>`

**Permanent fix:** Set `bpf.enableTCX: false` in Cilium Helm values.

#### CoreDNS Placement

Both CoreDNS replicas run on k8-0 (control-plane). Add pod anti-affinity to spread across nodes.

---

## 4. Certificate Management

### 4.1 PKI Architecture

```
CyberTribe CA Root CA (step-ca)
  └─ CyberTribe CA Intermediate CA
       ├─ router.cybertribe.com (VPN server cert)
       ├─ contabo-synapse.cybertribe.com (VPN client cert, 1-year)
       ├─ agent0-1-mhs.cybertribe.com (Caddy TLS, 1-year)
       ├─ agent0-2-mhs.cybertribe.com (Dendrite TLS, 1-year; pending migration)
       ├─ agent0-3-mhs.cybertribe.com (Dendrite TLS, 1-year; pending migration)
       └─ agent0-4-mhs.cybertribe.com (Caddy TLS, 1-year)
```

step-ca runs on tarnover at `https://localhost:9000`. All agent containers run on g2s.

### 4.2 Certificate Lifecycle

**Issue a certificate:**
```bash
step ca certificate "agent0-N-mhs.cybertribe.com" \
  agent0-N-mhs.crt agent0-N-mhs.key \
  --ca-url https://localhost:9000 \
  --root /home/l0r3zz/cybertribe-ca/step-store/certs/root_ca.crt \
  --san agent0-N-mhs.cybertribe.com \
  --not-after=8760h
```

**Verify:**
```bash
step certificate inspect agent0-N-mhs.crt --short
step certificate verify agent0-N-mhs.crt \
  --roots /home/l0r3zz/cybertribe-ca/step-store/certs/root_ca.crt
```

### 4.3 CA Bundle for Synapse (federation_custom_ca_list)

The `home-lab-ca` K8s Secret must contain **root CA + intermediate CA** (not intermediate alone):

```bash
cat root_ca.crt intermediate_ca.crt > home-lab-ca-bundle.pem

kubectl create secret generic home-lab-ca -n matrix \
  --from-file=home-lab-ca.pem=home-lab-ca-bundle.pem \
  --dry-run=client -o yaml | kubectl apply -f -
```

**Why both are required:** Python's Twisted TLS library (used by Synapse) requires the root CA as a trust anchor. The homeserver (Continuwuity via Caddy, or legacy Dendrite) sends the leaf + intermediate in the TLS handshake; Synapse must have the root to complete the chain. With intermediate-only bundles, Synapse reports `certificate verify failed` even though `curl --cacert` succeeds (curl is more lenient about trust anchors).

### 4.4 Let's Encrypt for Synapse

cert-manager handles public TLS for `matrix.v-site.net` automatically via HTTP-01 challenges. The ClusterIssuer `letsencrypt-prod` creates and auto-renews certificates stored in Secret `matrix-synapse-tls`.

### 4.5 Common Certificate Pitfalls

| Problem | Symptom | Fix |
|---------|---------|-----|
| Intermediate-only CA bundle | `certificate verify failed` on Synapse federation | Include root CA in the bundle |
| Expired cert | Federation silently fails | Check with `step certificate inspect --short`; re-issue |
| Key/cert mismatch | OpenVPN: `Private key does not match the certificate` | Re-issue from the same `step ca certificate` invocation |
| step-ca "too many positional arguments" | CLI flag error on step-ca 0.28.x-0.29.x | Use only the three positional arguments; no `--san`, `--kty`, etc. |

---

## 5. Homeserver (Continuwuity)

Continuwuity v0.5.6 is a Rust-based Matrix homeserver (a fork of Conduit/Conduwuit). It replaces Dendrite v0.15.2 as the agent homeserver. Continuwuity uses an embedded RocksDB database and is configured entirely via environment variables. A Caddy TLS sidecar provides HTTPS termination for federation.

> **Migration status:** agent0-1 and agent0-4 run Continuwuity. agent0-2 and agent0-3 remain on Dendrite (pending migration).

### 5.1 Configuration Reference

Continuwuity is configured via `CONTINUWUITY_` prefixed environment variables in `docker-compose.yml`. There is **no YAML configuration file** — this replaces the legacy `dendrite.yaml`.

**Key environment variables:**

| Variable | Example Value | Purpose |
|----------|---------------|---------|
| `CONTINUWUITY_SERVER_NAME` | `agent0-N-mhs.cybertribe.com` | Matrix server name (appears in user IDs) |
| `CONTINUWUITY_DATABASE_PATH` | `/var/lib/continuwuity` | RocksDB data directory |
| `CONTINUWUITY_PORT` | `6167` | Native listen port (HTTP only) |
| `CONTINUWUITY_ADDRESS` | `0.0.0.0` | Bind address |
| `CONTINUWUITY_REGISTRATION_TOKEN` | `<unique-per-instance>` | Token for REST API registration |
| `CONTINUWUITY_ALLOW_REGISTRATION` | `true` | Enable token-based registration |
| `CONTINUWUITY_ALLOW_FEDERATION` | `true` | Enable federation |
| `CONTINUWUITY_ALLOW_CHECK_FOR_UPDATES` | `false` | Disable update checks |
| `CONTINUWUITY_LOG` | `warn,state_res=warn` | Log level |
| `CONTINUWUITY_TRUSTED_SERVERS` | `["v-site.net"]` | Trusted servers for key fetching |
| `CONTINUWUITY_IP_RANGE_DENYLIST` | `[]` | Clear default RFC 1918 deny (required for private LAN federation) |

**Storage:** RocksDB embedded database stored as a single directory at the `CONTINUWUITY_DATABASE_PATH` mount point. On the host this maps to `./mhs/continuwuity-data/`. This replaces the multiple SQLite `.db` files used by Dendrite.

**Signing keys:** Continuwuity auto-generates its signing keys on first startup. No manual `matrix_key.pem` generation is required (unlike Dendrite).

### 5.2 Ports

| Port | Protocol | Container | Purpose |
|------|----------|----------|---------|
| 6167 | HTTP | agent0-N-continuwuity | Continuwuity native port (bridge-local only, not LAN-routable) |
| 8008 | HTTP | agent0-N-mhs (Caddy) | Client-Server API (reverse proxy to 6167) |
| 8448 | HTTPS | agent0-N-mhs (Caddy) | Federation API (TLS termination + reverse proxy to 6167) |

### 5.3 Caddy TLS Sidecar

Caddy holds the macvlan IP (172.23.89.N) and provides the network-facing endpoints. The Continuwuity container has no macvlan IP — it is reachable only on the `bridge-local` Docker network.

**Caddyfile** (located at `mhs/Caddyfile`):
```
:8008 {
    reverse_proxy agent0-N-continuwuity:6167
}

:8448 {
    tls /etc/caddy/server.crt /etc/caddy/server.key
    reverse_proxy agent0-N-continuwuity:6167
}
```

**TLS certificates:** Caddy uses the same step-ca issued certificates (`server.crt`, `server.key`) that were previously mounted directly into Dendrite. The certificate CN/SAN is `agent0-N-mhs.cybertribe.com`.

**Traffic flow:**
- **Client API:** Client → Caddy :8008 (HTTP) → Continuwuity :6167
- **Federation:** Remote server → Caddy :8448 (TLS) → Continuwuity :6167

This replaces Dendrite's built-in TLS via the `--https-bind-address :8448` command flag.

### 5.4 Registration

Continuwuity does not have a `create-account` binary. Account registration uses the standard Matrix REST API with a registration token.

**Register a new account:**
```bash
curl -s -X POST http://172.23.89.N:8008/_matrix/client/v3/register \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "agent0-N",
    "password": "<password>",
    "auth": {
      "type": "m.login.registration_token",
      "token": "<CONTINUWUITY_REGISTRATION_TOKEN>"
    }
  }'
```

The response includes `user_id`, `access_token`, and `device_id`.

**Retrieve registration token from compose:**
```bash
grep CONTINUWUITY_REGISTRATION_TOKEN /opt/agent-zero/agent0-N/docker-compose.yml
```

**Login to obtain access token:**
```bash
curl -s -X POST http://172.23.89.N:8008/_matrix/client/v3/login \
  -H 'Content-Type: application/json' \
  -d '{"type":"m.login.password","identifier":{"type":"m.id.user","user":"<user>"},"password":"<pw>","device_id":"AgentZeroBot"}'
```

### 5.5 Instance Configuration (all on g2s)

All Continuwuity-based agents run on g2s with the following pattern:

| Setting | Value |
|---------|--------|
| Host | g2s (172.23.100.121) |
| TLS | Via Caddy sidecar on port 8448 (not `--https-bind-address`) |
| Data path | `./mhs/continuwuity-data:/var/lib/continuwuity` (RocksDB) |
| Homeserver image | ghcr.io/continuwuity/continuwuity:latest |
| Proxy image | caddy:2-alpine |
| Compose | 3 containers per instance (agent + continuwuity + caddy) |

> **Legacy note:** agent0-2 and agent0-3 still use the Dendrite 2-container pattern pending migration. See the [continuwuity-migration.md](continuwuity-migration.md) guide.

---

## 6. Agent Zero Container Internals

### 6.1 Startup Sequence

The container's `command:` override in docker-compose launches startup-services.sh alongside supervisord. Note: supervisord manages the core Agent Zero web app; the Matrix bridge components (matrix-bot and matrix-mcp-server) are managed by the startup script:

```
command: /bin/bash -c '/a0/usr/workdir/startup-services.sh & exec /usr/bin/python3 /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf'
```

**Boot phases in startup-services.sh:**

| Phase | Action | Detail |
|-------|--------|--------|
| 1 | Start MCP server | Must listen on port 3000 before Agent Zero preloads MCP tools |
| 2 | Wait for Agent Zero API | Polls http://localhost:80 every 2s for up to 60s |
| 2.5 | Run startup-patch.sh | Computes deterministic API token, injects into bot .env |
| 3 | Install pip dependencies | matrix-nio, markdown, aiohttp (wiped on each container restart) |
| 4 | Start matrix-bot | Launches matrix_bot.py after API confirmed live |

### 6.2 API Token Flow

Agent Zero computes an internal `mcp_server_token` at runtime. The matrix-bot must use this exact token to authenticate to Agent Zero's `/api_message` endpoint.

**Token algorithm:**
```
mcp_server_token = Base64URL(SHA256(runtime_id + ":" + auth_login + ":" + auth_password))[:16]
```

Inputs:
- `A0_PERSISTENT_RUNTIME_ID` from `/a0/.env` (stable UUID, set once)
- `AUTH_LOGIN` from container environment
- `AUTH_PASSWORD` from container environment

**startup-patch.sh** (Phase 2.5) computes this token at boot and injects it into `/a0/usr/workdir/matrix-bot/.env` as `A0_API_KEY`. Without this, a container restart leaves the bot with a stale token, causing 401 errors.

### 6.3 matrix-bot (Python)

The reactive bridge component. Located at `/a0/usr/workdir/matrix-bot/`.

**How it works:**
1. Uses `matrix-nio` to maintain a persistent sync connection to the Caddy proxy (`http://agent0-N-mhs:8008`), which reverse-proxies to Continuwuity
2. Listens for `m.room.message` events in all joined rooms
3. Forwards incoming messages to Agent Zero's `/api_message` HTTP API with `A0_API_KEY` auth header
4. Posts Agent Zero's LLM response back to the Matrix room
5. Converts markdown responses to `org.matrix.custom.html` for proper rendering in Element
6. Prefixes forwarded messages with instructions telling Agent Zero to respond with plain text only (echo suppression — prevents the agent from re-invoking MCP Matrix tools)
7. Maintains `room_contexts.json` for conversation context across messages
8. Auto-joins rooms on invite

**Key files:**
| File | Path |
|------|------|
| Bot script | `/a0/usr/workdir/matrix-bot/matrix_bot.py` |
| Bot .env | `/a0/usr/workdir/matrix-bot/.env` |
| Bot log | `/a0/usr/workdir/matrix-bot/bot.log` |
| Room contexts | `/a0/usr/workdir/matrix-bot/room_contexts.json` |

### 6.4 matrix-mcp-server (Node.js)

The proactive bridge component. Located at `/a0/usr/workdir/matrix-mcp-server/`.

**How it works:**
1. Runs as an HTTP MCP server on port 3000
2. Exposes Matrix CS API operations as MCP tools
3. Credentials passed per-request via HTTP headers (`matrix_homeserver_url`, `matrix_user_id`, `matrix_access_token`)
4. Agent Zero invokes tools via HTTP to `http://localhost:3000/mcp`
5. Also supports env var fallback for credentials (`MATRIX_USER_ID`, `MATRIX_ACCESS_TOKEN`)

**MCP registration** in Agent Zero UI (Settings > MCP/A2A):
```json
{
  "mcpServers": {
    "matrix": {
      "description": "Matrix homeserver bridge for agent-to-agent and human-agent communication",
      "url": "http://localhost:3000/mcp",
      "type": "streamable-http"
    }
  }
}
```

> **⚠️ Note:** No headers are needed — the MCP server reads credentials from its own `.env` file. Using `"type": "http"` will fail with 405 Method Not Allowed.

### 6.5 Agent Profiles and .env Configuration

Profiles are set via `A0_SET_agent_profile` in the instance `.env`:

| Profile | `A0_SET_agent_profile` |
|---------|----------------------|
| Standard | `agent0` |
| Hacker | `hacker` |
| Developer | `developer` |
| Researcher | `researcher` |

Default models: `openrouter/google/gemini-2.0-flash-001` (chat), `openai/text-embedding-3-small` (embedding).

---


### 6.6 Email (SMTP) Capability

Agents can send outbound email via Gmail SMTP. Configuration is per-instance via the matrix-bot `.env` file:

| Variable | Value |
|----------|-------|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Gmail address |
| `SMTP_PASS` | 16-character App Password (NOT regular password) |
| `SMTP_FROM` | Gmail address |
| `FORCE_TLS` | `true` |

> **Requirement:** The Gmail account must have 2-Step Verification enabled. Regular passwords fail with `535 Username and Password not accepted`. App Passwords are generated at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

After updating `.env`, restart the bot:
```bash
kill $(pgrep -f matrix_bot.py) 2>/dev/null
cd /a0/usr/workdir/matrix-bot
/opt/venv-a0/bin/python3 matrix_bot.py &
```

## 7. Federation Walkthrough

### 7.1 End-to-End Message Flow (Human → Agent)

```
1. Human types message in Element (connected to matrix.v-site.net)
2. Element sends PUT to Synapse via Client-Server API
3. Synapse stores event in DAG, signs it
4. Synapse federates to Continuwuity (via Caddy):
   a. Looks up agent0-N-mhs.cybertribe.com via hostAliases → 172.23.89.N
   b. Sends via OpenVPN tunnel (tun0 → 172.23.200.1 → kama → /32 route → Docker host)
   c. TLS handshake with Caddy on port 8448 (step-ca cert)
   d. Caddy proxies to Continuwuity, which stores event
5. Continuwuity stores event, updates sync stream
6. matrix-bot (Python) receives event via sync response
7. matrix-bot POSTs to Agent Zero /api_message with A0_API_KEY header
8. Agent Zero processes with LLM, generates response
9. Agent Zero returns response to matrix-bot
10. matrix-bot sends response via Caddy proxy (http://172.23.89.N:8008 → Continuwuity)
11. Continuwuity federates response via Caddy TLS (reverse path through VPN)
12. Human sees response in Element
```

### 7.2 Room Creation and Invitation Flow

1. Agent creates room on Continuwuity via MCP `create-room` tool
2. Agent invites human via MCP `invite-user` tool with `@user:v-site.net`
3. Continuwuity sends invite to Synapse via Caddy (outbound federation, TLS via step-ca)
4. Synapse delivers invite to user's sync stream
5. Human sees invite in Element, clicks "Accept"
6. Synapse sends join request to Continuwuity via Caddy (inbound federation)
   - **This is where 502 errors occur if hostAliases are missing**
7. Continuwuity authorizes join, sends room state
8. Room is now federated — both servers maintain event DAG replicas

### 7.3 Synapse Whitelist and hostAliases

Every new agent homeserver requires two changes on the Synapse side:

1. **federation_domain_whitelist:** Application-layer control. Without this, Synapse rejects federation from the new domain.
2. **hostAliases:** DNS resolution. Agent domains have no public DNS. Without this, Synapse cannot connect to the Caddy proxy (returns 502).

After adding both, restart Synapse: `kubectl rollout restart deployment matrix-synapse -n matrix`

---

## 8. Troubleshooting Reference

Organized by symptom. Each entry includes the symptom, root cause, diagnostic commands, and fix.

### 8.1 Federation: 502 Bad Gateway on Room Join

**Symptom:** User receives invite but gets 502 when accepting/joining.

**Key insight:** Invite works = outbound federation (agent → Synapse) is fine. Join fails = inbound federation (Synapse → agent) is broken.

**Root cause (most common):** Missing `hostAliases` in Synapse K8s Deployment. Synapse cannot resolve the homeserver hostname.

**Diagnosis:**
```bash
kubectl exec -n matrix <synapse-pod> -c matrix -- \
  python3 -c "import socket; print(socket.gethostbyname('agent0-N-mhs.cybertribe.com'))"

kubectl get deployment matrix-synapse -n matrix \
  -o jsonpath='{.spec.template.spec.hostAliases}' | jq .
```

**Fix:** Add hostAliases (see Section 7.3), restart Synapse.

**Other possible causes:**
- Missing `federation_domain_whitelist` entry
- TLS certificate not trusted (CA bundle missing root)
- iptables FORWARD DROP on Docker host
- VPN route missing on kama

### 8.2 Federation: 401 Unauthorized from Agent Zero API

**Symptom:** Bot logs: `401 - {"error": "Invalid API key"}`

**Root cause:** `A0_API_KEY` in bot `.env` does not match Agent Zero's computed `mcp_server_token`.

**Diagnosis:**
```bash
# Compute expected token
python3 -c "
import hashlib, base64, os, dotenv
dotenv.load_dotenv('/a0/.env')
rid = os.environ.get('A0_PERSISTENT_RUNTIME_ID', '')
al = os.environ.get('AUTH_LOGIN', '')
ap = os.environ.get('AUTH_PASSWORD', '')
raw = f'{rid}:{al}:{ap}'
token = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest()).decode()[:16]
print(f'Expected: {token}')
"
# Compare with actual
grep A0_API_KEY /a0/usr/workdir/matrix-bot/.env
```

**Fix:**
```bash
bash /a0/usr/workdir/startup-patch.sh
kill $(pgrep -f matrix_bot.py)
cd /a0/usr/workdir/matrix-bot && nohup /opt/venv-a0/bin/python3 matrix_bot.py >> bot.log 2>&1 &
```

### 8.3 K8s: Cross-Node DNS Failure

**Symptom:** Pods on k8-1/k8-2 cannot resolve service names. Synapse enters CrashLoopBackOff with `could not translate host name`.

**Root cause:** UFW on K8s nodes blocks VXLAN (UDP 8472) and pod forwarding.

**Diagnosis:**
```bash
# Simultaneous tcpdump on receiving node
tcpdump -i cilium_vxlan -nn -c 5 &
tcpdump -i eth0 udp port 8472 -nn -c 5
# If eth0 sees packets but cilium_vxlan doesn't -> firewall dropping
```

**Fix on all K8s nodes:**
```bash
ufw default allow routed
ufw allow 8472/udp
ufw allow 4240/tcp
```

### 8.4 MCP: Wrong Matrix Identity or M_UNKNOWN_TOKEN (Gotcha #13)

**Symptom:** Matrix MCP tools fail with M_UNKNOWN_TOKEN, or logs show requests authenticated as the wrong user (e.g. old `@agent:` after migration to `@agent0-1:`).

**Root cause:** Agent Zero stores MCP config (including optional `headers`) in `settings.json`. When the matrix MCP entry has a `headers` block with `matrix_user_id` and `matrix_access_token`, those are sent on **every** MCP request and **override** whatever is in the MCP server's `.env`. Updating only the MCP server `.env` is not enough.

**Fix:** Update both the MCP server `.env` and the matrix MCP config in the Agent Zero UI (Settings -> MCP/A2A). Set the headers to the current Matrix identity and access token, or remove the headers block entirely so the MCP server uses only its `.env`. Restart the agent so it reloads settings.

### 8.5 Cilium: Stale BPF Programs After Restart

**Symptom:** After `kubectl rollout restart daemonset/cilium`, overlay networking breaks.

**Root cause:** Cilium 1.19 TCX mode doesn't clean up BPF programs on `cilium_vxlan`.

**Diagnosis:**
```bash
bpftool net show | grep cilium_vxlan
```

**Fix:**
```bash
bpftool link detach id <ingress_link_id>
bpftool link detach id <egress_link_id>
```

**Permanent:** Set `bpf.enableTCX: false` in Cilium Helm values.

### 8.6 Docker: macvlan Creation Fails

**Symptom:** `invalid subinterface vlan name`

**Root cause:** Docker running in rootless mode.

**Diagnosis:**
```bash
docker info | grep -i rootless
docker run --rm --net=host alpine ip link show  # If only lo, tap0, docker0 -> rootless
```

**Fix:** Switch to rootful Docker (see operations manual Section 1.1).

### 8.7 Certificate: Synapse federation_custom_ca_list Fails

**Symptom:** `certificate verify failed` on Synapse federation to agent homeserver.

**Root cause:** CA bundle contains only the intermediate CA, not the root.

**Fix:**
```bash
cat root_ca.crt intermediate_ca.crt > home-lab-ca-bundle.pem
kubectl create secret generic home-lab-ca -n matrix \
  --from-file=home-lab-ca.pem=home-lab-ca-bundle.pem \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment matrix-synapse -n matrix
```

### 8.8 Caddy: TLS Handshake Failure on Port 8448

**Symptom:** Federation fails with TLS errors; `curl -sk https://agent0-N-mhs.cybertribe.com:8448/` returns connection refused or certificate error.

**Root cause:** Caddy not loading certificates, or certificate/key mismatch.

**Diagnosis:**
```bash
# Check Caddy logs for TLS errors
docker logs agent0-N-mhs --tail=50 | grep -i tls

# Verify cert files exist and match
openssl x509 -noout -modulus -in /opt/agent-zero/agent0-N/mhs/server.crt | md5sum
openssl rsa -noout -modulus -in /opt/agent-zero/agent0-N/mhs/server.key | md5sum
# Both md5sums must match

# Test TLS handshake
curl -sk https://agent0-N-mhs.cybertribe.com:8448/_matrix/federation/v1/version
```

**Fix:** Re-issue certificate via step-ca (see Section 4.2), copy to `mhs/`, restart Caddy: `docker compose restart caddy`.

### 8.9 Continuwuity: Startup Fails or Database Error

**Symptom:** `agent0-N-continuwuity` container exits immediately or shows RocksDB errors.

**Root cause:** Permission issues on data directory, or corrupted RocksDB.

**Diagnosis:**
```bash
docker logs agent0-N-continuwuity --tail=50
ls -la /opt/agent-zero/agent0-N/mhs/continuwuity-data/
```

**Fix:**
- Permission issue: `chown -R 1000:1000 /opt/agent-zero/agent0-N/mhs/continuwuity-data/`
- Corrupted DB: Remove `mhs/continuwuity-data/`, restart (will re-create empty DB -- re-registration required)

### 8.10 Continuwuity: Registration Fails

**Symptom:** REST API registration returns 403 or `M_FORBIDDEN`.

**Root cause:** `CONTINUWUITY_ALLOW_REGISTRATION` not set to `true`, or wrong registration token.

**Diagnosis:**
```bash
grep CONTINUWUITY_REGISTRATION_TOKEN /opt/agent-zero/agent0-N/docker-compose.yml
grep CONTINUWUITY_ALLOW_REGISTRATION /opt/agent-zero/agent0-N/docker-compose.yml
```

**Fix:** Ensure both env vars are set correctly in docker-compose.yml, then `docker compose up -d`.

### 8.11 OpenVPN: Tunnel Breaks K8s Networking

**Symptom:** After VPN connects, cluster services/DNS fail from the Synapse pod.

**Root cause:** DD-WRT pushes `redirect-gateway def1`, routing all traffic through VPN.

**Fix:** Ensure `route-nopull` is in the client `.ovpn` config. Only route `172.23.0.0/16` through the tunnel.

---

## 9. Current System State

### 9.1 Hosts and Containers

| Container | Host | IP | MAC | Homeserver | Status |
|-----------|------|----|-----|------------|--------|
| agent0-1 | g2s | 172.23.88.1 | 02:42:AC:17:58:01 | -- | Operational |
| agent0-1-continuwuity | g2s | -- (bridge-local) | -- | Continuwuity v0.5.6 | Operational |
| agent0-1-mhs | g2s | 172.23.89.1 | 02:42:AC:17:59:01 | Caddy TLS proxy | Operational |
| agent0-2 | g2s | 172.23.88.2 | 02:42:AC:17:58:02 | -- | Operational |
| agent0-2-mhs | g2s | 172.23.89.2 | 02:42:AC:17:59:02 | Dendrite v0.15.2 | Operational (pending migration) |
| agent0-3 | g2s | 172.23.88.3 | 02:42:AC:17:58:03 | -- | Operational |
| agent0-3-mhs | g2s | 172.23.89.3 | 02:42:AC:17:59:03 | Dendrite v0.15.2 | Operational (pending migration) |
| agent0-4 | g2s | 172.23.88.4 | 02:42:AC:17:58:04 | -- | Operational |
| agent0-4-continuwuity | g2s | -- (bridge-local) | -- | Continuwuity v0.5.6 | Operational |
| agent0-4-mhs | g2s | 172.23.89.4 | 02:42:AC:17:59:04 | Caddy TLS proxy | Operational |

### 9.2 Matrix Identities

| Agent | Matrix ID | Homeserver | Profile |
|-------|-----------|------------|---------|
| agent0-1 | @agent0-1:agent0-1-mhs.cybertribe.com | agent0-1-mhs.cybertribe.com | Standard |
| agent0-2 | @agent0-2:agent0-2-mhs.cybertribe.com | agent0-2-mhs.cybertribe.com | (set at creation) |
| agent0-3 | @agent0-3:agent0-3-mhs.cybertribe.com | agent0-3-mhs.cybertribe.com | Standard |
| agent0-4 | @agent0-4:agent0-4-mhs.cybertribe.com | agent0-4-mhs.cybertribe.com | Standard |

> **Naming note:** agent0-1 was migrated from tarnover to g2s and re-registered with localpart `agent0-1`. All agents now use the `agent0-N` convention.

### 9.3 Federation Status (verified 2026-03)

| Test | agent0-1 (Continuwuity) | agent0-2 (Dendrite) | agent0-3 (Dendrite) | agent0-4 (Continuwuity) |
|------|-------------------------|---------------------|---------------------|-------------------------|
| CS API | OK | OK | OK | OK |
| Federation (8448) | OK | OK | OK | OK |
| Synapse whitelist | Listed | Listed | Listed | Listed |
| Synapse hostAliases | Present | Present | Present | Present |
| Room creation | OK | OK | OK | OK |
| Invite to human | OK | OK | OK | OK |
| Human joins room | OK | OK | OK | OK |
| Message round-trip | OK | OK | OK | OK |
| Bot auto-join | OK | OK | OK | OK |
| API token auth | OK | OK | OK | OK |

---

## 10. E2EE Roadmap

### 10.1 Current Limitation

E2EE is not supported. The matrix-js-sdk client in the MCP server has no Olm crypto support. Encrypted rooms are silently unreadable; sending to encrypted rooms fails. Only unencrypted rooms work for agent communication.

### 10.2 Rust Matrix MCP Server (Phase 2)

A Rust-based MCP server is planned to replace the Node.js implementation, providing native E2EE support via `matrix-sdk` and `matrix-sdk-crypto` crates.

**Roadmap:**
- **Week 1:** v1 compatibility spec (matching all existing MCP tools) + v2 E2EE spec stub
- **Week 2:** Rust MCP server with core v1 subset (unencrypted)
- **Week 3:** Full v1 parity, contract tests, switch-over
- **Week 4:** E2EE implementation (Olm/Megolm, key storage, bootstrap)
- **Week 5:** Hardening, rollout, documentation

**What the implementor needs to know:**
- Each MCP server instance will act as a verified Matrix device with its own cryptographic keys
- The persistent key store must survive container restarts (bind-mounted at `/a0/usr/`)
- Continuwuity supports E2EE at the server level; the limitation is entirely in the current MCP server
- The existing `matrix-js-sdk@28` has no crypto support compiled in
- The Rust implementation uses `matrix-sdk` / `matrix-sdk-crypto`, which include native Olm/Megolm
- Federation TLS uses step-ca certs -- the Rust client must trust the custom CA
- Per-agent homeserver means each agent has independent key management

See [rust-matrix-mcp-server-plan.md](../rust-matrix-mcp-server-plan.md) for the full roadmap.

---

## Appendix A: Configuration File Reference

### A.1 Docker Compose (Continuwuity Stack — agent0-N pattern)

```yaml
name: agent0-N

services:
  agent-zero:
    image: agent0ai/agent-zero
    container_name: agent0-N
    hostname: agent0-N
    restart: unless-stopped
    command: /bin/bash -c '/a0/usr/workdir/startup-services.sh & exec /usr/bin/python3 /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf'
    mac_address: "02:42:AC:17:58:NN"
    ports:
      - "5000N:80"
      - "5002(N+1):22"
    environment:
      - API_KEY_OPENROUTER=${API_KEY_OPENROUTER}
      - API_KEY_OPENAI=${API_KEY_OPENAI}
      - API_KEY_ANTHROPIC=${API_KEY_ANTHROPIC}
      - API_KEY_GOOGLE=${API_KEY_GOOGLE}
      - AUTH_LOGIN=${AUTH_LOGIN}
      - AUTH_PASSWORD=${AUTH_PASSWORD}
      - TZ=${TZ:-America/Los_Angeles}
      - MATRIX_HOMESERVER_URL=http://agent0-N-mhs:8008
    volumes:
      - ./usr:/a0/usr
    networks:
      macvlan-172-23:
        ipv4_address: 172.23.88.N
      bridge-local:

  continuwuity:
    image: ghcr.io/continuwuity/continuwuity:latest
    container_name: agent0-N-continuwuity
    hostname: agent0-N-continuwuity
    restart: unless-stopped
    environment:
      CONTINUWUITY_SERVER_NAME: agent0-N-mhs.cybertribe.com
      CONTINUWUITY_DATABASE_PATH: /var/lib/continuwuity
      CONTINUWUITY_PORT: 6167
      CONTINUWUITY_ADDRESS: "0.0.0.0"
      CONTINUWUITY_ALLOW_REGISTRATION: "true"
      CONTINUWUITY_REGISTRATION_TOKEN: "<unique-per-instance>"
      CONTINUWUITY_ALLOW_FEDERATION: "true"
      CONTINUWUITY_ALLOW_CHECK_FOR_UPDATES: "false"
      CONTINUWUITY_TRUSTED_SERVERS: '["v-site.net"]'
      CONTINUWUITY_LOG: "warn,state_res=warn"
      CONTINUWUITY_IP_RANGE_DENYLIST: '[]'
    volumes:
      - ./mhs/continuwuity-data:/var/lib/continuwuity
    networks:
      bridge-local:

  caddy:
    image: caddy:2-alpine
    container_name: agent0-N-mhs
    hostname: agent0-N-mhs
    restart: unless-stopped
    mac_address: "02:42:AC:17:59:NN"
    dns:
      - 172.23.1.1
    volumes:
      - ./mhs/Caddyfile:/etc/caddy/Caddyfile:ro
      - ./mhs/server.crt:/etc/caddy/server.crt:ro
      - ./mhs/server.key:/etc/caddy/server.key:ro
    networks:
      macvlan-172-23:
        ipv4_address: 172.23.89.N
      bridge-local:

networks:
  macvlan-172-23:
    external: true
  bridge-local:
    driver: bridge
```

### A.2 Continuwuity Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CONTINUWUITY_SERVER_NAME` | Yes | — | Matrix server name (e.g. `agent0-N-mhs.cybertribe.com`) |
| `CONTINUWUITY_DATABASE_PATH` | Yes | — | RocksDB data directory (e.g. `/var/lib/continuwuity`) |
| `CONTINUWUITY_PORT` | Yes | `6167` | HTTP listen port |
| `CONTINUWUITY_ADDRESS` | No | `127.0.0.1` | Bind address (`0.0.0.0` for container use) |
| `CONTINUWUITY_ALLOW_REGISTRATION` | No | `false` | Enable registration (requires token) |
| `CONTINUWUITY_REGISTRATION_TOKEN` | No | — | Token for `m.login.registration_token` auth |
| `CONTINUWUITY_ALLOW_FEDERATION` | No | `true` | Enable/disable federation |
| `CONTINUWUITY_ALLOW_CHECK_FOR_UPDATES` | No | `true` | Phone-home update check |
| `CONTINUWUITY_TRUSTED_SERVERS` | No | `["matrix.org"]` | Servers trusted for key fetching |
| `CONTINUWUITY_LOG` | No | `warn` | Log level filter |
| `CONTINUWUITY_IP_RANGE_DENYLIST` | No | RFC 1918 ranges | Set to `[]` for private LAN federation |
| `CONTINUWUITY_MAX_REQUEST_SIZE` | No | `20000000` | Max request body size (bytes) |
| `CONTINUWUITY_ALLOW_ROOM_CREATION` | No | `true` | Allow users to create rooms |

### A.3 Instance .env Template

```bash
# API Keys
API_KEY_OPENROUTER=
API_KEY_OPENAI=
API_KEY_ANTHROPIC=
API_KEY_GOOGLE=
API_KEY_GROQ=

# Authentication
AUTH_LOGIN=admin
AUTH_PASSWORD=changeme
ROOT_PASSWORD=changeme

# Locale
TZ=America/Los_Angeles
DEFAULT_USER_TIMEZONE=America/Los_Angeles

# Agent Zero
BRANCH=main
A0_SET_chat_model=openrouter/google/gemini-2.0-flash-001
A0_SET_embedding_model=openai/text-embedding-3-small
A0_SET_agent_profile=agent0
```

---

## Appendix B: DD-WRT Startup and Firewall Scripts

### Startup Script (Administration > Commands > Save Startup)

```bash
#!/bin/sh
# Agent container routes — add new agents here
ip route add 172.23.88.1/32 via 172.23.100.121  # agent0-1 (g2s)
ip route add 172.23.89.1/32 via 172.23.100.121  # agent0-1-mhs (g2s)
ip route add 172.23.88.2/32 via 172.23.100.121  # agent0-2 (g2s)
ip route add 172.23.89.2/32 via 172.23.100.121  # agent0-2-mhs (g2s)
ip route add 172.23.88.3/32 via 172.23.100.121  # agent0-3 (g2s)
ip route add 172.23.89.3/32 via 172.23.100.121  # agent0-3-mhs (g2s)
ip route add 172.23.88.4/32 via 172.23.100.121  # agent0-4 (g2s)
ip route add 172.23.89.4/32 via 172.23.100.121  # agent0-4-mhs (g2s)
```

### Firewall Script (saved via nvram)

```bash
nvram set rc_firewall='
iptables -t nat -A POSTROUTING -s 172.23.200.0/24 -j MASQUERADE
iptables -I FORWARD -p udp -s 172.23.200.0/24 -j ACCEPT
iptables -I INPUT -p udp --dport=1194 -j ACCEPT
iptables -I FORWARD -i tun2 -o br0 -j ACCEPT
iptables -I FORWARD -i br0 -o tun2 -j ACCEPT
iptables -t raw -I PREROUTING -i br0 -d 172.23.200.0/24 -j ACCEPT
'
nvram commit
```

### dnsmasq Additional Options

```
dhcp-option=br0,121,0.0.0.0/0,172.23.1.1,172.23.200.0/24,172.23.1.1
```

---

## Appendix C: Diagnostic Command Cheat Sheet

### Agent Zero Container

```bash
# Service status
docker exec agent0-N ps aux | grep -E 'http-server.js|matrix_bot' | grep -v grep

# Startup log
docker exec agent0-N cat /a0/usr/workdir/startup-services.log

# Bot log
docker exec agent0-N tail -50 /a0/usr/workdir/matrix-bot/bot.log

# MCP server log
docker exec agent0-N tail -50 /a0/usr/workdir/matrix-mcp-server/mcp-server.log

# Test MCP endpoint
docker exec agent0-N curl -s -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{'''"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'''' | grep -c 'name'

# Full service restart
docker exec agent0-N bash /a0/usr/workdir/startup-services.sh

# API token refresh
docker exec agent0-N bash /a0/usr/workdir/startup-patch.sh
```

### Continuwuity + Caddy (Homeserver)

```bash
# CS API health (via Caddy proxy)
curl -s http://172.23.89.N:8008/_matrix/client/versions | python3 -m json.tool

# Federation API health (TLS via Caddy)
curl -sk https://agent0-N-mhs.cybertribe.com:8448/_matrix/federation/v1/version

# Continuwuity logs
docker logs agent0-N-continuwuity --tail=50

# Caddy logs
docker logs agent0-N-mhs --tail=50

# Register account (Continuwuity REST API)
curl -s -X POST http://172.23.89.N:8008/_matrix/client/v3/register \
  -H 'Content-Type: application/json' \
  -d '{'''"username":"agent0-N","password":"<pw>","auth":{"type":"m.login.registration_token","token":"<token>"}}''''

# Check Continuwuity container connectivity (from Caddy)
docker exec agent0-N-mhs wget -qO- http://agent0-N-continuwuity:6167/_matrix/client/versions
```

### Dendrite (Legacy — agent0-2, agent0-3)

```bash
# CS API health
curl -s http://172.23.89.N:8008/_matrix/client/versions | python3 -m json.tool

# Federation API health (TLS)
curl -sk https://agent0-N-mhs.cybertribe.com:8448/_matrix/federation/v1/version

# Logs
docker logs agent0-N-mhs --tail=50

# Create admin user (Dendrite only)
docker exec agent0-N-mhs /usr/bin/create-account \
  -config /etc/dendrite/dendrite.yaml -username agentadmin -password <pw> -admin
```

### Synapse (K8s)

```bash
# Pod status
kubectl get pods -n matrix

# Synapse health
curl -s https://matrix.v-site.net/health

# Federation tester
curl -s https://federationtester.matrix.org/api/report?server_name=v-site.net | jq '.FederationOK'

# Admin API (requires port-forward)
kubectl port-forward -n matrix svc/matrix-synapse 8008:80 &
synadm user list
synadm room list

# Restart
kubectl rollout restart deployment matrix-synapse -n matrix

# Check hostAliases
kubectl get deployment matrix-synapse -n matrix \
  -o jsonpath='{.spec.template.spec.hostAliases}' | jq .

# VPN sidecar logs
kubectl logs -n matrix <synapse-pod> -c openvpn --tail=15

# Test home lab connectivity from Synapse pod
kubectl exec -n matrix <synapse-pod> -c matrix -- \
  python3 -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('172.23.1.1',53)); print('OK'); s.close()"

# Check DNS resolution for agent domains
kubectl exec -n matrix <synapse-pod> -c matrix -- \
  python3 -c "import socket; print(socket.gethostbyname('agent0-N-mhs.cybertribe.com'))"
```

### Network

```bash
# Routes on kama
ssh root@172.23.1.1 ip route show | grep '172.23.88\|172.23.89'

# VPN tunnel
ping 172.23.200.1    # VPN gateway from LAN
ping 172.23.200.2    # Contabo VPN endpoint from LAN

# macvlan verification
ping -c 1 172.23.88.N    # Agent Zero container
ping -c 1 172.23.89.N    # Caddy TLS proxy container

# mac0 bridge
ip addr show mac0
systemctl status mac0-macvlan.service
```

### Certificates

```bash
# step-ca health
step ca health

# Inspect certificate
step certificate inspect /opt/agent-zero/agent0-N/mhs/server.crt --short

# Verify certificate chain
step certificate verify /opt/agent-zero/agent0-N/mhs/server.crt \
  --roots /home/l0r3zz/cybertribe-ca/step-store/certs/root_ca.crt

# Check cert-manager status
kubectl get certificate -n matrix
kubectl describe certificate matrix-synapse-tls -n matrix
```

---

*Last updated: March 2026*


## Zero-Touch Hardening v3.17
See: ./zero-touch-hardening-v3.17.md


## Instance Acceptance Validation
See: ./validate-instance-guide.md
