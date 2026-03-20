"""Guide Agent — seat navigation and wayfinding."""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import AIMessage

from agents.plugins.base import AgentPlugin
from agents.state import AgentState


class GuidePlugin(AgentPlugin):
    """Provides seat navigation after check-in."""

    @property
    def name(self) -> str:
        return "guide"

    @property
    def description(self) -> str:
        return "Help attendees find their seat with map and directions"

    @property
    def intent_keywords(self) -> list[str]:
        return [
            "怎么走", "在哪", "找座位", "guide", "navigate",
            "座位在哪", "引导", "方向", "direction",
        ]

    @property
    def tools(self) -> list:
        return []

    @property
    def llm_model(self) -> str | None:
        return "fast"

    async def handle(self, state: AgentState) -> dict[str, Any]:
        """Provide seat guidance with real seat data."""
        profile = state.get("user_profile")
        if not profile:
            reply = "请先签到，我才能帮您找到座位。"
            return {
                "messages": [AIMessage(content=reply)],
                "current_plugin": "identity",
            }

        name = profile.get("name", "")
        attendee_id = profile.get("attendee_id")
        event_id = state.get("event_id")
        seat_svc = self.seat_svc

        # Try to find actual seat
        if seat_svc and event_id and attendee_id:
            try:
                seats = await seat_svc.get_seats(uuid.UUID(event_id))
                for s in seats:
                    if str(s.attendee_id) == attendee_id:
                        reply = (
                            f"{name}，您的座位是 {s.label}\n"
                            f"位置：第 {s.row_num} 排，"
                            f"第 {s.col_num} 列\n"
                            "请按指引牌前往。"
                        )
                        return {
                            "messages": [AIMessage(content=reply)],
                            "turn_output": reply,
                        }
                reply = (
                    f"{name}，暂时还没有分配座位，"
                    "请联系工作人员。"
                )
                return {
                    "messages": [AIMessage(content=reply)],
                    "turn_output": reply,
                }
            except Exception:
                pass

        reply = (
            f"{name}，正在为您查找座位...\n"
            "请稍候，我会发送座位图给您。"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }
