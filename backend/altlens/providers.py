"""Model provider adapters.

AltLens keeps model routing behind one narrow interface so the same agent
works against a hosted model, a local model, or no model at all. A provider
only ever decides *which approved tool to call* and *how to word the answer*.
It never sees a database and never produces a performance figure.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from altlens.config import Settings, settings as default_settings
from altlens.schemas import ProviderInfo

SYSTEM_PROMPT = (
    "You are AltLens AI, a research assistant for alternative-investment "
    "performance data. You may only answer using the results of the provided "
    "tools. Never invent a fund, a metric, or a performance figure. If the "
    "tools cannot answer the question — for example because the dataset only "
    "covers venture capital — say so plainly instead of guessing. All data is "
    "illustrative demo data; say so when you report figures."
)

OUT_OF_SCOPE_ANSWER = (
    "I can't answer that from the AltLens dataset. It currently covers "
    "illustrative venture-capital funds only — fund profiles, cash-flow based "
    "metrics (IRR, MOIC, DPI, RVPI), vintage-year cohorts, and portfolio "
    "sector exposure. Ask about one of those and I can pull the numbers."
)


@dataclass
class ToolInvocation:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelDecision:
    """What the provider decided to do with a question."""

    tool_calls: list[ToolInvocation] = field(default_factory=list)
    message: str | None = None


class ProviderError(RuntimeError):
    """Raised when a provider cannot be reached or returns nothing usable."""


class ModelProvider(ABC):
    name: str = "unknown"

    @abstractmethod
    def default_model(self) -> str | None: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def plan(
        self, question: str, tools: list[dict[str, Any]]
    ) -> ModelDecision: ...

    @abstractmethod
    def narrate(
        self, question: str, tool_outputs: list[tuple[str, str]]
    ) -> str: ...

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            available=self.is_available(),
            default_model=self.default_model(),
        )


class RuleBasedProvider(ModelProvider):
    """Keyword router used when no model provider is configured.

    This exists so the product demos end to end with no API key and no network
    access. It is deliberately conservative: anything it cannot map onto an
    approved tool is refused rather than answered.
    """

    name = "rule_based"

    def __init__(self, fund_names: list[str], manager_names: list[str]) -> None:
        self._fund_names = fund_names
        self._manager_names = manager_names

    def default_model(self) -> str | None:
        return None

    def is_available(self) -> bool:
        return True

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            available=True,
            default_model=None,
            notes=(
                "Deterministic keyword routing. Always available; used when no "
                "hosted or local model is configured."
            ),
        )

    def plan(self, question: str, tools: list[dict[str, Any]]) -> ModelDecision:
        text = question.casefold()
        mentioned = self._mentioned_funds(text)
        metric = self._mentioned_metric(text)

        if self._is_out_of_scope(text):
            return ModelDecision(message=OUT_OF_SCOPE_ANSWER)

        if any(word in text for word in ("how is", "how do you", "methodology",
                                         "how are", "calculated", "definition",
                                         "what does", "explain")) and metric:
            return ModelDecision(
                tool_calls=[
                    ToolInvocation("explain_metric_methodology", {"metric": metric})
                ]
            )

        if any(word in text for word in ("brief", "memo", "report", "write-up",
                                         "writeup", "diligence")):
            arguments: dict[str, Any] = {"question": question}

            if mentioned:
                arguments["fund_names"] = mentioned

            vintage = self._mentioned_vintage(text)

            if vintage is not None:
                arguments["vintage_year"] = vintage

            return ModelDecision(
                tool_calls=[ToolInvocation("generate_research_brief", arguments)]
            )

        if "sector" in text or "exposure" in text or "portfolio compan" in text:
            arguments = {"fund_names": mentioned} if mentioned else {}
            return ModelDecision(
                tool_calls=[ToolInvocation("get_sector_exposure", arguments)]
            )

        if "vintage" in text or "cohort" in text:
            vintage = self._mentioned_vintage(text)
            arguments = {} if vintage is None else {"vintage_year": vintage}
            return ModelDecision(
                tool_calls=[ToolInvocation("get_vintage_year_summary", arguments)]
            )

        if len(mentioned) >= 2 or ("compare" in text and mentioned):
            return ModelDecision(
                tool_calls=[ToolInvocation("compare_funds", {"fund_names": mentioned})]
            )

        if any(word in text for word in ("average", "mean", "across all",
                                         "all funds", "typical", "median")):
            return ModelDecision(
                tool_calls=[
                    ToolInvocation(
                        "get_top_performers",
                        {"metric": metric or "moic", "limit": 50},
                    )
                ]
            )

        if any(word in text for word in ("top", "best", "strongest", "highest",
                                         "rank", "leader", "worst", "weakest")):
            return ModelDecision(
                tool_calls=[
                    ToolInvocation(
                        "get_top_performers",
                        {"metric": metric or "irr", "limit": 5},
                    )
                ]
            )

        if mentioned:
            tool_name = "get_fund_metrics" if metric else "get_fund_profile"
            return ModelDecision(
                tool_calls=[ToolInvocation(tool_name, {"fund_name": mentioned[0]})]
            )

        vintage = self._mentioned_vintage(text)

        if vintage is not None:
            return ModelDecision(
                tool_calls=[
                    ToolInvocation("list_funds", {"vintage_year": vintage})
                ]
            )

        if any(word in text for word in ("list", "which funds", "what funds",
                                         "show me", "funds do you")):
            return ModelDecision(tool_calls=[ToolInvocation("list_funds", {})])

        return ModelDecision(message=OUT_OF_SCOPE_ANSWER)

    def narrate(self, question: str, tool_outputs: list[tuple[str, str]]) -> str:
        if not tool_outputs:
            return OUT_OF_SCOPE_ANSWER

        body = "\n\n".join(output for _, output in tool_outputs)

        return (
            f"{body}\n\nAll figures are calculated from AltLens' illustrative "
            "demo dataset, not verified fund reporting."
        )

    def _mentioned_funds(self, text: str) -> list[str]:
        matched = [name for name in self._fund_names if name.casefold() in text]

        if matched:
            return matched

        return [name for name in self._manager_names if name.casefold() in text]

    @staticmethod
    def _mentioned_metric(text: str) -> str | None:
        for metric in ("irr", "moic", "tvpi", "dpi", "rvpi"):
            if re.search(rf"\b{metric}\b", text):
                return metric

        if "internal rate of return" in text:
            return "irr"

        if "multiple on invested capital" in text:
            return "moic"

        return None

    @staticmethod
    def _mentioned_vintage(text: str) -> int | None:
        match = re.search(r"\b(19|20)\d{2}\b", text)

        if match is None:
            return None

        return int(match.group(0))

    @staticmethod
    def _is_out_of_scope(text: str) -> bool:
        out_of_scope_terms = (
            "hedge fund",
            "real estate",
            "private equity",
            "stock",
            "equities",
            "crypto",
            "bond",
            "etf",
            "s&p",
            "nasdaq",
        )

        return any(term in text for term in out_of_scope_terms)


class _HTTPToolCallingProvider(ModelProvider):
    """Shared logic for providers that speak an OpenAI-style chat API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _post(self, url: str, payload: dict[str, Any], headers: dict[str, str]):
        import httpx

        try:
            response = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=self._settings.request_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:  # noqa: BLE001 - surfaced as ProviderError
            raise ProviderError(
                f"{self.name} provider request failed: {error}"
            ) from error

    @staticmethod
    def _parse_arguments(raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw

        if not raw:
            return {}

        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return {}

        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _tool_payload(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            for tool in tools
        ]

    @staticmethod
    def _narration_prompt(
        question: str, tool_outputs: list[tuple[str, str]]
    ) -> str:
        rendered = "\n\n".join(
            f"Tool `{name}` returned:\n{output}" for name, output in tool_outputs
        )

        return (
            f"Question: {question}\n\n{rendered}\n\n"
            "Write a short, direct answer using only these tool results. Do not "
            "add figures that are not shown above. End by noting the data is "
            "illustrative demo data."
        )


class OpenAIProvider(_HTTPToolCallingProvider):
    """Hosted models through the OpenAI chat completions API."""

    name = "openai"

    def __init__(self, settings: Settings, model: str | None = None) -> None:
        super().__init__(settings)
        self._model = model or settings.openai_model

    def default_model(self) -> str | None:
        return self._model

    def is_available(self) -> bool:
        return bool(self._settings.openai_api_key)

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            available=self.is_available(),
            default_model=self._model,
            notes=(
                "Requires OPENAI_API_KEY. Uses tool calling restricted to the "
                "approved AltLens tools."
            ),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json",
        }

    def _chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.is_available():
            raise ProviderError(
                "OpenAI provider is not configured: set OPENAI_API_KEY."
            )

        data = self._post(
            f"{self._settings.openai_base_url.rstrip('/')}/chat/completions",
            payload,
            self._headers(),
        )

        choices = data.get("choices") or []

        if not choices:
            raise ProviderError("OpenAI returned no choices.")

        return choices[0].get("message") or {}

    def plan(self, question: str, tools: list[dict[str, Any]]) -> ModelDecision:
        message = self._chat(
            {
                "model": self._model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                "tools": self._tool_payload(tools),
                "tool_choice": "auto",
            }
        )

        tool_calls = [
            ToolInvocation(
                name=call.get("function", {}).get("name", ""),
                arguments=self._parse_arguments(
                    call.get("function", {}).get("arguments")
                ),
            )
            for call in message.get("tool_calls") or []
        ]

        return ModelDecision(
            tool_calls=[call for call in tool_calls if call.name],
            message=message.get("content"),
        )

    def narrate(self, question: str, tool_outputs: list[tuple[str, str]]) -> str:
        message = self._chat(
            {
                "model": self._model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": self._narration_prompt(question, tool_outputs),
                    },
                ],
            }
        )

        content = message.get("content")

        if not content:
            raise ProviderError("OpenAI returned an empty answer.")

        return content


class OllamaProvider(_HTTPToolCallingProvider):
    """Local models through an Ollama server.

    Smaller local models are inconsistent at multi-step tool use, so the agent
    falls back to rule-based routing whenever this provider fails to pick a
    tool. That keeps a local-model demo from silently producing prose with no
    data behind it.
    """

    name = "ollama"

    def __init__(self, settings: Settings, model: str | None = None) -> None:
        super().__init__(settings)
        self._model = model or settings.ollama_model

    def default_model(self) -> str | None:
        return self._model

    def is_available(self) -> bool:
        import httpx

        try:
            response = httpx.get(
                f"{self._settings.ollama_base_url.rstrip('/')}/api/tags",
                timeout=2.0,
            )
            return response.status_code == 200
        except Exception:  # noqa: BLE001 - availability probe only
            return False

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            available=self.is_available(),
            default_model=self._model,
            notes=(
                "Requires a running Ollama server. Small local models may not "
                "reliably choose tools; AltLens falls back to rule-based "
                "routing when that happens."
            ),
        )

    def _chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._post(
            f"{self._settings.ollama_base_url.rstrip('/')}/api/chat",
            payload,
            {"Content-Type": "application/json"},
        )

        return data.get("message") or {}

    def plan(self, question: str, tools: list[dict[str, Any]]) -> ModelDecision:
        message = self._chat(
            {
                "model": self._model,
                "stream": False,
                "options": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                "tools": self._tool_payload(tools),
            }
        )

        tool_calls = [
            ToolInvocation(
                name=call.get("function", {}).get("name", ""),
                arguments=self._parse_arguments(
                    call.get("function", {}).get("arguments")
                ),
            )
            for call in message.get("tool_calls") or []
        ]

        return ModelDecision(
            tool_calls=[call for call in tool_calls if call.name],
            message=message.get("content"),
        )

    def narrate(self, question: str, tool_outputs: list[tuple[str, str]]) -> str:
        message = self._chat(
            {
                "model": self._model,
                "stream": False,
                "options": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": self._narration_prompt(question, tool_outputs),
                    },
                ],
            }
        )

        content = message.get("content")

        if not content:
            raise ProviderError("Ollama returned an empty answer.")

        return content


def build_rule_based_provider() -> RuleBasedProvider:
    from altlens.analytics import list_funds

    funds = list_funds()

    return RuleBasedProvider(
        fund_names=[fund.name for fund in funds],
        manager_names=sorted(
            {fund.manager_name for fund in funds if fund.manager_name}
        ),
    )


def get_provider(
    name: str | None = None,
    model: str | None = None,
    settings: Settings | None = None,
) -> ModelProvider:
    settings = settings or default_settings
    resolved = (name or settings.model_provider or "rule_based").casefold()

    if resolved in {"openai", "hosted"}:
        return OpenAIProvider(settings, model=model)

    if resolved in {"ollama", "local"}:
        return OllamaProvider(settings, model=model)

    if resolved in {"rule_based", "rules", "deterministic", "none"}:
        return build_rule_based_provider()

    raise ProviderError(
        f"Unknown model provider '{name}'. Available providers: "
        "rule_based, openai, ollama."
    )


def list_providers(settings: Settings | None = None) -> list[ProviderInfo]:
    settings = settings or default_settings

    return [
        build_rule_based_provider().info(),
        OpenAIProvider(settings).info(),
        OllamaProvider(settings).info(),
    ]
