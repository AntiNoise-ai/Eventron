"""Tests for all agent plugins — mock LLM + mock services."""

import pytest
from langchain_core.messages import HumanMessage

from agents.plugins.badge import BadgePlugin
from agents.plugins.change import ChangePlugin
from agents.plugins.checkin import CheckinPlugin
from agents.plugins.guide import GuidePlugin
from agents.plugins.identity import IdentityPlugin
from agents.plugins.pagegen import PagegenPlugin
from agents.plugins.seating import SeatingPlugin
from agents.registry import PluginRegistry


def _state(msg: str, user_profile=None, event_id=None):
    return {
        "messages": [HumanMessage(content=msg)],
        "current_plugin": "chat",
        "user_profile": user_profile,
        "event_id": event_id,
        "pending_approval": None,
        "turn_output": None,
    }


class TestIdentityPlugin:
    plugin = IdentityPlugin()

    def test_metadata(self):
        assert self.plugin.name == "identity"
        assert self.plugin.requires_identity is False

    async def test_already_identified(self):
        state = _state("你好", user_profile={"name": "张三"})
        result = await self.plugin.handle(state)
        assert "张三" in result["turn_output"]

    async def test_asks_for_name(self):
        state = _state("hello")
        result = await self.plugin.handle(state)
        assert "姓名" in result["turn_output"]

    async def test_extracts_name_from_wo_shi(self):
        state = _state("我是张三")
        result = await self.plugin.handle(state)
        assert "张三" in result["turn_output"]

    def test_extract_name_hint_patterns(self):
        assert IdentityPlugin._extract_name_hint("我是张三") == "张三"
        assert IdentityPlugin._extract_name_hint("我叫李四") == "李四"
        assert IdentityPlugin._extract_name_hint("I am Bob") == "Bob"
        assert IdentityPlugin._extract_name_hint("今天天气不错") is None


class TestSeatingPlugin:
    plugin = SeatingPlugin()

    def test_metadata(self):
        assert self.plugin.name == "seating"
        assert "排座" in self.plugin.intent_keywords

    async def test_no_event_asks_which(self):
        state = _state("帮我排座")
        result = await self.plugin.handle(state)
        assert "哪个活动" in result["turn_output"]

    async def test_with_event_shows_options(self):
        state = _state("排座", event_id="evt-1")
        result = await self.plugin.handle(state)
        assert "自动排座" in result["turn_output"]


class TestCheckinPlugin:
    plugin = CheckinPlugin()

    def test_metadata(self):
        assert self.plugin.name == "checkin"
        assert "签到" in self.plugin.intent_keywords

    async def test_no_profile_redirects(self):
        state = _state("签到")
        result = await self.plugin.handle(state)
        assert result.get("current_plugin") == "identity"

    async def test_with_profile_checks_in(self):
        state = _state("签到", user_profile={"name": "张三"})
        result = await self.plugin.handle(state)
        assert "签到成功" in result["turn_output"]


class TestChangePlugin:
    plugin = ChangePlugin()

    def test_metadata(self):
        assert self.plugin.name == "change"

    async def test_leave_request(self):
        state = _state("我临时有事来不了了", user_profile={"name": "张三"})
        result = await self.plugin.handle(state)
        assert "请假" in result["turn_output"]

    async def test_swap_request(self):
        state = _state("我想跟李四换座", user_profile={"name": "张三"})
        result = await self.plugin.handle(state)
        assert "审批" in result["turn_output"]

    async def test_generic_change(self):
        state = _state("我需要变更", user_profile={"name": "张三"})
        result = await self.plugin.handle(state)
        assert "请假" in result["turn_output"]


class TestBadgePlugin:
    plugin = BadgePlugin()

    def test_metadata(self):
        assert self.plugin.name == "badge"

    async def test_shows_template_options(self):
        state = _state("生成胸牌", user_profile={"name": "张三"})
        result = await self.plugin.handle(state)
        assert "标准胸牌" in result["turn_output"]


class TestPagegenPlugin:
    plugin = PagegenPlugin()

    def test_metadata(self):
        assert self.plugin.name == "pagegen"
        assert self.plugin.llm_model == "strong"

    async def test_shows_page_options(self):
        state = _state("生成签到页面", user_profile={"name": "管理员"})
        result = await self.plugin.handle(state)
        assert "签到页" in result["turn_output"]


class TestGuidePlugin:
    plugin = GuidePlugin()

    def test_metadata(self):
        assert self.plugin.name == "guide"

    async def test_no_profile_redirects(self):
        state = _state("我的座位在哪")
        result = await self.plugin.handle(state)
        assert result.get("current_plugin") == "identity"

    async def test_with_profile_guides(self):
        state = _state("座位在哪", user_profile={"name": "张三"})
        result = await self.plugin.handle(state)
        assert "张三" in result["turn_output"]


class TestAllPluginsRegistry:
    """Integration: register all plugins and verify registry."""

    def test_register_all(self):
        from agents.plugins import ALL_PLUGINS

        reg = PluginRegistry()
        for cls in ALL_PLUGINS:
            reg.register(cls())
        assert len(reg.active_plugins) == 7
        prompt = reg.build_routing_prompt()
        for name in ["identity", "seating", "checkin", "change", "badge", "pagegen", "guide"]:
            assert name in prompt
