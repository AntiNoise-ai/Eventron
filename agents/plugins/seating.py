"""Seating Agent — venue setup and seat auto-assignment.

Handles seating-related requests using the SeatingService and
EventService from the injected services dict.
"""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from agents.plugins.base import AgentPlugin
from agents.state import AgentState


class SeatingPlugin(AgentPlugin):
    """Manages venue layout and seat assignment strategies."""

    @property
    def name(self) -> str:
        return "seating"

    @property
    def description(self) -> str:
        return "Manage venue layout, auto-assign seats, view seat map"

    @property
    def intent_keywords(self) -> list[str]:
        return [
            "排座", "座位", "assign", "seating", "布局", "layout",
            "自动排", "VIP", "座位图", "生成座位",
        ]

    @property
    def tools(self) -> list:
        return []

    @property
    def llm_model(self) -> str | None:
        return "smart"

    async def handle(self, state: AgentState) -> dict[str, Any]:
        """Handle seating-related requests with real services."""
        event_id = state.get("event_id")
        if not event_id:
            reply = (
                "请先告诉我是哪个活动的排座？"
                "您可以说活动名称，或者我帮您创建一个新活动。"
            )
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }

        # Parse user intent from last message
        last_msg = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_msg = msg.content
                break

        seat_svc = self.seat_svc
        event_svc = self.event_svc

        # Try to handle specific sub-intents
        if any(kw in last_msg for kw in ["生成", "创建座位", "generate"]):
            return await self._generate_seats(event_id, event_svc, seat_svc)
        if any(kw in last_msg for kw in ["自动排", "auto", "分配"]):
            strategy = "vip_first"
            if "随机" in last_msg or "random" in last_msg:
                strategy = "random"
            elif "部门" in last_msg or "department" in last_msg:
                strategy = "by_department"
            return await self._auto_assign(event_id, seat_svc, strategy)
        if any(kw in last_msg for kw in ["查看", "座位图", "view", "map"]):
            return await self._view_seats(event_id, seat_svc)

        # General help
        reply = (
            "好的，关于排座我可以帮您：\n"
            "1. **生成座位** — 按会场行列创建座位网格\n"
            "2. **自动排座** — 随机/VIP优先/按部门分组\n"
            "3. **查看座位图** — 当前座位分配情况\n\n"
            "请问需要哪项操作？"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }

    async def _generate_seats(
        self, event_id: str, event_svc, seat_svc
    ) -> dict[str, Any]:
        if not event_svc or not seat_svc:
            reply = "服务未就绪，请稍后再试。"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }
        try:
            eid = uuid.UUID(event_id)
            event = await event_svc.get_event(eid)
            existing = await seat_svc.get_seats(eid)
            if existing:
                reply = f"该活动已有 {len(existing)} 个座位，无需重复生成。"
            else:
                seats = await seat_svc.create_venue_grid(
                    eid, event.venue_rows, event.venue_cols
                )
                reply = (
                    f"✅ 已生成 {len(seats)} 个座位！"
                    f"（{event.venue_rows}排 × {event.venue_cols}列）"
                )
        except Exception as e:
            reply = f"生成失败：{e}"
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }

    async def _auto_assign(
        self, event_id: str, seat_svc, strategy: str
    ) -> dict[str, Any]:
        if not seat_svc:
            reply = "服务未就绪，请稍后再试。"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }
        label = {
            "random": "随机",
            "vip_first": "VIP优先",
            "by_department": "按部门",
        }.get(strategy, strategy)
        try:
            assignments = await seat_svc.auto_assign(
                uuid.UUID(event_id), strategy=strategy
            )
            if not assignments:
                reply = "没有需要分配的参会者（都已有座位或没有参会者）。"
            else:
                reply = (
                    f"✅ 排座完成！策略：{label}，"
                    f"共分配 {len(assignments)} 个座位。"
                )
        except Exception as e:
            reply = f"排座失败：{e}"
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }

    async def _view_seats(
        self, event_id: str, seat_svc
    ) -> dict[str, Any]:
        if not seat_svc:
            reply = "服务未就绪，请稍后再试。"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }
        try:
            seats = await seat_svc.get_seats(uuid.UUID(event_id))
            if not seats:
                reply = "该活动还没有座位，要先生成座位网格吗？"
            else:
                occupied = sum(1 for s in seats if s.attendee_id)
                total = len(seats)
                reply = (
                    f"当前座位概况：共 {total} 个座位，"
                    f"已分配 {occupied} 个，"
                    f"空闲 {total - occupied} 个。\n"
                    "请在「座位图」标签页查看详细可视化。"
                )
        except Exception as e:
            reply = f"查询失败：{e}"
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }
