# Docker Deploy Standards. Version 5.2.0

This document defines rules and conventions for deploying services in Docker. It supplements `doc/standards/project_standards.md` and applies on top of it. All core requirements remain in force unless this document explicitly overrides them.

---

## Table of Contents

**01. Structure and deploy order:** 01.01 File structure - 01.02 Volumes - 01.03 Network - 01.04 Service dependencies - 01.05 Service addition order - 01.06 Docker address space (daemon.json) - 01.07 Restoring compose containers after Docker start

**02. docker-compose.yml template:** 02.01 Mandatory elements - 02.02 Optional sections (02.02.01 environment - 02.02.06 Docker socket) - 02.03 Rules - 02.04 Volume naming - 02.05 Network - 02.06 Port publication - 02.07 Reverse proxy (internet access)

**03. Firewall (ufw):** 03.01 Rules - 03.02 Setup order

**04. Backup:** 04.01 What to back up - 04.02 Archive location and naming - 04.03 Backup requirements

**05. Service documentation template:** 05.01 Mandatory sections - 05.02 Optional sections - 05.03 Run-based services (ephemeral tools)

**06. Machine documentation overrides:** 06.01 Purpose - 06.02 `override/` structure - 06.03 Rules - 06.04 Machine addition order

**07. Relations and versioning:** 07.01 Related documents - 07.02 Versioning

---

## 01. Structure and deploy order

### 01.01. File structure

*Mandatory.*

- Each service gets its own folder `~/.docker/<service>/`
- Inside the service folder - `docker-compose.yml` and, when needed, subfolders with configuration files (keys, parameters)
- For a web application subsystem the service placement follows `web_standards.md` (06.01): `docker-compose.yml` lives in the repository (`web/deploy/docker/`), not in `~/.docker/<service>/`

### 01.02. Volumes

*Mandatory.*

- Volumes are created automatically on the first `docker compose up -d` - no explicit creation needed
- Service data is stored **only in named volumes** - never in bind mounts
- Declare every volume with an explicit `name:` to exclude project auto-prefixes (see 02.04)
- Name pattern: `<service>_vol` for one volume, `<service>_<purpose>_vol` for several (for example `scrutiny_config_vol`, `scrutiny_influxdb_vol`)
- `docker compose down` stops and removes the container but **does not remove named volumes** - data survives
- To delete volume data completely, remove the volume explicitly
- Bind mounts are allowed for:
  - **Configuration files** (keys, parameters): path relative to the service folder `./<dir>:<container_path>:ro`, always read-only (`:ro`), files placed in a service subfolder (`~/.docker/<service>/keys/`)
  - **Docker socket** for Docker management: `/var/run/docker.sock:/var/run/docker.sock` (without `:ro`)

### 01.03. Network

*Mandatory.*

- All containers run on one external network `docker_network`
- Create the network once before the first service
- Containers address each other by `container_name` (for example `postgres:5432`)
- In every compose file the network is declared as external
- The default bridge and auto-network address space is configured separately via daemon.json (see 01.06)

### 01.04. Service dependencies

*Mandatory.*

- If a service depends on another (for example Gitea needs PostgreSQL), configure and start the dependency first
- Deploy order is governed by documentation, not by `depends_on` in the compose file
- Connect to a dependency through `container_name` and the internal port (for example `postgres:5432`)

### 01.05. Service addition order

*Mandatory.*

1. Create the service folder and, when needed, subfolders for configuration files
2. Create `docker-compose.yml` from the template (section 02)
3. Start the container (`docker compose up -d`)
4. Decide port publication and host interface binding (02.06); do not create ufw rules for published Docker ports (03.01)
5. Verify operation (healthcheck, curl, docker exec)
6. If needed, perform initial setup inside the container (create users, databases, load data)

### 01.06. Docker address space (daemon.json)

*Mandatory.*

- Move the default bridge `docker0` and auto-networks (default bridge, compose project networks, `docker network create` without an explicit subnet) out of `172.16.0.0/12` via `/etc/docker/daemon.json`: `bip` sets the `docker0` subnet, `default-address-pools` sets the pool for auto-networks.
- Chosen blocks must not overlap `docker_network` (01.03), the site LAN or the VPN range.
- Concrete `bip` and `default-address-pools` values depend on the site VPN/LAN range: an example for VPN `172.16.0.0/12` is in `install/01_docker/docker.md`; applied values are recorded in `override/<hostname>/_machine/network.md`.
- The working network `docker_network` (01.03) is created with an explicit subnet outside Docker and VPN ranges and does not depend on `daemon.json`.
- The same `/etc/docker/daemon.json` sets default log driver limits for containers without their own `logging` section: keys `log-driver` and `log-opts` (`max-size`, `max-file`; 02.03).

### 01.07. Restoring compose containers after Docker start

*Mandatory to diagnose after every Docker restart.*

- **Symptom** - after a Docker restart, running containers have no network endpoints: `.NetworkSettings.Networks` and `Ports` are empty, the network `containers` section is empty, bridges are DOWN and no veth interfaces exist; services are unreachable although containers report `Up`.
- **Cause class** - an upstream Docker regression on affected versions, fixed in newer releases; do not look for application or compose configuration errors first.
- **Action** - recreate compose containers without configuration changes (volumes persist): `cd ~/.docker/<service> && docker compose up -d --force-recreate`.
- **Diagnostics** - `docker network inspect <network>` (empty `containers` section) and `systemctl is-enabled docker-compose-restore.service` confirm the state.
- **Restart ordering unit** - on affected Docker versions only, add a restore systemd unit (`After=docker.service`, `Requires=docker.service`) that recreates compose containers after Docker starts; remove it after the Docker upgrade.
- **DHCP LAN port bindings** - on any Docker version, a host publishing ports on a DHCP LAN address requires `NetworkManager-wait-online.service` to be enabled before `docker.service` starts; this is a boot-order requirement independent of the regression.

---

## 02. docker-compose.yml template

### 02.01. Mandatory elements

*Mandatory.*

Every `docker-compose.yml` must contain:

```yaml
services:
  <service>:
    image: <image>:<tag>
    container_name: <service>
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    ports:
      - "<host_ip>:<host_port>:<container_port>"
    volumes:
      - <service>_vol:<container_path>
    networks:
      - docker_network

volumes:
  <service>_vol:
    name: <service>_vol

networks:
  docker_network:
    external: true
```

Include the `ports` section only when port publication is needed (02.06); omit it for a service reachable only by other `docker_network` containers. The `<host_ip>` binding follows 02.06.

### 02.02. Optional sections

*Optional - as the service requires.*

#### 02.02.01. environment - environment variables

Used to pass configuration to the service (credentials, database settings, launch parameters).

```yaml
environment:
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  GITEA__database__HOST: postgres:5432
```

- Documentation may show default password values for copy-paste convenience, marked as requiring a change for production
- For production, move secrets to a `.env` file with `${VARIABLE}` substitution
- `.env` is not committed to the repository
- `.env.example` is a template listing all `${VARIABLE}` entries used in the service compose files, without values. Keep it next to `.env`, update it in sync when variables are added or removed, and commit it to the repository
- To connect to another service use `container_name:port` (for example `postgres:5432`)

#### 02.02.02. Multiple ports

If a service listens on several ports (HTTP + SSH, REST + gRPC, TCP + UDP), describe each on a separate line:

```yaml
ports:
  - "3001:3001"
  - "222:22"
  - "6881:6881"
  - "6881:6881/udp"
```

The `<host_ip>` binding (prefix before `<host_port>`) for each published port follows 02.06.

#### 02.02.03. Multiple volumes

For services with several volumes, clarify purpose with a suffix:

```yaml
volumes:
  - sftp_vol:/home
  - ./keys:/home/admin/.ssh/keys:ro
```

```yaml
volumes:
  sftp_vol:
    name: sftp_vol
```

- Named volumes - for service data
- Bind mounts (`./`) - only for configuration files, always `:ro`

#### 02.02.04. deploy - GPU acceleration

For GPU services (for example LLM):

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

- Requires `nvidia-container-toolkit` preinstalled on the host

#### 02.02.05. cap_add and devices - hardware access

For services requiring direct device access (for example reading disk SMART data):

```yaml
cap_add:
  - SYS_RAWIO
devices:
  - /dev/nvme0n1:/dev/nvme0n1
```

- `cap_add` - additional Linux capabilities unavailable to the container by default
- `devices` - pass host block devices into the container

#### 02.02.06. Docker socket - Docker management

For services managing Docker (monitoring, orchestration):

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

- The Docker socket grants full access to the Docker API on the host

### 02.03. Rules

*Mandatory.*

- **container_name** - set explicitly. Otherwise Docker generates a name with the folder prefix
- **restart: unless-stopped** - the standard restart policy for all services
- **image** - specify a version tag (`postgres:18`) or `:latest` when auto-update is acceptable. Never use untagged images - state `:latest` explicitly. For custom images built from a Dockerfile, specify `build:` together with `image:` - the name and tag of the built image (for example `image: superset-custom:latest` with `build: .`), so the image gets an explicit name instead of an anonymous hash
- **logging** - `json-file` driver limits: `max-size` (for example `10m`) and `max-file` (for example `3`); without limits container logs grow unbounded; the global alternative for all services is `log-driver` and `log-opts` in `/etc/docker/daemon.json` (01.06)
- **ports** - format `"[<host_ip>:]<host_port>:<container_port>"` in quotes; set the `<host_ip>` binding per 02.06. For UDP add a suffix: `"6881:6881/udp"`
- **volumes** - named volumes only for data. Bind mounts are allowed for configuration files with `:ro` and for the Docker socket without `:ro`
- **networks** - all services connect to the external network `docker_network`
- Do not use the `version` directive in docker-compose.yml (obsolete since Compose v2)

### 02.04. Volume naming

*Mandatory.*

- Named volumes are declared with an explicit `name:` to exclude project auto-prefixes
- Name pattern: `<service>_vol` for one volume, `<service>_<purpose>_vol` for several
- Without `name:` Docker prepends the folder name (for example `postgres_postgres_vol`)

### 02.05. Network

*Mandatory.*

Canon - 01.03: one external network `docker_network`, created once before the first service; every compose file declares it as external; containers address each other by `container_name` (for example `postgres:5432`).

### 02.06. Port publication

*Mandatory when publishing ports.*

Publish ports only when the service must be reachable from outside `docker_network` - inter-service traffic needs no publication, containers communicate by `container_name` (01.03).

Docker published ports **are not governed by ufw**: the daemon inserts its own iptables rules (`nat/DOCKER`, `FORWARD`) before ufw chains, so a port published without binding is reachable from the LAN regardless of firewall rules. Access control is done by binding to a host interface:

| Who is allowed | Format | ufw |
|----------------|--------|-----|
| Only other containers | `ports` not published | Not needed |
| Only the host itself | `"127.0.0.1:<host_port>:<container_port>"` | Not needed |
| From the LAN | `"<LAN_IP>:<host_port>:<container_port>"` - a deliberate decision; access is governed by the service itself (authentication) or VPN | Rule has no effect |
| From the internet | via reverse proxy (02.07): backends publish no ports, the proxy publishes `80/443` | Not needed |

If source filtering is required for a published port, use the `ufw-docker` utility (rules in the `DOCKER-USER` chain). This option is optional: apply it for individual tasks on explicit user request; it is not part of the base setup.

Binding to `<LAN_IP>` opens the port only on that address - the machine's own `localhost` does not answer because the port does not listen on loopback. For a web interface used both from other machines and from the machine itself (dashboard, admin panel), add both bindings to `ports` - LAN (`<LAN_IP>:<host_port>:<container_port>`) and loopback (`127.0.0.1:<host_port>:<container_port>`, the "Only the host itself" row above). After publication verify reachability on both addresses: a missing loopback binding looks like a service failure from the outside - the port works from the LAN while `localhost` connections are refused.

### 02.07. Reverse proxy (internet access)

*Optional - when the service is reachable from the internet.*

The canonical way to publish a Docker service to the internet is a reverse proxy as a separate service:

- The proxy (caddy, nginx or similar) is deployed by the common template (section 02) on `docker_network`
- The proxy publishes ports `80` and `443` without a `<host_ip>` binding - the only standard case of publication on all interfaces
- Backend services publish no ports ("Only other containers" row of 02.06); the proxy reaches them by `container_name` and internal port (for example `gitea:3000`)
- TLS terminates on the proxy: automatic ACME certificates (Let's Encrypt) or certificate files via a `:ro` bind mount
- Request routing is by domain name; public IP, DNS records and router port forwarding are outside the standard, actual values are recorded in the machine override (section 06)

Direct internet publication without a proxy (`"0.0.0.0:<host_port>:<container_port>"` or a format without `<host_ip>`) is an exception by explicit user decision: the service must provide TLS and authentication itself, and the service documentation must state the rationale.

---

## 03. Firewall (ufw)

### 03.01. Rules

*Mandatory.*

- Use `ufw` as the firewall for host services
- SSH (port 22) - allow only from the trusted subnet
- Host service ports - open individually, one rule per service
- Add a comment with the service name to every rule
- If a service uses several ports, describe each port with a separate commented rule
- Do not create `ufw` rules for published Docker ports: the daemon inserts its own iptables chains before ufw chains, so the rules have no effect (02.06). Access is determined by the port binding to the host interface

### 03.02. Setup order

*Mandatory.*

The firewall is configured at the base stage (SSH) and for host services. When adding a Docker service, no ufw rules are created - port publication and binding follow 02.06.

---

## 04. Backup

### 04.01. What to back up

*Mandatory.*

- The `~/.docker/` folder - all compose files and configurations
- All named Docker volumes
- Container logs (`json-file`) are not backed up: growth is limited by `logging` limits in compose (02.03) or the daemon.json default (01.06)

### 04.02. Archive location and naming

*Mandatory.*

- Archives live in `~/backup/docker/`
- Compose file archives: `compose_YYYYMMDD_HHMMSS.tar.gz`
- Volume archives: `<volume_name>_YYYYMMDD.tar.gz`

### 04.03. Backup requirements

*Mandatory.*

- Data in volumes of active containers may be inconsistent
- For DBMS (PostgreSQL and similar) take a dump (`pg_dump`) before backing up the volume
- When restoring a volume, create the volume first, then unpack the archive into it

---

## 05. Service documentation template

Each service is described in a separate file `<install_dir>/<service>.md`. Files follow one structure.

File locations by domain:
- `install/02_apps_main/` - main services and applications
- `install/03_apps_analytics/` - analytics stack services (databases, storage, data processing tools)

Documents in both folders follow the same template (05.01-05.03).

### 05.01. Mandatory sections

*Mandatory.*

1. **Название** (`# <service>`) + краткое описание (1-2 sentences, state ports)
2. **Установка** - folder creation + `docker-compose.yml` via heredoc (`cat > docker-compose.yml << 'EOF'`)
3. **Расположение** - host paths:
   - Compose files: `~/.docker/<service>/`
   - Volume(s): `/var/lib/docker/volumes/<volume_name>/_data`
4. **Управление** - 5 commands: start (`up -d`), stop (`down`), status (`ps`), logs (`logs -f`), update (`pull` + `up -d`). For services built from a Dockerfile (`build:`), update is `build --pull` + `up -d`
5. **Файрвол** - "Not needed": ufw does not govern published Docker ports (02.06). State the actual binding of each port - `127.0.0.1`, LAN IP, `80/443` reverse proxy (02.07) or no publication; for a LAN binding explain what governs access (service authentication, VPN)
6. **Проверка** - healthcheck commands (`curl`, `docker exec`, `docker inspect`)

### 05.02. Optional sections

*Optional - as needed.*

Add before "Установка" or after "Файрвол" as needed:

- **Подготовка** (before "Установка") - preliminary steps: package installation, database creation, key generation
- **Базовая настройка** (after "Файрвол") - mandatory initial configuration after launch: account creation, client connection, loading required data
- **Конфигурация** (after "Базовая настройка") - optional and alternative service configurations: performance tuning, advanced options. Not part of mandatory initial setup

Section order: `Подготовка` -> `Установка` -> `Расположение` -> `Управление` -> `Файрвол` -> `Базовая настройка` -> `Конфигурация` -> `Проверка`

**Root level (`##`):** only the sections listed above are allowed at the document root (`Preparation`, `Installation`, `Location`, `Management`, `Firewall`, `Base setup`, `Configuration`, `Verification`). No other sections may exist at `##` level. Put any additional material in lower-level subsections (`###` and deeper) inside one of the standard sections.

### 05.03. Run-based services (ephemeral tools)

*Optional - for ephemeral tools without a permanent service and compose file.*

For tools run as an ephemeral container via `docker run --rm` without a permanent service and compose file (for example dbt), adapt 05.01:

- **Installation** - `docker pull <image>:<tag>` (no compose file)
- **Location** - config and project file paths (profiles, mounted directory); there is no named Docker volume - state this explicitly
- **Management** - image and run commands: `pull`, `run`, `--version`, `rmi` (instead of `up`/`down`/`ps`/`logs`)
- **Firewall** - "Not needed": ports are not published, the container runs in `docker_network` and reaches dependencies by `container_name`

Root section names and their order stay standard (05.01, 05.02).

---

## 06. Machine documentation overrides (`override/`)

*Optional - for Docker documentation repositories where base instructions are universal and deviations depend on the host.*

### 06.01. Purpose

*Mandatory when machine overrides are used.*

- `install/` (or an equivalent base document directory) - the **universal base**: commands and parameters common to any machine
- `override/<hostname>/` - **ready-to-run overrides** for a specific host: not an abstract description of differences but a concrete replacement (what -> with what, where, how to apply)
- Do not store secrets (passwords, tokens, keys) in `override/` - only in `.env` / secrets of the target machine

### 06.02. `override/` structure

*Mandatory when machine overrides are used.*

```
override/
└── <hostname>/                         # short hostname (`hostname -s`), lowercase
    ├── <hostname>_services_summary.md  # machine profile and service summary table
    ├── _machine/                       # topics without an original in install/ (gpu, network, etc.)
    │   └── *.md
    └── <path_mirrored_from_install/>   # only files with real deviations
        └── <service>.md
```

### 06.03. Rules

*Mandatory when machine overrides are used.*

1. **One folder per machine.** Name = short hostname in lowercase.
2. **Mirror of the base.** The override path repeats the base document path: `install/02_apps_main/postgres.md` -> `override/<hostname>/02_apps_main/postgres.md`. Create only files with deviations.
3. **Ready commands.** The override document contains copyable bash blocks for replacement/application (sed, file rewrite, `docker compose up -d` and similar), plus a link to the base document in `install/`.
4. **No base original.** Machine topics absent from `install/` go only to `override/<hostname>/_machine/`.
5. **Machine profile.** `<hostname>_services_summary.md` - hardware/network/Docker profile and the service summary table for this machine; before work the agent determines the host (`hostname -s`) and reads the profile.
6. **Documentation in Russian**; commands as ready-to-run blocks.
7. **Web addresses in the machine profile.** In the service summary table `<hostname>_services_summary.md`, for every service with a published HTTP/HTTPS port reachable from a browser (web interface, dashboard, REST UI), state the concrete connection address `http(s)://<IP>:<port>` - with the real machine LAN IP and a subpath when needed (for example `/dashboard`); for services behind a reverse proxy - the domain `https://<domain>` (02.07). Do not state an address for services without a published web port (DB without UI, Redis, run-based, SSH-only).

### 06.04. Machine addition order

*Mandatory when machine overrides are used.*

1. Create `override/<hostname>/`.
2. Create `<hostname>_services_summary.md` (collect facts with host commands: `hostname -s`, `uname -r`, `lscpu`, `lspci`, `free -h`, `lsblk`, `ip`, `docker ps`, `docker volume ls` and GPU commands when needed).
3. For each deviation from `install/` - a mirrored override file.
4. Topics without a base - in `_machine/`.

---

## 07. Relations and versioning

### 07.01. Related documents

| Document | Relation |
|----------|----------|
| `doc/standards/project_standards.md` | Core standard; this document applies on top of it (repository structure, security, documentation) |
| `install/01_docker/docker.md`, `override/<hostname>/` | Target documents of the Docker documentation repository, formatted by sections 02, 05 and 06 of this standard |

### 07.02. Versioning

Standards package versioning is unified for all package documents. The versioning policy, registry and routing map live in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see _index_standards.md).
