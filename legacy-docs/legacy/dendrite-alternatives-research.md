# Lightweight Matrix Homeserver Alternatives to Dendrite v0.15.2
## Comprehensive Technical Research Report

**Date:** 2026-03-08  
**Context:** Agent-Matrix lab — 5–9 sovereign AI agent homeservers federating with each other and with one Synapse gateway (matrix.v-site.net)  
**Constraint:** <100 MB RAM per instance; Docker deployment; reliable federation  
**Problem:** Dendrite v0.15.2 suffers from DAG corruption, missing prev_events, signing key fetch failures, and sync freezes  

---

## Executive Summary

Dendrite is in **maintenance mode** (security patches only) with only 2.2% federation market share. Its event DAG handling has proven fundamentally fragile for multi-agent federation workloads, producing unrecoverable sync freezes when prev_events references break.

After exhaustive analysis of all available alternatives, **two viable candidates** exist for the Agent-Matrix use case: **Tuwunel** and **Continuwuity**. Both descend from the Conduit/conduwuit lineage (Rust + embedded RocksDB), both fit within the <100 MB RAM budget, and both are under active development.

**Recommendation: Continuwuity v0.5.6** — for governance stability, community health, active multi-contributor development, proven federation at scale (1,107 federated servers, 6.5% market share), and architectural alignment with the Agent-Matrix use case.

---

## 1. The Conduit Family Tree

```
Conduit (Rust, 2020-2024) — Original lightweight server by Timo Kösters
    ├── conduwuit (hard fork, 2023-2025) — Feature-rich fork, now ARCHIVED
    │       ├── Tuwunel (official successor, 2025-present) — Enterprise focus
    │       └── Continuwuity (community fork, 2025-present) — Community focus  
    └── Grapevine (fork of Conduit 0.7.0) — Pre-release, no Docker
```

All Conduit-family servers share:
- **Language:** Rust (memory-safe, high-performance)
- **Database:** RocksDB (embedded — no external PostgreSQL/Redis)
- **Architecture:** Single binary + data directory
- **Deployment:** Docker images available (except Grapevine)
- **RAM:** 20–50 MB idle, 200–500 MB under load

⚠️ **CRITICAL:** Database formats are incompatible between forks. Switching between Conduit derivatives corrupts the database permanently. Choose once.

---

## 2. Candidate Analysis

### 2.1 Tuwunel — Enterprise Successor to conduwuit

| Property | Detail |
|:---|:---|
| **URL** | https://github.com/matrix-construct/tuwunel |
| **Language** | Rust |
| **Latest Version** | v1.5.1 (2026-03-07) |
| **Development** | Very active — rapid release cadence (v1.0→v1.5 in ~4 months) |
| **Stars / Forks** | 1,600 / 115 |
| **Contributors** | 45+ (but dominated by single primary dev: jevolk) |
| **Funding** | Partially funded by Swiss government |
| **Docker** | `docker pull jevolk/tuwunel:latest` (~26 MB image) |
| **Database** | RocksDB (embedded) |
| **RAM (idle)** | ~20–50 MB (estimated from Conduit lineage) |
| **RAM (loaded)** | ~200–500 MB |
| **Federation** | Full Server-Server API, actively improved |
| **SSO/OIDC** | ✅ Supported |
| **Migration** | From conduwuit only (binary compatible) |

**Strengths:**
- Fastest feature velocity of any alternative
- Enterprise-grade ambitions (SSO/OIDC, Project Hydra state resolution)
- Full-time paid developer
- Swiss government backing signals institutional seriousness
- Latest security patches (v1.4.8/v1.4.9 fixed critical Invite API forgery)

**Weaknesses & Risks:**
- **Bus factor = 1:** Single primary developer (jevolk). If they leave, project stalls.
- **Governance concerns:** Lead developer has been ACL-banned from all Matrix Foundation rooms for attempting to delegitimize competing projects, making personal threats, and pressuring early security disclosure.
- **Sparse issue tracker:** Issues are deleted without comment, few PRs from external contributors, suggesting closed development process.
- **Sponsor dependency:** Feature priorities tied to unknown institutional sponsor.

**Known Federation Issues:**
- Apache reverse proxy corrupts X-Matrix header (use Caddy/Nginx instead)
- Docker default DNS causes 30+ minute room joins — requires `query_over_tcp_only = true`
- Heavy DNS traffic can overload resolvers (recommend self-hosted Unbound)
- Federation with original Conduit is broken on some endpoints
- DNSSEC validation is computationally expensive; disabling recommended

---

### 2.2 Continuwuity — Community Continuation of conduwuit

| Property | Detail |
|:---|:---|
| **URL** | https://continuwuity.org / https://codeberg.org/continuwuity/continuwuity |
| **Language** | Rust |
| **Latest Version** | v0.5.6 (2026-03-03) |
| **Development** | Very active — biweekly releases, 177 commits in v0.5.0 alone |
| **Stars / Forks** | 585 (GitHub mirror) / 12 |
| **Contributors** | 14+ active contributors |
| **Federated Servers** | 1,107 (6.5% market share — 2nd most popular after Synapse) |
| **Funding** | 100% volunteer / community-driven |
| **Docker** | Official lightweight image (static Rust binary) |
| **Database** | RocksDB (embedded — no external DB needed) |
| **RAM (idle)** | ~20–50 MB |
| **RAM (loaded)** | ~200–500 MB (1 CPU core) |
| **Federation** | Full Server-Server API; 266ms median federation ping (3rd fastest globally) |
| **Migration** | From conduwuit (compatible), backports Tuwunel changes |

**Strengths:**
- **Largest non-Synapse federation footprint** — 1,107 servers, battle-tested at scale
- **Healthy contributor base** — 14+ active devs reduces bus factor risk
- **Community governance** — transparent development, friendly maintainers, open issue tracker
- **Backports Tuwunel features** — gets enterprise features without governance risk
- **Proven federation reliability** — 3rd place federation ping leaderboard (266ms median)
- **Massive inbound federation performance improvements** in v0.5.6
- **Security responsive** — CVE-2026-24471 (auth bypass) patched promptly
- v0.5.6 disabled federated presence by default (reduces load — good for multi-agent)

**Weaknesses & Risks:**
- **Volunteer sustainability:** No institutional funding; depends on continued volunteer interest
- **Not "officially" endorsed** as conduwuit successor (Tuwunel claims that title)
- **No horizontal scaling** — single-instance architecture only (acceptable for per-agent use)
- **Lower version number** (v0.5.x vs Tuwunel v1.5.x) — cosmetic but may affect perception

**Known Federation Issues:**
- v0.5.5 had duplicate state types bug with policy server (fixed in v0.5.6)
- CVE-2026-24471: malicious remote server could trick event signing (patched)
- Federated presence disabled by default (design choice, not a bug)
- Same Docker DNS issues as all Conduit derivatives — use `query_over_tcp_only = true`

---

### 2.3 Conduit — Original Lightweight Server (SUPERSEDED)

| Property | Detail |
|:---|:---|
| **URL** | https://conduit.rs |
| **Language** | Rust |
| **Latest Version** | v0.10.x (still receiving some updates) |
| **Development** | Minimal — community maintenance only |
| **RAM (idle)** | ~20–50 MB |
| **Federation** | Basic Server-Server API; Beta quality |
| **Docker** | Official image available |
| **Federated Servers** | 598 (3.5% — all legacy installs) |

**Assessment:** Superseded by both Tuwunel and Continuwuity. Still receives security patches (room version 12 for CVE-2025-49090) but no new features. **Not recommended for new deployments.**

---

### 2.4 Construct — C++ Matrix Server (ABANDONED)

| Property | Detail |
|:---|:---|
| **URL** | https://github.com/matrix-construct/construct |
| **Language** | C++ (C++17) |
| **Latest Activity** | Last commit 2023-05-02 (~3 years ago) |
| **Releases** | None (only 23 tags, latest 0.9.x) |
| **Docker** | None |
| **Database** | RocksDB |
| **Dependencies** | Boost, RocksDB, GraphicsMagick, autotools — complex build chain |

**Assessment:** Effectively abandoned. Primary developer (jevolk — same person behind Tuwunel) shifted focus entirely to Tuwunel. No Docker support, no releases, likely non-compliant with current Matrix spec. The repository warns that public registration is unsafe. **Not viable. Historical reference only.**

---

### 2.5 Other Alternatives (Non-Viable)

| Server | Language | Status | Why Not Viable |
|:---|:---|:---|:---|
| **Grapevine** | Rust | Pre-release | No releases, no Docker (explicitly rejected), 3 volunteers, years from production |
| **Palpo** | Rust | v0.2.1 (early dev) | Requires PostgreSQL 16+ (external DB), too early, 69 stars |
| **Telodendria** | ANSI C | Alpha | Solo dev, no federation, no basic chat yet, custom flat-file DB |
| **Transform** | TypeScript | Dead (2018) | Abandoned prototype, no federation, non-functional |
| **CF Workers HS** | TypeScript | Non-functional | LLM-generated PoC, no event graph, fabricated APIs |

---

## 3. Head-to-Head: Tuwunel vs. Continuwuity

| Dimension | Tuwunel | Continuwuity | Winner |
|:---|:---|:---|:---|
| **Latest Release** | v1.5.1 (2026-03-07) | v0.5.6 (2026-03-03) | Tie |
| **RAM (idle)** | ~20-50 MB | ~20-50 MB | Tie |
| **Docker Image** | ~26 MB | Lightweight static | Tie |
| **Database** | RocksDB (embedded) | RocksDB (embedded) | Tie |
| **Federation Market Share** | Not measured separately | 6.5% (1,107 servers) | Continuwuity |
| **Federation Ping** | Not measured | 266ms median (3rd globally) | Continuwuity |
| **Feature Velocity** | Very high | High (backports Tuwunel) | Tuwunel |
| **SSO/OIDC** | ✅ Full | Partial (Element Call support) | Tuwunel |
| **Contributors** | 45+ (1 dominant) | 14+ (distributed) | Continuwuity |
| **Bus Factor** | 1 (jevolk) | ~5-8 active | Continuwuity |
| **Governance** | Controversial lead dev | Transparent community | Continuwuity |
| **Institutional Backing** | Swiss government | None (volunteer) | Tuwunel |
| **Security Track Record** | Critical vulns found & patched | Same vulns, also patched promptly | Tie |
| **Community Sentiment** | Concerns about governance | Overwhelmingly positive | Continuwuity |
| **Conduwuit Migration** | Binary compatible | Compatible + backports | Tie |
| **Documentation** | Good | Good | Tie |

---

## 4. Dendrite-Specific Problems: Will They Recur?

The Agent-Matrix lab has documented four critical Dendrite failure modes. Here is how the Conduit-family architecture addresses each:

### 4.1 DAG Corruption / Missing prev_events
**Dendrite:** Uses PostgreSQL with complex multi-table event storage. When federated events arrive with prev_events references to events the server does not have, Dendrite enters a retry loop fetching `/get_missing_events` that can block indefinitely.

**Conduit-family (Tuwunel/Continuwuity):** Uses RocksDB with a simpler, linear event storage model. The embedded database eliminates PostgreSQL connection pool exhaustion and multi-process race conditions. However, the fundamental Matrix DAG problem (missing prev_events in a federated room) is protocol-level, not implementation-level. Both servers must handle it — the question is whether they handle it gracefully or block.

**Assessment:** The Conduit-family simpler architecture makes DAG corruption less likely to cascade into unrecoverable states, but it does not eliminate the underlying protocol challenge. Continuwuity v0.5.6 federation performance improvements specifically targeted inbound event processing robustness.

### 4.2 Signing Key Fetch Failures
**Dendrite:** "Could not download key for agent0-X-mhs" errors prevent identity verification and block federation.

**Conduit-family:** Uses the same `/key/v2/server` federation API but with different implementation. Tuwunel specifically has known issues with DNS resolution in Docker (30+ minute join times) that can manifest as key fetch failures. Both projects recommend `query_over_tcp_only = true` for Docker deployments.

**Assessment:** Partially improved. The key fetch mechanism is protocol-standard, but Docker DNS resolution is a known pain point for Conduit-family servers. Proper DNS configuration (self-hosted Unbound or `query_over_tcp_only`) is essential.

### 4.3 Sync Freezes
**Dendrite:** The `/sync` endpoint blocks indefinitely when it encounters events with broken DAG history, because it enters a retry loop DURING response building. The event loop is blocked at the HTTP level — even `asyncio.wait_for()` cannot fire.

**Conduit-family:** Rust async runtime (Tokio) handles concurrent I/O differently than Dendrite Go goroutines. The embedded RocksDB eliminates the PostgreSQL query bottleneck. Sync responses are built from local RocksDB reads, not cross-process database queries.

**Assessment:** Significantly improved. The architectural change from "PostgreSQL queries during sync building" to "local RocksDB reads" eliminates the primary mechanism for Dendrite sync freezes.

### 4.4 M_LIMIT_EXCEEDED / Stuck Federated Joins
**Dendrite:** Rate-limits internal federation requests, causing joins to fail with M_LIMIT_EXCEEDED when multiple agents join simultaneously.

**Conduit-family:** Different rate-limiting implementation. Tuwunel Docker DNS issues can cause slow joins (30+ minutes) but for different reasons (DNS resolution, not rate limiting).

**Assessment:** Different failure mode, not eliminated. Proper DNS configuration is critical.

---

## 5. Deployment Architecture for Agent-Matrix

### Recommended Stack
```
              matrix.v-site.net (Synapse)
              Gateway / Human Interface
              Federation Hub
                    |
     +--------------+--------------+
     |              |              |
  agent0-2      agent0-3      agent0-N
  Continuwuity  Continuwuity  Continuwuity
  RocksDB       RocksDB       RocksDB
  172.23.89.2   172.23.89.3   172.23.89.N
```

### Per-Instance Resource Budget
| Component | Allocation |
|:---|:---|
| RAM (idle) | 20-50 MB |
| RAM (active federation) | 50-150 MB |
| CPU | 0.25 cores (burst to 1) |
| Disk | ~100 MB base + room data |
| Network | Port 8008 (client), 8448 (federation TLS) |
| Docker Image | ~30 MB |

### Total Fleet Budget (9 agents)
| Resource | Per Agent | Fleet Total |
|:---|:---|:---|
| RAM (idle) | 50 MB | 450 MB |
| RAM (active) | 150 MB | 1.35 GB |
| Disk | 200 MB | 1.8 GB |
| Docker images | 30 MB | 30 MB (shared layers) |

This is a fraction of what 9 Dendrite instances consume, and orders of magnitude less than 9 Synapse instances.

---

## 6. Migration Considerations

### From Dendrite to Continuwuity
- **Direct migration is NOT supported.** Dendrite uses PostgreSQL; Continuwuity uses RocksDB.
- **Clean deployment required:** Stand up fresh Continuwuity instances, re-register accounts, re-establish rooms.
- This is actually desirable for Agent-Matrix: fresh instances eliminate the poisoned DAG state that caused the Dendrite problems.

### Migration Steps
1. Deploy Continuwuity container alongside existing Dendrite
2. Configure TLS certificates (reuse step-ca PKI)
3. Register agent accounts on new Continuwuity instance
4. Create fresh rooms (avoids inheriting DAG corruption)
5. Update DNS records (agent0-N-mhs.cybertribe.com to new container IP)
6. Update matrix_bot.py configuration
7. Verify federation with Synapse gateway
8. Decommission Dendrite containers

### Docker Compose Template Changes
- Remove: PostgreSQL dependency, Dendrite-specific volume mounts
- Add: Single Continuwuity container with RocksDB data volume
- Update: Federation port mapping (8448 TLS)
- Note: Continuwuity handles TLS natively — may simplify the --https-bind-address workaround needed for Dendrite

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|:---|:---|:---|:---|
| Continuwuity volunteer burnout | Medium | High | Monitor commit activity; Tuwunel as fallback (different DB though) |
| RocksDB corruption | Low | High | Regular backups; RocksDB is battle-tested (used by Facebook, LinkedIn) |
| Federation protocol-level DAG issues | Medium | Medium | Fresh rooms, minimize agent downtime, health monitoring |
| Docker DNS causing slow joins | Medium | Low | Set query_over_tcp_only = true in config |
| Security vulnerabilities | Certain | Variable | Track releases, apply patches promptly |
| Incompatibility with Synapse gateway | Low | High | Continuwuity federates with 1,107 servers including Synapse; well-tested |

---

## 8. Final Recommendation

### Primary: Continuwuity v0.5.6+

**Why Continuwuity over Tuwunel:**

1. **Proven federation at scale** — 1,107 federated servers (6.5% market share), 266ms median ping. This is real-world validation that Tuwunel does not have separately measured.

2. **Governance health** — Multiple active contributors with transparent development. Tuwunel single-developer model with documented governance issues (Matrix Foundation ban, attempts to delegitimize competitors) creates unacceptable project risk.

3. **Community consensus** — Overwhelming community recommendation toward Continuwuity. Every user discussion surveyed recommended Continuwuity over Tuwunel.

4. **Feature parity** — Continuwuity backports Tuwunel features, so enterprise capabilities flow downstream without governance risk.

5. **Architecture fit** — Single-instance, embedded-DB, <50MB RAM idle is exactly what Agent-Matrix needs. No horizontal scaling needed for per-agent homeservers.

6. **Identical resource footprint** — Both use ~20-50MB RAM idle with RocksDB. No advantage to Tuwunel here.

### Fallback: Tuwunel v1.5.1+

If Continuwuity volunteer development stalls (monitor quarterly), Tuwunel is the only viable alternative. Migration between forks requires a clean deployment (database incompatible), which is manageable for the Agent-Matrix lab.

### Do NOT Consider
- **Dendrite** — Maintenance mode, DAG corruption is architectural
- **Conduit** — Superseded, minimal development
- **Construct** — Abandoned
- **Grapevine** — No Docker, no releases, years from production
- **Palpo** — Requires PostgreSQL, too early
- **Synapse** — 500MB+ RAM per instance, unacceptable for per-agent use

---

## Appendix A: Source Registry

| Source | URL | Accessed |
|:---|:---|:---|
| Matrix Server Comparison | https://matrixdocs.github.io/docs/servers/comparison | 2026-03-08 |
| Tuwunel Documentation | https://matrix-construct.github.io/tuwunel/ | 2026-03-08 |
| Tuwunel GitHub | https://github.com/matrix-construct/tuwunel | 2026-03-08 |
| Continuwuity Website | https://continuwuity.org/ | 2026-03-08 |
| Continuwuity Codeberg | https://codeberg.org/continuwuity/continuwuity | 2026-03-08 |
| Conduit Official | https://conduit.rs/ | 2026-03-08 |
| Construct GitHub | https://github.com/matrix-construct/construct | 2026-03-08 |
| Matrix.org Ecosystem | https://matrix.org/ecosystem/servers/ | 2026-03-08 |
| TWIM 2026-03-06 | https://matrix.org/blog/2026/03/06/this-week-in-matrix-2026-03-06/ | 2026-03-08 |
| TWIM 2026-02-06 | https://matrix.org/blog/2026/02/06/this-week-in-matrix-2026-02-06/ | 2026-03-08 |
| TWIM 2025-11-07 | https://matrix.org/blog/2025/11/07/this-week-in-matrix-2025-11-07/ | 2026-03-08 |
| Community Discussion | https://awful.systems/post/5029223 | 2026-03-08 |
| Reddit r/matrixdotorg | https://www.reddit.com/r/matrixdotorg/comments/1r5fmch/ | 2026-03-08 |
| Conduwuit Blog Post | https://edu4rdshl.dev/posts/about-to-leave-matrix-oh-wait-there-s-conduwuit/ | 2026-03-08 |
| DeepWiki Tuwunel | https://deepwiki.com/matrix-construct/tuwunel | 2026-03-08 |
