# Synapse on matrix.v-site.net:  Operational Testing, Configuration & Networking Guide

**Date:** February 16, 2026  
**Environment:** Contabo K8s cluster  MetalLB + Traefik Cilium CNI  
**Domain:** matrix.v-site.net · User IDs: `@user:matrix.v-site.net`  
**VPN:** OpenVPN server on DD-WRT at `port.nexsys.net` (DNSexit dynamic DNS)  
**Home Lab CIDR:** 172.23.0.0/16  
**Internal PKI:** Private CA signing all home-lab server certificates  

---

## Table of Contents

1. [Smoke-Testing Your Synapse Instance](#1-smoke-testing-your-synapse-instance)
1b. [TLS Certificate Management (cert-manager + Let's Encrypt)](#1b-tls-certificate-management-cert-manager--lets-encrypt)
1c. [Federation DNS Delegation (SRV Records)](#1c-federation-dns-delegation-srv-records)
1d. [Privacy & Federation Hardening (homeserver.yaml overlay)](#1d-privacy--federation-hardening-homeserveryaml-overlay)
1e. [Ingress Lockdown (Client-Only Public Access)](#1e-ingress-lockdown-client-only-public-access)
1f. [OpenVPN Sidecar Deployment](#1f-openvpn-sidecar-deployment)
2. [Synapse & Matrix Documentation — Theory of Operation](#2-synapse--matrix-documentation--theory-of-operation)
3. [Federation & Privacy Configuration](#3-federation--privacy-configuration)
   - 3A. External clients, no public federation
   - 3B. Private rooms only
   - 3C. Federation only with home-lab homeservers via VPN
4. [Dual Address-Space Networking on Kubernetes](#4-dual-address-space-networking-public--private-on-kubernetes)
5. [Complete homeserver.yaml Reference Snippet](#5-complete-homeserveryaml-reference-snippet)
6. [Open Items & Next Steps](#6-open-items--next-steps)

---

## 1. Smoke-Testing Your Synapse Instance

Run these checks in order. If all pass, Synapse is fully operational at the Client-Server and Admin API levels.

### Step 1 — Health & Version (no auth)

```bash
# Basic liveness — should return 200 OK with body "OK"
# /health was added to the Ingress as an Exact path rule (not in the Helm chart default)
curl -s -o /dev/null -w "%{http_code}" https://matrix.v-site.net/health

# Server version (Client-Server API) — works through Ingress
curl -s https://matrix.v-site.net/_matrix/client/versions | jq .

# Federation endpoint version (proves federation listener is up) — works through Ingress
curl -s https://matrix.v-site.net/_matrix/federation/v1/version | jq .
```

### Step 2 — Register an Admin User (admin-only registration)

Since public registration is disabled (`enable_registration: false`), create the first user from inside the Synapse pod:

```bash
# NOTE: The Helm chart (matrix-2.9.14) generates the final config at startup
# by merging /etc/synapse/config/homeserver.yaml (ConfigMap) with PG creds
# and writing the result to /tmp/synapse.yaml.  There is NO /data/homeserver.yaml.
kubectl exec -it <synapse-pod> -n matrix -- \
  register_new_matrix_user \
    -c /tmp/synapse.yaml \
    -u admin -p '<strong-password>' -a \
    http://localhost:8008
```

The `-a` flag grants server-admin privileges. This uses the `registration_shared_secret` in the generated config and works regardless of the `enable_registration` setting. The trailing `http://localhost:8008` is required because the container's Synapse listener is on port 8008 (not the default 8448).

### Step 3 — Login and Obtain an Access Token

```bash
curl -s -X POST https://matrix.v-site.net/_matrix/client/v3/login \
  -H "Content-Type: application/json" \
  -d '{
    "type": "m.login.password",
    "user": "admin",
    "password": "<strong-password>"
  }' | jq .
```

Save the returned `access_token`. Export it for convenience:

```bash
export TOKEN="syt_<your_token_here>"
```

### Step 4 — Create a Room, Send a Message, Read It Back

```bash
# Create a private room
ROOM=$(curl -s -X POST https://matrix.v-site.net/_matrix/client/v3/createRoom \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"preset":"private_chat","name":"smoke-test"}' | jq -r '.room_id')

echo "Room ID: $ROOM"

# Send a message
curl -s -X PUT \
  "https://matrix.v-site.net/_matrix/client/v3/rooms/$ROOM/send/m.room.message/txn001" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"msgtype":"m.text","body":"Hello from curl — smoke test!"}'

# Read it back via sync (last 1 message)
curl -s "https://matrix.v-site.net/_matrix/client/v3/sync?filter=%7B%22room%22%3A%7B%22timeline%22%3A%7B%22limit%22%3A1%7D%7D%7D" \
  -H "Authorization: Bearer $TOKEN" | jq '.rooms.join'
```

### Step 5 — Admin API Sanity

```bash
# List registered users
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://matrix.v-site.net/_synapse/admin/v2/users?from=0&limit=10" | jq .

# Server version via admin API
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://matrix.v-site.net/_synapse/admin/v1/server_version" | jq .
```

### Step 6 — External Validation (Optional)

Before locking down federation, verify public reachability with the Matrix Federation Tester:

```bash
# Use server_name (v-site.net), NOT the delegated host (matrix.v-site.net)
curl -s https://federationtester.matrix.org/api/report?server_name=v-site.net | jq .
```

This confirms DNS, SRV delegation, TLS, and federation endpoint availability. Note: the tester
first tries `.well-known` on `v-site.net`, then falls back to SRV records.

**Last run (Feb 19, 2026):** `FederationOK: true` — `.well-known` delegation working,
TLS valid (Let's Encrypt R12 / ISRG Root X1), Ed25519 signing key valid, Synapse 1.147.1.

### Summary: If All Pass

| Check | What It Proves |
|---|---|
| `/health` → 200 | Synapse process is alive, Traefik routing works |
| `/_matrix/client/versions` | Client-Server API reachable through TLS/ingress |
| `/_matrix/federation/v1/version` | Federation listener is up |
| `register_new_matrix_user` succeeds | Database writes work, shared secret is correct |
| Login returns `access_token` | Auth pipeline & database reads work |
| Room create + send + sync | Full DAG pipeline: event creation, signing, storage, retrieval |
| Admin API returns users | Admin role is granted, admin endpoints are routed |

---

## 1b. TLS Certificate Management (cert-manager + Let's Encrypt)

Installed **cert-manager v1.19.3** to automate TLS certificate issuance and renewal
via Let's Encrypt. This replaces Traefik's default self-signed certificate.

### What Was Deployed

```bash
# cert-manager (CRDs + controller + webhook + cainjector)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.19.3/cert-manager.yaml
```

### ClusterIssuer (Let's Encrypt production)

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@v-site.net
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - http01:
        ingress:
          ingressClassName: traefik
```

### Ingress Changes

Two changes were applied to the `matrix-synapse` Ingress in the `matrix` namespace:

1. **Annotation:** `cert-manager.io/cluster-issuer: letsencrypt-prod`
2. **TLS secretName:** `matrix-synapse-tls` added to the existing `tls:` block

cert-manager automatically creates a `Certificate` resource, performs the HTTP-01
challenge via a temporary Ingress, and stores the signed cert + key in Secret
`matrix-synapse-tls`. Traefik picks it up immediately — both replicas read the
same Secret.

### Verify / Troubleshoot

```bash
# Certificate status (READY should be True)
kubectl get certificate -n matrix

# Inspect certificate details
kubectl describe certificate matrix-synapse-tls -n matrix

# Check for failed challenges
kubectl get challenges -n matrix

# View cert-manager controller logs
kubectl logs -n cert-manager -l app=cert-manager --tail=30
```

Certificates auto-renew ~30 days before expiry. No manual intervention needed.

---

## 1c. Federation DNS Delegation (SRV Records)

### The Problem

Synapse's `server_name` is `v-site.net` (user IDs are `@user:v-site.net`), but Synapse
runs on `matrix.v-site.net` (the K8s cluster at 147.93.135.115). Federation peers need
to discover this delegation.

### Solution: `.well-known` Delegation via Caddy on v-site.net

The Matrix spec's preferred delegation method is `.well-known`. A minimal Caddy instance
on `v-site.net` (92.243.27.73) serves the delegation file over HTTPS:

```
https://v-site.net/.well-known/matrix/server → {"m.server":"matrix.v-site.net:443"}
```

**Setup on 92.243.27.73 (precipice):**

```bash
# /etc/caddy/Caddyfile
v-site.net {
    root * /var/www
    file_server
}

# /var/www/.well-known/matrix/server
{"m.server":"matrix.v-site.net:443"}
```

Caddy auto-provisions and auto-renews a Let's Encrypt TLS cert for `v-site.net`.
Ports 80 and 443 must be open in the firewall for ACME and HTTPS.

**Why `.well-known` over SRV:** SRV delegation requires the K8s cluster to present a
TLS cert valid for `v-site.net` (the server_name), which would require DNS-01 challenges
via the Gandi API. `.well-known` delegation only requires a cert for `matrix.v-site.net`
(the delegated host), which HTTP-01 handles easily since that domain points to the cluster.

### DNS SRV Records (fallback)

SRV records are also configured as a fallback. The SRV target MUST be an A record
(not a CNAME — forbidden by RFC 2782). `matrix.v-site.net` was changed from
`CNAME k-ingress.v-site.net` to `A 147.93.135.115` for this reason.

```
_matrix._tcp.v-site.net.      3600  IN  SRV  0 0 443 matrix.v-site.net.
_matrix-fed._tcp.v-site.net.  3600  IN  SRV  0 0 443 matrix.v-site.net.
```

### Current DNS Layout

| Record                           | Type | Value                      |
|----------------------------------|------|----------------------------|
| `v-site.net`                     | A    | 92.243.27.73 (Caddy for .well-known) |
| `matrix.v-site.net`             | A    | 147.93.135.115 (K8s/MetalLB) |
| `k-ingress.v-site.net`          | A    | 147.93.135.115 (K8s/MetalLB) |
| `_matrix._tcp.v-site.net`       | SRV  | 0 0 443 matrix.v-site.net  |
| `_matrix-fed._tcp.v-site.net`   | SRV  | 0 0 443 matrix.v-site.net  |

### Verify

```bash
# .well-known delegation (should return instantly)
curl -s https://v-site.net/.well-known/matrix/server
# Expected: {"m.server":"matrix.v-site.net:443"}

# matrix.v-site.net must be an A record (no CNAME)
dig matrix.v-site.net +short
# Expected: 147.93.135.115

# Federation tester
curl -s https://federationtester.matrix.org/api/report?server_name=v-site.net | jq .
# Look for: "FederationOK": true
```

---

## 1d. Privacy & Federation Hardening (homeserver.yaml overlay)

Applied **Feb 19, 2026** by patching the `matrix-synapse` ConfigMap in the `matrix`
namespace, then restarting the Synapse deployment.

### Settings Added

| Setting | Value | Purpose |
|---|---|---|
| `allow_public_rooms_without_auth` | `false` | No unauthenticated room directory browsing |
| `allow_profile_lookup_over_federation` | `false` | Don't leak user profiles to federated servers |
| `allow_device_name_lookup_over_federation` | `false` | Don't leak device names to federated servers |
| `enable_room_list_search` | `false` | Room directory search disabled |
| `room_list_publication_rules` | deny-all (see below) | No rooms appear in public directory |
| `ip_range_whitelist` | `172.23.0.0/16`, `10.8.0.0/24` | Pre-whitelisted for future VPN federation |
| `suppress_key_server_warning` | `true` | Suppress trusted key server warning |

The `room_list_publication_rules` deny-all rule:

```yaml
room_list_publication_rules:
  - user_id: "*"
    alias: "*"
    room_id: "*"
    action: deny
```

The email `notif_from` was also corrected from the Helm default (`matrix@example.org`)
to `admin@v-site.net`.

### How to Apply / Reproduce

```bash
# Patch the ConfigMap
kubectl patch configmap matrix-synapse -n matrix --type merge -p '{"data":{"homeserver.yaml":"..."}}'

# Restart to pick up changes
kubectl rollout restart deployment matrix-synapse -n matrix

# Verify settings in the merged config
kubectl exec -n matrix <synapse-pod> -- \
  grep -A2 'room_list_publication_rules\|ip_range_whitelist\|allow_profile_lookup\|enable_room_list_search\|suppress_key_server' /tmp/synapse.yaml
```

---

## 1e. Ingress Lockdown (Client-Only Public Access)

Applied **Feb 19, 2026** by replacing the broad `/_matrix` and `/_synapse` Ingress
path prefixes with narrower, client-only paths.

### Before (Helm default)

| Path | PathType | Exposes |
|---|---|---|
| `/_matrix` | Prefix | Client API, Federation API, Key endpoints |
| `/_synapse` | Prefix | Client endpoints, Admin API |
| `/.well-known/matrix` | Prefix | Client/server discovery |
| `/health` | Exact | Health check |

### After (locked down)

| Path | PathType | Exposes |
|---|---|---|
| `/_matrix/client` | Prefix | Client-Server API only |
| `/_synapse/client` | Prefix | Synapse client endpoints only |
| `/.well-known/matrix` | Prefix | Client/server discovery |
| `/health` | Exact | Health check |

### What's Now Blocked from the Public Internet

| Endpoint | HTTP Status | Notes |
|---|---|---|
| `/_synapse/admin/*` | 404 | Admin API (use `kubectl exec` or port-forward) |

> **Update (Feb 22):** `/_matrix/federation` and `/_matrix/key` paths were
> **re-added** to the Ingress when agent federation was enabled in Phase 1.
> These endpoints are required for Dendrite homeservers to federate with
> Synapse. The `federation_domain_whitelist` provides application-layer
> protection (only whitelisted domains can federate). Consider adding a
> Traefik `IPAllowList` middleware to restrict these paths to VPN source IPs
> only (see Section 3C for the pattern).

### Verification

```bash
# These should return 200
curl -s -o /dev/null -w "%{http_code}" https://matrix.v-site.net/health
curl -s -o /dev/null -w "%{http_code}" https://matrix.v-site.net/_matrix/client/versions
curl -s -o /dev/null -w "%{http_code}" https://matrix.v-site.net/.well-known/matrix/client

# These should return 404
curl -s -o /dev/null -w "%{http_code}" https://matrix.v-site.net/_matrix/federation/v1/version
curl -s -o /dev/null -w "%{http_code}" https://matrix.v-site.net/_matrix/key/v2/server
curl -s -o /dev/null -w "%{http_code}" https://matrix.v-site.net/_synapse/admin/v1/server_version
```

**Note:** Login (`/_matrix/client/v3/login`) remains fully accessible from the internet.
The Admin API can still be reached internally via `kubectl exec` or `kubectl port-forward`.

---

## 1f. OpenVPN Sidecar Deployment

Deployed **Feb 20, 2026**. An OpenVPN client sidecar runs alongside Synapse in the same
pod, providing a VPN tunnel to the home lab at `172.23.0.0/16` via the DD-WRT router at
`port.nexsys.net`.

### PKI

Client certificate issued by step-ca (CyberTribe CA) with 1-year validity:

```bash
step ca certificate contabo-synapse.cybertribe.com contabo-synapse.crt contabo-synapse.key
```

Cert valid: Feb 20, 2026 → Feb 20, 2027. Issued by `CyberTribe CA Intermediate CA`.

### Client .ovpn Config

Key directives in `contabo-synapse.ovpn`:

```conf
client
dev tun
proto udp
remote port.nexsys.net 1194
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-CBC
auth SHA256
keepalive 10 60
verb 3
route-nopull
route 172.23.0.0 255.255.0.0 vpn_gateway
```

**Critical:** `route-nopull` is required because the DD-WRT server pushes
`redirect-gateway def1` which would route ALL pod traffic through the VPN, breaking
cluster networking. With `route-nopull`, only `172.23.0.0/16` goes through the tunnel;
all other traffic (public internet, cluster services) uses the normal pod routes.

The `<ca>`, `<cert>`, and `<key>` blocks are embedded inline (same structure as the
test-client.ovpn). The `<ca>` contains the CyberTribe CA Root CA; the `<cert>` contains
the leaf cert + intermediate CA chain.

### K8s Secret

```bash
kubectl create secret generic openvpn-client-config \
  --from-file=client.ovpn=contabo-synapse.ovpn \
  -n matrix
```

### Deployment Patch

The sidecar was added via strategic merge patch on the `matrix-synapse` Deployment:

```bash
kubectl patch deployment matrix-synapse -n matrix --type strategic -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "openvpn",
          "image": "alpine:3.19",
          "command": ["sh", "-c"],
          "args": ["apk add --no-cache openvpn && mkdir -p /dev/net && [ -c /dev/net/tun ] || mknod /dev/net/tun c 10 200 && exec openvpn --config /vpn/client.ovpn"],
          "securityContext": {"capabilities": {"add": ["NET_ADMIN"]}},
          "resources": {"requests": {"cpu": "10m", "memory": "32Mi"}, "limits": {"cpu": "100m", "memory": "64Mi"}},
          "volumeMounts": [{"name": "vpn-config", "mountPath": "/vpn", "readOnly": true}]
        }],
        "volumes": [{"name": "vpn-config", "secret": {"secretName": "openvpn-client-config"}}]
      }
    }
  }
}'
```

The sidecar shares the pod's network namespace with Synapse. When OpenVPN creates `tun0`
and adds routes, they are visible to the Synapse container automatically.

### Verification

```bash
POD=$(kubectl get pod -n matrix -l app.kubernetes.io/name=matrix -o jsonpath='{.items[0].metadata.name}')

# Both containers should be ready (2/2)
kubectl get pod -n matrix "$POD"

# Check OpenVPN logs — look for "Initialization Sequence Completed"
kubectl logs -n matrix "$POD" -c openvpn --tail=15

# Ping VPN gateway from openvpn container
kubectl exec -n matrix "$POD" -c openvpn -- ping -c 3 172.23.200.1

# Ping LAN host from openvpn container
kubectl exec -n matrix "$POD" -c openvpn -- ping -c 3 172.23.1.1

# Verify Synapse container can also reach the home lab (shared network namespace)
kubectl exec -n matrix "$POD" -c matrix -- python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
try:
    s.connect(('172.23.1.1', 53))
    print('Home lab reachable from Synapse!')
except Exception as e:
    print(f'Failed: {e}')
finally:
    s.close()
"

# Confirm public access still works (not broken by VPN routes)
curl -s -o /dev/null -w "%{http_code}" https://matrix.v-site.net/health
curl -s -o /dev/null -w "%{http_code}" https://matrix.v-site.net/_matrix/client/versions
```

### Working State (Feb 20, 2026)

| Item | Value |
|---|---|
| VPN server | `port.nexsys.net:1194` (DD-WRT, `kama.cybertribe.com`) |
| Pod VPN IP | `172.23.200.x/24` on `tun0` |
| VPN gateway | `172.23.200.1` |
| Route via tunnel | `172.23.0.0/16` only |
| TLS | v1.3, AES-256-GCM |
| Public access | Intact (health 200, client API 200) |
| Lab access | TCP to `172.23.1.1:53` succeeds from Synapse container |

### Gotcha: `redirect-gateway def1`

The DD-WRT server pushes `redirect-gateway def1` to all clients, which installs
`0.0.0.0/1` and `128.0.0.0/1` routes through the VPN — effectively routing ALL traffic
through the tunnel. This breaks Kubernetes cluster networking (service IPs, pod CIDR,
DNS). The fix is `route-nopull` in the client config. If you need the server to stop
pushing this to all clients, remove `redirect-gateway def1` from the DD-WRT OpenVPN
additional config.

---

## 2. Synapse & Matrix Documentation — Theory of Operation

### Conceptual / Architecture

| Resource | URL | What It Covers |
|---|---|---|
| **Matrix Specification** | https://spec.matrix.org | Authoritative source: event DAGs, room structure, federation model, Client-Server & Server-Server APIs, eventual consistency |
| **Matrix Concepts** | https://matrix.org/docs/matrix-concepts/elements-of-matrix/ | Gentler intro: homeservers, rooms, events, federation |

**Key mental model:** Every Matrix room is a **replicated DAG (Directed Acyclic Graph) of cryptographically signed JSON events** shared across all participating homeservers. State events (membership, room name, power levels) are resolved deterministically via the *state resolution algorithm* regardless of event arrival order. This is what makes Matrix eventually consistent and partition-tolerant.

### Synapse-Specific Documentation

| Resource | URL | What It Covers |
|---|---|---|
| **Synapse Welcome & Overview** | https://element-hq.github.io/synapse/latest/welcome_and_overview.html | Installation, upgrade, workers, modules |
| **Configuration Manual** ⭐ | https://element-hq.github.io/synapse/latest/usage/configuration/config_documentation.html | **Every** `homeserver.yaml` option with defaults and examples |
| **Sample homeserver.yaml** | https://matrix-org.github.io/synapse/latest/usage/configuration/homeserver_sample_config.html | Full annotated config for reference |
| **Admin API** | https://element-hq.github.io/synapse/latest/usage/administration/admin_api/ | REST endpoints for user/room/server management |
| **Workers & Scalability** | https://element-hq.github.io/synapse/latest/workers.html | Splitting Synapse into multiple processes |
| **Modules API** | https://element-hq.github.io/synapse/latest/modules/ | Pluggable Python modules for auth, spam, room rules |
| **GitHub (source)** | https://github.com/element-hq/synapse | Issue tracker, release notes, Dockerfile |

### For Expanding Your Deployment

- **Modules API**: Custom Python modules for auth callbacks, spam filtering, room-creation rules. Hooks like `check_event_allowed` let you enforce policies (e.g., reject any room with `join_rule: public`).
- **Application Service API**: For bridges and bots that puppet users or act on behalf of multiple accounts. Defined in the Matrix spec.
- **Room Versions**: Control the state resolution algorithm and event format. Default is currently v10. Understanding these matters when federating between different homeserver implementations (Synapse, Dendrite, Conduit).

---

## 3. Federation & Privacy Configuration

Your requirements decompose into three policy layers:

### 3A — External Clients Connect; No Public Internet Federation

External clients (Element Web, FluffyChat, etc.) connect via the Client-Server API (`/_matrix/client/...`). This is **completely independent** of federation. You can serve clients while blocking all federation.

#### homeserver.yaml settings

```yaml
# ── Federation lockdown ──────────────────────────────────────
# Empty list = federate with NO ONE
federation_domain_whitelist: []

# Don't serve room directory over federation
allow_public_rooms_over_federation: false

# Don't allow unauthenticated room directory browsing
allow_public_rooms_without_auth: false

# Don't leak user profiles over federation
allow_profile_lookup_over_federation: false
allow_device_name_lookup_over_federation: false
```

Setting `federation_domain_whitelist` to `[]` effectively **disables all outbound and inbound federation** at the application layer. Remote servers that attempt to connect will be rejected.

#### Traefik Ingress — Belt-and-Suspenders

As an additional layer, configure your Traefik `IngressRoute` to **only expose client paths** to the public internet and block federation paths entirely:

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: synapse-public
  namespace: matrix
spec:
  entryPoints:
    - websecure
  routes:
    # Client-Server API — open to the internet
    - match: Host(`matrix.v-site.net`) && PathPrefix(`/_matrix/client`)
      kind: Rule
      services:
        - name: synapse
          port: 8008
    # Synapse client-side endpoints
    - match: Host(`matrix.v-site.net`) && PathPrefix(`/_synapse/client`)
      kind: Rule
      services:
        - name: synapse
          port: 8008
    # Health check
    - match: Host(`matrix.v-site.net`) && PathPrefix(`/health`)
      kind: Rule
      services:
        - name: synapse
          port: 8008
    # Admin API — consider restricting by source IP or removing from public
    # - match: Host(`matrix.v-site.net`) && PathPrefix(`/_synapse/admin`)
    #   kind: Rule
    #   services:
    #     - name: synapse
    #       port: 8008
  tls:
    certResolver: letsencrypt  # adjust to your cert-manager setup
```

**Note:** `/_matrix/federation` and `/_matrix/key` paths are deliberately **absent** — Traefik will return 404 for any federation probes from the public internet. This firewall-level block is the recommended complement to the application-layer whitelist.

### 3B — Private Rooms Only (All Users)

Synapse doesn't have a single "private rooms only" toggle, but you can achieve it with these settings:

```yaml
# ── Private rooms enforcement ────────────────────────────────
# Block ALL rooms from appearing in the public room directory
room_list_publication_rules:
  - user_id: "*"
    alias: "*"
    room_id: "*"
    action: deny

# Disable room directory search
enable_room_list_search: false
```

This means:
- No room will ever appear in a public directory listing
- The room directory search endpoint returns nothing
- All rooms are effectively discoverable only by direct invite

**For stricter enforcement** (blocking the `public_chat` preset entirely), write a Synapse module with a `check_event_allowed` callback that rejects `m.room.create` events where `join_rule` is `public`. This is documented in the Modules API.

### 3C — Federation ONLY with Home-Lab Homeservers (via VPN)

When you bring up future homeservers (Dendrite, Conduit, etc.) on the `172.23.0.0/16` network reachable via VPN, whitelist them explicitly:

```yaml
# ── Selective lab federation ─────────────────────────────────
federation_domain_whitelist:
  - synapse.home        # Home-lab Synapse
  - conduit.home        # Home-lab Conduit
  - dendrite.home       # Home-lab Dendrite
  # Add future VPN-accessible servers here

# CRITICAL: Synapse blocks RFC 1918 IPs by default.
# You MUST whitelist your VPN/lab subnets or federation will silently fail.
ip_range_whitelist:
  - '172.23.0.0/16'     # Home-lab network
  - '10.8.0.0/24'       # OpenVPN tunnel subnet (adjust to your tun0 config)
```

#### Internal CA Configuration

Since your home-lab servers use certificates signed by your private CA, configure Synapse to trust that CA **for federation traffic**:

```yaml
# ── Internal CA trust ────────────────────────────────────────
# IMPORTANT: This REPLACES the system CA bundle for federation.
# You must include BOTH your internal CA AND any public CAs you need.
# For your use case (no public federation), just the internal CA is fine.
federation_custom_ca_list:
  - /etc/synapse/certs/home-lab-ca.pem

# Keep certificate verification enabled (default is true)
federation_verify_certificates: true
```

**⚠️ Critical caveat:** `federation_custom_ca_list` **replaces** the operating system's CA bundle for federation connections. Since you've disabled public federation (`federation_domain_whitelist` only contains `.home` domains), this is fine — Synapse only needs to verify your internal CA. If you ever re-enable limited public federation, you'll need to bundle your internal CA with the system CAs into a single PEM file.

**⚠️ CA bundle must include root CA (Feb 22 lesson):** The `home-lab-ca` K8s secret
must contain the **root CA + intermediate CA** bundle, not the intermediate alone.
Python's Twisted TLS library requires the root CA as a trust anchor. The server
(Dendrite) sends the leaf + intermediate in the TLS handshake; Synapse's trust store
must contain the root to complete the chain. With intermediate-only, you get
`certificate verify failed` errors even though `curl --cacert` works fine (curl is
more lenient about trust anchors).

```bash
# Create the correct CA bundle
cat root_ca.crt intermediate_ca.crt > home-lab-ca-bundle.pem

# Update the K8s secret
kubectl create secret generic home-lab-ca -n matrix \
  --from-file=home-lab-ca.pem=home-lab-ca-bundle.pem \
  --dry-run=client -o yaml | kubectl apply -f -
```

**Mounting the CA into the pod:**

```yaml
# In your Synapse Deployment spec:
volumes:
  - name: internal-ca
    secret:
      secretName: home-lab-ca  # kubectl create secret generic home-lab-ca --from-file=home-lab-ca.pem=./ca.pem
containers:
  - name: synapse
    volumeMounts:
      - name: internal-ca
        mountPath: /etc/synapse/certs
        readOnly: true
```

#### Traefik — Federation IngressRoute for VPN Only

Create a **second IngressRoute** that exposes federation paths only to VPN source IPs. With Traefik, use an `IPAllowList` middleware:

```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: vpn-only
  namespace: matrix
spec:
  ipAllowList:
    sourceRange:
      - "172.23.0.0/16"   # Home-lab network
      - "10.8.0.0/24"     # OpenVPN tunnel subnet
---
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: synapse-federation-vpn
  namespace: matrix
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`matrix.v-site.net`) && PathPrefix(`/_matrix/federation`)
      kind: Rule
      middlewares:
        - name: vpn-only
      services:
        - name: synapse
          port: 8008
    - match: Host(`matrix.v-site.net`) && PathPrefix(`/_matrix/key`)
      kind: Rule
      middlewares:
        - name: vpn-only
      services:
        - name: synapse
          port: 8008
  tls:
    certResolver: letsencrypt
```

This ensures that even if someone discovers the federation endpoints, only traffic from VPN/lab subnets can reach them.

---

## 4. Dual Address-Space Networking (Public + Private) on Kubernetes

### The Core Challenge

Synapse in a K8s pod on Contabo must simultaneously:
- **Serve the public internet** via `matrix.v-site.net` (Client-Server API)
- **Reach and be reached by** private lab homeservers on `172.23.0.0/16` through OpenVPN

Synapse itself doesn't need dual-homing — it binds to `0.0.0.0:8008` inside its pod. The question is how the pod's network namespace gets routes to both the public internet and the VPN subnet.

### Your VPN Topology

```
DD-WRT Router (port.nexsys.net)          Contabo K8s Cluster
┌─────────────────────────────┐          ┌──────────────────────────────┐
│  OpenVPN SERVER              │          │  OpenVPN CLIENT              │
│  172.23.0.1 (LAN gateway)  │◄────────►│  tun0: 10.8.0.x             │
│  tun0: 10.8.0.1            │  tunnel   │  Routes: 172.23.0.0/16      │
│                             │          │          via tun0             │
│  Home-lab servers:          │          │                              │
│  - synapse.home 172.23.x.x │          │  Synapse pod needs to reach  │
│  - conduit.home 172.23.x.x │          │  172.23.x.x via this tunnel  │
│  - dendrite.home 172.23.x.x│          │                              │
└─────────────────────────────┘          └──────────────────────────────┘
```

The OpenVPN **server** is on your DD-WRT. The Contabo side runs an OpenVPN **client** that connects to `port.nexsys.net` and receives routes to `172.23.0.0/16`.

### Three Architectural Options for the VPN Terminus

| # | Approach | Where OpenVPN Client Runs | Pros | Cons |
|---|---|---|---|---|
| **A** | **VPN Gateway Pod** (recommended long-term) | Dedicated Deployment in the cluster | Clean separation; all cluster pods can route to VPN; Cilium egress policies give fine-grained control | Requires Cilium route/policy configuration |
| **B** | **Sidecar in Synapse pod** (recommended Phase 1) | Container in the Synapse pod | Fast to implement; tunnel is scoped to Synapse; no cluster-wide changes | Tightly couples VPN lifecycle to Synapse; other services can't use the tunnel |
| **C** | **Node-level VPN** | OpenVPN client on the K8s node itself (host network) | Simplest routing — all pods on that node see the VPN routes | Requires host access; not portable; breaks if pods move nodes |

### Recommended: Start with Option B (Sidecar), Graduate to Option A

#### Phase 1 — Sidecar Pattern

Containers in the same pod share a network namespace. The OpenVPN client creates a `tun0` interface visible to Synapse. Routes to `172.23.0.0/16` go through the tunnel automatically.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: synapse
  namespace: matrix
spec:
  replicas: 1
  selector:
    matchLabels:
      app: synapse
  template:
    metadata:
      labels:
        app: synapse
    spec:
      containers:
        # ── Synapse container ──
        - name: synapse
          image: matrixdotorg/synapse:latest
          ports:
            - containerPort: 8008
          volumeMounts:
            - name: synapse-data
              mountPath: /data
            - name: internal-ca
              mountPath: /etc/synapse/certs
              readOnly: true
          # ... resource limits, env vars, etc.

        # ── OpenVPN sidecar ──
        - name: openvpn
          image: dperson/openvpn-client:latest  # or kylemanna/openvpn
          securityContext:
            capabilities:
              add: ["NET_ADMIN"]
            # Note: some CNIs may require privileged: true
            # Try without first; Cilium usually works with just NET_ADMIN
          env:
            - name: ROUTE
              value: "172.23.0.0 255.255.0.0"
          volumeMounts:
            - name: vpn-config
              mountPath: /vpn
              readOnly: true

      volumes:
        - name: synapse-data
          persistentVolumeClaim:
            claimName: synapse-data
        - name: internal-ca
          secret:
            secretName: home-lab-ca
        - name: vpn-config
          secret:
            secretName: openvpn-client-config
            # Contains: client.ovpn, ca.crt, client.crt, client.key
            # (or a single .ovpn with inline certs)
```

**Creating the OpenVPN client secret:**

```bash
# Package your OpenVPN client config + certs into a K8s secret
kubectl create secret generic openvpn-client-config \
  --from-file=client.ovpn=./contabo-client.ovpn \
  --from-file=ca.crt=./vpn-ca.crt \
  --from-file=client.crt=./contabo.crt \
  --from-file=client.key=./contabo.key \
  -n matrix
```

**Your OpenVPN client config (`contabo-client.ovpn`) should include:**

```
client
dev tun
proto udp
remote port.nexsys.net 1194    # Your DD-WRT OpenVPN server
resolv-retry infinite
nobind
persist-key
persist-tun
ca /vpn/ca.crt
cert /vpn/client.crt
key /vpn/client.key
# Push routes from server, or define explicitly:
route 172.23.0.0 255.255.0.0
# Keep alive
keepalive 10 60
verb 3
```

#### Phase 2 — VPN Gateway Pod with Cilium

When MCP servers, monitoring, and other services need lab connectivity, extract the VPN sidecar into a standalone gateway:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vpn-gateway
  namespace: matrix
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vpn-gateway
  template:
    metadata:
      labels:
        app: vpn-gateway
    spec:
      containers:
        - name: openvpn
          image: dperson/openvpn-client:latest
          securityContext:
            capabilities:
              add: ["NET_ADMIN"]
          env:
            - name: ROUTE
              value: "172.23.0.0 255.255.0.0"
          volumeMounts:
            - name: vpn-config
              mountPath: /vpn
              readOnly: true
      volumes:
        - name: vpn-config
          secret:
            secretName: openvpn-client-config
```

**Cilium routing to the gateway:**

With Cilium as your CNI, you have powerful options for routing `172.23.0.0/16` traffic through the VPN gateway pod:

**Option 1 — CiliumEgressGatewayPolicy** (if Cilium Egress Gateway is enabled):

```yaml
apiVersion: cilium.io/v2
kind: CiliumEgressGatewayPolicy
metadata:
  name: vpn-lab-egress
spec:
  selectors:
    - podSelector:
        matchLabels:
          app: synapse         # Pods that need VPN access
  destinationCIDRs:
    - "172.23.0.0/16"          # Route lab traffic...
  egressGateway:
    nodeSelector:
      matchLabels:
        kubernetes.io/hostname: <node-running-vpn-gateway>
```

**Option 2 — CiliumNetworkPolicy + node static route:**

If Egress Gateway isn't enabled, add a static route on the node running the VPN gateway pod:

```bash
# On the K8s node (or via a DaemonSet init script):
ip route add 172.23.0.0/16 via <vpn-gateway-pod-ip>
```

Then use a `CiliumNetworkPolicy` to allow the Synapse pod to reach `172.23.0.0/16`:

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: synapse-to-lab
  namespace: matrix
spec:
  endpointSelector:
    matchLabels:
      app: synapse
  egress:
    - toCIDR:
        - "172.23.0.0/16"
    - toCIDR:
        - "10.8.0.0/24"
```

### Decision Matrix: Sidecar vs. Gateway

| Factor | Sidecar (Phase 1) | Gateway (Phase 2) |
|---|---|---|
| Time to implement | ~30 minutes | ~2-4 hours |
| Other services use VPN? | No — tunnel scoped to Synapse pod | Yes — cluster-wide routing |
| VPN restart impact | Restarts Synapse pod (shared lifecycle) | Only VPN pod restarts |
| Cilium config needed? | None | Egress Gateway Policy or static routes |
| Good enough for now? | **Yes** | Needed when MCP servers, monitoring, etc. need lab access |

---

## 5. Complete homeserver.yaml Reference Snippet

This is a consolidated snippet of all the settings discussed above. Merge into your existing `homeserver.yaml`:

```yaml
# ═══════════════════════════════════════════════════════════════
# matrix.v-site.net — Synapse Configuration Overlay
# Merge these settings into your existing homeserver.yaml
# ═══════════════════════════════════════════════════════════════

# ── Server identity ──────────────────────────────────────────
server_name: "matrix.v-site.net"

# ── Registration (admin-created accounts only) ───────────────
enable_registration: false
registration_shared_secret: "<generate-a-long-random-string>"
# Use: register_new_matrix_user -c /data/homeserver.yaml -u <user> -p <pass> [-a]

# ── Federation lockdown (Phase 1: no federation) ─────────────
# Change to explicit domain list when ready for lab federation
federation_domain_whitelist: []

# When ready for lab federation, replace the above with:
# federation_domain_whitelist:
#   - synapse.home
#   - conduit.home
#   - dendrite.home

# ── IP range whitelist (required for private-IP federation) ──
# Synapse blocks RFC 1918 by default; whitelist your lab + VPN
ip_range_whitelist:
  - '172.23.0.0/16'
  - '10.8.0.0/24'

# ── Internal CA for federation TLS ──────────────────────────
# NOTE: This REPLACES the OS CA bundle for federation connections.
# Fine when you only federate with internal servers.
federation_custom_ca_list:
  - /etc/synapse/certs/home-lab-ca.pem

federation_verify_certificates: true

# ── Privacy: don't leak data over federation ─────────────────
allow_public_rooms_over_federation: false
allow_public_rooms_without_auth: false
allow_profile_lookup_over_federation: false
allow_device_name_lookup_over_federation: false

# ── Private rooms only ───────────────────────────────────────
room_list_publication_rules:
  - user_id: "*"
    alias: "*"
    room_id: "*"
    action: deny

enable_room_list_search: false

# ── Suppress key-server warning ──────────────────────────────
suppress_key_server_warning: true
```

---

## 6. Open Items & Next Steps

### Immediate (Phase 1)

- [x] Run the smoke-test sequence from Section 1 (Steps 1–6 passed, Feb 15–19)
- [x] TLS certificates via cert-manager + Let's Encrypt (Section 1b, Feb 17)
- [x] Federation DNS delegation via `.well-known` + Caddy (Section 1c, Feb 17–18)
- [x] Apply privacy & federation hardening overlay to homeserver.yaml (Section 1d, Feb 19)
- [x] Ingress lockdown: client-only public paths, federation/admin blocked (Section 1e, Feb 19)
- [x] OpenVPN client cert issued from step-ca for Contabo endpoint (1-year validity, Feb 20)
- [x] OpenVPN sidecar deployed in Synapse pod with split-tunnel (Section 1f, Feb 20)
- [x] VPN connectivity verified: ping 172.23.200.1 + 172.23.1.1, TCP from Synapse container

### Before Lab Federation (Phase 1.5) — COMPLETED Feb 22

- [x] Export internal CA certificate and create the `home-lab-ca` K8s secret (root+intermediate bundle)
- [x] Stand up home-lab homeserver: Dendrite 0.15.2 at `agent0-1-mhs.cybertribe.com` (172.23.89.1)
- [x] Update `federation_domain_whitelist` to `[agent0-1-mhs.cybertribe.com]`
- [x] Add `/_matrix/federation` and `/_matrix/key` to Ingress (were removed in lockdown)
- [x] Add `hostAliases` to Synapse deployment for Dendrite DNS resolution
- [x] Fix `home-lab-ca` K8s secret: must contain root+intermediate CA bundle
- [x] Test federation: room create, invite, bidirectional message delivery — **PASS**

### Phase 2

- [ ] Extract VPN sidecar into standalone gateway pod
- [ ] Configure Cilium Egress Gateway Policy for cluster-wide lab routing
- [ ] Deploy MCP servers, point them at lab + public homeservers
- [ ] Enable Prometheus metrics endpoint on Synapse for monitoring

### Admin API Endpoint Security

**Done (Section 1e):** `/_synapse/admin` is no longer exposed publicly — it returns 404
from the internet. Access via `kubectl exec` or `kubectl port-forward` only.

---

*Generated: February 16, 2026. Reference design documents: EECOM-TANK-LAB.md, tank-eecom-lab.md.*