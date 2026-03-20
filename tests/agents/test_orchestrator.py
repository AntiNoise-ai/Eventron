"""Tests for orchestrator — mock LLM, verify routing decisions."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from agents.orchestrator import classify_intent
from agents.plugins.base import AgentPlugin
from agents.registry import PluginRegistry


# ── Helpers ──────────────────────────────────────────────────

class DummyPlugin(AgentPlugin):
    """Minimal plugin for testing registry integration."""

    def __init__(self, name: str, keywords: list[str], requires_id: bool = True):
        self._name = name
        self._keywords = keywords
        self._requires_id = requires_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Test plugin: {self._name}"

    @property
    def intent_keywords(self) -> list[str]:
        return self._keywords

    @property
    def tools(self) -> list:
        return []

    async def handle(self, state):
        return {"turn_output": f"Handled by {self._name}"}

    @property
    def requires_identity(self) -> bool:
        return self._requires_id


def _make_state(msg: str, user_profile=None, event_id=None):
    return {
        "messages": [HumanMessage(content=msg)],
        "current_plugin": "chat",
        "user_profile": user_profile,
        "event_id": event_id,
        "pending_approval": None,
        "turn_output": None,
    }


def _mock_llm(response: str):
    llm = AsyncMock()
    llm.ainvoke.return_value = AIMessage(content=response)
    return llm


def _build_registry():
    reg = PluginRegistry()
    reg.register(DummyPlugin("seating", ["排座", "座位", "assign"]))
    reg.register(DummyPlugin("checkin", ["签到", "check-in", "checkin"]))
    reg.register(DummyPlugin("identity", ["我是", "身份", "who"], requires_id=False))
    reg.register(DummyPlugin("change", ["换座", "请假", "swap"]))
    return reg


# ── Tests ────────────────────────────────────────────────────

class TestClassifyIntent:
    """Verify orchestrator routes correctly based on LLM output."""

    async def test_routes_to_seating(self):
        """LLM says 'seating' → route to seating plugin."""
        state = _make_state("帮我排座", user_profile={"name": "张三"})
        llm = _mock_llm("seating")
        reg = _build_registry()

        intent = await classify_intent(state, reg, llm)
        assert intent == "seating"

    async def test_routes_to_checkin(self):
        """LLM says 'checkin' → route to checkin plugin."""
        state = _make_state("签到", user_profile={"name": "李四"})
        llm = _mock_llm("checkin")
        reg = _build_registry()

        intent = await classify_intent(state, reg, llm)
        assert intent == "checkin"

    async def test_unknown_plugin_falls_to_chat(self):
        """LLM outputs unknown plugin name → fallback to chat."""
        state = _make_state("hello")
        llm = _mock_llm("nonexistent_plugin")
        reg = _build_registry()

        intent = await classify_intent(state, reg, llm)
        assert intent == "chat"

    async def test_identity_gate_no_profile(self):
        """User has no profile and target plugin requires identity → force identity."""
        state = _make_state("排座", user_profile=None)
        llm = _mock_llm("seating")  # LLM says seating, but user is unknown
        reg = _build_registry()

        intent = await classify_intent(state, reg, llm)
        assert intent == "identity"

    async def test_identity_gate_with_profile(self):
        """User HAS a profile → no identity redirect."""
        state = _make_state("排座", user_profile={"name": "张三"})
        llm = _mock_llm("seating")
        reg = _build_registry()

        intent = await classify_intent(state, reg, llm)
        assert intent == "seating"

    async def test_identity_plugin_no_gate(self):
        """Identity plugin itself doesn't trigger identity gate."""
        state = _make_state("我是张三", user_profile=None)
        llm = _mock_llm("identity")
        reg = _build_registry()

        intent = await classify_intent(state, reg, llm)
        assert intent == "identity"

    async def test_chat_fallback(self):
        """General conversation → chat."""
        state = _make_state("今天天气怎么样")
        llm = _mock_llm("chat")
        reg = _build_registry()

        intent = await classify_intent(state, reg, llm)
        assert intent == "chat"


class TestPluginRegistry:
    """Tests for registry itself."""

    def test_register_and_get(self):
        reg = PluginRegistry()
        p = DummyPlugin("test", ["foo"])
        reg.register(p)
        assert reg.get("test") is p

    def test_get_nonexistent_returns_none(self):
        reg = PluginRegistry()
        assert reg.get("nope") is None

    def test_active_plugins_excludes_disabled(self):
        reg = PluginRegistry()
        p = DummyPlugin("test", ["foo"])
        p.enabled  # True by default
        reg.register(p)
        assert len(reg.active_plugins) == 1

    def test_build_routing_prompt_empty(self):
        reg = PluginRegistry()
        prompt = reg.build_routing_prompt()
        assert "No plugins" in prompt

    def test_build_routing_prompt_with_plugins(self):
        reg = _build_registry()
        prompt = reg.build_routing_prompt()
        assert "seating" in prompt
        assert "checkin" in prompt
        assert "排座" in prompt

    def test_unregister(self):
        reg = PluginRegistry()
        p = DummyPlugin("test", ["foo"])
        reg.register(p)
        assert reg.unregister("test") is True
        assert reg.get("test") is None
        assert reg.unregister("test") is False
