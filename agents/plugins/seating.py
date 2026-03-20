"""Seating Agent — venue layout generation, zone painting, seat assignment.

Handles seating-related requests using the SeatingService and
EventService from the injected services dict.  Supports:
  - Layout generation (grid / theater / roundtable / banquet / u_shape / classroom)
  - Zone assignment (bulk zone painting via chat)
  - Auto-assign with priority_first / random / by_department / by_zone strategies
  - Seat map overview
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from agents.plugins.base import AgentPlugin
from agents.state import AgentState

# ---------------------------------------------------------------------------
# Layout / strategy / zone keyword maps
# ---------------------------------------------------------------------------

_LAYOUT_KEYWORDS: dict[str, str] = {
    "圆桌": "roundtable",
    "roundtable": "roundtable",
    "round": "roundtable",
    "剧院": "theater",
    "theater": "theater",
    "theatre": "theater",
    "弧形": "theater",
    "U形": "u_shape",
    "u_shape": "u_shape",
    "u-shape": "u_shape",
    "U型": "u_shape",
    "课桌": "classroom",
    "classroom": "classroom",
    "教室": "classroom",
    "宴会": "banquet",
    "banquet": "banquet",
    "长桌": "banquet",
    "网格": "grid",
    "grid": "grid",
    "方阵": "grid",
}

_STRATEGY_KEYWORDS: dict[str, str] = {
    "随机": "random",
    "random": "random",
    "优先": "priority_first",
    "priority": "priority_first",
    "重要": "priority_first",
    "部门": "by_department",
    "department": "by_department",
    "分区排": "by_zone",
    "按区": "by_zone",
    "zone": "by_zone",
}

_LAYOUT_LABELS: dict[str, str] = {
    "grid": "网格",
    "theater": "剧院弧形",
    "roundtable": "圆桌",
    "banquet": "宴会长桌",
    "u_shape": "U形",
    "classroom": "课桌式",
}

# Regex to extract numbers like "10排8列", "10x8", "10行8列", "rows=10 cols=8"
_DIM_RE = re.compile(
    r"(\d+)\s*[排行rows]*\s*[×xX*]\s*(\d+)\s*[列cols]*"
    r"|(\d+)\s*排\s*(\d+)\s*列"
    r"|(\d+)\s*行\s*(\d+)\s*列"
)

_TABLE_SIZE_RE = re.compile(r"(\d+)\s*人[一/每]*桌|桌\s*(\d+)\s*人|table.?size\s*(\d+)", re.I)


def _parse_dims(text: str) -> tuple[int, int] | None:
    """Extract (rows, cols) from natural language."""
    m = _DIM_RE.search(text)
    if not m:
        return None
    groups = m.groups()
    for i in range(0, len(groups), 2):
        if groups[i] and groups[i + 1]:
            return int(groups[i]), int(groups[i + 1])
    return None


def _parse_table_size(text: str) -> int | None:
    m = _TABLE_SIZE_RE.search(text)
    if not m:
        return None
    for g in m.groups():
        if g:
            return int(g)
    return None


def _detect_layout(text: str) -> str | None:
    lower = text.lower()
    for kw, layout in _LAYOUT_KEYWORDS.items():
        if kw.lower() in lower:
            return layout
    return None


def _detect_strategy(text: str) -> str:
    lower = text.lower()
    for kw, strat in _STRATEGY_KEYWORDS.items():
        if kw in lower:
            return strat
    return "priority_first"


def _detect_zone(text: str) -> str | None:
    """Extract zone name from text like '设为贵宾区' / '标记为嘉宾区'."""
    m = re.search(r"[设标划归].*?[为成入][\s「「]*([\w]+区)", text)
    if m:
        return m.group(1)
    # Also match bare zone names
    for zone in ("贵宾区", "嘉宾区", "普通区", "VIP区", "媒体区", "工作区"):
        if zone in text:
            return zone
    return None


class SeatingPlugin(AgentPlugin):
    """Manages venue layout, zone painting, and seat assignment strategies."""

    @property
    def name(self) -> str:
        return "seating"

    @property
    def description(self) -> str:
        return (
            "Manage venue layout (6 types), zone painting, "
            "and auto-assign seats (priority/random/department/zone)"
        )

    @property
    def intent_keywords(self) -> list[str]:
        return [
            "排座", "座位", "assign", "seating", "布局", "layout",
            "自动排", "座位图", "生成座位", "圆桌", "剧院", "U形",
            "课桌", "宴会", "分区", "zone", "贵宾区", "嘉宾区",
            "优先排座", "网格", "弧形", "长桌",
        ]

    @property
    def tools(self) -> list:
        return []

    @property
    def llm_model(self) -> str | None:
        return "smart"

    async def handle(self, state: AgentState) -> dict[str, Any]:
        """Route seating sub-intents to appropriate handlers."""
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

        last_msg = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_msg = msg.content
                break

        seat_svc = self.seat_svc
        event_svc = self.event_svc

        # --- Sub-intent routing (order matters) ---

        # 1. Layout generation: "生成剧院式布局 10排20列"
        if any(kw in last_msg for kw in [
            "生成", "创建座位", "generate", "布局", "layout",
            "圆桌", "剧院", "U形", "课桌", "宴会", "网格", "弧形", "长桌",
        ]):
            layout = _detect_layout(last_msg)
            if layout:
                return await self._generate_layout(
                    event_id, event_svc, seat_svc, last_msg, layout
                )
            # No layout type detected — check if they just want a basic grid
            if any(kw in last_msg for kw in ["生成", "创建座位", "generate"]):
                return await self._generate_layout(
                    event_id, event_svc, seat_svc, last_msg, "grid"
                )

        # 2. Zone operations: "把前两排设为贵宾区"
        if any(kw in last_msg for kw in ["分区", "zone", "区域", "设为", "标记", "划为"]):
            zone_name = _detect_zone(last_msg)
            if zone_name:
                return await self._set_zone(event_id, seat_svc, last_msg, zone_name)
            return await self._zone_help(event_id, seat_svc)

        # 3. Auto-assign: "自动排座 / 按优先级分配"
        if any(kw in last_msg for kw in [
            "自动排", "auto", "分配", "排座",
            "随机", "优先", "部门", "priority",
        ]):
            strategy = _detect_strategy(last_msg)
            return await self._auto_assign(event_id, seat_svc, strategy)

        # 4. View seat map
        if any(kw in last_msg for kw in ["查看", "座位图", "view", "map", "概况"]):
            return await self._view_seats(event_id, seat_svc)

        # 5. General help
        reply = (
            "好的，关于排座我可以帮您：\n"
            "1. **生成座位布局** — 支持6种布局：网格、剧院弧形、圆桌、"
            "宴会长桌、U形、课桌式\n"
            "   例：「生成剧院式布局 10排20列」\n"
            "2. **座位分区** — 把指定区域设为贵宾区/嘉宾区等\n"
            "   例：「把前3排设为贵宾区」\n"
            "3. **自动排座** — 按优先级/随机/部门/分区\n"
            "   例：「按优先级自动排座」\n"
            "4. **查看座位图** — 当前座位分配情况\n\n"
            "请问需要哪项操作？"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }

    # ------------------------------------------------------------------
    # Layout generation
    # ------------------------------------------------------------------

    async def _generate_layout(
        self,
        event_id: str,
        event_svc,
        seat_svc,
        msg: str,
        layout_type: str,
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

            # Parse dimensions from message, fall back to event venue dims
            dims = _parse_dims(msg)
            rows = dims[0] if dims else event.venue_rows
            cols = dims[1] if dims else event.venue_cols
            if rows <= 0 or cols <= 0:
                rows, cols = 10, 10  # sensible default

            table_size = _parse_table_size(msg) or 8
            label = _LAYOUT_LABELS.get(layout_type, layout_type)

            seats = await seat_svc.create_venue_layout(
                eid,
                layout_type=layout_type,
                rows=rows,
                cols=cols,
                table_size=table_size,
                replace=True,
            )
            reply = (
                f"已生成 **{label}** 布局，共 {len(seats)} 个座位"
                f"（{rows}排 × {cols}列"
            )
            if layout_type in ("roundtable", "banquet"):
                reply += f"，每桌{table_size}人"
            reply += "）。\n请在「座位图」标签页查看并调整。"

        except Exception as e:
            reply = f"生成布局失败：{e}"
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }

    # ------------------------------------------------------------------
    # Zone operations
    # ------------------------------------------------------------------

    async def _set_zone(
        self,
        event_id: str,
        seat_svc,
        msg: str,
        zone_name: str,
    ) -> dict[str, Any]:
        """Set zone on seats based on natural language row/position description."""
        if not seat_svc:
            reply = "服务未就绪，请稍后再试。"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }
        try:
            eid = uuid.UUID(event_id)
            seats = await seat_svc.get_seats(eid)
            if not seats:
                reply = "该活动还没有座位，请先生成座位布局。"
                return {
                    "messages": [AIMessage(content=reply)],
                    "turn_output": reply,
                }

            # Parse row range from message: "前3排", "第1-3排", "后两排"
            target_ids = self._select_seats_by_description(seats, msg)

            if not target_ids:
                reply = (
                    f"未能确定要设为「{zone_name}」的座位范围。\n"
                    "请说明具体范围，例如：\n"
                    "- 「把前3排设为贵宾区」\n"
                    "- 「第1-5排设为嘉宾区」\n"
                    "- 「后两排设为普通区」\n"
                    "或者在座位图上框选后操作。"
                )
            else:
                count = await seat_svc.bulk_update_zone(target_ids, zone_name)
                reply = (
                    f"已将 {count} 个座位设为 **{zone_name}**。\n"
                    "请在「座位图」标签页查看效果。"
                )
        except Exception as e:
            reply = f"分区设置失败：{e}"
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }

    async def _zone_help(
        self, event_id: str, seat_svc
    ) -> dict[str, Any]:
        """Show zone overview and suggestions."""
        try:
            eid = uuid.UUID(event_id)
            seats = await seat_svc.get_seats(eid)
            if not seats:
                reply = "该活动还没有座位，请先生成座位布局再进行分区。"
            else:
                zones: dict[str | None, int] = {}
                for s in seats:
                    z = getattr(s, "zone", None)
                    zones[z] = zones.get(z, 0) + 1

                lines = [f"当前共 {len(seats)} 个座位，分区情况："]
                for z, cnt in sorted(
                    zones.items(), key=lambda x: (x[0] is None, x[0])
                ):
                    label = z or "未分区"
                    lines.append(f"  · {label}：{cnt} 个")

                lines.append("\n您可以说：")
                lines.append("- 「把前3排设为贵宾区」")
                lines.append("- 「第4-8排设为嘉宾区」")
                lines.append("- 「剩余座位设为普通区」")
                reply = "\n".join(lines)
        except Exception as e:
            reply = f"查询分区失败：{e}"
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }

    @staticmethod
    def _select_seats_by_description(
        seats: list, msg: str
    ) -> list[uuid.UUID]:
        """Parse row descriptions and return matching seat IDs."""
        if not seats:
            return []

        max_row = max(s.row_num for s in seats)
        target_rows: set[int] = set()

        # "前N排"
        m = re.search(r"前\s*(\d+)\s*排", msg)
        if m:
            n = int(m.group(1))
            target_rows = set(range(1, min(n + 1, max_row + 1)))

        # "后N排"
        if not target_rows:
            m = re.search(r"后\s*(\d+)\s*排", msg)
            if m:
                n = int(m.group(1))
                target_rows = set(range(max(1, max_row - n + 1), max_row + 1))

        # "第X排" or "第X-Y排"
        if not target_rows:
            m = re.search(r"第\s*(\d+)\s*[-到至]\s*(\d+)\s*排", msg)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                target_rows = set(range(a, b + 1))
            else:
                m = re.search(r"第\s*(\d+)\s*排", msg)
                if m:
                    target_rows = {int(m.group(1))}

        # "剩余" / "其余" — seats with no zone
        if not target_rows and any(kw in msg for kw in ["剩余", "其余", "剩下", "其他"]):
            return [
                s.id for s in seats
                if getattr(s, "zone", None) is None
            ]

        if not target_rows:
            return []

        return [s.id for s in seats if s.row_num in target_rows]

    # ------------------------------------------------------------------
    # Auto-assign
    # ------------------------------------------------------------------

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
            "priority_first": "优先级优先",
            "by_department": "按部门",
            "by_zone": "按分区",
        }.get(strategy, strategy)
        try:
            assignments = await seat_svc.auto_assign(
                uuid.UUID(event_id), strategy=strategy
            )
            if not assignments:
                reply = "没有需要分配的参会者（都已有座位或没有参会者）。"
            else:
                reply = (
                    f"排座完成！策略：**{label}**，"
                    f"共分配 {len(assignments)} 个座位。\n"
                    "请在「座位图」标签页查看结果。"
                )
        except Exception as e:
            reply = f"排座失败：{e}"
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }

    # ------------------------------------------------------------------
    # View seats
    # ------------------------------------------------------------------

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
                reply = (
                    "该活动还没有座位。\n"
                    "要生成座位布局吗？支持6种类型：\n"
                    "网格、剧院弧形、圆桌、宴会长桌、U形、课桌式"
                )
            else:
                occupied = sum(1 for s in seats if s.attendee_id)
                total = len(seats)
                zones: dict[str | None, int] = {}
                for s in seats:
                    z = getattr(s, "zone", None)
                    zones[z] = zones.get(z, 0) + 1

                reply = (
                    f"当前座位概况：共 {total} 个座位，"
                    f"已分配 {occupied} 个，空闲 {total - occupied} 个。\n"
                )
                if any(z is not None for z in zones):
                    zone_parts = []
                    for z, cnt in sorted(
                        zones.items(), key=lambda x: (x[0] is None, x[0])
                    ):
                        if z:
                            zone_parts.append(f"{z}({cnt})")
                    if zone_parts:
                        reply += f"分区：{'、'.join(zone_parts)}\n"
                reply += "请在「座位图」标签页查看详细可视化。"
        except Exception as e:
            reply = f"查询失败：{e}"
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }
