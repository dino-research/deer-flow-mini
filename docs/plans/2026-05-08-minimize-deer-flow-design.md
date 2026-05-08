# Deer-Flow Mini — Minimization Design

> **Goal**: Minimize the Deer-Flow codebase into a lean, internally deployable version optimized for Gemma 4 E4B (32K context) on small-company infrastructure.

## 🎯 Design Decisions Summary

| Decision | Choice |
|---|---|
| LLM Provider | OpenAI-compatible only (Gemma 4 E4B, 32K) — test with GPT-4 mini |
| Search | SearXNG (new integration, deployed via Docker Compose) |
| Web Fetch | Local fetcher (httpx + readabilipy) |
| Sandbox | AIO Sandbox |
| Deployment | Docker Compose (primary) |
| Auth | Keep basic auth, multi-user |
| Subagents | Keep, max 2 concurrent, simplified prompt |
| Memory | Keep, reduced to 500 max_injection_tokens |
| Summarization | Keep, trigger at ~8K tokens |
| Skills | Keep 7, remove 14 |

## Context Budget (32K tokens)

```
Total Context:               32,768 tokens
System Prompt (target):      ~2,500 tokens (was ~8-10K)
Memory injection:              ~500 tokens (max)
Available for conversation:  ~29,700 tokens
```

## 7 Phases

1. Dependencies Cleanup
2. Dead Code Removal — Backend (channels, model providers, tracing, community tools, ACP, guardrails)
3. New Integrations (SearXNG + Local Web Fetch)
4. System Prompt Optimization for 32K context
5. Frontend Cleanup
6. Skills Cleanup (keep 7, remove 14)
7. Docker Compose & Documentation

See full design: `.gemini/antigravity/brain/c28e3a90-73fc-482b-9339-776900dc32b0/minimize-deer-flow-design.md`
