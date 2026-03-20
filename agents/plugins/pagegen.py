"""PageGen Agent — dynamically generates H5 pages (check-in, event intro, etc)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from agents.plugins.base import AgentPlugin
from agents.state import AgentState


class PagegenPlugin(AgentPlugin):
    """Generates H5 pages from Jinja2 templates + LLM-written copy."""

    @property
    def name(self) -> str:
        return "pagegen"

    @property
    def description(self) -> str:
        return "Generate H5 pages: check-in page, event intro, dashboard"

    @property
    def intent_keywords(self) -> list[str]:
        return [
            "页面", "page", "签到页", "活动介绍", "主页",
            "H5", "链接", "二维码", "生成页面",
        ]

    @property
    def tools(self) -> list:
        return []

    @property
    def llm_model(self) -> str | None:
        return "strong"  # Needs creativity for copywriting

    async def handle(self, state: AgentState) -> dict[str, Any]:
        """Generate an H5 page.

        In production:
        1. Determine page type from user request
        2. Fetch event data from service
        3. LLM generates copy/content
        4. Jinja2 renders template
        5. Deploy to static server
        6. Return URL + QR code
        """
        reply = (
            "好的，我可以帮您生成以下页面：\n"
            "1. **签到页** — 扫码签到 + 确认身份\n"
            "2. **活动介绍** — 活动详情 + 日程\n"
            "3. **座位图** — 实时座位分配\n"
            "4. **数据看板** — 签到统计 + 出席率\n\n"
            "请问需要生成哪种页面？"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }
