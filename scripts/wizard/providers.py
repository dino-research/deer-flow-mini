"""LLM and search provider definitions for the Setup Wizard."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LLMProvider:
    name: str
    display_name: str
    description: str
    use: str
    models: list[str]
    default_model: str
    env_var: str | None
    package: str | None
    # Optional: some providers use a different field name for the API key in YAML
    api_key_field: str = "api_key"
    # Extra config fields beyond the common ones (merged into YAML)
    extra_config: dict = field(default_factory=dict)
    auth_hint: str | None = None


@dataclass
class WebProvider:
    name: str
    display_name: str
    description: str
    use: str
    env_var: str | None  # None = no API key required
    tool_name: str
    extra_config: dict = field(default_factory=dict)


@dataclass
class SearchProvider:
    name: str
    display_name: str
    description: str
    use: str
    env_var: str | None  # None = no API key required
    tool_name: str = "web_search"
    extra_config: dict = field(default_factory=dict)


LLM_PROVIDERS: list[LLMProvider] = [
    LLMProvider(
        name="openai",
        display_name="OpenAI",
        description="GPT-4o, GPT-4.1, o3",
        use="langchain_openai:ChatOpenAI",
        models=["gpt-4o", "gpt-4.1", "o3"],
        default_model="gpt-4o",
        env_var="OPENAI_API_KEY",
        package="langchain-openai",
    ),
    LLMProvider(
        name="google",
        display_name="Google Gemini",
        description="2.0 Flash, 2.5 Pro",
        use="langchain_google_genai:ChatGoogleGenerativeAI",
        models=["gemini-2.0-flash", "gemini-2.5-pro"],
        default_model="gemini-2.0-flash",
        env_var="GEMINI_API_KEY",
        package="langchain-google-genai",
        api_key_field="gemini_api_key",
    ),
    LLMProvider(
        name="openrouter",
        display_name="OpenRouter",
        description="OpenAI-compatible gateway with broad model catalog",
        use="langchain_openai:ChatOpenAI",
        models=["google/gemini-2.5-flash-preview", "openai/gpt-5-mini", "anthropic/claude-sonnet-4"],
        default_model="google/gemini-2.5-flash-preview",
        env_var="OPENROUTER_API_KEY",
        package="langchain-openai",
        extra_config={
            "base_url": "https://openrouter.ai/api/v1",
            "request_timeout": 600.0,
            "max_retries": 2,
            "max_tokens": 8192,
            "temperature": 0.7,
        },
    ),
    LLMProvider(
        name="other",
        display_name="Other OpenAI-compatible",
        description="Custom gateway with base_url and model name (vLLM, Ollama, LiteLLM)",
        use="langchain_openai:ChatOpenAI",
        models=["gpt-4o"],
        default_model="gpt-4o",
        env_var="OPENAI_API_KEY",
        package="langchain-openai",
    ),
]

SEARCH_PROVIDERS: list[SearchProvider] = [
    SearchProvider(
        name="ddg_search",
        display_name="DuckDuckGo (no Docker, no key needed)",
        description="Lightweight web search via duckduckgo-search Python package",
        use="deerflow.community.ddg_search.tools:web_search_tool",
        env_var=None,
        extra_config={"max_results": 5},
    ),
]

WEB_FETCH_PROVIDERS: list[WebProvider] = [
    WebProvider(
        name="local_fetch",
        display_name="Local fetch (httpx + readabilipy, no key needed)",
        description="Built-in web fetcher, no external API required",
        use="deerflow.community.local_fetch.tools:web_fetch_tool",
        env_var=None,
        tool_name="web_fetch",
    ),
]
