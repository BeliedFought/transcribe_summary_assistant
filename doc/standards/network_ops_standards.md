# Network & Operations Standards. Version 5.2.0

Rules for connection retries, channel liveness probes, SSH client configuration, embedded SSH targets, DPI-filtered networks, selective routing, SMB shares, and system configuration mutation patterns. Apply on top of `project_standards.md`. For decision priority, see `project_standards.md` (Section 07.06).

## Table of Contents

| Section | Contents |
|---------|----------|
| **01. Connection Retries and Channel Liveness** | Exponential backoff, `[retry]` config, `Retry-After`, and HTTP status interpretation for channel probes |
| 01.01 | Exponential Backoff, `[retry]` Parameters, and Retryable Errors |
| 01.02 | HTTP Status Code Interpretation for Channel Liveness vs Endpoint Checks |
| **02. SSH Client Config and Embedded Device Quirks** | `~/.ssh/config` host blocks, `HostKeyAlias`, password-only embedded SSH, lockout protection, and `terminfo` |
| 02.01 | `~/.ssh/config` Rules, `HostKeyAlias`, and Host Key Verification |
| 02.02 | Non-Interactive SSH on Embedded Devices (`SSH_ASKPASS_REQUIRE=force`, Lockout Protection, and `TERM` / Binary Path) |
| **03. Filtered / DPI Networks, Tunnels, and SMB** | VPN protocols under DPI, DNS hijacking, SNI desync + tunnel, IPv6 blackholes, CDN routing, vendor geo-gates, and SMB |
| 03.01 | IKEv2/IPsec Blocking Under DPI |
| 03.02 | UDP-53 DNS Spoofing and Interception vs DoT/DoH |
| 03.03 | SOCKS5 TLS SNI Desync and Double-Layer Tunneling |
| 03.04 | IPv6 Tunnel Blackhole Trap |
| 03.05 | Selective CDN Domain Routing and `curl --resolve` Verification |
| 03.06 | Vendor Anti-VPN and Geo-Gates |
| 03.07 | Samba/SMB Server and Client (`/etc/fstab` `nofail,x-systemd.automount`) |
| **04. System Reliability and Config Mutation Patterns** | Periodic state from unreliable sources, phased system migrations, running-app configs, and derived vendor files |
| 04.01 | Watchdog and State Retention for Periodic Builds from Unreliable Sources |
| 04.02 | Multi-Phase Bootloader and System Config Migrations Across Reboots |
| 04.03 | Checking `/proc` Before Editing Configs Owned by Running Applications |
| 04.04 | Hashing Vendor Base Files When Generating Derived Configs |
| **05. Cross-References and Versioning** | Related standards and package versioning |
| 05.01 | Related Standards |
| 05.02 | Versioning |

---

# 01. Connection Retries and Channel Liveness

*Optional - required when the project connects to external resources or diagnoses network channels.*

## 01.01. Exponential Backoff, `[retry]` Parameters, and Retryable Errors

- Implement a shared `retry()` helper in `src/` for all external connections (databases, APIs, Ollama, SMTP).
- Read retry parameters from `[retry]` in `config/config.ini`:
  - `retry_count` - number of retry attempts (default `3`)
  - `retry_delay` - initial delay in seconds between attempts (default `2`)
- Apply exponential backoff `retry_delay * 2^attempt` capped at a maximum delay of `30` seconds.
- Log every retry attempt (`attempt`, delay, and reason). After exhausting all attempts, log the error and exit with code `1` (`project_standards.md`, Section 05.03).
- **Retryable vs non-retryable errors:**
  - Never retry authentication errors (`401`, `403`) or validation/request errors (`400`, `422`).
  - Retry only network timeouts, connection drops (`ConnectionError`, `TimeoutError`), HTTP `5xx`, and HTTP `429` (`Too Many Requests`).
  - For HTTP `429`: if the response includes a `Retry-After` header (seconds or HTTP-date), use that delay for the current attempt instead of exponential backoff and log the `Retry-After` value; otherwise use standard exponential backoff.
  - For databases: retry on `OperationalError` and `TimeoutError`; never retry on `ProgrammingError` (SQL syntax or schema errors).

## 01.02. HTTP Status Code Interpretation for Channel Liveness vs Endpoint Checks

- **Channel/route liveness checks:** when testing whether a network route, proxy, or tunnel works, treat **any HTTP status code other than `000`** as proof of a live channel. Many services return `3xx`, `403`, or `404` on root URLs over a healthy connection; record expected baseline status codes per reference URL.
- **Interpreting `000`:** when route coverage is verified as healthy, HTTP `000` indicates that the target host itself is globally unreachable rather than a local tunnel or proxy failure. Always verify and report route coverage first before diagnosing target availability.
- **CDN-backed services:** probe actual content asset URLs rather than only the apex domain, and validate from the client side in addition to inspecting routing tables (normal CDN IP rotation causes isolated route table mismatches).

---

# 02. SSH Client Config and Embedded Device Quirks

*Optional - required when accessing remote hosts or embedded devices over SSH.*

## 02.01. `~/.ssh/config` Rules, `HostKeyAlias`, and Host Key Verification

- Define a dedicated `Host <shortname>` block in `~/.ssh/config` for every managed machine and connect by `<shortname>` rather than raw IP (IPs change across DHCP and networks):

```sshconfig
Host <shortname>
    HostName <host>
    Port <port>
    User <user>
    IdentityFile ~/.ssh/<key>
    HostKeyAlias <shortname>
```

- **`HostKeyAlias` is mandatory** on every concrete `Host` block (defaulting to the first host pattern on the `Host` line; preserve any existing `HostKeyAlias` value; omit on wildcard `*` or `?` blocks). Storing keys in `known_hosts` under `HostKeyAlias` prevents `REMOTE HOST IDENTIFICATION HAS CHANGED` collisions when different machines on separate private subnets share the same RFC1918 IP (e.g., `192.168.1.1`).
- **Changed host keys:** on `REMOTE HOST IDENTIFICATION HAS CHANGED`, never wipe `known_hosts` blindly. Verify the host fingerprint on the target machine (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`), confirm the change is legitimate (OS reinstall or hardware replacement), and remove the stale entry by alias (`ssh-keygen -R <shortname>`).
- **Connection check:** run `ssh -o BatchMode=yes <shortname> 'hostname; whoami'`. For first-time connections to new hosts, `StrictHostKeyChecking=accept-new` is permitted; never use `StrictHostKeyChecking=no`.

## 02.02. Non-Interactive SSH on Embedded Devices (`SSH_ASKPASS_REQUIRE=force`, Lockout Protection, and `TERM` / Binary Path)

- **Password-only embedded SSH targets (routers, NAS without `authorized_keys` support):** automate non-interactive logins using a file-backed askpass wrapper that complies with Level 3 privilege rules (`project_standards.md`, Section 05.04: `0600` password file outside the repo, wrapper prints only the first line to `stdout` with `\r` stripped, diagnostics to `stderr` only, single-attempt marker per run). Invoke SSH with:
  - `SSH_ASKPASS_REQUIRE=force` (requires OpenSSH 8.4+)
  - `-o PubkeyAuthentication=no -o PreferredAuthentications=password -o NumberOfPasswordPrompts=1`
- **Brute-force lockout protection:** treat authentication attempts on embedded devices as a scarce resource. Never loop over multiple passwords or password files on failure. Validate the askpass wrapper locally before contacting the device, and identify the target device immediately after the first successful login via an identity command rather than pre-auth banners or unauthenticated probes.
- **Bypassing shell wrappers and `terminfo` rejections:** shell functions, aliases, or terminal multiplexers wrapping `ssh` often forward non-standard `TERM` / `terminfo` data that causes embedded CLIs (Entware, OpenWrt, Keenetic/NDMS) to drop the session immediately after authentication. In automation scripts, invoke the system binary by absolute path (`/usr/bin/ssh`) and, when needed, pass a safe fallback terminal (`TERM=xterm`).

---

# 03. Filtered / DPI Networks, Tunnels, and SMB

*Optional - required when operating in networks with active DPI, selective routing, or SMB shares.*

## 03.01. IKEv2/IPsec Blocking Under DPI

- State-level DPI systems fingerprint UDP IKEv2/IPsec packets and silently drop the initial handshake (logs show repeated IKE retransmits with zero responses). Distinguish this from bad credentials: the config is valid, but handshake packets never return. Use protocols with obfuscated or indistinguishable handshakes; note that some VPN providers disable WireGuard/OpenVPN config generation in restricted regions.

## 03.02. UDP-53 DNS Spoofing and Interception vs DoT/DoH

- **DNS response spoofing:** multiple blocked domains resolve to the same forged IP; mitigate by running a local resolver with encrypted DoT/DoH upstreams.
- **Transparent UDP-53 interception:** queries to any external UDP-53 resolver return a fixed pair of transparent proxy IPs regardless of domain. While DoT/DoH bypasses UDP-53 interception, filter out known interceptor IPs whenever aggregating DNS resolution results.

## 03.03. SOCKS5 TLS SNI Desync and Double-Layer Tunneling

- When DPI blocks by TLS SNI after TCP/TLS handshake completion (HTTP status arrives, transfer stalls at a few KB), use a two-layer bypass:
  1. Local SOCKS5 TLS desync proxy (splitting the TLS record inside the SNI extension) to hide the hostname from local DPI.
  2. Routing the target traffic through an encrypted tunnel where DPI is absent (because raw desynced `ClientHello` packets on the direct path are themselves flagged as anomalous).
- Route DNS queries through the proxy as well so domain resolution does not leak directly and bypass the desync path.

## 03.04. IPv6 Tunnel Blackhole Trap

- When DNS returns `AAAA` records on a host without working global IPv6 connectivity, a tunnel client that captures global IPv6 routes without forwarding IPv6 traffic creates an IPv6 blackhole (applications try IPv6 first and fail with TLS EOF). Configure the tunnel client for IPv4-only mode or disable IPv6 at the OS level if the network does not carry IPv6.

## 03.05. Selective CDN Domain Routing and `curl --resolve` Verification

- Shared CDN assets and subdomains resolve to IP pools distinct from the apex domain (symptom: HTML loads, but CSS/JS/images time out in the browser network tab). Inspect the exact failing asset URLs from the browser console.
- Never route entire shared CDN CIDR blocks through a selective tunnel; resolve and route specific target domains with periodic IP refresh.
- Verify whether a failure is caused by missing route coverage by testing with explicit IP resolution: `curl --resolve <host>:443:<covered-ip> https://<host>/...`. A successful response proves the tunnel works and only domain/IP route coverage is missing.

## 03.06. Vendor Anti-VPN and Geo-Gates

- Some vendors block downloads from both restricted client regions and known datacenter/VPN exit IPs (returning "location hidden" or access denied errors). Routing through a datacenter VPN will not fix this and may trigger it. Check the exit IP classification (residential vs datacenter) rather than debugging tunnel routes, or use an official mirror/package channel without the geo-gate.

## 03.07. Samba/SMB Server and Client (`/etc/fstab` `nofail,x-systemd.automount`)

- **Samba server:** the `samba` package does not always generate a valid default config before first start, and its default log path may point to an unwritable directory; write the config and explicit log path before starting `smbd`. Enable `nmbd` (NetBIOS name service) only if LAN browse discovery is required; direct IP/DNS shares need only `smbd`.
- **SMB client (`/etc/fstab`):** store credentials in a dedicated `0600` file outside home directories and always mount with `nofail` (and `x-systemd.automount` where appropriate) so an unreachable SMB server never blocks OS boot.

---

# 04. System Reliability and Config Mutation Patterns

*Required when building periodic state updaters, system config mutators, or derived vendor configs.*

## 04.01. Watchdog and State Retention for Periodic Builds from Unreliable Sources

- Bound every external query with a strict timeout or watchdog process so a hung upstream never blocks the periodic update loop indefinitely.
- Never overwrite working state with an empty aggregate result caused by a transient upstream outage.
- Retain the last known good value per item (using per-item state files) when an item fails to respond in the current cycle; expire stale entries only for items that actively responded.
- Apply volatile runtime state that does not survive reboot (routes, firewall sets, sysctl/runtime knobs) via full idempotent reload from on-disk state rather than incremental deltas between cycles.

## 04.02. Multi-Phase Bootloader and System Config Migrations Across Reboots

- Execute high-risk system state migrations (bootloader parameters, initramfs, core network/auth services) in separate phases across a reboot or service restart.
- Keep fallback/legacy entries intact during the migration phase; remove legacy state only in a separate cleanup command after automated verification confirms the new state is active.
- Guard the destructive cleanup step with an explicit live-state invariant check (e.g., abort cleanup if the target kernel/mode is not currently active), never relying on a confirmation flag alone.

## 04.03. Checking `/proc` Before Editing Configs Owned by Running Applications

- Applications that rewrite their own config files on exit will overwrite external edits made while the process is running. Modify such configs only while the owning application is stopped (`stop -> atomic write -> start and wait for readiness`).
- Detect whether the owning application is running by inspecting `/proc` directly without spawning fragile external wrapper utilities. If the user explicitly targeted that item, fail and stop when the process is running; in batch mode (`--all`), skip the item with a `[*]` warning (`cli_data_standards.md`, Section 05.02).
- Validate service configuration syntax with the daemon's native check command (e.g., `sshd -t`, `nginx -t`, `visudo -cf`) before restarting the service.

## 04.04. Hashing Vendor Base Files When Generating Derived Configs

- When generating a config artifact by patching or templating on top of a vendor-supplied file, record the source file path and cryptographic hash alongside the derived artifact.
- On subsequent runs (such as after an OS package upgrade), recompute the vendor file hash and rebuild the derived artifact if the base file changed. When encountering an existing file without recorded state metadata, establish the baseline without blindly overwriting user modifications.

---

# 05. Cross-References and Versioning

## 05.01. Related Standards

| Document | Relationship |
|----------|--------------|
| `doc/standards/project_standards.md` | Core standard: `[retry]` in `config.ini` (01.02), external connections (02.01-02.08), atomic file writes and `--dry-run` (03.01), security and sudoers/privilege levels 0-3 (05.01, 05.04) |
| `doc/standards/cli_data_standards.md` | Entry points (`run/`), CLI contract, mutator item status contract (`05.02`), and hardware/environment diagnostics (`02.02`) |
| `doc/standards/code_standards.md` | Bash and busybox `ash` scripting rules (`05.01`-`05.07`) |

## 05.02. Versioning

Unified package SemVer is governed by `doc/standards/_index_standards.md` and `project_standards.md` (Sections 07.04, 07.05).
