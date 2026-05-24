# Tarnover Refresh Runbook

**Host:** tarnover (172.23.0.103) -- System76 Onyx Pro, 11th Gen i7-11800H, 64 GB RAM
**From:** Pop!_OS 22.04 LTS
**To:** Pop!_OS 24.04 LTS (fresh install on new 1 TB system disk)

## Disk Layout Reference

| Device | Current Use | Migration Action |
|---|---|---|
| `/dev/nvme0n1` (1 TB) | System disk: `/boot/efi`, `/recovery`, `/`, swap | **Replace** with new 1 TB SSD. Old disk removed or kept as spare. |
| `/dev/nvme1n1p1` (2 TB) | `/home` | **Preserve untouched.** Contains `/home/l0r3zz`. |

### Target Partition Layout (new nvme0)

| Partition | Size | Filesystem | Mount Point |
|---|---|---|---|
| `/dev/nvme0n1p1` | 2 GB | fat32 | `/boot/efi` |
| `/dev/nvme0n1p2` | 4 GB | fat32 | `/recovery` |
| `/dev/nvme0n1p3` | ~900 GB | ext4 | `/` |
| `/dev/nvme0n1p4` | 96 GB | linux-swap | (swap) |

---

## Phase 0: Pre-flight (before shutdown -- on live system)

Running the collector **online** while the OS is still booted gives the best-quality
package inventories. Online mode can query running daemons (Docker API, snap, flatpak,
pipx, npm, cargo, go) that are unavailable from a live USB.

### 0.1 Copy scripts to a stable location on the /home disk

```bash
cp -a /home/l0r3zz/Dropbox/GEN-AI/AGENT-MATRIX/agent-matrix-repo/migration/tarnover-refresh \
  /home/l0r3zz/tarnover-refresh-scripts
```

### 0.2 Record the l0r3zz account identity

Capture the exact UID, GID, group memberships, and shell so they can be
faithfully reproduced on the new system:

```bash
id l0r3zz > /home/l0r3zz/tarnover-refresh-scripts/l0r3zz-identity.txt
getent passwd l0r3zz >> /home/l0r3zz/tarnover-refresh-scripts/l0r3zz-identity.txt
getent group | grep l0r3zz >> /home/l0r3zz/tarnover-refresh-scripts/l0r3zz-identity.txt
cat /home/l0r3zz/tarnover-refresh-scripts/l0r3zz-identity.txt
```

Expected output (your system):

```
uid=1000(l0r3zz) gid=1000(l0r3zz) groups=1000(l0r3zz),4(adm),20(dialout),27(sudo),121(lpadmin),1001(docker),998(ollama)
l0r3zz:x:1000:1000::/home/l0r3zz:/bin/bash
```

Save this file -- you will need the UID (1000), GID (1000), and supplementary
group list in Phase 5.

### 0.3 Run collect-old.sh in online mode

```bash
cd /home/l0r3zz/tarnover-refresh-scripts
sudo ./collect-old.sh /home/l0r3zz/tarnover-refresh-export
```

### 0.4 Verify export

```bash
ls -lR /home/l0r3zz/tarnover-refresh-export | head -80
```

Confirm you see populated files under `apt/`, `flatpak/`, `snap/`, `python/`, `node/`,
`rust/`, `go/`, `docker/`, `systemd/`, `cron/`.

### 0.5 Spot-check key inventories

```bash
wc -l /home/l0r3zz/tarnover-refresh-export/apt/apt-manual.txt
wc -l /home/l0r3zz/tarnover-refresh-export/docker/containers.tsv
cat  /home/l0r3zz/tarnover-refresh-export/meta/host.txt
```

If the apt manual list has fewer than ~50 packages, investigate before proceeding.

---

## Phase 1: Hardware Refresh

1. **Shut down** tarnover cleanly: `sudo shutdown -h now`
2. Disconnect power and battery.
3. Open the back panel.
4. Clean cooling fans and heat pipes (compressed air + brush).
5. Remove old thermal paste from CPU and GPU die surfaces using isopropyl alcohol.
6. Apply new thermal paste (pea-sized dot, center of each die).
7. **Install the new 1 TB NVMe SSD** into the nvme0 slot (the system disk slot).
   - If keeping the old system disk as a spare, physically remove it to eliminate
     any risk of the installer touching it.
8. **Leave nvme1 (the /home disk) physically connected.** Do not remove it.
9. Reassemble, reconnect power.

---

## Phase 2: Boot Live USB

### 2.1 Create the live USB (if not already done)

Download Pop!_OS 24.04 LTS ISO from https://pop.system76.com/ and write it to USB:

```bash
# From any Linux machine:
sudo dd bs=4M if=pop-os_24.04_amd64_nvidia_XX.iso of=/dev/sdX conv=fsync status=progress
```

### 2.2 Boot from USB

Insert USB, power on tarnover, press F7 (System76 boot menu) to select the USB drive.

### 2.3 Verify disks are visible

Once the live desktop loads, open a terminal:

```bash
lsblk -f
```

You should see:
- `nvme0n1` -- the new blank 1 TB SSD (no partitions)
- `nvme1n1p1` -- the existing /home partition (ext4, ~2 TB)

### 2.4 Optional: verify Phase 0 export is on /home disk

```bash
sudo mkdir -p /mnt/old-home
sudo mount -o ro /dev/nvme1n1p1 /mnt/old-home
ls /mnt/old-home/l0r3zz/tarnover-refresh-export/meta/host.txt
sudo umount /mnt/old-home
```

If the file exists, Phase 0 succeeded and the export is safe on the /home disk.

### 2.5 Optional: run collect-old.sh in offline mode (supplemental)

Only needed if Phase 0 was skipped or you want to capture data from the old
system disk (if it is still physically present):

```bash
sudo mkdir -p /mnt/old-root /mnt/old-home
sudo mount /dev/<old-system-partition> /mnt/old-root   # e.g., nvme0n1p3 if old disk present
sudo mount -o ro /dev/nvme1n1p1 /mnt/old-home

cd /mnt/old-home/l0r3zz/tarnover-refresh-scripts
SOURCE_ROOT=/mnt/old-root SOURCE_HOME=/mnt/old-home/l0r3zz \
  sudo -E ./collect-old.sh /mnt/old-home/l0r3zz/tarnover-refresh-export

sudo umount /mnt/old-root /mnt/old-home
```

---

## Phase 3: Install Pop!_OS 24.04 -- Safe Strategy

> **CRITICAL: Read this entire phase before clicking anything in the installer.**

### Why a temporary user?

The Pop!_OS installer creates a home directory for the user you specify during
installation. If you enter `l0r3zz` as the username and later mount nvme1 as `/home`,
the installer's skeleton `/home/l0r3zz` (on the root partition) would shadow or conflict
with your real `/home/l0r3zz` on nvme1. Using a throwaway user like `setupadmin`
eliminates this risk entirely.

### 3.1 Launch installer

From the live desktop, open **Install Pop!_OS** from Applications.

Select your region, language, and keyboard layout.

### 3.2 Choose Custom (Advanced)

Select **Custom (Advanced)**. This opens the partition editor.

### 3.3 Partition the NEW system disk (nvme0n1) using GParted

> **WARNING:** If GParted opens showing both drives, be extremely careful to only
> modify `/dev/nvme0n1`. Triple-check the device name before every operation.

If the new SSD has no partition table yet:
1. Select `/dev/nvme0n1` in the top-right device selector.
2. Device -> Create Partition Table -> select `gpt` -> Apply.

Create partitions in this order:

| # | Size | Filesystem | Label (optional) |
|---|---|---|---|
| 1 | 2048 MiB | fat32 | EFI |
| 2 | 4096 MiB | fat32 | recovery |
| 3 | ~900 GiB (all remaining minus 96 GiB) | ext4 | pop-root |
| 4 | 98304 MiB (96 GiB) | linux-swap | swap |

Apply all operations.

### 3.4 Assign mount points in the Pop!_OS installer

Back in the Pop!_OS installer partition selection screen:

**For `/dev/nvme0n1p1` (2 GB fat32):**
- Check **Use partition**
- Check **Format**
- Set Use as: **Boot /boot/efi**
- Filesystem: **fat32**

**For `/dev/nvme0n1p2` (4 GB fat32):**
- Check **Use partition**
- Check **Format**
- Set Use as: **Custom**, enter `/recovery`
- Filesystem: **fat32**

**For `/dev/nvme0n1p3` (~900 GB ext4):**
- Check **Use partition**
- Check **Format**
- Set Use as: **Root (/)**
- Filesystem: **ext4**

**For `/dev/nvme0n1p4` (96 GB swap):**
- Check **Use partition**
- Set Use as: **Swap**

### 3.5 DO NOT TOUCH nvme1

> **CRITICAL: For every partition on `/dev/nvme1n1`:**
> - Do NOT check "Use partition"
> - Do NOT check "Format"
> - Do NOT assign any mount point
> - If any checkbox is already checked, UNCHECK it

### 3.6 Create a temporary user

When prompted for user account details:

- **Full Name:** Setup Admin
- **Username:** `setupadmin`
- **Password:** (choose a temporary password you will remember)

Do NOT use `l0r3zz` as the username during installation.

### 3.7 Confirm and install

Review the partition summary one final time:
- Only nvme0n1 partitions should have checkmarks.
- nvme1n1 partitions must show no checkmarks.

Click **Erase and Install** to proceed.

Wait for installation to complete. When prompted, remove the USB drive and reboot.

---

## Phase 4: First Boot and System Baseline

### 4.1 Log in as setupadmin

After reboot, log in to the COSMIC desktop as `setupadmin`.

### 4.2 Verify nvme1 is visible but NOT mounted

```bash
lsblk -f
```

You should see `/dev/nvme1n1p1` with type `ext4` and NO mount point. If it is
auto-mounted somewhere under `/media/`, unmount it:

```bash
sudo umount /dev/nvme1n1p1
```

### 4.3 Update the base system

```bash
sudo apt update && sudo apt upgrade -y
```

### 4.4 Install tools needed by restore-new.sh

```bash
sudo apt install -y jq rsync curl flatpak snapd pipx python3-pip docker.io
sudo usermod -aG docker setupadmin
```

### 4.5 Record the setupadmin UID for reference

```bash
id setupadmin
# Expect uid=1000(setupadmin)
```

This matters because the old `/home/l0r3zz` was likely owned by UID 1000.

---

## Phase 5: Mount /home and Create l0r3zz User

This is the most critical post-install phase. Follow each step exactly.

> **IMPORTANT -- UID Preservation:** The old `l0r3zz` account was `uid=1000 gid=1000`.
> Every file on the preserved `/home` disk is owned by UID 1000. The new `l0r3zz`
> account **must** be created with the same UID/GID or you will have widespread
> permission errors. The installer's `setupadmin` user currently holds UID 1000,
> so we must reassign it first.

> **IMPORTANT -- Shell:** The `cosmic-greeter` login screen requires `/bin/bash` as
> the user's login shell. If the shell is set to `zsh` or another non-default
> shell, COSMIC enters a login loop and refuses to start the session. Always
> create the user with `-s /bin/bash`. You can switch to zsh later after
> confirming COSMIC login works.

### 5.1 Get the UUID of the home partition

```bash
sudo blkid /dev/nvme1n1p1
```

Note the `UUID="..."` value (e.g., `UUID="abcd1234-5678-90ef-..."`).

### 5.2 Move setupadmin's home directory off the /home mount point

The /home directory on the root partition currently contains `/home/setupadmin`.
We need to move it before mounting nvme1 over `/home`.

```bash
sudo mkdir /home-setup
sudo mv /home/setupadmin /home-setup/
```

### 5.3 Add /home to /etc/fstab

```bash
echo 'UUID=<paste-uuid-here>  /home  ext4  defaults  0  2' | sudo tee -a /etc/fstab
```

Replace `<paste-uuid-here>` with the actual UUID from step 5.1.

### 5.4 Mount /home

```bash
sudo mount /home
```

### 5.5 Verify your old data is intact

```bash
ls -la /home/l0r3zz/
ls /home/l0r3zz/tarnover-refresh-export/meta/host.txt
```

You should see your existing files. If not, STOP and troubleshoot before continuing.

### 5.6 Verify file ownership UIDs match expectations

```bash
stat -c '%u %g %n' /home/l0r3zz/.bashrc
```

Expected: `1000 1000 /home/l0r3zz/.bashrc`. Cross-reference with the identity
file saved in Phase 0:

```bash
cat /home/l0r3zz/tarnover-refresh-scripts/l0r3zz-identity.txt
```

### 5.7 Reassign setupadmin's UID/GID to free up 1000

The installer gave `setupadmin` UID 1000. We need to move it out of the way:

```bash
sudo usermod -u 1100 setupadmin
sudo groupmod -g 1100 setupadmin
sudo find /home-setup/setupadmin -user 1000 -exec chown 1100 {} \;
sudo find /home-setup/setupadmin -group 1000 -exec chgrp 1100 {} \;
sudo find /run /tmp -user 1000 -exec chown 1100 {} \; 2>/dev/null || true
```

### 5.8 Create required groups (if they don't exist yet)

Some supplementary groups from the old system may not exist on the fresh install.
Create them before adding the user:

```bash
getent group docker  >/dev/null || sudo groupadd docker
getent group ollama  >/dev/null || sudo groupadd ollama
getent group dialout >/dev/null || true   # usually exists by default
getent group lpadmin >/dev/null || true   # usually exists by default
getent group plugdev >/dev/null || true   # usually exists by default
```

### 5.9 Create the l0r3zz user with preserved UID 1000

Reproduce the exact identity from the old system (UID 1000, GID 1000, all
supplementary groups, `/bin/bash` shell):

```bash
sudo groupadd -g 1000 l0r3zz
sudo useradd -u 1000 -g 1000 -d /home/l0r3zz -s /bin/bash \
  -G sudo,adm,dialout,lpadmin,docker,ollama,plugdev \
  -M l0r3zz
```

The `-M` flag prevents creating a new home directory (the existing one is already there).

Verify the identity matches the old system:

```bash
id l0r3zz
# Expected: uid=1000(l0r3zz) gid=1000(l0r3zz) groups=1000(l0r3zz),4(adm),20(dialout),27(sudo),121(lpadmin),...,docker,...,ollama
```

### 5.10 Set password for l0r3zz

```bash
sudo passwd l0r3zz
```

### 5.11 Register l0r3zz with AccountsService (for COSMIC login screen)

The `cosmic-greeter` login screen uses AccountsService to discover users. Users
created via `useradd` (command-line) do not automatically get an AccountsService
entry, which means `l0r3zz` may not appear on the graphical login screen.

Create the entry manually:

```bash
sudo mkdir -p /var/lib/AccountsService/users
sudo tee /var/lib/AccountsService/users/l0r3zz > /dev/null <<'EOF'
[User]
SystemAccount=false
Language=en_US.UTF-8
Session=cosmic
EOF

sudo systemctl restart accounts-daemon
```

### 5.12 Verify l0r3zz can log in via TTY first

Open a new TTY (Ctrl+Alt+F3) and log in as `l0r3zz` with the password you set.

Verify:

```bash
whoami
# l0r3zz

id
# uid=1000(l0r3zz) gid=1000(l0r3zz) groups=1000(l0r3zz),4(adm),20(dialout),27(sudo),...

ls ~/
# Should show your existing files

ls ~/tarnover-refresh-export/meta/host.txt
# Should exist
```

### 5.13 Log in to COSMIC desktop as l0r3zz

Return to the graphical login screen (Ctrl+Alt+F1 or F2), log out of `setupadmin`,
and log in as `l0r3zz`.

On first COSMIC login, `cosmic-initial-setup` will launch a setup wizard. This is
normal -- it configures accessibility, display scaling, dock placement, and theme
preferences for the new COSMIC desktop. The old GNOME configuration in `~/.config/dconf/`
and `~/.config/gnome-*` is harmless and ignored by COSMIC. COSMIC stores its own
config in `~/.config/cosmic/` using RON files, which it auto-generates with defaults.

Complete the setup wizard, then continue to Phase 6.

---

## Phase 6: Run restore-new.sh

### 6.1 Copy scripts into place (Dropbox is not available yet)

```bash
cp -a /home/l0r3zz/tarnover-refresh-scripts /home/l0r3zz/restore-scripts
cd /home/l0r3zz/restore-scripts
```

### 6.2 Run the restore

```bash
sudo ./restore-new.sh /home/l0r3zz/tarnover-refresh-export
```

This will:
- Restore third-party APT repos and signing keys
- Install every manually-installed APT package from the old system
- Reinstall Flatpak apps
- Reinstall Snap packages and restore snapshots
- Reinstall pipx, pip --user, npm global, rustup, cargo, and Go tools
- Restore systemd user units and cron jobs
- Restore Docker engine state, volumes, bind mounts, and compose projects

**Expected duration:** 30--90 minutes depending on network speed and package count.

### 6.3 Review failures

```bash
for f in ~/.cache/tarnover-refresh-restore/*.txt; do
  echo "=== $(basename "$f") ==="
  cat "$f"
  echo
done
```

Common issues:
- **apt-install-failed.txt**: Packages renamed or removed in 24.04. Search for
  replacements: `apt search <keyword>`
- **snap-install-failed.txt**: May need `--classic` or `--channel` flags. Install manually.
- **flatpak-install-failed.txt**: Remote may have changed. Try `flatpak install flathub <app-id>`.
- **cargo-install-failed.txt**: May need newer Rust toolchain. Run `rustup update` first.

### 6.4 Fix stale APT repos

After restore, some old PPAs may not support the `noble` codename:

```bash
sudo apt update 2>&1 | grep -i "does not have a Release file\|NO_PUBKEY"
```

Disable broken repos:

```bash
# Example: disable a stale PPA
sudo rm /etc/apt/sources.list.d/<stale-repo>.list
sudo apt update
```

---

## Phase 7: Post-Restore Validation

### 7.1 System health

```bash
sudo apt update
sudo apt -f install -y
journalctl -p err -b --no-pager | head -50
systemctl --failed
systemctl --user --failed
```

### 7.2 SSH and GPG

```bash
ssh-add -l
gpg --list-secret-keys
ssh -T git@github.com    # or your common remote
```

### 7.3 Docker

```bash
docker ps -a
docker images
docker compose ls
```

If Docker workloads were restored from engine state backup, containers may need
`docker compose up -d` in their project directories.

### 7.4 Development tools

```bash
rustc --version && cargo --version
go version
node --version && npm --version
python3 --version && pipx list
```

### 7.5 Reinstall Dropbox

Dropbox was intentionally excluded from the backup. Reinstall the client:

```bash
# Download and install from https://www.dropbox.com/install-linux
# Or via the .deb package:
cd /tmp
wget -O dropbox.deb "https://www.dropbox.com/download?dl=packages/ubuntu/dropbox_2024.04.17_amd64.deb"
sudo dpkg -i dropbox.deb
sudo apt -f install -y
```

Launch Dropbox, sign in, and it will re-sync `~/Dropbox`. Your repo checkouts
and working trees will reappear as the sync completes.

### 7.6 Remove setupadmin (optional, after everything is confirmed working)

```bash
sudo userdel -r setupadmin 2>/dev/null || true
sudo rm -rf /home-setup
```

Only do this after you are confident that:
- l0r3zz can log in to the desktop
- l0r3zz has sudo access
- All critical services and tools are working

---

## Phase 8: Re-enable 2FA (future, not automated)

Login 2FA was intentionally excluded from the automated migration. When you are
ready to re-enable it on the new system:

```bash
sudo apt install -y libpam-google-authenticator
google-authenticator
```

Follow the prompts to generate a new TOTP secret and scan the QR code with your
authenticator app. Then edit `/etc/pam.d/common-auth` to add:

```
auth required pam_google_authenticator.so
```

Place this line **before** the `pam_unix.so` line. Then set SSH to allow
keyboard-interactive auth in `/etc/ssh/sshd_config`:

```
UsePAM yes
KbdInteractiveAuthentication yes
```

Restart SSH:

```bash
sudo systemctl restart ssh
```

**Always test from a second session before closing your current one.**

---

## Quick Reference: Environment Variables

### collect-old.sh

| Variable | Default | Purpose |
|---|---|---|
| `SOURCE_ROOT` | `/` | Root of old system (use `/mnt/old-root` for live USB) |
| `SOURCE_HOME` | `$HOME` | Home dir of target user (use `/mnt/old-home/l0r3zz` for live USB) |
| `EXCLUDE_DROPBOX` | `1` | Skip Dropbox directory |
| `DROPBOX_PATH` | `$SOURCE_HOME/Dropbox` | Path to exclude |
| `BACKUP_DOCKER_VOLUMES` | `1` | Archive Docker volumes (online only) |
| `BACKUP_DOCKER_BINDS` | `1` | Archive Docker bind mounts (online only) |
| `BACKUP_HOME_CONFIG` | `0` | Archive ~/.config etc. (skip when preserving /home disk) |

### restore-new.sh

| Variable | Default | Purpose |
|---|---|---|
| `RESTORE_DOCKER_VOLUMES` | `1` | Restore Docker volume archives |
| `RESTORE_DOCKER_BINDS` | `1` | Restore Docker bind mount archives |
| `RESTORE_COMPOSE_PROJECTS` | `1` | Restore Compose project directories |
| `RUN_COMPOSE_UP` | `1` | Auto-start restored Compose projects |
| `RESTORE_DOCKER_ENGINE_STATE` | `1` | Restore /var/lib/docker from tgz |
| `RESTORE_HOME_CONFIG` | `0` | Restore ~/.config etc. (skip when preserving /home disk) |

---

## Checklist Summary

- [ ] Phase 0: Record l0r3zz identity (UID/GID/groups), run collect-old.sh online, verify export
- [ ] Phase 1: Shut down, clean hardware, install new SSD
- [ ] Phase 2: Boot live USB, verify disks and export
- [ ] Phase 3: Install Pop!_OS 24.04 with `setupadmin` user, DO NOT touch nvme1
- [ ] Phase 4: First boot, update system, install base tools
- [ ] Phase 5: Mount /home, reassign UID 1000, create l0r3zz (preserve UID/GID/groups), register with AccountsService
- [ ] Phase 6: Run restore-new.sh, review failures
- [ ] Phase 7: Validate SSH, GPG, Docker, dev tools, reinstall Dropbox
- [ ] Phase 8: Re-enable 2FA when ready (manual, not scripted)
