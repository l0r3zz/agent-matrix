# OpenVPN on DD-WRT with step-ca: Ops Run Book

**Date:** February 2026
**Environment:** DD-WRT router at `port.nexsys.net`, step-ca PKI on home lab
**VPN CIDR:** 172.23.200.0/24 (clients) within home lab 172.23.0.0/16
**Purpose:** Allow remote K8s cluster (matrix.v-site.net) to reach home lab hosts

---

## 1. Goal

Expose DD-WRT OpenVPN on `port.nexsys.net` using `step-ca` certs so remote clients
get `172.23.200.0/24` addresses and can reach `172.23.0.0/16`.

## 2. Final Working State

- OpenVPN server on DD-WRT:
  - TUN: `tun2`, network `172.23.200.0/24`, server IP `172.23.200.1`.
  - UDP 1194 listening on WAN.
- PKI:
  - Root: `CyberTribe CA Root CA` (step-ca root).
  - Intermediate: `CyberTribe CA Intermediate CA` (issuer of server and client certs).
  - CA chain file: `cybertribe-openvpn-ca-chain.crt` = `intermediate + root` (PEM).
- Client:
  - Cert: `test-client.cybertribe.com` (issued by intermediate).
  - `.ovpn` embeds `<ca>`, `<cert>`, `<key>`.

---

## 3. DD-WRT GUI Navigation

1. Open browser to your DD-WRT router's LAN IP (e.g., `http://192.168.1.1`).
2. Click **Services** tab at the top.
3. Click **VPN** sub-tab.
4. In the **OpenVPN Daemon** section, click **Enable**.

**Important:** You want the **OpenVPN Daemon/Server** section — not the "OpenVPN Client"
section. The server section is what allows the router to receive incoming VPN connections
from remote hosts like matrix.v-site.net.

### Fields in the OpenVPN Daemon section

| Field               | What to paste                              |
|---------------------|--------------------------------------------|
| CA Cert             | `cybertribe-openvpn-ca-chain.crt` (intermediate + root) |
| Public Server Cert  | `server.crt`                               |
| Private Server Key  | `server.key`                               |

Include the full PEM blocks (`-----BEGIN ...-----` through `-----END ...-----`).

### OpenVPN Additional Config

```conf
push "dhcp-option DNS 172.23.1.1"
push "dhcp-option DOMAIN cybertribe.com"
push "route 172.23.0.0 255.255.0.0"
```

The `push "route 172.23.0.0 255.255.0.0"` line tells connecting clients that traffic
for 172.23.0.0/16 should be routed through the VPN tunnel.

---

## 4. Firewall Rules

After saving the VPN config, go to **Administration -> Commands** and add:

```bash
iptables -t nat -A POSTROUTING -s 172.23.200.0/24 -j MASQUERADE
iptables -I FORWARD -p udp -s 172.23.200.0/24 -j ACCEPT
iptables -I INPUT -p udp --dport=1194 -j ACCEPT
iptables -I FORWARD -i tun2 -o br0 -j ACCEPT
iptables -I FORWARD -i br0 -o tun2 -j ACCEPT
```

Click **Save Firewall** to persist these rules across reboots.

---

## 5. Certificate Generation with step-ca

### 5.1 Prerequisites

The step-ca server must be running and bootstrapped on the machine where you issue certs.
Verify with:

```sh
step ca health
```

### 5.2 Build the CA Chain

Locate the root and intermediate certs in your step-ca store and build the chain file:

```sh
cat ~/.step/certs/intermediate_ca.crt ~/.step/certs/root_ca.crt > cybertribe-openvpn-ca-chain.crt
```

### 5.3 Issue Server Certificate

```sh
step ca certificate router.cybertribe.com server.crt server.key --provisioner admin
```

You'll be prompted for the provisioner password. Enter the JWK provisioner password
set during `step ca init`.

**Gotcha:** Do NOT add `--san`, `--kty`, `--size`, `--not-after`, `--no-password`, or
`--insecure` flags to `step ca certificate`. In the installed version (0.28.x–0.29.x),
these extra flags cause `too many positional arguments` errors. The basic three-argument
form works reliably. SANs default to the subject CN; key type defaults to EC P-256
(which OpenVPN accepts).

### 5.4 Issue Client Certificate

```sh
step ca certificate test-client.cybertribe.com test-client.crt test-client.key --provisioner admin
```

Each VPN client should have its own unique certificate with a unique Common Name.

### 5.5 Verify Certificates

```sh
# Inspect a certificate
step certificate inspect server.crt --short

# Verify the chain
step certificate verify server.crt --roots cybertribe-openvpn-ca-chain.crt
```

No output from `verify` means the certificate is valid and properly signed.

### 5.6 File Summary

| File                             | Where It Goes                      | Secret? |
|----------------------------------|------------------------------------|---------|
| `cybertribe-openvpn-ca-chain.crt` | DD-WRT CA Cert + client `<ca>`   | No      |
| `server.crt`                     | DD-WRT Public Server Cert          | No      |
| `server.key`                     | DD-WRT Private Server Key          | Yes     |
| `test-client.crt`               | Client `.ovpn` `<cert>` block      | No      |
| `test-client.key`               | Client `.ovpn` `<key>` block       | Yes     |

---

## 6. Client .ovpn Configuration

```ovpn
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
verb 3

<ca>
[contents of cybertribe-openvpn-ca-chain.crt]
</ca>

<cert>
[contents of test-client.crt]
</cert>

<key>
[contents of test-client.key]
</key>
```

---

## 7. Verifying Connection

Once the client connects:

1. Check in DD-WRT GUI: **Status -> OpenVPN**. A successful connection shows
   "CONNECTED SUCCESS" with the assigned VPN IP.
2. From the client, verify the tunnel:

```sh
# VPN gateway
ping 172.23.200.1

# LAN host
ping 172.23.1.x

# DNS resolution via home lab
nslookup host.cybertribe.com
```

---

## 8. TLS Error Reference

### 8.1 Server: "Private key does not match the certificate"

**Log snippet:**

```text
OpenSSL: error:140A80B1:lib(20):func(168):reason(177)
Private key does not match the certificate
```

**Fix:** Re-paste matching `server.crt` and `server.key` into DD-WRT. They must be
from the same `step ca certificate` invocation.

---

### 8.2 Server: "unable to get local issuer certificate"

**Log snippet:**

```text
VERIFY ERROR: depth=0, error=unable to get local issuer certificate: CN=test-client.cybertribe.com
TLS_ERROR: BIO read tls_read_plaintext error
SIGUSR1[soft,tls-error] received, client-instance restarting
```

**Cause:** Client cert was issued by the intermediate CA, but DD-WRT CA Cert field
only contains the root. The server can't build the trust chain.

**Fix:**

1. Confirm which CA issued the client cert:

   ```sh
   step certificate inspect test-client.crt | grep -A1 "Issuer:"
   ```

2. Build the chain with both intermediate and root:

   ```sh
   cat ~/.step/certs/intermediate_ca.crt ~/.step/certs/root_ca.crt > cybertribe-openvpn-ca-chain.crt
   ```

3. Paste the full chain into DD-WRT **CA Cert** and embed in the client `<ca>` block.

---

### 8.3 Client: "CONNECTION_TIMEOUT" with silent server log

**Cause:** Packets never reach OpenVPN — firewall or NAT issue.

**Fix:**

```sh
# On the router, check if packets arrive:
tcpdump -ni eth0 udp port 1194

# Verify OpenVPN is listening:
netstat -lunp | grep 1194

# Temporarily allow UDP 1194:
iptables -I INPUT 1 -p udp --dport 1194 -j ACCEPT
```

---

### 8.4 Server sees TLS handshake but it fails

**Cause:** CA / cert mismatch — client cert signed by a CA not in the server's chain.

**Fix:** Verify the issuer chain matches on both sides:

```sh
step certificate inspect server.crt | grep -A1 "Issuer:"
step certificate inspect test-client.crt | grep -A1 "Issuer:"
```

Both should show `CyberTribe CA Intermediate CA`. The CA chain in DD-WRT and in the
client `<ca>` block must contain both the intermediate and root.

---

### 8.5 step-ca: "too many positional arguments"

**Symptom:** Adding flags like `--san`, `--kty`, `--size`, `--not-after` to
`step ca certificate` causes:

```text
too many positional arguments were provided in 'step ca certificate <subject> <crt-file> <key-file>'
```

**Fix:** Use only the three positional arguments. The extra flags are not supported by
`step ca certificate` in versions 0.28.x–0.29.x. Run the bare form:

```sh
step ca certificate kama.cybertribe.com server.crt server.key
```

SANs default to the subject CN. To check what flags your version supports:

```sh
step ca certificate --help | head -n 25
```

---

## 9. Notes from First Bring-Up

This run-book was reconstructed from an interactive debugging session. Key lessons:

- The most common failure mode is **CA chain mismatch**: DD-WRT CA Cert has only the
  root but certs were issued by the intermediate. Always use the full chain
  (intermediate + root).

- The second most common failure is **key/cert pair mismatch** from copy-paste errors
  in the DD-WRT GUI. Always paste from the same `step ca certificate` invocation.

- The `step ca certificate` CLI is sensitive to extra flags in certain versions.
  When in doubt, use the minimal three-argument form and accept defaults.

- DD-WRT requires unencrypted private keys (it can't prompt for a passphrase at boot).
  step-ca issues unencrypted keys by default for leaf certs.

---

## 10. LAN-to-VPN Routing (Feb 20, 2026)

By default, LAN hosts on `172.23.0.0/16` cannot reach VPN clients on `172.23.200.0/24`
due to two issues:

### Problem 1: OpenVPN raw table anti-spoof rule

OpenVPN auto-generates a rule that drops all traffic to `172.23.200.0/24` arriving on
any interface other than `tun2`:

```
iptables -t raw: DROP all -- !tun2 * 0.0.0.0/0 172.23.200.0/24
```

This blocks LAN (br0) traffic from reaching VPN clients. **Fix:** Insert an ACCEPT
rule for br0 before the DROP, rather than deleting the DROP (which OpenVPN regenerates).

### Problem 2: iptables FORWARD chain

Even with the raw table fixed, the FORWARD chain must allow br0↔tun2 traffic.

### Firewall Rules (persisted via nvram)

```bash
# Saved via: nvram set rc_firewall='...' && nvram commit
# DO NOT use the DD-WRT GUI "Save Firewall" button — it triggers a full
# firewall + OpenVPN restart that bounces the tunnel and can lock out SSH.

iptables -t raw -I PREROUTING -i br0 -d 172.23.200.0/24 -j ACCEPT
iptables -I FORWARD -i br0 -o tun2 -j ACCEPT
iptables -I FORWARD -i tun2 -o br0 -j ACCEPT
```

### DHCP Route Push (dnsmasq option 121)

LAN hosts have a `/16` route for `172.23.0.0/16` on-link, so they try ARP for
`172.23.200.x` instead of routing through the gateway. DHCP option 121 (classless
static routes) pushes a more-specific `/24` route automatically:

```
# In DD-WRT Services > Additional DNSMasq Options:
dhcp-option=121,172.23.200.0/24,172.23.1.1
```

Clients pick this up on DHCP renewal. Force with: `sudo dhclient -r && sudo dhclient`

### Gotcha: DD-WRT GUI "Save Firewall"

**Never use the GUI Save Firewall button** for VPN-related iptables rules. It triggers
a full firewall reload that also restarts OpenVPN, bouncing the tunnel and potentially
locking out SSH. Always use `nvram set rc_firewall` + `nvram commit` from the CLI.

To verify saved rules: `nvram get rc_firewall`

### VPN Client Addresses

| Client | VPN IP | Certificate CN |
|--------|--------|----------------|
| Contabo Synapse sidecar | 172.23.200.2 | contabo-synapse.cybertribe.com |

---

## 11. Smoke-Test Checklist

Run after any cert rotation, config change, or firmware update:

1. Client connects and gets an IP in `172.23.200.0/24`.
2. `ping 172.23.200.1` (router VPN IP) succeeds.
3. `ping 172.23.1.x` (LAN host) succeeds.
4. `nslookup host.cybertribe.com` resolves via `172.23.1.1` and is reachable.
5. From a LAN host: `ping 172.23.200.2` (Contabo VPN endpoint) succeeds.
