# Agent0-1 migration: tarnover → g2s

Backup tarballs are already on g2s at `/tmp/agent0-1-backup.tar.gz` and `/tmp/agent0-1-mhs-backup.tar.gz`.

## On g2s (after SSH)

1. Copy the migration script to g2s. From your **local machine** (where this repo lives):
   ```bash
   scp /home/l0r3zz/k8-build/Agent0/migration/run-on-g2s-phases-2-8.sh l0r3zz@172.23.100.121:/tmp/
   ```
   Or from tarnover:
   ```bash
   scp /path/to/run-on-g2s-phases-2-8.sh l0r3zz@172.23.100.121:/tmp/
   ```

2. SSH to g2s and run the script (will prompt for sudo password):
   ```bash
   ssh l0r3zz@172.23.100.121
   chmod +x /tmp/run-on-g2s-phases-2-8.sh
   /tmp/run-on-g2s-phases-2-8.sh
   ```

3. When the script stops and prints **"Run Phase 5 on TARNOVER"**, do the following on **tarnover** (where step-ca runs):
   ```bash
   step ca certificate agent0-1-mhs.cybertribe.com /tmp/agent0-1-server.crt /tmp/agent0-1-server.key --not-after=8760h
   step ca root /tmp/root.pem
   cat /tmp/agent0-1-server.crt /tmp/root.pem > /tmp/agent0-1-server-bundled.crt
   scp /tmp/agent0-1-server-bundled.crt l0r3zz@172.23.100.121:/opt/agent-zero/agent0-1/mhs/server.crt
   scp /tmp/agent0-1-server.key l0r3zz@172.23.100.121:/opt/agent-zero/agent0-1/mhs/server.key
   ```

4. On **g2s** again, set cert permissions and re-run the script to complete Phase 6–8:
   ```bash
   sudo chmod 644 /opt/agent-zero/agent0-1/mhs/server.crt
   sudo chmod 600 /opt/agent-zero/agent0-1/mhs/server.key
   sudo chown 65534:65534 /opt/agent-zero/agent0-1/mhs/server.crt /opt/agent-zero/agent0-1/mhs/server.key
   /tmp/run-on-g2s-phases-2-8.sh
   ```

5. Then continue with **Phase 9** (register Matrix account), **Phase 10** (MCP server + bot), **Phase 11** (dashboard MCP config) per the main context bundle.

---

## Fixes applied (for future migrations)

- **Dendrite data volume:** Must be `./mhs/data:/var/lib/dendrite` (not `/var/dendrite/`). Wrong path causes roomserver panic on start.
- **Dendrite federation (8448):** Compose `command` must include `--tls-cert /etc/dendrite/server.crt` and `--tls-key /etc/dendrite/server.key` in addition to `--https-bind-address :8448`; otherwise the HTTPS listener does not start.
- **Compose:** `version:` is obsolete in Compose V2 and can be removed to avoid warnings.
