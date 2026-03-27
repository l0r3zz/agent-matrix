# Agent-Matrix Theory of Operations

**Version:** 2.0  
**Date:** March 16, 2026  
**Audience:** SREs, developers implementing the Rust MCP server, deep troubleshooters  
**Companion Documents:** [agent-matrix-design.md](agent-matrix-design.md) | [operations-manual.md](operations-manual.md)

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Network Deep Dive](#2-network-deep-dive)
3. [Kubernetes Cluster](#3-kubernetes-cluster)
4. [Certificate Management](#4-certificate-management)
5. [Continuwuity Homeserver](#5-continuwuity-homeserver)
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
                              │   Contabo K8s Cluster      │
                              │   MetalLB: 147.93.135.115  │
                              │   Traefik + cert-manager   │
                              │                            │
                              │  matrix namespace:         │
                              │  ┌──────────────────────┐  │
                              │  │ Synapse 1.147.1      │  │
                              │  │ server_name: v-site   │  │
                              │  │ .net                  │  │
                              │  │ + OpenVPN sidecar     │  │
                              │  └──────────┬───────────┘  │
                              │  ┌──────────────────────┐  │
                              │  │ Element Web          │  │
                              │  └──────────────────────┘  │
                              │  ┌──────────────────────┐  │
                              │  │ PostgreSQL           │  │
                              │  └──────────────────────┘  │
                              └────────────┬──────────────-┘
                                           │ OpenVPN tunnel
                                           │ 172.23.200.2 <-> 172.23.200.1
                              ┌────────────▼──────────────-┐
                              │  kama (DD-WRT v3)          │
                              │  172.23.1.1                │
                              │  tun2: 172.23.200.1        │
                              │  DHCP + DNS (dnsmasq)      │
                              │  OpenVPN server            │
                              │  Per-container /32 routes  │
                              └──┬──────────────────┬─────-┘
                                 │ LAN 172.23.0.0/16│
                ┌────────────────▼──┐   ┌───────────▼──────────────────┐
                │ tarnover           │   │ g2s (172.23.100.121)         │
                │ 172.23.0.103       │   │ NIC: eno1, 128 GB RAM       │
                │ step-ca PKI (:9000)│   │ Docker rootful (PRIMARY)     │
                │ Admin workstation  │   │                              │
                │ No agent workloads │   │  5 agent triplets:           │
                │                    │   │  agent0-1 thru agent0-5      │
                └────────────────────┘   │  Each = A0 + Continuwuity    │
                                         │         + Caddy (TLS)        │
                                         └─────────────────────────────┘
```

### Host Inventory

| Host | IP | Role | OS | Notes |
|------|----|------|-----|-------|
| kama (DD-WRT) | 172.23.1.1 | Gateway, DHCP, DNS, VPN server | DD-WRT v3 | tun2: 172.23.200.1 |
| tarnover | 172.23.0.103 | step-ca PKI, admin workstation | Pop!_OS, kernel 6.17.9 | NIC: enp36s0. No agent workloads. |
| g2s | 172.23.100.121 | Primary Docker host (all agents) | Pop!_OS 22.04 | NIC: eno1, 128 GB RAM |
| agent0-1 | 172.23.88.1 | Agent Zero container #1 | Docker (agent0ai/agent-zero) | MAC 02:42:AC:17:58:01 |
| agent0-1-continuwuity | bridge-local | Continuwuity homeserver #1 | Docker (continuwuity:latest) | port 6167 |
| agent0-1-mhs | 172.23.89.1 | Caddy TLS proxy #1 | Docker (caddy:2-alpine) | MAC 02:42:AC:17:59:01 |
| agent0-2 | 172.23.88.2 | Agent Zero container #2 | Docker (agent0ai/agent-zero) | MAC 02:42:AC:17:58:02 |
| agent0-2-continuwuity | bridge-local | Continuwuity homeserver #2 | Docker (continuwuity:latest) | port 6167 |
| agent0-2-mhs | 172.23.89.2 | Caddy TLS proxy #2 | Docker (caddy:2-alpine) | MAC 02:42:AC:17:59:02 |
| agent0-3 | 172.23.88.3 | Agent Zero container #3 | Docker (agent0ai/agent-zero) | MAC 02:42:AC:17:58:03 |
| agent0-3-continuwuity | bridge-local | Continuwuity homeserver #3 | Docker (continuwuity:latest) | port 6167 |
| agent0-3-mhs | 172.23.89.3 | Caddy TLS proxy #3 | Docker (caddy:2-alpine) | MAC 02:42:AC:17:59:03 |
| agent0-4 | 172.23.88.4 | Agent Zero container #4 | Docker (agent0ai/agent-zero) | MAC 02:42:AC:17:58:04 |
| agent0-4-continuwuity | bridge-local | Continuwuity homeserver #4 | Docker (continuwuity:latest) | port 6167 |
| agent0-4-mhs | 172.23.89.4 | Caddy TLS proxy #4 | Docker (caddy:2-alpine) | MAC 02:42:AC:17:59:04 |
| agent0-5 | 172.23.88.5 | Agent Zero container #5 | Docker (agent0ai/agent-zero) | MAC 02:42:AC:17:58:05 |
| agent0-5-continuwuity | bridge-local | Continuwuity homeserver #5 | Docker (continuwuity:latest) | port 6167 |
| agent0-5-mhs | 172.23.89.5 | Caddy TLS proxy #5 | Docker (caddy:2-alpine) | MAC 02:42:AC:17:59:05 |
| mac0 (g2s) | 172.23.88.254 | macvlan bridge interface | Virtual | Host-local, not LAN-routable |
| step-ca | 172.23.0.103:9000 | Certificate authority | step-ca on tarnover | CyberTribe CA |
| k8-0 | 144.126.131.105 | K8s control-plane | Ubuntu 24.04 | Contabo |
| k8-1 | 207.244.225.169 | K8s worker | Ubuntu 24.04 | Contabo |
| k8-2 | 207.244.237.219 | K8s worker | Ubuntu 24.04 | Contabo |

### Network Segments

| Segment | CIDR | Purpose |
|---------|------|---------|
| Home LAN | 172.23.0.0/16 | All lab hosts and containers |
| Agent containers | 172.23.88.0/24 | Agent Zero instances |
| Homeserver containers | 172.23.89.0/24 | Caddy TLS proxies (MHS endpoints) |
| VPN tunnel | 172.23.200.0/24 | Contabo <-> home lab |
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

**Critical requirement:** Docker must run in **rootful** mode. Rootless Docker operates in a user namespace with `slirp4netns`/`pasta` and cannot see host interfaces. The error message `invalid subinterface vlan name` is misleading -- the real issue is namespace isolation.

**Three-network design:** Each agent triplet connects to Docker networks as follows:

| Container | Networks | Purpose |
|-----------|----------|---------|
| agent0-N (Agent Zero) | macvlan-172-23 + bridge-local | LAN-routable IP (172.23.88.N), localhost port-mapping for Web UI |
| agent0-N-continuwuity | bridge-local only | Internal homeserver on port 6167, not LAN-routable |
| agent0-N-mhs (Caddy) | macvlan-172-23 + bridge-local | LAN-routable IP (172.23.89.N), TLS termination for federation |

### 2.2 mac0 Bridge (Host-to-Container Access)

Linux kernel macvlan blocks traffic between a host and its own macvlan containers. The `mac0` bridge interface creates a virtual endpoint into the container subnet:

```bash
ip link add mac0 link <NIC> type macvlan mode bridge
ip addr add 172.23.88.254/32 dev mac0
ip link set mac0 up
ip route add 172.23.88.0/24 dev mac0
ip route add 172.23.89.0/24 dev mac0
```

Persisted via a systemd service (`mac0-macvlan.service` or `agent-bridge.service`) on g2s. The IP `172.23.88.254` is host-local, not LAN-routable. Promiscuous mode must be enabled on the host NIC: `ip link set <NIC> promisc on`.

### 2.3 DD-WRT Configuration (kama)

#### Static DHCP Leases

Each agent triplet gets two DHCP static leases (Agent Zero + Caddy MHS). Continuwuity has no macvlan IP and thus no lease. Configured via Services > Services > Static Leases.

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
| 02:42:AC:17:58:05 | agent0-5 | 172.23.88.5 |
| 02:42:AC:17:59:05 | agent0-5-mhs | 172.23.89.5 |

These leases also drive dnsmasq hostname resolution -- `agent0-1-mhs.cybertribe.com` resolves to `172.23.89.1` for any LAN client using kama as DNS.

#### Per-Container /32 Routes

Each agent triplet gets two `/32` routes on kama pointing to g2s. This is more flexible than per-host /24 -- it allows containers on different hosts to share the same address space (though currently all agents are on g2s).

```bash
ip route add 172.23.88.1/32 via 172.23.100.121  # agent0-1 (g2s)
ip route add 172.23.89.1/32 via 172.23.100.121  # agent0-1-mhs (g2s)
ip route add 172.23.88.2/32 via 172.23.100.121  # agent0-2 (g2s)
ip route add 172.23.89.2/32 via 172.23.100.121  # agent0-2-mhs (g2s)
ip route add 172.23.88.3/32 via 172.23.100.121  # agent0-3 (g2s)
ip route add 172.23.89.3/32 via 172.23.100.121  # agent0-3-mhs (g2s)
ip route add 172.23.88.4/32 via 172.23.100.121  # agent0-4 (g2s)
ip route add 172.23.89.4/32 via 172.23.100.121  # agent0-4-mhs (g2s)
ip route add 172.23.88.5/32 via 172.23.100.121  # agent0-5 (g2s)
ip route add 172.23.89.5/32 via 172.23.100.121  # agent0-5-mhs (g2s)
```

Saved via Administration > Commands > Save Startup.

#### DHCP Option 121 (VPN Route Push)

```
dhcp-option=br0,121,0.0.0.0/0,172.23.1.1,172.23.200.0/24,172.23.1.1
```

When DHCP Option 121 (Classless Static Routes) is present, most clients (especially `systemd-networkd`) **ignore Option 3** (default gateway). The default route `0.0.0.0/0` **must** be included in Option 121 or clients lose internet connectivity.

### 2.4 OpenVPN Tunnel (kama <-> Contabo K8s)

The VPN connects the Contabo K8s cluster to the home lab, allowing Synapse to federate with agent homeservers on the private LAN.

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

**Resilience:** When the VPN is down, agents on the private LAN can still communicate with each other (Continuwuity-to-Continuwuity federation over LAN). Agents also retain full internet access -- their traffic routes via kama to the ISP, not through the VPN. Only human <-> agent connectivity via Synapse is interrupted.

#### LAN-to-VPN Routing

By default, LAN hosts cannot reach VPN clients (172.23.200.0/24) due to:

1. **OpenVPN raw table anti-spoof rule:** Auto-generated DROP for traffic to 172.23.200.0/24 from non-tun2 interfaces. Fixed with: `iptables -t raw -I PREROUTING -i br0 -d 172.23.200.0/24 -j ACCEPT`
2. **FORWARD chain:** Must explicitly allow br0<->tun2 traffic.
3. **On-link ARP issue:** LAN hosts with /16 route try ARP for 172.23.200.x. Fixed with DHCP Option 121 pushing a more-specific /24 route.

**DD-WRT GUI "Save Firewall" caveat:** Never use the GUI button for VPN-related iptables rules -- it triggers a full firewall + OpenVPN restart that bounces the tunnel. Always use `nvram set rc_firewall` + `nvram commit` from CLI.

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
- Admin API not exposed publicly -- use `kubectl port-forward svc/matrix-synapse 8008:80` + `synadm`

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
https://v-site.net/.well-known/matrix/server -> {"m.server":"matrix.v-site.net:443"}
```

**SRV records (fallback):**
```
_matrix._tcp.v-site.net.      3600  IN  SRV  0 0 443 matrix.v-site.net.
_matrix-fed._tcp.v-site.net.  3600  IN  SRV  0 0 443 matrix.v-site.net.
```

`matrix.v-site.net` must be an A record (not CNAME -- SRV targets pointing to CNAMEs violate RFC 2782).

### 3.5 OpenVPN Sidecar Pattern

The OpenVPN client runs as a sidecar container in the Synapse pod (Alpine 3.19, `NET_ADMIN` capability). It shares the pod's network namespace -- when OpenVPN creates `tun0` and adds routes, they are visible to the Synapse container automatically.

The sidecar mounts the VPN config from K8s Secret `openvpn-client-config` at `/vpn/client.ovpn`.

### 3.6 Synapse Federation Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `federation_domain_whitelist` | `[agent0-1-mhs.cybertribe.com, agent0-2-mhs.cybertribe.com, agent0-3-mhs.cybertribe.com, agent0-4-mhs.cybertribe.com, agent0-5-mhs.cybertribe.com]` | Only federate with listed domains |
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
  - ip: "172.23.89.5"
    hostnames: ["agent0-5-mhs.cybertribe.com"]
```

A future phase will use CoreDNS conditional forwarding to kama, eliminating per-agent hostAliases patches and pod restarts.

### 3.7 Known K8s Issues

#### Cilium UFW Interaction

UFW's `deny (routed)` default drops VXLAN-decapsulated packets in the FORWARD chain. Additionally, UDP 8472 must be explicitly allowed in the INPUT chain -- Cilium's nftables ACCEPT rule does NOT override iptables INPUT DROP (both chains evaluate independently).

**Required UFW rules on all K8s nodes:**
```bash
ufw default allow routed
ufw allow 8472/udp
ufw allow 4240/tcp
```

#### Cilium TCX Mode Bug (#44194)

Cilium 1.19 with TCX attachment mode has a bug where BPF programs on `cilium_vxlan` are NOT cleaned up when the agent pod terminates. New pods cannot replace them.

**Detection:** `bpftool net show` -- stale programs have lower `prog_id` values than active ones.

**Workaround:** Detach stale links before restarting: `bpftool link detach id <id>`

**Permanent fix:** Set `bpf.enableTCX: false` in Cilium Helm values.

#### CoreDNS Placement

Both CoreDNS replicas run on k8-0 (control-plane). Add pod anti-affinity to spread across nodes.

---

## 4. Certificate Management

### 4.1 PKI Architecture

```
CyberTribe CA Root CA (step-ca on tarnover)
  +-- CyberTribe CA Intermediate CA
       +-- router.cybertribe.com (VPN server cert)
       +-- contabo-synapse.cybertribe.com (VPN client cert, 1-year)
       +-- agent0-1-mhs.cybertribe.com (Caddy TLS, 1-year)
       +-- agent0-2-mhs.cybertribe.com (Caddy TLS, 1-year)
       +-- agent0-3-mhs.cybertribe.com (Caddy TLS, 1-year)
       +-- agent0-4-mhs.cybertribe.com (Caddy TLS, 1-year)
       +-- agent0-5-mhs.cybertribe.com (Caddy TLS, 1-year)
```

step-ca runs on tarnover at `https://localhost:9000`.

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

**Why both are required:** Python's Twisted TLS library (used by Synapse) requires the root CA as a trust anchor. Caddy sends the leaf + intermediate in the TLS handshake; Synapse must have the root to complete the chain. With intermediate-only bundles, Synapse reports `certificate verify failed` even though `curl --cacert` succeeds (curl is more lenient about trust anchors).

### 4.4 Caddy TLS Configuration

Each agent's Caddy sidecar (`agent0-N-mhs`) holds the step-ca certificate and key. The Caddyfile configures TLS termination for federation port 8448 and passes through client API port 8008 unencrypted:

```
:8008 {
    reverse_proxy agent0-N-continuwuity:6167
}

:8448 {
    tls /etc/caddy/server.crt /etc/caddy/server.key
    reverse_proxy agent0-N-continuwuity:6167
}
```

Certificates are bind-mounted from the host at `/opt/agent-zero/agent0-N/mhs/server.crt` and `server.key`.

### 4.5 Let's Encrypt for Synapse

cert-manager handles public TLS for `matrix.v-site.net` automatically via HTTP-01 challenges. The ClusterIssuer `letsencrypt-prod` creates and auto-renews certificates stored in Secret `matrix-synapse-tls`.

### 4.6 Common Certificate Pitfalls

| Problem | Symptom | Fix |
|---------|---------|-----|
| Intermediate-only CA bundle | `certificate verify failed` on Synapse federation | Include root CA in the bundle |
| Expired cert | Federation silently fails | Check with `step certificate inspect --short`; re-issue |
| Key/cert mismatch | OpenVPN: `Private key does not match the certificate` | Re-issue from the same `step ca certificate` invocation |
| step-ca "too many positional arguments" | CLI flag error on step-ca 0.28.x-0.29.x | Use `--not-after=8760h` (equals syntax, not space-separated) |

---

## 5. Continuwuity Homeserver

Continuwuity replaced Dendrite across the entire fleet in March 2026. It is a Rust-based Matrix homeserver (Conduit/Conduwuit fork) with RocksDB storage. See [continuwuity-migration.md](continuwuity-migration.md) for migration details.

### 5.1 Architecture

Continuwuity runs as a standalone container (`agent0-N-continuwuity`) on a bridge-local Docker network only. It is **not** directly LAN-routable. All external access goes through the Caddy reverse proxy (`agent0-N-mhs`).

| Property | Value |
|----------|-------|
| Image | `ghcr.io/continuwuity/continuwuity:latest` |
| Internal port | 6167 |
| Database | RocksDB (embedded, single data dir) |
| Memory usage | ~20-50 MB |
| Configuration | Environment variables (`CONTINUWUITY_` prefix) |
| Data directory | `/opt/agent-zero/agent0-N/mhs/continuwuity-data/` (host) |

### 5.2 Configuration

Continuwuity uses environment variables instead of a YAML config file. Key variables are set in the `docker-compose.yml` environment section:

| Variable | Example Value | Purpose |
|----------|---------------|---------|
| `CONTINUWUITY_SERVER_NAME` | `agent0-N-mhs.cybertribe.com` | Matrix server identity |
| `CONTINUWUITY_DATABASE_PATH` | `/data` | RocksDB data directory |
| `CONTINUWUITY_PORT` | `6167` | Listener port |
| `CONTINUWUITY_ALLOW_REGISTRATION` | `true` (initial) / `false` (after) | Account registration |
| `CONTINUWUITY_REGISTRATION_TOKEN` | `<random-token>` | One-time registration token |
| `CONTINUWUITY_ALLOW_FEDERATION` | `true` | Enable federation |

### 5.3 Ports

| Port | Protocol | Container | Purpose |
|------|----------|-----------|---------|
| 6167 | HTTP | agent0-N-continuwuity | Client-Server + Federation (internal) |
| 8008 | HTTP | agent0-N-mhs (Caddy) | Client-Server API (external, unencrypted) |
| 8448 | HTTPS | agent0-N-mhs (Caddy) | Federation API (external, TLS via step-ca) |

### 5.4 Account Management

Continuwuity uses a **one-time registration token** flow, not a `create-account` binary.

**Extract the registration token** (emitted in container logs on first boot):
```bash
docker logs agent0-N-continuwuity 2>&1 | tr -d '\033' | grep -oE 'token[^" ]+' | head -1
```

**Register a user:**
```bash
curl -s -X POST http://172.23.89.N:8008/_matrix/client/v3/register \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "agent0-N",
    "password": "<secure-password>",
    "auth": {
      "type": "m.login.registration_token",
      "token": "<registration-token>"
    }
  }' | python3 -m json.tool
```

Save the returned `access_token`.

**Login to obtain a new access token:**
```bash
curl -s -X POST http://172.23.89.N:8008/_matrix/client/v3/login \
  -H 'Content-Type: application/json' \
  -d '{"type":"m.login.password","identifier":{"type":"m.id.user","user":"agent0-N"},"password":"<pw>","device_id":"AgentZeroBot"}'
```

### 5.5 Key Differences from Dendrite

| Aspect | Dendrite (historical) | Continuwuity (current) |
|--------|----------------------|----------------------|
| Language | Go | Rust |
| Config | YAML file (dendrite.yaml) | Environment variables (`CONTINUWUITY_` prefix) |
| Database | SQLite (multiple .db files) | RocksDB (single data dir) |
| Memory | ~200-400 MB | ~20-50 MB |
| TLS | Built-in (`--https-bind-address :8448`) | External via Caddy sidecar |
| Account creation | `create-account` binary | REST API with registration token |
| Container model | 2 containers (A0 + Dendrite) | 3 containers (A0 + Continuwuity + Caddy) |
| Admin API | `/_dendrite/admin/` | Conduit-heritage admin bot (`@conduit:`) |
| Status | Stalled since Aug 2025 | Actively developed |

---

## 6. Agent Zero Container Internals

### 6.1 Startup Sequence

The container's `command:` override in docker-compose launches `startup-services.sh` alongside supervisord. Supervisord manages the core Agent Zero web app; the Matrix bridge components (matrix-bot and matrix-mcp-server) are managed by the startup script:

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
| 4 | Start matrix-bot | Launches `run-matrix-bot.sh` (Python default, Rust optional) |
| 5 | Start watchdog | Monitors bot and MCP server processes, periodic health checks |

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

### 6.3 matrix-bot (Python default, Rust optional)

The reactive bridge component. Located at `/a0/usr/workdir/matrix-bot/`.

**How it works:**
1. Uses `matrix-nio` to maintain a persistent sync connection to the agent's homeserver (via Caddy at port 8008)
2. Listens for `m.room.message` events in all joined rooms
3. Forwards incoming messages to Agent Zero's `/api_message` HTTP API with `A0_API_KEY` auth header
4. Posts Agent Zero's LLM response back to the Matrix room
5. Converts markdown responses to `org.matrix.custom.html` for proper rendering in Element
6. Prefixes forwarded messages with instructions telling Agent Zero to respond with plain text only (echo suppression -- prevents the agent from re-invoking MCP Matrix tools)
7. Maintains `room_contexts.json` for conversation context across messages
8. Auto-joins rooms on invite

**Key files:**
| File | Path |
|------|------|
| Bot launcher | `/a0/usr/workdir/matrix-bot/run-matrix-bot.sh` |
| Python bot script | `/a0/usr/workdir/matrix-bot/matrix_bot.py` |
| Runtime selector | `/a0/usr/workdir/matrix-bot/.bot_runtime` |
| Runtime switch helper | `/a0/usr/workdir/switch-matrix-bot.sh` |
| Runtime smoke test | `/a0/usr/workdir/smoke-test-matrix-bot.sh` |
| Bot .env | `/a0/usr/workdir/matrix-bot/.env` |
| Bot log | `/a0/usr/workdir/matrix-bot/bot.log` |
| Room contexts | `/a0/usr/workdir/matrix-bot/room_contexts.json` |

### 6.4 matrix-mcp-server (Node.js)

The proactive bridge component. Located at `/a0/usr/workdir/matrix-mcp-server/`.

**How it works:**
1. Runs as an HTTP MCP server on port 3000
2. Exposes Matrix CS API operations as MCP tools
3. Credentials read from `.env` file (`MATRIX_USER_ID`, `MATRIX_ACCESS_TOKEN`)
4. Agent Zero invokes tools via HTTP to `http://localhost:3000/mcp`
5. Supports credential override via HTTP headers (`matrix_homeserver_url`, `matrix_user_id`, `matrix_access_token`)

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

> **Note:** `"type": "http"` will fail with 405 Method Not Allowed. Must be `"streamable-http"`.

### 6.5 Agent Profiles and .env Configuration

Profiles are set via `A0_SET_agent_profile` in the instance `.env`:

| Profile | `A0_SET_agent_profile` |
|---------|----------------------|
| Standard | `agent0` |
| Hacker | `hacker` |
| Developer | `developer` |
| Researcher | `researcher` |

Default models: `openrouter/google/gemini-2.0-flash-001` (chat), `openai/text-embedding-3-small` (embedding).

All five current agents use the Standard profile.

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

---

## 7. Federation Walkthrough

### 7.1 End-to-End Message Flow (Human -> Agent)

```
1.  Human types message in Element (connected to matrix.v-site.net)
2.  Element sends PUT to Synapse via Client-Server API
3.  Synapse stores event in DAG, signs it
4.  Synapse federates to agent homeserver:
    a. Looks up agent0-N-mhs.cybertribe.com via hostAliases -> 172.23.89.N
    b. Sends via OpenVPN tunnel (tun0 -> 172.23.200.1 -> kama -> /32 route -> g2s)
    c. TLS handshake with Caddy on port 8448 (step-ca cert)
    d. Caddy proxies to Continuwuity on port 6167
    e. Delivers event via Server-Server API
5.  Continuwuity stores event, updates sync stream
6.  matrix-bot runtime receives event via sync response (polling Caddy :8008)
7.  matrix-bot POSTs to Agent Zero /api_message with A0_API_KEY header
8.  Agent Zero processes with LLM, generates response
9.  Agent Zero returns response to matrix-bot
10. matrix-bot sends response via CS API (http://agent0-N-mhs:8008)
11. Caddy proxies to Continuwuity, which federates to Synapse (reverse path through VPN)
12. Human sees response in Element
```

### 7.2 Room Creation and Invitation Flow

1. Agent creates room on Continuwuity via MCP `create-room` tool
2. Agent invites human via MCP `invite-user` tool with `@user:v-site.net`
3. Continuwuity sends invite to Synapse (outbound federation via Caddy TLS)
4. Synapse delivers invite to user's sync stream
5. Human sees invite in Element, clicks "Accept"
6. Synapse sends join request to Continuwuity (inbound federation via Caddy)
   - **This is where 502 errors occur if hostAliases are missing**
7. Continuwuity authorizes join, sends room state
8. Room is now federated -- both servers maintain event DAG replicas

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

**Key insight:** Invite works = outbound federation (agent -> Synapse) is fine. Join fails = inbound federation (Synapse -> agent) is broken.

**Root cause (most common):** Missing `hostAliases` in Synapse K8s Deployment. Synapse cannot resolve the agent hostname.

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
docker exec agent0-N python3 -c "
import hashlib, base64, os, dotenv
dotenv.load_dotenv('/a0/.env')
rid = os.environ.get('A0_PERSISTENT_RUNTIME_ID', '')
al = os.environ.get('AUTH_LOGIN', '')
ap = os.environ.get('AUTH_PASSWORD', '')
raw = f'{rid}:{al}:{ap}'
token = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest()).decode()[:16]
print(f'Expected: {token}')
"
grep A0_API_KEY /a0/usr/workdir/matrix-bot/.env
```

**Fix:**
```bash
docker exec agent0-N bash /a0/usr/workdir/startup-patch.sh
docker exec agent0-N bash -c "kill \$(pgrep -f 'run-matrix-bot.sh|matrix_bot.py|matrix-bot-rust'); cd /a0/usr/workdir/matrix-bot && nohup ./run-matrix-bot.sh >> bot.log 2>&1 &"
```

### 8.3 K8s: Cross-Node DNS Failure

**Symptom:** Pods on k8-1/k8-2 cannot resolve service names. Synapse enters CrashLoopBackOff with `could not translate host name`.

**Root cause:** UFW on K8s nodes blocks VXLAN (UDP 8472) and pod forwarding.

**Diagnosis:**
```bash
tcpdump -i cilium_vxlan -nn -c 5 &
tcpdump -i eth0 udp port 8472 -nn -c 5
```

**Fix on all K8s nodes:**
```bash
ufw default allow routed
ufw allow 8472/udp
ufw allow 4240/tcp
```

### 8.4 Cilium: Stale BPF Programs After Restart

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

### 8.5 Docker: macvlan Creation Fails

**Symptom:** `invalid subinterface vlan name`

**Root cause:** Docker running in rootless mode.

**Diagnosis:**
```bash
docker info | grep -i rootless
docker run --rm --net=host alpine ip link show
```

**Fix:** Switch to rootful Docker (see operations manual Section 1.1).

### 8.6 Certificate: Synapse federation_custom_ca_list Fails

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

### 8.7 MCP Server: Token Mismatch (M_UNKNOWN_TOKEN)

**Symptom:** MCP server logs show `M_UNKNOWN_TOKEN` errors. Agent cannot use Matrix tools.

**Root cause:** Token in MCP server's `.env` does not match Agent Zero's `settings.json` MCP headers.

**Diagnosis:**
```bash
docker exec agent0-N python3 /a0/usr/workdir/check-token-sync.py
```

**Fix:** See operations manual Section 7.6 (Token Mismatch Prevention System).

### 8.8 Caddy: Federation Port Not Responding

**Symptom:** `curl -sk https://agent0-N-mhs.cybertribe.com:8448` times out.

**Root cause:** Caddy container not running, or certificates not mounted.

**Diagnosis:**
```bash
docker ps | grep agent0-N-mhs
docker logs agent0-N-mhs --tail=20
```

**Fix:** Check that `server.crt` and `server.key` exist in `/opt/agent-zero/agent0-N/mhs/` and are valid. Restart: `cd /opt/agent-zero/agent0-N && docker compose restart agent0-N-mhs`.

### 8.9 OpenVPN: Tunnel Breaks K8s Networking

**Symptom:** After VPN connects, cluster services/DNS fail from the Synapse pod.

**Root cause:** DD-WRT pushes `redirect-gateway def1`, routing all traffic through VPN.

**Fix:** Ensure `route-nopull` is in the client `.ovpn` config. Only route `172.23.0.0/16` through the tunnel.

---

## 9. Current System State

### 9.1 Fleet Registry

| Container | Host | IP | MAC | Status |
|-----------|------|----|-----|--------|
| agent0-1 | g2s | 172.23.88.1 | 02:42:AC:17:58:01 | Operational |
| agent0-1-continuwuity | g2s | bridge-local | -- | Operational |
| agent0-1-mhs | g2s | 172.23.89.1 | 02:42:AC:17:59:01 | Operational |
| agent0-2 | g2s | 172.23.88.2 | 02:42:AC:17:58:02 | Operational |
| agent0-2-continuwuity | g2s | bridge-local | -- | Operational |
| agent0-2-mhs | g2s | 172.23.89.2 | 02:42:AC:17:59:02 | Operational |
| agent0-3 | g2s | 172.23.88.3 | 02:42:AC:17:58:03 | Operational |
| agent0-3-continuwuity | g2s | bridge-local | -- | Operational |
| agent0-3-mhs | g2s | 172.23.89.3 | 02:42:AC:17:59:03 | Operational |
| agent0-4 | g2s | 172.23.88.4 | 02:42:AC:17:58:04 | Operational |
| agent0-4-continuwuity | g2s | bridge-local | -- | Operational |
| agent0-4-mhs | g2s | 172.23.89.4 | 02:42:AC:17:59:04 | Operational |
| agent0-5 | g2s | 172.23.88.5 | 02:42:AC:17:58:05 | Operational |
| agent0-5-continuwuity | g2s | bridge-local | -- | Operational |
| agent0-5-mhs | g2s | 172.23.89.5 | 02:42:AC:17:59:05 | Operational |

### 9.2 Matrix Identities

| Agent | Matrix ID | Homeserver | Profile |
|-------|-----------|------------|---------|
| agent0-1 | @agent:agent0-1-mhs.cybertribe.com | agent0-1-mhs.cybertribe.com | Standard |
| agent0-2 | @agent0-2:agent0-2-mhs.cybertribe.com | agent0-2-mhs.cybertribe.com | Standard |
| agent0-3 | @agent0-3:agent0-3-mhs.cybertribe.com | agent0-3-mhs.cybertribe.com | Standard |
| agent0-4 | @agent0-4:agent0-4-mhs.cybertribe.com | agent0-4-mhs.cybertribe.com | Standard |
| agent0-5 | @agent0-5:agent0-5-mhs.cybertribe.com | agent0-5-mhs.cybertribe.com | Standard |

> **Naming note:** agent0-1 was created manually during Phase 1 with localpart `agent`. Subsequent agents follow the `agent0-N` convention. The localpart difference has no functional impact.

### 9.3 Federation Status

| Test | agent0-1 | agent0-2 | agent0-3 | agent0-4 | agent0-5 |
|------|----------|----------|----------|----------|----------|
| CS API (8008) | OK | OK | OK | OK | OK |
| Federation (8448) | OK | OK | OK | OK | OK |
| Synapse whitelist | Listed | Listed | Listed | Listed | Listed |
| Synapse hostAliases | Present | Present | Present | Present | Present |
| Room creation | OK | OK | OK | OK | OK |
| Invite to human | OK | OK | OK | OK | OK |
| Human joins room | OK | OK | OK | OK | OK |
| Message round-trip | OK | OK | OK | OK | OK |
| Bot auto-join | OK | OK | OK | OK | OK |
| API token auth | OK | OK | OK | OK | OK |

---

## 10. E2EE Roadmap

### 10.1 Current Limitation

E2EE is not supported. The matrix-js-sdk client in the Node.js MCP server has no Olm crypto support. Encrypted rooms are silently unreadable; sending to encrypted rooms fails. Only unencrypted rooms work for agent communication.

### 10.2 Rust Matrix MCP Server (Phase 2)

A Rust-based MCP server is scaffolded (Phase 0 complete) to replace the Node.js implementation, providing native E2EE support via `matrix-sdk` and `matrix-sdk-crypto` crates. Implementation has not yet started.

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
- The Rust implementation uses `matrix-sdk` / `matrix-sdk-crypto`, which include native Olm/Megolm
- Federation TLS uses step-ca certs via Caddy -- the Rust client must trust the custom CA
- Per-agent homeserver means each agent has independent key management

See [rust-matrix-mcp-server-plan.md](../../docs/rust-matrix-mcp-server-plan.md) for the full roadmap.

---

## Appendix A: Configuration File Reference

### A.1 Docker Compose (3-Container Stack)

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
      - CONTINUWUITY_SERVER_NAME=agent0-N-mhs.cybertribe.com
      - CONTINUWUITY_DATABASE_PATH=/data
      - CONTINUWUITY_PORT=6167
      - CONTINUWUITY_ALLOW_REGISTRATION=true
      - CONTINUWUITY_REGISTRATION_TOKEN=<random-token>
      - CONTINUWUITY_ALLOW_FEDERATION=true
    volumes:
      - ./mhs/continuwuity-data:/data
      - ./mhs/matrix_key.pem:/data/matrix_key.pem:ro
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

### A.2 Caddyfile

```
:8008 {
    reverse_proxy agent0-N-continuwuity:6167
}

:8448 {
    tls /etc/caddy/server.crt /etc/caddy/server.key
    reverse_proxy agent0-N-continuwuity:6167
}
```

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
# Agent container routes -- all agents on g2s
ip route add 172.23.88.1/32 via 172.23.100.121  # agent0-1 (g2s)
ip route add 172.23.89.1/32 via 172.23.100.121  # agent0-1-mhs (g2s)
ip route add 172.23.88.2/32 via 172.23.100.121  # agent0-2 (g2s)
ip route add 172.23.89.2/32 via 172.23.100.121  # agent0-2-mhs (g2s)
ip route add 172.23.88.3/32 via 172.23.100.121  # agent0-3 (g2s)
ip route add 172.23.89.3/32 via 172.23.100.121  # agent0-3-mhs (g2s)
ip route add 172.23.88.4/32 via 172.23.100.121  # agent0-4 (g2s)
ip route add 172.23.89.4/32 via 172.23.100.121  # agent0-4-mhs (g2s)
ip route add 172.23.88.5/32 via 172.23.100.121  # agent0-5 (g2s)
ip route add 172.23.89.5/32 via 172.23.100.121  # agent0-5-mhs (g2s)
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
docker exec agent0-N ps aux | grep -E 'http-server.js|run-matrix-bot.sh|matrix-bot-rust|matrix_bot.py' | grep -v grep

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
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | grep -c 'name'

# Full service restart
docker exec agent0-N bash /a0/usr/workdir/startup-services.sh

# API token refresh
docker exec agent0-N bash /a0/usr/workdir/startup-patch.sh

# Token sync check
docker exec agent0-N python3 /a0/usr/workdir/check-token-sync.py
```

### Continuwuity Homeserver

```bash
# CS API health (via Caddy)
curl -s http://172.23.89.N:8008/_matrix/client/versions | python3 -m json.tool

# Federation API health (TLS via Caddy)
curl -sk https://agent0-N-mhs.cybertribe.com:8448/_matrix/federation/v1/version

# Signing keys
curl -sk https://agent0-N-mhs.cybertribe.com:8448/_matrix/key/v2/server | python3 -m json.tool

# Continuwuity logs
docker logs agent0-N-continuwuity --tail=50

# Caddy logs
docker logs agent0-N-mhs --tail=50
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

# macvlan verification (all 5 agents)
for N in 1 2 3 4 5; do ping -c 1 -W 1 172.23.88.$N && echo "agent0-$N OK" || echo "agent0-$N FAIL"; done
for N in 1 2 3 4 5; do ping -c 1 -W 1 172.23.89.$N && echo "agent0-$N-mhs OK" || echo "agent0-$N-mhs FAIL"; done

# mac0 bridge
ip addr show mac0
systemctl status agent-bridge.service
```

### Certificates

```bash
# step-ca health (on tarnover)
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

*Last updated: March 16, 2026*
