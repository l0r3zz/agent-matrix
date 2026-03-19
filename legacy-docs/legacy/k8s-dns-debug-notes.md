# K8s Cluster DNS Debug Notes — 2026-02-15

## Cluster Topology

| Node | Role          | Internal IP       | Status | K8s Version |
|------|---------------|-------------------|--------|-------------|
| k8-0 | control-plane | 144.126.131.105   | Ready  | v1.35.1     |
| k8-1 | worker        | 207.244.225.169   | Ready  | v1.35.1     |
| k8-2 | worker        | 207.244.237.219   | Ready  | v1.35.1     |

- **CNI:** Cilium (agent 1/1 Ready on all 3 nodes)
- **kube-proxy:** Running on all 3 nodes (still installed alongside Cilium)
- **Container runtime:** containerd 1.7.28
- **OS:** Ubuntu 24.04.4 LTS, kernel 6.8.0-100-generic

---

## Step 1: CoreDNS / kube-dns Service & Endpoints

### Service: `kube-dns` (kube-system)

| Field         | Value                     |
|---------------|---------------------------|
| ClusterIP     | **10.96.0.10**            |
| Type          | ClusterIP                 |
| Selector      | `k8s-app=kube-dns`        |
| Port dns      | **53/UDP** → targetPort 53 |
| Port dns-tcp  | **53/TCP** → targetPort 53 |
| Port metrics  | 9153/TCP → targetPort 9153 |

### Endpoints: `kube-dns`

| Pod Name                     | Pod IP         | Node | Ports            |
|------------------------------|----------------|------|------------------|
| coredns-7d764666f9-qw944    | 10.200.0.175   | k8-0 | 53/UDP, 53/TCP, 9153/TCP |
| coredns-7d764666f9-vdpsf    | 10.200.0.201   | k8-0 | 53/UDP, 53/TCP, 9153/TCP |

**FINDING:** Both CoreDNS endpoints reside on **k8-0 only** (control-plane).
Endpoints are **NOT** spread across worker nodes.
Any pod on k8-1 or k8-2 must route cross-node to reach CoreDNS.

### CoreDNS Corefile (ConfigMap `coredns`)

```
.:53 {
    errors
    health { lameduck 5s }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf { max_concurrent 1000 }
    cache 30 {
       disable success cluster.local
       disable denial cluster.local
    }
    loop
    reload
    loadbalance
}
```

Corefile looks standard — no misconfigurations apparent.

---

## Step 2: CoreDNS Pod Details

### coredns-7d764666f9-qw944

| Field        | Value                         |
|--------------|-------------------------------|
| Status       | **Running** (Ready 1/1)       |
| Pod IP       | 10.200.0.175                  |
| Host IP      | 144.126.131.105 (k8-0)       |
| Restarts     | 0                             |
| Image        | coredns/coredns:v1.13.1       |
| Started      | 2026-02-14T03:50:27Z          |

### coredns-7d764666f9-vdpsf

| Field        | Value                         |
|--------------|-------------------------------|
| Status       | **Running** (Ready 1/1)       |
| Pod IP       | 10.200.0.201                  |
| Host IP      | 144.126.131.105 (k8-0)       |
| Restarts     | 0                             |
| Image        | coredns/coredns:v1.13.1       |
| Started      | 2026-02-14T03:50:27Z          |

### CoreDNS Logs (tail)

```
CoreDNS-1.13.1
linux/amd64, go1.25.2, 1db4568
```

Clean startup, no errors logged. The pods themselves are healthy.

**FINDING:** CoreDNS is healthy and serving on k8-0. The problem is that
DNS queries from pods on k8-1/k8-2 never reach these CoreDNS pods.

---

## Step 3: Matrix Namespace — Services, Endpoints & Synapse Dependencies

### Services in `matrix` namespace

| Service Name                   | ClusterIP        | Port(s)    | Has Endpoints? |
|--------------------------------|------------------|------------|----------------|
| matrix-synapse                 | 10.103.7.3       | 80/TCP     | **NO (empty)** |
| matrix-synapse-element         | 10.104.113.164   | 80/TCP     | YES (10.200.1.204:8080) |
| matrix-synapse-postgresql      | 10.101.75.74     | 5432/TCP   | YES (10.200.1.32:5432)  |
| matrix-synapse-postgresql-hl   | None (headless)  | 5432/TCP   | YES (10.200.1.32:5432)  |

### Pods in `matrix` namespace

| Pod                                    | Status              | Ready | Node | Pod IP        | Restarts |
|----------------------------------------|---------------------|-------|------|---------------|----------|
| matrix-synapse-7c677997b9-6ncqd        | **CrashLoopBackOff**| 0/1   | k8-2 | 10.200.2.230  | **230**  |
| matrix-synapse-element-59b4565d9-zbvfl | Running             | 1/1   | k8-1 | 10.200.1.204  | 0        |
| matrix-synapse-postgresql-0            | Running             | 1/1   | k8-1 | 10.200.1.32   | 0        |
| matrix-synapse-secret-x8mf8            | Completed           | 0/1   | k8-2 | 10.200.2.58   | 0        |

### Synapse Service Dependencies

Synapse depends on:
1. **matrix-synapse-postgresql** (ClusterIP 10.101.75.74:5432) — PostgreSQL database
   - Synapse resolves hostname `matrix-synapse-postgresql` via DNS at startup
   - The PostgreSQL pod (10.200.1.32) is healthy on k8-1

### Synapse Crash Root Cause — DNS Resolution Failure

From previous container logs:

```
psycopg2.OperationalError: could not translate host name
  "matrix-synapse-postgresql" to address: Temporary failure in name resolution
```

Synapse on **k8-2** cannot resolve the DNS name `matrix-synapse-postgresql`.
This confirms DNS is broken for pods on worker nodes.

---

## Summary & Diagnosis

### What Works
- CoreDNS pods are healthy and running on k8-0
- kube-dns Service (10.96.0.10) has correct endpoints
- Cilium agents are 1/1 Ready on all nodes
- kube-proxy is running on all nodes
- Pods that don't need DNS at startup (Element, PostgreSQL) are fine

### What's Broken
- **DNS queries from pods on k8-1/k8-2 cannot reach CoreDNS on k8-0**
- Synapse (k8-2) fails to resolve `matrix-synapse-postgresql` → CrashLoopBackOff
- The `matrix-synapse` Service has empty endpoints because Synapse pod is never Ready

### Root Cause Chain
```
Pod on k8-2 → DNS query to 10.96.0.10:53 (kube-dns ClusterIP)
  → kube-proxy/Cilium should DNAT to 10.200.0.175 or 10.200.0.201 (CoreDNS on k8-0)
    → Cross-node packet delivery FAILS
      → DNS timeout → "Temporary failure in name resolution"
        → Synapse cannot connect to PostgreSQL → CrashLoopBackOff
```

---

## Resolution — 2026-02-16

### Cilium Configuration

| Setting | Value |
|---------|-------|
| Cilium version | 1.19.0 |
| Routing mode | Tunnel (VXLAN, UDP 8472) |
| Host routing | Legacy |
| KubeProxyReplacement | false (kube-proxy still running) |
| Attach mode | TCX |
| IPAM | Kubernetes |
| Pod CIDRs | k8-0: 10.200.0.0/24, k8-1: 10.200.1.0/24, k8-2: 10.200.2.0/24 |

### Phase 1 — Initial Diagnosis

Cilium cluster health from every node: **1/3 reachable** (each node could only see itself).

Cross-node connectivity tests (busybox debug pods):

| Test | Result |
|------|--------|
| DNS from k8-2 pod → ClusterIP 10.96.0.10 | TIMEOUT |
| DNS from k8-1 pod → ClusterIP 10.96.0.10 | TIMEOUT |
| DNS from k8-2 pod → CoreDNS pod IP 10.200.0.175 | TIMEOUT |
| DNS from k8-0 pod → ClusterIP 10.96.0.10 (same node) | **SUCCESS** |
| ICMP from k8-1 pod → k8-0 pod | 100% packet loss |
| ICMP from k8-1 pod → k8-2 pod | 100% packet loss |

Conclusion: **All cross-node pod-to-pod traffic was broken. Same-node worked.**

### Phase 2 — Root Cause: UFW Blocking VXLAN

#### Problem 1: FORWARD chain (policy DROP)

UFW on all nodes had:
```
Default: deny (incoming), allow (outgoing), deny (routed)
                                             ^^^^^^^^^^^^^
```

`deny (routed)` sets iptables FORWARD chain policy to DROP. Cilium VXLAN needs
forwarding for decapsulated inner packets to reach destination pods.

**Fix:** `ufw default allow routed` on all 3 nodes.

#### Problem 2: INPUT chain dropping UDP 8472 (the real killer)

This was the deceptive one. The iptables INPUT chain had `policy DROP` and the
`ufw-user-input` chain contained only TCP allow rules (6443, 10250, 22, 80, 443,
etc.) — **no UDP 8472 rule**.

The VXLAN packet lifecycle on the receiving node:
```
1. UDP 8472 packet arrives on eth0              ← tcpdump sees it here
2. cil_from_netdev BPF on eth0 → TC_ACT_OK     ← passes through
3. iptables INPUT chain evaluates:
   - CILIUM_INPUT: no match (not proxy traffic)
   - KUBE-* chains: no match
   - ufw-before-input: RELATED,ESTABLISHED → no match (UNTRACKED)
   - ufw-user-input: only TCP rules → no match
   - ufw-after-input, ufw-reject-input: no match
   - DEFAULT POLICY → DROP                     ← killed here
4. Packet never reaches VXLAN kernel socket
5. No decapsulation → nothing on cilium_vxlan   ← tcpdump sees 0 packets
```

#### Why it was deceptive

Cilium injects its own nftables rule: `udp dport 8472 accept`. Running
`nft list ruleset | grep 8472` showed this rule **counting packets** (355
accepted), making it appear VXLAN was allowed through the firewall.

But in the nf_tables framework, the iptables INPUT chain and Cilium's nftables
chain evaluate **independently**. An ACCEPT in Cilium's chain does NOT prevent
the iptables INPUT chain from dropping the same packet. Both chains must accept
for the packet to be delivered.

**Fix:** `ufw allow 8472/udp` on all 3 nodes.

#### Verification method: simultaneous tcpdump

The definitive diagnostic was running both captures concurrently on k8-0:
```bash
tcpdump -i cilium_vxlan -nn -c 5 &
tcpdump -i eth0 udp port 8472 -nn -c 5
```

Result: eth0 showed VXLAN packets arriving from k8-1 and k8-2, but
cilium_vxlan showed **only outgoing** packets (encapsulation worked, decapsulation
did not). This proved packets were being consumed between eth0 and the VXLAN socket.

### Phase 3 — Additional Fix: Cilium Health Probes

Cilium node-to-node health probes use TCP 4240 between cilium-health endpoints.
After fixing VXLAN, cluster health showed `Endpoints: 1/1` but `Node: 0/1`.

**Fix:** `ufw allow 4240/tcp` on all 3 nodes.

Final result: **Cluster health 3/3 reachable.**

### Phase 4 — Synapse Recovery

After DNS was restored, deleted the CrashLoopBackOff Synapse pod. The replacement
pod resolved `matrix-synapse-postgresql` successfully, connected to PostgreSQL on
k8-1, and reached **Running 1/1** with zero restarts.

### Known Issue Encountered: Cilium #44194 — Stale TCX BPF Programs

During debugging, `kubectl rollout restart daemonset/cilium` was used. Cilium 1.19
with TCX attachment mode has a bug where BPF programs on `cilium_vxlan` are NOT
cleaned up when the agent pod terminates. The new pod cannot replace them.

**Detection:** Run `bpftool net show` and compare `prog_id` values. If
`cilium_vxlan` has lower prog_ids than `eth0` or `lxc*` interfaces, the overlay
programs are stale.

**Workaround:** Before restarting Cilium, detach the stale links:
```bash
# Find stale link IDs on cilium_vxlan
bpftool net show | grep cilium_vxlan
# Detach them
bpftool link detach id <ingress_link_id>
bpftool link detach id <egress_link_id>
```

**Permanent fix:** Set `bpf.enableTCX: false` in Cilium Helm values to use
traditional TC attachment, which handles cleanup correctly.

Reference: https://github.com/cilium/cilium/issues/44194

### Summary of all UFW rules applied

All nodes:
```bash
ufw default allow routed       # FORWARD chain: allow pod traffic forwarding
ufw allow 8472/udp             # INPUT chain: allow VXLAN tunnel decapsulation
ufw allow 4240/tcp             # INPUT chain: allow Cilium health probes
```

### Future Recommendations

1. **Remove kube-proxy:** With Cilium as CNI, kube-proxy is redundant. Enable
   `kubeProxyReplacement: true` in Cilium Helm values and delete the kube-proxy
   DaemonSet to eliminate dual-stack iptables complexity.

2. **Fix Cilium #44194:** Set `bpf.enableTCX: false` until Cilium patches the
   TCX cleanup bug, to prevent stale BPF programs after agent restarts.

3. **Spread CoreDNS across nodes:** Both CoreDNS pods are on k8-0. Consider
   adding a pod anti-affinity rule to the CoreDNS Deployment to spread replicas
   across nodes for resilience.
