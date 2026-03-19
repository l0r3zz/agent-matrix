# Matrix Homeserver Alternatives: Technical Research Report

**Date:** 2026-03-08  
**Scope:** Lightweight Matrix homeserver implementations suitable for Agent-Matrix sovereign node architecture  
**Context:** Evaluating replacements for Dendrite (maintenance mode, 2.2% market share) in a one-homeserver-per-agent deployment model

---

## Executive Summary

The Matrix homeserver landscape has consolidated significantly since 2024. The Conduit→conduwuit lineage split into two stable forks: **Continuwuity** (community-driven) and **Tuwunel** (enterprise, Swiss government-backed). These two Rust implementations now represent the only viable lightweight alternatives to Synapse for production federation.

| Homeserver | Language | Status | Latest Version | Release Date | Idle RAM | Federation | Docker | Stars |
|:-----------|:---------|:-------|:---------------|:-------------|:---------|:-----------|:-------|:------|
| **Continuwuity** | Rust | ✅ Stable | v0.5.6 | 2026-03-03 | 20-50 MB | ✅ Full (6.5% share) | ✅ Yes | 585 (GH mirror) |
| **Tuwunel** | Rust | ✅ Stable | v1.5.1 | 2026-03-07 | 20-50 MB | ✅ Full | ✅ Yes (~26MB image) | 1,600 |
| **Conduit** | Rust | ⚠️ Archived | v0.7.0 | 2023 | 20-50 MB | ✅ Full (3.5% share) | ✅ Yes | N/A |
| **Dendrite** | Go | ⚠️ Maintenance | — | Security only | 50-100 MB | ✅ Full (2.2% share) | ✅ Yes | N/A |
| **Palpo** | Rust | 🔨 Early Dev | v0.2.1 | 2026-02-05 | Unknown | 🔨 Testing | Unknown | 69 |
| **Grapevine** | Rust | 🔨 Pre-release | No releases | — | Unknown | Unknown | ❌ Non-goal | ~0 |
| **Telodendria** | ANSI C | 🔨 Alpha | No releases | — | Minimal | ❌ None | ❌ Unknown | N/A |
| **Transform** | TypeScript | ❌ Obsolete | — | ~2018 | — | ❌ None | ❌ No | 16 |
| **CF Workers HS** | TypeScript | ❌ Non-functional | — | 2026-01-28 | — | ❌ None | N/A | N/A |

---

## 1. Continuwuity

### Identity
- **URL**: https://continuwuity.org/ | https://forgejo.ellis.link/continuwuation/continuwuity
- **GitHub Mirror**: https://github.com/continuwuity/continuwuity (585 stars, 12 forks)
- **Language**: Rust (100%)
- **License**: Apache-2.0
- **Lineage**: Conduit → conduwuit (archived May 2025) → Continuwuity (community fork)
- **Matrix Room**: #continuwuity:continuwuity.org

### Current Version & Activity
- **Latest Release**: v0.5.6 (announced TWIM 2026-03-06)
- **Release History**: v0.5.0 (2025-12-22), v0.5.2 (2026-01-09), v0.5.4 (2026-02-08), v0.5.5, v0.5.6
- **Commits**: 6,235+
- **Contributors**: 14+ (v0.5.0 alone had 249 commits from 14 contributors)
- **Development Activity**: Very active — multiple releases per month, conventional commit enforcement

### Resource Footprint
- **Idle RAM**: ~20-50 MB (inherited from Conduit architecture, embedded RocksDB)
- **Under Load (1000+ users)**: ~200-500 MB RAM, 1 CPU core
- **Database**: RocksDB (embedded — no external database server required)
- **Disk**: Varies by room count; RocksDB is space-efficient
- **No external dependencies**: No PostgreSQL, no Redis — single binary + data directory

### Federation
- **Status**: Full federation support, production-proven
- **Market Share**: 1,107 discovered servers (6.5%) — 2nd most popular after Synapse
- **Ping Leaderboard**: 3rd place with 266ms median
- **v0.5.6 Improvements**: Massive inbound federation performance improvements, federated presence disabled by default (reduces load)
- **Known Issues**: v0.5.5 had a bug with duplicate state types when policy server is enabled (fixed in v0.5.6)
- **Security**: CVE-2026-24471 (malicious remote server could trick signing arbitrary events on user room leave/join/knock) — patched

### Docker Deployment
- **Full Docker support** via Forgejo container registry
- **Migration from conduwuit**: As simple as changing the image name in docker-compose
- **Image size**: Lightweight (Rust static binary)

### Key Features (v0.5.6)
- Simplified Sliding Sync with typing indicators
- MSC3814 Dehydrated Devices (receive encrypted messages while offline)
- Bundled aggregations
- Appservice device masquerading (improves mautrix bridge compatibility)
- Configurable URL previews with purge command
- Limited-use registration tokens
- Server-wide invite anti-spam
- Journald logging support
- Room Version 12 support

### Known Issues & Risks
- Community-driven (no corporate backing) — sustainability depends on volunteer contributors
- Fork drama: Split from Tuwunel due to governance concerns with single developer (jevolk)
- Smaller community than Tuwunel (585 vs 1,600 GitHub stars)
- No horizontal scaling (single instance architecture)

---

## 2. Tuwunel

### Identity
- **URL**: https://github.com/matrix-construct/tuwunel
- **Docs**: https://matrix-construct.github.io/tuwunel/
- **Language**: Rust (100%)
- **License**: Apache-2.0
- **Lineage**: Conduit → conduwuit → Tuwunel (official successor)
- **Matrix Room**: #tuwunel:matrix.org
- **Developer**: Jason Volk (jevolk) — also created Construct (C++, now abandoned)

### Current Version & Activity
- **Latest Release**: v1.5.1 (2026-03-07)
- **Total Releases**: 16
- **Key Releases**: v1.5.0 (2026-01-31) added SSO/OIDC support
- **GitHub Stars**: 1,600 | Forks: 115 | Watchers: 16
- **Development Activity**: Very active, frequent releases

### Resource Footprint
- **Docker Image**: ~26 MB (extremely compact)
- **Idle RAM**: ~20-50 MB (same Conduit-derived embedded DB architecture)
- **Under Load**: ~200-500 MB RAM, 1 CPU core
- **Database**: RocksDB exclusively (embedded — no external DB)
- **Binary compatible** with conduwuit databases (zero-migration upgrade path)

### Federation
- **Status**: Full federation support, production-deployed
- **Project Hydra**: State resolution optimizations for federation reliability
- **Security Patches**: v1.4.8/1.4.9 fixed Invite API forgery and membership state vulnerabilities
- **Swiss Government Deployment**: Funded and deployed for Swiss citizens — strong production validation

### Docker Deployment
- **Full Docker support** with multiple registries:
  - DockerHub: `docker pull jevolk/tuwunel:latest`
  - GHCR: `docker pull ghcr.io/matrix-construct/tuwunel:latest`
- **Tags**: `:latest` (stable), `:preview` (release candidates)
- **Also available**: Static binaries, Deb/RPM packages, AUR, Nix, Alpine packages

### Key Features (v1.5.x)
- SSO/OIDC support (login via GitHub, etc.)
- Full Matrix spec implementation
- Enterprise-ready scalability
- Project Hydra federation optimizations
- 45+ contributors

### Known Issues & Risks
- **Single primary developer** (jevolk) — bus factor risk
- **Governance friction** with Matrix Foundation led to community fork (Continuwuity)
- Same developer abandoned Construct (C++) — pattern concern
- Community perception issues around project leadership style

---

## 3. Grapevine

### Identity
- **URL**: https://gitlab.computer.surgery/matrix/grapevine
- **Website**: https://grapevine.computer.surgery/
- **Language**: Rust
- **License**: Inherited from Conduit (Apache-2.0)
- **Lineage**: Forked from Conduit 0.7.0 (April 28, 2024)
- **Matrix Room**: #grapevine:computer.surgery

### Current Status
- **Status: Active but PRE-RELEASE — NOT ready for general use**
- Website explicitly states: "There aren't any releases, there isn't very much user-facing documentation"
- Focus on reliability and correctness over feature velocity
- Plans to eventually rewrite from scratch in a separate repository
- Last observed activity: December 31, 2025

### Development
- **Commits**: 2,874
- **Tags**: 1 (no formal releases)
- **Maintainers**: 3 volunteers (charles, olivia, xiretza)
- **Community**: Very small, GitLab stars ~0

### Resource Requirements
- **Not documented** — too early-stage for benchmarks
- Inherits Conduit's RocksDB/SQLite backend architecture

### Federation
- **Unknown** — inherited from Conduit codebase but no explicit federation testing or claims

### Docker
- **Docker is explicitly a NON-GOAL** — project won't provide first-party Docker images
- Recommended: Pre-built static binaries or build from source
- Users can create their own Docker images if needed

### Assessment
Grapevine is an interesting correctness-focused project but is years from production readiness. The explicit rejection of Docker support makes it incompatible with the Agent-Matrix containerized deployment model.

---

## 4. Transform

### Identity
- **URL**: https://github.com/bettiah/transform
- **Language**: TypeScript (100%)
- **License**: Apache-2.0
- **Database**: Redis 5.0 RC (streams) + SQLite/PostgreSQL

### Current Status
- **Status: OBSOLETE** (confirmed by matrix.org ecosystem page)
- **GitHub Stars**: 16 | Forks: 2 | Watchers: 3
- **Commits**: 96
- **Last meaningful activity**: ~2018 era (references Node 10, Riot client)

### Features (Partial)
- Register, Login, CreateRoom, Invite, Join, Sync — basic client-server API only
- **No federation support** — only client-server API implemented
- Auto-generated code from Swagger specs
- Not functional enough for any real use

### Assessment
Transform is a dead prototype from ~2018. Completely non-viable.

---

## 5. Other Alternatives

### 5a. Palpo (Rust — Early Development)
- **URL**: https://github.com/palpo-im/palpo | https://palpo.chat/
- **Language**: Rust (Salvo web framework)
- **Latest Version**: v0.2.1 (2026-02-05)
- **GitHub Stars**: 69 | Forks: 8
- **Database**: PostgreSQL 16+ (external, unlike Continuwuity/Tuwunel)
- **Federation**: Active testing with Complement test suite
- **Docker**: Not documented
- **Status**: Under active development, announced on Rust forum Dec 4, 2025
- **Assessment**: Interesting alternative approach (PostgreSQL instead of embedded DB) but far too early for production use. Worth monitoring.

### 5b. Telodendria (ANSI C — Alpha)
- **URL**: https://telodendria.org/ | https://git.telodendria.org/Telodendria/telodendria
- **Language**: ANSI C (C99)
- **License**: MIT
- **Status**: Very early alpha — local user chat not yet implemented as of July 2025
- **Developer**: Solo volunteer (recently graduated university)
- **Database**: Custom flat-file (via Cytoplasm support library, also in development)
- **Federation**: Not implemented
- **Target Spec**: Matrix v1.16 with Room Version 12
- **No releases, no timeline commitments**
- **Assessment**: Fascinating minimal-footprint approach but realistically 2+ years from being useful.

### 5c. Conduit (Rust — Archived/Superseded)
- **URL**: https://gitlab.com/famedly/conduit
- **Status**: Original project archived; superseded by Continuwuity and Tuwunel
- **Market Share**: Still 3.5% of federation (598 servers) — running on legacy installs
- **Assessment**: Do not deploy new instances. Migrate existing ones to Continuwuity or Tuwunel.

### 5d. Cloudflare Workers Matrix Homeserver (TypeScript — Non-functional)
- **URL**: https://github.com/nkuntz1934/matrix-workers
- **Blog Post**: https://blog.cloudflare.com/serverless-matrix-homeserver-workers/ (2026-01-27)
- **Status**: Non-functional proof of concept, LLM-generated (Claude Code Opus 4.5)
- **Critical Issues**:
  - Does NOT model rooms as replicated event graphs (fundamental Matrix requirement)
  - No permission checking or power level enforcement
  - Federation authentication is TODO stubs only
  - Fabricated API endpoints (LLM hallucinations)
  - Claims spec v1.12 (current is v1.17)
- **Matrix.org Response**: "Well-intentioned but rather flawed" — "not yet a functional Matrix server"
- **Assessment**: Do not use.

### 5e. Exotic Language Implementations
- **Zig**: No Matrix homeserver found
- **Nim**: No Matrix homeserver found
- **Haskell**: No Matrix homeserver found
- **OCaml**: Client library only (mirage/ocaml-matrix), no homeserver
- **Elixir**: Only Matrex (toy/obsolete)

---

## 6. Federation Market Share (March 2026)

From MatrixRooms.info via TWIM 2026-03-06 (17,151 federated servers discovered):

| Server | Count | Share |
|:-------|------:|------:|
| Synapse | 13,828 | 80.6% |
| Continuwuity | 1,107 | 6.5% |
| Conduit | 598 | 3.5% |
| Dendrite | 376 | 2.2% |
| Other | ~1,242 | 7.2% |

---

## 7. Comparative Resource Analysis

### Idle State
| Server | RAM | CPU | Disk I/O | External DB Required |
|:-------|:----|:----|:---------|:--------------------|
| Synapse | 300-500 MB | Medium | Medium | PostgreSQL (required) |
| Dendrite | 50-100 MB | Low | Low | PostgreSQL (recommended) |
| Continuwuity | 20-50 MB | Very Low | Low | None (RocksDB embedded) |
| Tuwunel | 20-50 MB | Very Low | Low | None (RocksDB embedded) |
| Conduit | 20-50 MB | Very Low | Low | None (embedded) |

### Under Load (1000+ users)
| Server | RAM | CPU Cores | Scaling |
|:-------|:----|:----------|:--------|
| Synapse | 2-8 GB | 2-4+ | Single → Workers → Multi-instance |
| Dendrite | 500 MB-2 GB | 1-2 | Monolith → Polylith |
| Continuwuity | 200-500 MB | 1 | Single instance only |
| Tuwunel | 200-500 MB | 1 | Single instance only |

---

## 8. Recommendation for Agent-Matrix

For the Agent-Matrix sovereign node architecture (one homeserver per agent, containerized, federated):

### Primary Candidates

**1. Continuwuity (Recommended)** ✅
- Community-driven, active multi-contributor development
- 20-50 MB RAM per instance — ideal for multi-agent fleet
- No external database — single container per agent
- Docker support with easy migration from conduwuit
- 2nd most popular server on federation — proven at scale
- Lower governance risk (multiple maintainers vs single developer)

**2. Tuwunel (Strong Alternative)** ✅
- Enterprise-grade, Swiss government validation
- ~26 MB Docker images — smallest footprint
- Same embedded RocksDB architecture
- More features (SSO/OIDC, Project Hydra)
- Larger community (1,600 stars)
- Higher governance risk (single primary developer)

### Migration Path from Dendrite
- Dendrite uses PostgreSQL/SQLite; Continuwuity/Tuwunel use RocksDB
- **No direct database migration** — requires fresh deployment with room re-creation
- This aligns with the planned hub-and-spoke architectural pivot

### Not Recommended
- **Grapevine**: No Docker, no releases, too early
- **Telodendria**: Years from usability
- **Transform**: Dead project
- **Palpo**: Too early, requires PostgreSQL (adds container complexity)
- **Cloudflare Workers HS**: Non-functional

---

## Sources

1. Matrix.org Ecosystem Servers: https://matrix.org/ecosystem/servers/
2. TWIM 2026-03-06: https://matrix.org/blog/2026/03/06/this-week-in-matrix-2026-03-06/
3. Continuwuity Releases: https://forgejo.ellis.link/continuwuation/continuwuity/releases
4. Tuwunel GitHub: https://github.com/matrix-construct/tuwunel
5. Grapevine Website: https://grapevine.computer.surgery/
6. Grapevine GitLab: https://gitlab.computer.surgery/matrix/grapevine
7. Telodendria Status: https://telodendria.org/blog/status-update-july-2025
8. Transform GitHub: https://github.com/bettiah/transform
9. Palpo GitHub: https://github.com/palpo-im/palpo
10. Matrix Server Comparison: https://matrixdocs.github.io/docs/servers/comparison
11. Matrix.org on CF Workers: https://matrix.org/blog/2026/01/28/matrix-on-cloudflare-workers/
12. CF Workers Critical Analysis: https://nexy.blog/2026/01/28/cf-matrix-workers/
13. Continuwuity GitHub Mirror: https://github.com/continuwuity/continuwuity
14. Tuwunel Releases: https://github.com/matrix-construct/tuwunel/releases
