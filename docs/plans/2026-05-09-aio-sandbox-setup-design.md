# AIO Sandbox Setup — Local Docker (DooD) Mode

**Date:** 2026-05-09
**Status:** Implemented

## Overview

Setup [AIO Sandbox](https://github.com/agent-infra/sandbox) for code execution in
deer-flow-mini using Docker-outside-of-Docker (DooD) mode. The gateway container
manages sandbox containers on the host Docker daemon via the mounted docker socket.

## Architecture

```
┌──────────────────────────────────────┐
│  Docker Host (macOS)                 │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ deer-flow-gateway container   │  │
│  │  (FastAPI + AioSandboxProvider)│  │
│  │  mount: /var/run/docker.sock  │──┼──► Docker daemon (host)
│  └────────────────────────────────┘  │
│                                      │
│  ┌──────────┐ ┌──────────┐          │
│  │ sandbox-1│ │ sandbox-2│  ← created via docker.sock
│  │ :random  │ │ :random  │
│  └──────────┘ └──────────┘          │
└──────────────────────────────────────┘
```

## Changes Made

### 1. `config.yaml` — Explicit sandbox settings

Added `image`, `port`, `idle_timeout`, `replicas` instead of relying on hidden defaults.

### 2. `config.example.yaml` — Updated template

Changed from `LocalSandboxProvider` to `AioSandboxProvider` with full documentation.

### 3. `docker/docker-compose.yaml` — Fixed DooD env vars

Added 3 missing environment variables in the production gateway service:

- `DEER_FLOW_SANDBOX_HOST=host.docker.internal` — so gateway reaches sandbox containers
- `DEER_FLOW_HOST_BASE_DIR` — so sandbox volume mounts reference host paths
- `DEER_FLOW_HOST_SKILLS_PATH` — so skills are accessible inside sandbox containers

Without these, sandbox containers would be unreachable or have broken volume mounts
in production Docker deployment.

## Key Configuration

```yaml
# config.yaml
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  image: enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest
  port: 8080
  idle_timeout: 600   # 10 minutes
  replicas: 3         # Max concurrent sandbox containers
```

## Verification

- Docker v29.4.1 ✓
- Docker socket at `/var/run/docker.sock` ✓
- Sandbox image pulled ✓
- Sandbox container starts and health endpoint (`/v1/sandbox`) responds HTTP 200 ✓
