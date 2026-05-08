# 🦌 DeerFlow Mini

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](./backend/pyproject.toml)
[![Node.js](https://img.shields.io/badge/Node.js-22%2B-339933?logo=node.js&logoColor=white)](./Makefile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**DeerFlow Mini** is a streamlined fork of [DeerFlow 2.0](https://github.com/bytedance/deer-flow) — optimized for **32K-context models**, **local/self-hosted LLMs**, and **minimal external dependencies**.

> [!NOTE]
> This is a **minimized** edition. It strips vendor-specific integrations, IM channels, and heavy third-party tools to keep the project lean and focused on core agent capabilities. If you need the full-featured version, see the [upstream repository](https://github.com/bytedance/deer-flow).

---

## What Changed from Upstream

| Area | Upstream DeerFlow 2.0 | DeerFlow Mini |
|------|----------------------|---------------|
| **LLM Providers** | 9 providers (OpenAI, Anthropic, DeepSeek, Google, vLLM, Codex CLI, Claude Code OAuth, OpenRouter, Other) | **4 providers** — OpenAI, Google Gemini, OpenRouter, Other OpenAI-compatible |
| **Web Search** | 5 providers (DDG, Tavily, InfoQuest, Exa, Firecrawl) | **1 provider** — SearXNG (local, no API key) |
| **Web Fetch** | 4 providers (Jina AI, Exa, InfoQuest, Firecrawl) | **1 provider** — Local fetch (httpx + readabilipy, no API key) |
| **IM Channels** | 6 channels (Telegram, Slack, Feishu, WeChat, WeCom, DingTalk) | **Removed** |
| **Tracing** | LangSmith + Langfuse | **Removed** |
| **Skills** | 21 skills | **7 core skills** |
| **System Prompt** | ~830 lines | **~450 lines** (optimized for 32K context) |
| **Config** | ~1070 lines | **~160 lines** |
| **Custom Model Providers** | vLLM, Codex CLI, Claude Code OAuth | **Removed** (use `langchain_openai:ChatOpenAI` with `base_url` for any OpenAI-compatible endpoint) |

---

## Table of Contents

- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [Advanced](#advanced)
  - [Sandbox Mode](#sandbox-mode)
  - [MCP Server](#mcp-server)
- [Architecture](#architecture)
  - [Core Features](#core-features)
  - [Skills & Tools](#skills--tools)
  - [Sub-Agents](#sub-agents)
  - [Sandbox & File System](#sandbox--file-system)
  - [Context Engineering](#context-engineering)
  - [Long-Term Memory](#long-term-memory)
- [Recommended Models](#recommended-models)
- [Documentation](#documentation)
- [Security Notice](#️-security-notice)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Quick Start

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.12+ | [python.org](https://www.python.org/) |
| Node.js | 22+ | [nodejs.org](https://nodejs.org/) |
| pnpm | latest | `npm install -g pnpm` |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| nginx | latest | `brew install nginx` (macOS) / `sudo apt install nginx` (Ubuntu) |

### Configuration

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd deer-flow-mini
   ```

2. **Run the setup wizard**

   ```bash
   make setup
   ```

   The wizard guides you through:
   - **LLM provider** — OpenAI, Google Gemini, OpenRouter, or any OpenAI-compatible endpoint (vLLM, Ollama, LiteLLM)
   - **Web search** — SearXNG (local, no API key) or skip
   - **Web fetch** — Local fetch (built-in, no API key) or skip
   - **Execution mode** — Local sandbox or container sandbox
   - **Safety options** — Bash execution, file write tools

   It generates a minimal `config.yaml` and writes your keys to `.env`. Takes about 2 minutes.

3. **Verify your setup**

   ```bash
   make doctor
   ```

   > **Manual configuration**: If you prefer to edit `config.yaml` directly, run `make config` to copy the full template. See `config.example.yaml` for the complete reference.

   <details>
   <summary>Manual model configuration examples</summary>

   ```yaml
   models:
     # OpenAI
     - name: gpt-4o
       display_name: GPT-4o
       use: langchain_openai:ChatOpenAI
       model: gpt-4o
       api_key: $OPENAI_API_KEY

     # OpenRouter (access any model via OpenAI-compatible gateway)
     - name: openrouter-gemini
       display_name: Gemini 2.5 Flash (OpenRouter)
       use: langchain_openai:ChatOpenAI
       model: google/gemini-2.5-flash-preview
       api_key: $OPENROUTER_API_KEY
       base_url: https://openrouter.ai/api/v1

     # vLLM / Ollama / LiteLLM (any OpenAI-compatible endpoint)
     - name: local-model
       display_name: Local Model (vLLM)
       use: langchain_openai:ChatOpenAI
       model: google/gemma-4-e4b
       api_key: $OPENAI_API_KEY
       base_url: http://localhost:8000/v1
       request_timeout: 600.0
       max_tokens: 4096

     # Google Gemini (native)
     - name: gemini-flash
       display_name: Gemini 2.0 Flash
       use: langchain_google_genai:ChatGoogleGenerativeAI
       model: gemini-2.0-flash
       gemini_api_key: $GEMINI_API_KEY
   ```

   API keys should be set in `.env`:

   ```bash
   OPENAI_API_KEY=your-openai-api-key
   GEMINI_API_KEY=your-gemini-api-key
   OPENROUTER_API_KEY=your-openrouter-api-key
   ```

   </details>

### Running the Application

#### Option 1: Docker (Recommended)

**Development** (hot-reload, source mounts):

```bash
make docker-init    # Pull sandbox image (only once)
make docker-start   # Start services
```

**Production** (builds images locally):

```bash
make up     # Build images and start all production services
make down   # Stop and remove containers
```

Access: http://localhost:2026

#### Option 2: Local Development

1. **Check prerequisites**:
   ```bash
   make check
   ```

2. **Install dependencies**:
   ```bash
   make install
   ```

3. **Start services**:
   ```bash
   make dev
   ```

4. **Access**: http://localhost:2026

#### Startup Modes

| | **Local Foreground** | **Local Daemon** | **Docker Dev** | **Docker Prod** |
|---|---|---|---|---|
| **Dev** | `make dev` | `make dev-daemon` | `make docker-start` | — |
| **Prod** | `make start` | `make start-daemon` | — | `make up` |

| Action | Local | Docker Dev | Docker Prod |
|---|---|---|---|
| **Stop** | `make stop` | `make docker-stop` | `make down` |

#### Deployment Sizing

| Deployment target | Starting point | Recommended |
|---------|-----------|------------|
| Local dev / `make dev` | 4 vCPU, 8 GB RAM | 8 vCPU, 16 GB RAM |
| Docker dev / `make docker-start` | 4 vCPU, 8 GB RAM | 8 vCPU, 16 GB RAM |
| Server / `make up` | 8 vCPU, 16 GB RAM | 16 vCPU, 32 GB RAM |

These numbers cover DeerFlow itself. If you also host a local LLM, size that service separately.

---

## Advanced

### Sandbox Mode

DeerFlow supports multiple sandbox execution modes:

- **Local Execution** — runs sandbox code directly on the host machine (default)
- **Docker Execution** — runs sandbox code in isolated Docker containers
- **Docker Execution with Kubernetes** — runs sandbox code in Kubernetes pods via provisioner service

See the [Sandbox Configuration Guide](backend/docs/CONFIGURATION.md#sandbox) for details.

### MCP Server

DeerFlow supports configurable MCP servers and skills to extend its capabilities.
For HTTP/SSE MCP servers, OAuth token flows are supported (`client_credentials`, `refresh_token`).
See the [MCP Server Guide](backend/docs/MCP_SERVER.md) for detailed instructions.

---

## Architecture

### Core Features

### Skills & Tools

Skills are structured capability modules — Markdown files that define workflows, best practices, and references. DeerFlow Mini ships with **7 core skills**:

```
skills/public/
├── chart-visualization/SKILL.md
├── code-documentation/SKILL.md
├── consulting-analysis/SKILL.md
├── data-analysis/SKILL.md
├── deep-research/SKILL.md
├── github-deep-research/SKILL.md
└── systematic-literature-review/SKILL.md
```

Skills are loaded progressively — only when the task needs them, not all at once. This keeps the context window lean for 32K-context models.

**Core tools** included:

| Tool | Description |
|------|-------------|
| `web_search` | SearXNG meta search (local, no API key) |
| `web_fetch` | httpx + readabilipy page fetcher |
| `ls`, `read_file`, `glob`, `grep` | File system operations |
| `write_file`, `str_replace` | File writing & editing |
| `bash` | Shell command execution (opt-in) |

Custom tools can be added via MCP servers and Python functions.

### Sub-Agents

The lead agent can spawn sub-agents on the fly — each with its own scoped context, tools, and termination conditions. Sub-agents run in parallel when possible, report back structured results, and the lead agent synthesizes everything into a coherent output.

### Sandbox & File System

Each task gets its own execution environment with a full filesystem view — skills, workspace, uploads, outputs.

With `AioSandboxProvider`, shell execution runs inside isolated containers. With `LocalSandboxProvider`, file tools map to per-thread directories on the host, but host `bash` is disabled by default.

```
/mnt/user-data/
├── uploads/          ← your files
├── workspace/        ← agents' working directory
└── outputs/          ← final deliverables
```

### Context Engineering

- **Isolated Sub-Agent Context**: Each sub-agent runs in its own isolated context
- **Summarization**: DeerFlow manages context aggressively — summarizing completed sub-tasks, compressing what's no longer immediately relevant (tuned for 32K context)
- **Strict Tool-Call Recovery**: Strips provider-level raw tool-call metadata on forced-stop and injects placeholder tool results for dangling calls

### Long-Term Memory

Across sessions, DeerFlow builds a persistent memory of your profile, preferences, and accumulated knowledge. Memory is stored locally and stays under your control.

---

## Recommended Models

DeerFlow Mini is optimized for **32K-context models** but works with any LLM that implements the OpenAI-compatible API. Best results with:

- **Long context windows** (32K+ tokens) for research and multi-step tasks
- **Reasoning capabilities** for adaptive planning
- **Strong tool-use** for reliable function calling

**Tested configurations**:

| Model | Provider | Notes |
|-------|----------|-------|
| GPT-4o / GPT-4.1 | OpenAI | Excellent tool-use |
| Gemini 2.0 Flash / 2.5 Pro | Google / OpenRouter | Fast, large context |
| Qwen3-32B | vLLM (via OpenAI-compatible) | Self-hosted, supports thinking |
| Gemma 4 E4B | vLLM (via OpenAI-compatible) | Self-hosted |

## Embedded Python Client

DeerFlow can be used as an embedded Python library without running the full HTTP services:

```python
from deerflow.client import DeerFlowClient

client = DeerFlowClient()

# Chat
response = client.chat("Analyze this paper for me", thread_id="my-thread")

# Streaming
for event in client.stream("hello"):
    if event.type == "messages-tuple" and event.data.get("type") == "ai":
        print(event.data["content"])

# Management
models = client.list_models()
skills = client.list_skills()
```

See `backend/packages/harness/deerflow/client.py` for the full API.

## Documentation

- [Contributing Guide](CONTRIBUTING.md) — Development environment setup and workflow
- [Configuration Guide](backend/docs/CONFIGURATION.md) — Setup and configuration instructions
- [Architecture Overview](backend/CLAUDE.md) — Technical architecture details
- [Backend Architecture](backend/README.md) — Backend architecture and API reference
- [MCP Server Guide](backend/docs/MCP_SERVER.md) — MCP server integration

## ⚠️ Security Notice

### Improper Deployment May Introduce Security Risks

DeerFlow has high-privilege capabilities including **system command execution** and **file operations**, and is designed by default to be **deployed in a local trusted environment** (accessible only via the 127.0.0.1 loopback interface).

### Security Recommendations

**We strongly recommend deploying DeerFlow in a local trusted network environment.** If you need cross-device or cross-network deployment, implement strict security measures:

- **IP allowlist**: Configure firewall rules to deny access from unauthorized addresses
- **Authentication gateway**: Use a reverse proxy (e.g., nginx) with strong pre-authentication
- **Network isolation**: Place the agent and trusted devices in a dedicated VLAN

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, workflow, and guidelines.

## License

This project is open source and available under the [MIT License](./LICENSE).

## Acknowledgments

DeerFlow Mini is a fork of [DeerFlow](https://github.com/bytedance/deer-flow) by ByteDance. Built upon:

- **[LangChain](https://github.com/langchain-ai/langchain)** — LLM interactions and chains
- **[LangGraph](https://github.com/langchain-ai/langgraph)** — Multi-agent orchestration

### Original Authors

- **[Daniel Walnut](https://github.com/hetaoBackend/)**
- **[Henry Li](https://github.com/magiccube/)**
