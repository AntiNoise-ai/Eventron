"""Badge Agent — generates printable name badges and tent cards."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from agents.plugins.base import AgentPlugin
from agents.state import AgentState


class BadgePlugin(AgentPlugin):
    """Generates badge PDFs from Jinja2 templates."""

    @property
    def name(self) -> str:
        return "badge"

    @property
    def description(self) -> str:
        return "Generate printable name badges and tent cards as PDF"

    @property
    def intent_keywords(self) -> list[str]:
        return [
            "胸牌", "badge", "桌签", "tent card", "名牌",
            "打印", "print", "PDF", "证件",
        ]

    @property
    def tools(self) -> list:
        return []

    @property
    def llm_model(self) -> str | None:
        return "fast"

    async def handle(self, state: AgentState) -> dict[str, Any]:
        """Generate badges.

        In production:
        1. Fetch attendee list from service
        2. Select badge template (standard/VIP/tent)
        3. Render via badge_render tool
        4. Return download link
        """
        reply = (
            "好的，我来生成胸牌/桌签。请选择模板：\n"
            "1. **标准胸牌** — 90mm×54mm，A4纸8张/页\n"
            "2. **VIP胸牌** — 含金色边框\n"
            "3. **桌签** — A5对折式\n\n"
            "请选择，或者直接说「全部生成」。"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }
