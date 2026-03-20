"""Identity Agent — recognizes user identity, binds IM user_id to attendee."""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from agents.plugins.base import AgentPlugin
from agents.state import AgentState


class IdentityPlugin(AgentPlugin):
    """Identifies who the user is by matching against the attendee list."""

    @property
    def name(self) -> str:
        return "identity"

    @property
    def description(self) -> str:
        return "Identify user identity, match IM user to attendee list"

    @property
    def intent_keywords(self) -> list[str]:
        return ["我是", "身份", "who am i", "identity", "叫什么", "名字"]

    @property
    def tools(self) -> list:
        return []

    @property
    def requires_identity(self) -> bool:
        return False  # This plugin IS the identity resolver

    @property
    def llm_model(self) -> str | None:
        return "fast"

    async def handle(self, state: AgentState) -> dict[str, Any]:
        """Try to identify user from their message.

        Flow:
        1. Check if user already identified -> return greeting
        2. Extract name from message (e.g. "我是张三")
        3. Match against attendee list via service
        4. If unique match -> bind and confirm
        5. If ambiguous -> ask for clarification
        6. If no match -> ask user to provide name
        """
        if state.get("user_profile"):
            name = state["user_profile"].get("name", "")
            reply = f"您好 {name}，我已经知道您的身份了。有什么可以帮您的？"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }

        # Extract name from last user message
        last_msg = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_msg = msg.content
                break

        name_hint = self._extract_name_hint(last_msg)

        if not name_hint:
            reply = "请问您是哪位？请告诉我您的姓名，我帮您在参会名单中查找。"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }

        # Try real service lookup if available
        att_svc = self.attendee_svc
        event_id = state.get("event_id")

        if att_svc and event_id:
            try:
                attendees = await att_svc.list_attendees_for_event(
                    uuid.UUID(event_id)
                )
                matches = [
                    a for a in attendees if name_hint in a.name
                ]
                if len(matches) == 1:
                    a = matches[0]
                    reply = (
                        f"找到了！您是 {a.name}"
                        f"（{a.organization or ''} {a.title or ''}）。"
                        f"\n身份已确认，有什么可以帮您的？"
                    )
                    return {
                        "messages": [AIMessage(content=reply)],
                        "user_profile": {
                            "name": a.name,
                            "attendee_id": str(a.id),
                            "role": a.role,
                        },
                        "turn_output": reply,
                    }
                elif len(matches) > 1:
                    names = "、".join(a.name for a in matches[:5])
                    reply = (
                        f"找到多位匹配：{names}。"
                        f"\n请说出您的全名以便确认。"
                    )
                    return {
                        "messages": [AIMessage(content=reply)],
                        "turn_output": reply,
                    }
            except Exception:
                pass  # Fall through to generic response

        # Generic confirmation (no service or no event)
        reply = (
            f"您好！请确认您是 {name_hint} 吗？"
            "如果是的话我会帮您绑定身份，之后就可以直接操作了。"
        )
        return {
            "messages": [AIMessage(content=reply)],
            "turn_output": reply,
        }

    @staticmethod
    def _extract_name_hint(message: str) -> str | None:
        """Simple heuristic to extract a name from user message.

        Handles patterns like:
        - "我是张三"
        - "张三"
        - "I am Zhang San"
        """
        prefixes = ["我是", "我叫", "i am ", "i'm ", "this is "]
        lower = message.strip().lower()
        for prefix in prefixes:
            if lower.startswith(prefix):
                name = message.strip()[len(prefix):].strip()
                if name:
                    return name

        # If message is very short Chinese name (2-4 chars)
        stripped = message.strip()
        if 2 <= len(stripped) <= 4 and all(
            "\u4e00" <= ch <= "\u9fff" for ch in stripped
        ):
            return stripped

        return None
