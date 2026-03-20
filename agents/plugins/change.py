"""Change Agent — handles seat swap, leave, add person with HITL approval."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from agents.plugins.base import AgentPlugin
from agents.state import AgentState


class ChangePlugin(AgentPlugin):
    """Processes seat changes that may require human approval."""

    @property
    def name(self) -> str:
        return "change"

    @property
    def description(self) -> str:
        return "Handle seat swap, leave, add person — with approval workflow"

    @property
    def intent_keywords(self) -> list[str]:
        return [
            "换座", "swap", "请假", "leave", "不来了", "加人",
            "add person", "临时", "调整", "变更", "change",
        ]

    @property
    def tools(self) -> list:
        return []

    @property
    def llm_model(self) -> str | None:
        return "smart"

    async def handle(self, state: AgentState) -> dict[str, Any]:
        """Handle change requests.

        In production:
        1. Parse change type (swap/leave/add)
        2. Validate the request
        3. If approval needed → create ApprovalRequest + LangGraph interrupt()
        4. If auto-approved → execute immediately
        """
        from langchain_core.messages import HumanMessage

        last_msg = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_msg = msg.content
                break

        # Detect change type from message
        if any(kw in last_msg for kw in ["请假", "不来了", "来不了"]):
            reply = (
                "好的，已记录您的请假信息。\n"
                "您的座位将被释放，如果后续能参加，随时告诉我，我帮您重新安排。"
            )
        elif any(kw in last_msg for kw in ["换座", "swap", "坐一起", "想跟"]):
            reply = (
                "收到换座申请，正在提交给管理员审批...\n"
                "审批通过后会通知您和相关人员。"
            )
        elif any(kw in last_msg for kw in ["加人", "临时", "add"]):
            reply = (
                "收到加人申请，请告诉我新参会人的姓名和职位，"
                "我会提交给管理员审批。"
            )
        else:
            reply = (
                "您需要什么变更？我可以帮您：\n"
                "- **请假** — 释放座位\n"
                "- **换座** — 与他人交换座位\n"
                "- **加人** — 临时添加参会人员\n"
            )

        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }
