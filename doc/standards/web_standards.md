# Web Standards. Version 5.2.0

This document defines rules for developing and deploying web applications: a FastAPI backend (uvicorn) and an nginx web server with one or more fronts. Part I (sections 01-04) covers development and local launch; Part II (sections 05-13) covers deployment and relations. It supplements `project_standards.md` and applies on top of it. All core requirements remain in force unless this document explicitly overrides them. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

---

## Table of Contents

**01. Scope and architecture:** 01.01 Purpose and applicability - 01.02 Terms - 01.03 Production topology - 01.04 Deployment models

**02. Repository structure:** 02.01 Autonomous web subsystem - 02.02 Tooling - 02.03 Single front - 02.04 Multiple fronts - 02.05 Deploy artifacts - 02.06 Agent folders in the repository - 02.07 Runtime data - 02.08 Front UI base

**03. Application:** 03.01 FastAPI skeleton - 03.02 Health endpoint - 03.03 Prefixes and access - 03.04 Configuration - 03.05 Graceful shutdown - 03.06 Database

**04. Local launch:** 04.01 Entry point - 04.02 Static without nginx

**05. Model A (host):** 05.01 Placement - 05.02 systemd unit - 05.03 nginx on the host

**06. Model B (Docker):** 06.01 Application compose - 06.02 nginx service - 06.03 Deploy order

**07. nginx:** 07.01 Server block template - 07.02 Proxying - 07.03 Static - 07.04 Multiple fronts

**08. TLS:** 08.01 VPS (ACME) - 08.02 LAN (self-signed)

**09. Firewall:** 09.01 Model A - 09.02 Model B

**10. Update and rollback:** 10.01 Update sequence - 10.02 Rollback

**11. Logging:** 11.01 Backend - 11.02 nginx

**12. Service documentation:** 12.01 Document template - 12.02 Boundary with the deploy family - 12.03 spec_ui.html

**13. Relations and versioning:** 13.01 Related documents - 13.02 Versioning

---

# Part I. Development

## 01. Scope and architecture

### 01.01. Purpose and applicability

*Mandatory when creating a web application.*

- The subject is a web application: an HTTP backend in Python (FastAPI) and an nginx web server serving one or more fronts
- The standard applies to repositories containing a `web/` directory (02.01); it does not apply to repositories without a web subsystem
- Core standard requirements apply from inside `web/` - exact adaptations are listed in 02.01; other requirements (code, output, security, git, workflow) apply unchanged

### 01.02. Terms

*Mandatory.*

- **Backend** - the FastAPI application under uvicorn: the single API serving process for all fronts
- **Front** - an nginx instance (server block) with its own port, interface binding, static and template set, and list of proxied prefixes; there is one backend - there may be several fronts (07.04)
- Package terms - `project_standards.md`, 08

### 01.03. Production topology

*Mandatory.*

Target image of the deployed application, shared by both models:

1. nginx is the only entry point: publishes 80 and 443; port 80 serves only ACME challenge and redirects to 443
2. TLS terminates on nginx (08)
3. The backend is not reachable directly from the network: model A listens on `127.0.0.1:<port>`, model B publishes no ports
4. nginx serves front static files directly (07.03); API is proxied to the backend (07.02)
5. The backend exposes an unauthenticated health endpoint `GET /healthz` (03.02) - used by launch and update procedures

### 01.04. Deployment models

*Mandatory - choose one model per application.*

| Model | Composition | When to choose |
|-------|-------------|----------------|
| A - host | backend systemd unit + nginx from host packages (05, 07, 08, 09.01) | Host without Docker; minimum layers |
| B - Docker | compose: backend container + nginx container on `docker_network` (06) | Host already on Docker infrastructure |

Mixing models in one application is not allowed. Existing host Docker infrastructure is described in `deploy_docker_standards.md`.

---

## 02. Repository structure

### 02.01. Autonomous web subsystem

*Mandatory.*

The whole web subsystem lives in the `web/` directory and is autonomous: its own configuration, secrets, data, logs, SQL and tooling. Core rules about root folders (`project_standards.md`, 01.01, 01.02, 04.06) apply from inside `web/`: `config` -> `web/config`, runtime data -> `web/var/` (02.07: portable - `web/var/user`, service - `web/var/system`), `sql` -> `web/sql`, entry points `run` -> `web/run`, `.env` -> `web/.env`, `pyproject.toml` -> `web/pyproject.toml` (including the `[project]` section with application dependencies), `uv.lock` -> `web/uv.lock`. `requirements.txt` and `requirements-dev.txt` are not kept in `web/` - dependencies are pinned in `pyproject.toml` and the lockfile. A pure web repository does not create root `config/`, `data/`, `sql/`, `log/`, `var/`, `.env`. Placing code in `web/` instead of `src/` is a deliberate deviation from `project_standards.md` (01.01), recorded by this document.

```
web/                              # autonomous web subsystem
├── __init__.py                   # web package
├── __main__.py                   # entry point: read [web] from config.ini, start uvicorn
├── app.py                        # app factory: create_app()
├── routes/                       # routers: api_*.py (JSON API), page_*.py (SSR)
├── deps.py                       # FastAPI dependencies (authorization, DB sessions)
├── health.py                     # GET /healthz (03.02)
├── localization.py               # backend i18n (project_standards.md, 04.01)
├── config/
│   ├── config.ini                # [app] mandatory, [web] - host, port, reload; prod file not committed (12.02)
│   └── config.ini.example        # structure template; migration source (12.02); committed
├── .env                          # secrets (0600); not committed
├── .env.example                  # variable template without values
├── .dockerignore                 # build context exclusions (06.01), at the web/ context root
├── pyproject.toml                # [project] dependencies (== pins), [dependency-groups] dev, [tool.ruff], [tool.mypy]
├── uv.lock                       # full dependency tree lockfile; committed, used in deploy (uv sync --frozen)
├── static/                       # front static files: css/, js/, img/
├── templates/                    # Jinja2 templates (SSR)
├── var/                          # runtime data (02.07); not committed
│   ├── user/                     # portable, backed up: db/, upload/, export/, backup/, keys/, ext/
│   └── system/                   # machine-local, reproducible: log/, cache/, tmp/, state/, session/, static/
├── sql/
│   ├── ddl/                      # schema
│   ├── migrations/               # M<N>_<description>.sql (project_standards.md, 03.02.03)
│   ├── queries/, dml/
│   └── _index_sql.md
├── run/                          # CLI scripts: db_migrate.py and others (project_standards.md, 03.03)
└── deploy/
    ├── nginx/<app>.conf          # server block template (multiple fronts - <front>.conf)
    ├── systemd/<app>.service     # unit template (model A)
    └── docker/
        ├── Dockerfile            # backend image (model B)
        └── docker-compose.yml    # model B
```

- The `.venv` directory and `.python-version` file live in the repository root (`project_standards.md`, 01.07); run from the repository root
- Create folders only when used: an API-only project has no `templates/`; a project without a DB has no `sql/` and no `var/user/db/`; model A has no `deploy/docker/`
- Initializing a pure web repository adapts `project_standards.md` steps (07.03): subsystem structure per this section (02.01), runtime `web/var/` (02.07), config and secrets in `web/`

### 02.02. Tooling

*Mandatory.*

- Application dependencies - `[project] dependencies` in `web/pyproject.toml` pinned with `==` (`project_standards.md`, 01.06); dev dependencies (ruff, mypy) - the `[dependency-groups] dev` group; do not mix mechanisms
- `web/uv.lock` - full dependency tree lock; committed and used in deploy: host model - `uv sync --frozen --no-dev`, Docker - `uv sync --frozen --no-install-project --no-dev` (05.01, 06.01); local development - `uv sync`
- Set the environment path with `UV_PROJECT_ENVIRONMENT`: without it uv creates `.venv` next to `pyproject.toml` (in `web/`), while the norms require root `.venv` (01.01, `project_standards.md`, 01.07) and `/opt/<app>/.venv` (05.01). Local development from `web/`: `UV_PROJECT_ENVIRONMENT=../.venv uv sync`; a relative `UV_PROJECT_ENVIRONMENT` path resolves from the workspace root (`web/`)
- ruff and mypy configuration live in `web/pyproject.toml`, sections `[tool.ruff]`, `[tool.mypy]` (sets and parameters per `code_standards.md`, 08); do not add build sections to pyproject - a web application is not a CLI package
- Pre-commit checks from `web/`: `ruff check .` and `mypy .`

### 02.03. Single front

*Mandatory - default mode.*

By default the application has one front: its assets are `web/static/` and `web/templates/`. The nginx configuration name is `<app>.conf` (07.01).

### 02.04. Multiple fronts

*Optional - only by explicit user decision.*

When adding a second and further fronts, group assets by front:

```
web/
└── fronts/
    ├── public/
    │   ├── static/               # public front static files
    │   └── templates/            # public front templates
    └── local/
        ├── static/               # local front static files
        └── templates/            # local front templates
```

- Front name - Latin, kebab-case, role-descriptive: `public`, `local`, `admin`
- When moving to `fronts/`, do not keep single `web/static/` and `web/templates/`; nginx templates are named `<front>.conf` (07.04)
- Each front is described by four items: name, port + binding, TLS, list of proxied prefixes (07.04)

### 02.05. Deploy artifacts

*Mandatory when deploying.*

- `web/deploy/` is the source of deploy artifacts; real configurations live in system locations: `/etc/nginx/sites-available/`, `/etc/systemd/system/`, on a model B host - in the container
- When changing production configuration, update the `web/deploy/` template in the same change; template and production configuration must not diverge
- Do not create executable deploy scripts in the repository - describe procedures in the service documentation (12.01)

### 02.06. Agent folders in the repository

*Mandatory.*

`doc/`, `diag/`, `test/`, `debug/`, `tmp/` stay in the repository root per `project_standards.md` (01.01) - they belong to the repository, not the web subsystem, and do not move into `web/`. The mandatory `doc/specs/spec_ui.html` covers console output and API (12.03).

### 02.07. Runtime data

*Mandatory.*

All data the application creates during operation lives in one directory `web/var/` and is split into two classes: `var/user/` - user runtime (portable and backed up), `var/system/` - service runtime (machine-local, reproducible). `web/var/` is not committed.

**User runtime `web/var/user/`:**

| Folder | Purpose | Examples |
| --- | --- | --- |
| `db/` | Embedded databases and local stores | application SQLite, local mart, local job queue, WAL journals next to the DB |
| `upload/` | User files (originals) | documents, images, attachments, imported datasets |
| `export/` | Artifacts produced for delivery | reports, exports, archives, generated documents |
| `backup/` | Application data backups | DB dumps, snapshots, pre-migration copies |
| `keys/` | Keys without which data is unreadable or unrecoverable | data encryption, data-bound signatures; mode 700 |
| `ext/` | Extensions installed at runtime | plugins, themes, custom templates |

**Service runtime `web/var/system/`:**

| Folder | Purpose | Examples |
| --- | --- | --- |
| `log/` | Application logs | log files, `keep_last` rotation |
| `cache/` | Reproducible cache | responses, computations, thumbnails and derived media, search indexes, downloaded external artifacts and models |
| `tmp/` | Temporary and intermediate | partial uploads, unpacking, intermediate exports; cleaned by TTL and at startup |
| `state/` | Small mutable state | locks, pids, counters, sync cursors, mail queue |
| `session/` | Server-side sessions | for file storage instead of a DB |
| `static/` | Generated static files | built assets, static collection when served from files |

**Mapping (to avoid creating new folders):**

| Artifact | Class |
| --- | --- |
| media, attachments, incoming downloads | `user/upload/` (derived - `system/cache/`) |
| reports, generated, outgoing downloads | `user/export/` |
| snapshots, dumps | `user/backup/` |
| thumbnails, search-index, models, compiled | `system/cache/` |
| locks, pid, counters, spool | `system/state/` |
| themes, plugins | `user/ext/` |
| session keys (ephemeral) | `system/session/` or `.env` |

The listed subfolders are a closed vocabulary: a new artifact type maps to the nearest subfolder by the mapping table; extending the vocabulary requires editing this document only, without project overrides.

**Rules:**

- One root, one config key: `[paths] var_folder` (default `var/` inside `web/`); subfolders derive from the root, no separate keys
- The application idempotently creates required subfolders at startup; unused ones are not created
- Owner of `web/var/` - the service user; `user/keys/` - mode 700
- `web/var/` is fully excluded from git (`.gitignore`)
- Docker (model B): a named volume mounts only under `var/user/`; `var/system/` stays inside the container and is rebuilt on recreation; to preserve file logs - a separate volume on `var/system/log/`
- Backup: all of `var/user/`, including `keys/`, but excluding `var/user/backup/` (excluded to avoid recursion); `var/system/` is not backed up
- Moving to another machine with the same data: the package is `var/user/` + `config/config.ini` + `.env`; `var/system/` is recreated
- File-based server sessions (`system/session/`) are allowed only for single-process deployment; with multiple workers store sessions in a DB or external store, otherwise a shared volume is required
- Volume mount point ownership (model B): the runtime directory owner is the unprivileged service user; set with `chown` during image build or in the container entrypoint at startup; the application runs as an unprivileged user
- `system/cache` and `system/tmp` may be mounted as tmpfs: data is regenerable and does not survive container restart - that is normal
- Migrating an existing web project to `var/`: `web/data` -> `web/var/user/db`, `web/data/backup` -> `web/var/user/backup`, `web/log` -> `web/var/system/log`; update the config key and compose; migrate with the service stopped
- Combined project (CLI + `web/`): each part has its own runtime (CLI - root `data/`, `log/`; web - `web/var/`). A shared DB lives in exactly one place, per the project specification; duplication is not allowed
- External DBMS (PostgreSQL, MySQL and others) are not placed in `var/` - they have their own volume or service; `user/db/` is for embedded databases only
- Cleanup: `tmp/` - at startup and by TTL, `cache/` - by TTL, `log/` - by `keep_last` rotation (`project_standards.md`, 04.06)
- Runtime never contains: code, templates, source static files, `config/`, `.env`, SQL migrations

### 02.08. Front UI base

*Mandatory - choose one UI base per front; record the choice in the project specification (`project_standards.md`, 07.02).*

| Base | Composition | When to choose |
|--------|-------------|----------------|
| A - no framework (vanilla) | own CSS/JS in `web/static/` | Simplest interface: one or two pages without typical components |
| B - Bootstrap 5 | Bootstrap component CSS and JS | Classic interface on ready components; maximum documentation and examples |
| C - Tabler | dashboard style on top of Bootstrap | Portals and dashboards: ready neat look, dark and light themes |

- Mixing several UI bases on one front is not allowed. Tabler is built on Bootstrap: its capabilities are available and it does not count as a second base
- Frontend builds (npm, webpack, vite and similar) are not used. Connect the base in one of two ways: a CDN link or a vendor copy in `web/static/vendor/` (files under git)
- For an externally accessible service prefer the vendor copy - independence from the external network; a local tool may use a CDN. Static caching - 07.03
- General-purpose client libraries (charts, tables and similar) are connected the same way, without a build; example - Apache ECharts for charts
- External resources over `https://` only (`code_standards.md`, 04.03)

---

## 03. Application

### 03.01. FastAPI skeleton

*Mandatory.*

- App factory: `web/app.py` exports `create_app()` - application configuration is assembled in the factory, there is no global application object
- Routers in `web/routes/`: files `api_<domain>.py` - JSON API, `page_<domain>.py` - SSR pages (Jinja2 via `templates/`); name hierarchy from general to specific (`code_standards.md`, 02.01)
- Shared dependencies (authorization, DB sessions) in `web/deps.py` through `Depends`
- Naming, typing, docstrings per `code_standards.md` (02.01, 02.03, 02.04); errors per core standard 05.02; validate external input before use (05.01)

### 03.02. Health endpoint

*Mandatory.*

- Route `GET /healthz` - unauthenticated, response `200` with JSON `{"status": "ok", "version": "<APP_VERSION>"}`
- Used by: local launch (04.01), update and rollback procedures (10), post-start checks
- Business checks (database availability) are not included in `/healthz` - the endpoint reports process liveness

### 03.03. Prefixes and access

*Mandatory.*

- Prefix `/api/` - public JSON API
- Prefix `/admin/` - protected routes; authorization is performed in the application (`web/deps.py`)
- nginx is not a security boundary: front separation (07.04) limits the perimeter, but every protected application must verify authorization itself
- HTTP status codes: request errors - 4xx, application errors - 5xx; error body - one line, no raw traceback

### 03.04. Configuration

*Mandatory.*

- `web/config/config.ini` per `project_standards.md` (01.02): section `[app]` is mandatory (name, version); section `[web]` - `host`, `port`, `reload`
- Port and host come from configuration only, never hardcoded; in model B the environment variables `WEB_HOST`, `WEB_PORT` override `[web]` values (06.01)
- Secrets only in `web/.env` (mode 0600, `project_standards.md`, 05.01); keep `web/.env.example` in sync
- The web application root (analog of PROJECT_ROOT) is the `web/` directory; compute it once in `web/app.py` from `__file__`, other code imports it (`project_standards.md`, 01.04)
- Runtime data: the `[paths] var_folder` key (default `var/` inside `web/`) sets the single runtime root (02.07); subfolders derive from the root, no separate keys

### 03.05. Graceful shutdown

*Mandatory.*

- The application shuts down correctly on SIGTERM (`project_standards.md`, 05.03): uvicorn stops accepting connections and finishes active requests
- Lifespan shutdown releases resources: closes database connections, files, background tasks
- systemd and Docker deliver SIGTERM normally; `Restart=on-failure` (05.02) does not turn a normal stop into a restart

### 03.06. Database

*Mandatory when a DB is present.*

- SQL and migrations per the core standard from inside `web/`: `web/sql/` (ddl, queries, dml, migrations, `_index_sql.md`), migrations `M<N>_<description>.sql` with a `schema_version` table (`project_standards.md`, 03.02.03); DROP + CREATE on live data is forbidden
- Service scripts in `web/run/`: `db_check_connection.py`, `db_check_schema.py`, `db_init.py`, `db_migrate.py` (`project_standards.md`, 03.03.01)
- Embedded database file (SQLite) in `web/var/user/db/` (02.07); the path derives from the runtime root, never hardcoded
- A backup before migration is a mandatory step of the update procedure (10.01)

---

## 04. Local launch

### 04.01. Entry point

*Mandatory.*

- Entry point - `web/__main__.py`: reads `[web]` from `web/config/config.ini` and calls `uvicorn.run("web.app:create_app", factory=True, host=host, port=port, reload=reload)`
- Launch from the repository root: `.venv/bin/python -m web`
- Key `[web] reload = true` - development only; `false` in production
- Post-start check: `curl http://127.0.0.1:<port>/healthz`

### 04.02. Static without nginx

*Mandatory.*

- In dev mode (`[web] reload = true`) the application mounts `web/static/` via `StaticFiles` - the full cycle works without nginx
- In production nginx serves static files (07.03); serving static files from both the application and nginx at the same time is not allowed

---

# Part II. Deployment

## 05. Model A (host)

### 05.01. Placement

*Mandatory.*

- The repository lives in `/opt/<app>/` (clone/pull as root; files - `root:root`)
- Run as a dedicated system user `<app>` (`useradd --system --no-create-home <app>`); running as root or a personal user is not allowed
- File ownership - `root:root`; exception - `web/var/` (runtime data, 02.07: `var/user/` and, with file logs, `var/system/log/`): owner is the `<app>` user (set with `chown`), the service writes there under its own name
- Virtual environment - `/opt/<app>/.venv`; dependencies from the lockfile: `cd /opt/<app>/web && UV_PROJECT_ENVIRONMENT=/opt/<app>/.venv uv sync --frozen --no-dev` (exact dependency tree reproduction; without `UV_PROJECT_ENVIRONMENT` uv creates `web/.venv`, not `/opt/<app>/.venv`)

### 05.02. systemd unit

*Mandatory.*

Template - `web/deploy/systemd/<app>.service`:

```ini
[Unit]
Description=<app> web service
After=network.target

[Service]
Type=simple
User=<app>
Group=<app>
WorkingDirectory=/opt/<app>
ExecStart=/opt/<app>/.venv/bin/python -m web
EnvironmentFile=/opt/<app>/web/.env
Restart=on-failure
RestartSec=5

# hardening: recommended minimum for a service with user data
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/opt/<app>/web/var
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

- `EnvironmentFile` loads secrets from `web/.env` (0600); secrets are not stored in the unit
- The hardening block (optional, recommended minimum for a service with user data): writes only to `web/var/` - user runtime and `var/system/log/` (02.07), the rest of the filesystem is read-only for the process
- Install: `cp web/deploy/systemd/<app>.service /etc/systemd/system/` -> `systemctl daemon-reload` -> `systemctl enable --now <app>`
- Control: `start`, `stop`, `restart`, `status`; logs - `journalctl -u <app> -f` (11.01)

### 05.03. nginx on the host

*Mandatory.*

- Front config: `cp web/deploy/nginx/<app>.conf /etc/nginx/sites-available/` + symlink into `sites-enabled`
- Backend upstream: `http://127.0.0.1:<port>` - the port from the application `[web]` configuration
- Check and apply: `nginx -t` -> `systemctl reload nginx`

---

## 06. Model B (Docker)

### 06.01. Application compose

*Mandatory.*

Compose file - `web/deploy/docker/docker-compose.yml`; the image is built from repository sources, so compose lives in the repo, not in `~/.docker/<service>/` (a deliberate deviation from `deploy_docker_standards.md`, 01.01); the volume rules (02.04), network (01.03), port publication (02.06) and template (02.01, 02.03) of the Docker standard apply:

```yaml
services:
  <app>:
    image: <app>:latest
    build:
      context: ../..
      dockerfile: deploy/docker/Dockerfile
    container_name: <app>
    restart: unless-stopped
    environment:
      WEB_HOST: 0.0.0.0
    env_file:
      - ../../.env
    volumes:
      - <app>_user_vol:/srv/web/var/user
      - ../../config:/srv/web/config:ro
    networks:
      - docker_network

volumes:
  <app>_user_vol:
    name: <app>_user_vol

networks:
  docker_network:
    external: true
```

- Backend ports are not published - nginx reaches the backend by `container_name` (02.06, 01.03 of the Docker standard)
- Portable data (`web/var/user`, 02.07) - a named volume with explicit `name:` (02.04 of the Docker standard); service runtime `web/var/system` stays inside the container; configuration - a `:ro` bind mount
- `WEB_HOST=0.0.0.0` overrides `[web] host` - inside the container the backend listens on all interfaces; the port does not leave the container
- Secrets via `env_file` from `web/.env`; they never enter the image because `web/.dockerignore` excludes them from the build context

Dockerfile (`web/deploy/docker/Dockerfile`, build context - the `web/` directory):

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY . /srv/web
ENV PATH="/srv/.venv/bin:$PATH"
RUN useradd --system --no-create-home <app> \
    && mkdir -p /srv/web/var/user \
    && chown -R <app>:<app> /srv
USER <app>
CMD ["python", "-m", "web"]
```

The mandatory `web/.dockerignore` sits at the build context root, not in `deploy/docker/`: `COPY . /srv/web` copies the whole context, and without exclusions `.env` and `var/` would enter the image. Minimum content:

```
.env
var/
__pycache__/
.venv/
```

- `ENV PATH` includes `.venv/bin`: `CMD ["python", "-m", "web"]` runs the interpreter from the environment with dependencies, not the image system python
- The container runs as the unprivileged user `<app>` (02.07): the owner of `/srv` and the pre-created `var/user/` is `<app>`; on first attach the named volume inherits the mount point owner from the image

### 06.02. nginx service

*Mandatory.*

nginx is added to the same compose as a second service:

```yaml
  <app>-nginx:
    image: nginx:<tag>
    container_name: <app>-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ../nginx/<app>.conf:/etc/nginx/conf.d/<app>.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ../../static:/srv/web/static:ro
    networks:
      - docker_network
```

- Publishing `80`/`443` without a `<host_ip>` binding is the only standard case of publication on all interfaces (`deploy_docker_standards.md`, 02.06, 02.07)
- Proxying: `proxy_pass http://<app>:<port>` - by `container_name` and the internal port from `[web]`
- TLS certificates - a `:ro` bind mount from the `deploy/docker/ssl/` subfolder (08)
- Static files - a read-only bind mount `../../static:/srv/web/static:ro` from the build context root (`web/`). A plain nginx image contains no application static files, so without this mount `/static/` returns 404. The server block for model B uses `root /srv/web;`, which maps `/static/<path>` to the mounted `/srv/web/static/<path>`
- Service start order is governed by documentation; `depends_on` is not used (`deploy_docker_standards.md`, 01.04)

### 06.03. Deploy order

*Mandatory.*

Order per `deploy_docker_standards.md` (01.05): create folders, prepare `web/.env`, build the image (`docker compose build --pull`), start (`docker compose up -d`), verify (`/healthz` via `docker exec` or curl on the published nginx port).

---

## 07. nginx

### 07.01. Server block template

*Mandatory.*

Template - `web/deploy/nginx/<app>.conf` (model A - into `sites-available` + symlink; model B - bind mount into `conf.d`):

```nginx
server {
    listen 80;
    server_name <domain>;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    http2 on;
    server_name <domain>;

    ssl_certificate     /etc/nginx/ssl/<app>.crt;
    ssl_certificate_key /etc/nginx/ssl/<app>.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;

    root /opt/<app>/web;
    client_max_body_size 10m;

    location /static/ {
        expires 7d;
        access_log off;
    }

    location / {
        proxy_pass http://127.0.0.1:<port>;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

- Port 80 serves only the ACME challenge (08.01) and redirects to 443
- The minimum SSL profile is mandatory: `ssl_protocols TLSv1.2 TLSv1.3`, session cache (`ssl_session_cache`, `ssl_session_timeout`); enable HTTP/2 with `http2 on` - do not use the obsolete `listen 443 ssl http2` form
- Certificate paths and `root` adapt per model: model A - as in the template; model B - certificates in `/etc/nginx/ssl/` (bind mount, 06.02), `root /srv/web;` for static files mounted from `web/static` (06.02), API - `proxy_pass http://<app>:<port>`

### 07.02. Proxying

*Mandatory.*

- Always pass headers: `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`; the application trusts `X-Forwarded-*` only from the proxy address
- Timeouts: `proxy_connect_timeout 5s`, `proxy_send_timeout` and `proxy_read_timeout` - per API needs (default 60s)
- `client_max_body_size` - per API needs (default 10m); for file uploads state the explicit value in the service documentation

### 07.03. Static

*Mandatory.*

- `root` points to the web subsystem directory: requests `/static/<path>` map to `web/static/<path>` without involving the backend
- Caching: `expires 7d` for `/static/`; `access_log off` for static files
- Static file names change when content changes (hash or version in the name) - stale client caches never serve old content

### 07.04. Multiple fronts

*Mandatory with multiple fronts.*

Each front gets its own server block with four items: name, port + binding (`listen <ip>:<port>`), TLS, `root` (its own static set from 02.04) and the list of proxied prefixes. Typical "external + local" configuration:

| Front | Listens | Binding | TLS | Root | Proxied prefixes |
|-------|---------|---------|-----|------|------------------|
| `public` | 443 | all interfaces | ACME (08.01) | `fronts/public/static` | `/api/` |
| `local` | 8443 | `127.0.0.1` or LAN IP | self-signed (08.02) or HTTP on a trusted LAN | `fronts/local/static` | `/api/`, `/admin/` |

- The local front is never published on all interfaces: isolation comes from binding and firewall (09), authorization in the application (03.03)
- Model B: the external front is published without binding (`"443:443"`), the local front with binding (`"<LAN_IP>:8443:8443"` or `"127.0.0.1:8443:8443"`), per `deploy_docker_standards.md` (02.06)

---

## 08. TLS

### 08.01. VPS (ACME)

*Mandatory for a public domain.*

- Certificates - Let's Encrypt via certbot: `certbot --nginx -d <domain>` (the plugin updates the config automatically) or webroot mode while keeping the 07.01 template
- Model B: run certbot in a container or in webroot mode through a volume; variant and commands - per certbot documentation, record the choice in the project specification
- Auto-renewal - the certbot systemd timer (`systemctl list-timers | grep certbot`); do not create a manual crontab
- Before certificate issuance the 07.01 template may use self-signed paths (08.02) - certbot replaces them after issuance

### 08.02. LAN (self-signed)

*Mandatory for a LAN without a public domain.*

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/<app>.key \
  -out /etc/nginx/ssl/<app>.crt \
  -subj "/CN=<app>.local" \
  -addext "subjectAltName=DNS:<app>.local,IP:<lan-ip>"
chmod 600 /etc/nginx/ssl/<app>.key
```

- Issue the certificate with `subjectAltName`: without SAN modern clients (browsers, curl) reject the certificate regardless of CN trust; list all connection addresses in SAN - DNS name and IP (LAN IP, `127.0.0.1`)
- Validity 365 days: renew by repeating the command; key mode - 600
- Trust the certificate by manual import on clients; without import the browser warns. API clients use `verify` with the CA certificate path; `verify=False` only per `project_standards.md` (05.01): with justification and a limited scope

---

## 09. Firewall

### 09.01. Model A

*Mandatory.*

- ufw: rules only for `80/tcp`, `443/tcp` and SSH from the trusted subnet; comment every rule with the service name (`deploy_docker_standards.md`, 03.01):

```bash
ufw allow 80/tcp comment '<app> http'
ufw allow 443/tcp comment '<app> https'
```

- The backend port (127.0.0.1) is not opened externally; the local front (07.04) needs no ufw rule - isolation comes from the `listen <ip>:` binding

### 09.02. Model B

*Mandatory.*

- ufw does not affect published Docker ports (`deploy_docker_standards.md`, 02.06) - access control is done by the `<host_ip>` binding in `ports` lines
- External front - `"80:80"`, `"443:443"` without binding; local - `"<LAN_IP>:8443:8443"` or `"127.0.0.1:8443:8443"`; no ufw rules are created for them

---

## 10. Update and rollback

### 10.01. Update sequence

*Mandatory - do not skip or reorder steps.*

1. Data backup: `pg_dump` for a DBMS or a copy of the SQLite file - model A: copy to `web/var/user/backup/`; model B: copy from the `var/user` volume (`docker exec` with `sqlite3 .backup` or `docker cp`). Backup scope - `var/user/` without `backup/` (02.07)
2. Code update: `git pull` in `/opt/<app>/` (model A) or `git pull` + `docker compose build --pull` (model B)
3. Migrations: `web/run/db_migrate.py` (`project_standards.md`, 03.03.01)
4. Restart: `systemctl restart <app>` (model A) or `docker compose up -d` (model B)
5. Health-check: `curl http://127.0.0.1:<port>/healthz`; on failure - `journalctl -u <app>` or `docker compose logs`

The backup from step 1 is the rollback prerequisite (10.02); do not start an update without a successful backup.

### 10.02. Rollback

*Mandatory.*

- Code rollback: `git checkout <tag-or-commit>` + restart (step 4) + health-check (step 5)
- Migrations are not rolled back automatically: fix the schema with a new migration only (`project_standards.md`, 03.02.03); rolling back to a pre-migration schema means restoring the DB from the step 1 backup
- Zero-downtime is out of scope: a short restart outage is acceptable

---

## 11. Logging

### 11.01. Backend

*Mandatory.*

- Dev: log files in `web/var/system/log/` per `project_standards.md` (04.06): name `log_<script>_<timestamp>.log`, rotation via `[logging] keep_last`
- Production: the primary channel is stdout/stderr, journald collects automatically; view with `journalctl -u <app> -f`; rotation by journald (`SystemMaxUse` when needed). File output in production only when stdout is abandoned (never write one event to both channels); in a container the file is ephemeral without a separate volume (02.07)
- Message format, markers, secret masking - per `project_standards.md` (04.02, 04.04, 05.01)

### 11.02. nginx

*Mandatory.*

- Model A: `access_log` and `error_log` in system paths `/var/log/nginx/` on the host; do not set custom paths without justification. Rotation - the standard `/etc/logrotate.d/nginx` from the package; do not create custom logrotate configurations for nginx
- Model B: nginx logs are container output, viewed via `docker logs` / `docker compose logs`; rotation - `json-file` driver limits in the compose `logging` section or globally in daemon.json (`deploy_docker_standards.md`, 02.03, 01.06)

---

## 12. Service documentation

### 12.01. Document template

*Mandatory.*

Each deployed application is described in a separate document following `deploy_docker_standards.md` (05.01), adapted for web:

1. **Название** (`# <app>`) + краткое описание (1-2 sentences): model, ports, domains
2. **Подготовка** (optional, before "Установка") - packages, user, DB, certificates
3. **Установка** - repository placement, venv, unit, nginx, firewall - with commands from `web/deploy/` templates
4. **Расположение** - host paths: repository, venv, nginx configuration, unit, data
5. **Управление** - start, stop, status, logs, update (sequence 10.01)
6. **Файрвол** - actual ufw rules or port bindings (09.01, 09.02)
7. **Базовая настройка** (optional, after "Файрвол") - initial configuration after launch
8. **Конфигурация** (optional) - tuning and advanced options
9. **Проверка** - health-check, `curl`, log inspection

Section order and the root-level rule (`##` - standard sections only) - as in `deploy_docker_standards.md` (05.01, 05.02).

### 12.02. Boundary with the deploy family

*Mandatory.*

- `deploy_standards.md`, `deploy_lin_standards.md`, `deploy_win_standards.md` do not apply to web applications: their subject is installing a Python project as a CLI tool via `uv tool`
- `install.py`/`update.py` scripts are not canonicalized in web repositories: deploy and update procedures live only in the service documentation (12.01)
- A project combining an installable CLI tool and a `web/` subsystem in one repository: the deploy family applies to the CLI part and packaging, this document applies to the `web/` subsystem; the boundary is the `web/` directory. Record the junction and order in the project specification (12.01)
- The CLI runtime (root `data/`, `log/`, `output/`) and the web runtime (`web/var/`) are separate entities: each part manages its own data, and a shared DB lives in exactly one place (02.07)
- Production `web/config/config.ini` and `web/.env` are not committed - `.gitignore` exceptions in the `web/` subsystem; production values live only on the host, `git pull` (step 2 of 10.01) does not conflict with them
- When the key set of `web/config/config.ini` or `web/.env` changes, migrate production files within step 2 of 10.01 per `deploy_standards.md` (04.01): new keys from the example (structure sources - the committable templates `web/config/config.ini.example` and `web/.env.example`, 02.01), preserve user values

### 12.03. spec_ui.html

*Mandatory.*

- `doc/specs/spec_ui.html` is mandatory for a web repository with user-facing output - per `console_ui_standards.md` 01.02
- In a web repository the mockup covers: output on local launch and in `web/run/` scripts, log format, API response examples (examples in `sample/api_*.json`)
- The browser UI is not fixed in `spec_ui.html` - it is defined by templates and module specifications (`project_standards.md`, 07.02)

---

## 13. Relations and versioning

### 13.01. Related documents

| Document | Relation |
|----------|----------|
| `doc/standards/project_standards.md` | Core standard; this document applies on top of it; root folder rules apply from inside `web/` (02.01) |
| `doc/standards/deploy_docker_standards.md` | Model B: volumes (01.02), network (01.03), compose template (02.01, 02.03), port publication (02.06), reverse proxy (02.07), service addition order (01.05) |
| `doc/standards/console_ui_standards.md` | Mandatory `doc/specs/spec_ui.html`; applicability boundary for a web repository - 12.03 |
| `doc/standards/deploy_standards.md`, `deploy_lin_standards.md`, `deploy_win_standards.md` | Do not apply to web applications (subject - CLI tools); boundary - 12.02 |
| `doc/standards/_index_standards.md` | Package registry, routing map, versioning policy |

### 13.02. Versioning

Standards package versioning is unified for all package documents. The versioning policy, registry and routing map live in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see _index_standards.md).
