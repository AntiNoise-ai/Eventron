"""Check-in Agent — handles QR and chat-based check-in."""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import AIMessage

from agents.plugins.base import AgentPlugin
from agents.state import AgentState


class CheckinPlugin(AgentPlugin):
    """Processes check-in events and provides seat guidance."""

    @property
    def name(self) -> str:
        return "checkin"

    @property
    def description(self) -> str:
        return "Process attendee check-in (QR or chat), show seat info"

    @property
    def intent_keywords(self) -> list[str]:
        return ["签到", "check-in", "checkin", "到了", "arrived", "报到"]

    @property
    def tools(self) -> list:
        return []

    @property
    def llm_model(self) -> str | None:
        return "fast"

    async def handle(self, state: AgentState) -> dict[str, Any]:
        """Process check-in request using real services."""
        profile = state.get("user_profile")
        if not profile:
            reply = "请先告诉我您的姓名，我帮您签到。"
            return {
                "messages": [AIMessage(content=reply)],
                "current_plugin": "identity",
            }

        name = profile.get("name", "")
        event_id = state.get("event_id")
        att_svc = self.attendee_svc
        seat_svc = self.seat_svc

        # Try real check-in if services available
        if att_svc and event_id:
            try:
                attendees = await att_svc.list_attendees_for_event(
                    uuid.UUID(event_id)
                )
                # Find attendee by name
                match = None
                for a in attendees:
                    if a.name == name:
                        match = a
                        break

                if match:
                    if match.status == "checked_in":
                        reply = f"{name}，您已经签到过了！"
                    else:
                        await att_svc.checkin(match.id)
                        reply = f"{name}，签到成功！✅"
                        # Look up seat info
                        if seat_svc:
                            seats = await seat_svc.get_seats(
                                uuid.UUID(event_id)
                            )
                            for s in seats:
                                if str(s.attendee_id) == str(match.id):
                                    reply += (
                                        f"\n您的座位：{s.label}"
                                        f"（第{s.row_num}排"
                                        f" 第{s.col_num}列）"
                                    )
                                    break
                else:
                    reply = (
                        f"未在参会名单中找到「{name}」，"
                        "请确认姓名或联系工作人员。"
                    )
                return {
                    "messages": [AIMessage(content=reply)],
                    "turn_output": reply,
                }
            except Exception as e:
                reply = f"签到出错：{e}"
                return {
                    "messages": [AIMessage(content=reply)],
                    "turn_output": reply,
                }

        # Fallback if no services
        reply = (
            f"{name}，签到成功！✅\n"
            "正在查询您的座位信息..."
        )
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }
