"""Build and compile the LangGraph StateGraph.

Wiring:
  Entry → orchestrator → conditional edge → [plugin nodes | chat] → END

When attachments are present, the orchestrator routes to the planner
plugin first, which analyzes the files and creates a task plan.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from agents.orchestrator import chat_fallback_node, orchestrator_node
from agents.registry import PluginRegistry
from agents.state import AgentState


def build_graph(
    registry: PluginRegistry,
    llm: Any,
    plugin_llms: dict[str, Any] | None = None,
) -> StateGraph:
    """Build the Eventron agent graph.

    Args:
        registry: Plugin registry with all active plugins.
        llm: Default LLM for orchestrator and chat fallback.
        plugin_llms: Optional per-plugin LLM overrides {plugin_name: llm}.

    Returns:
        Compiled StateGraph ready for invocation.
    """
    graph = StateGraph(AgentState)

    # ── Orchestrator node ────────────────────────────────────
    # ── Scope → plugin name mapping ─────────────────────────
    _SCOPE_MAP = {
        "badge": "badge",
        "checkin": "checkin",
        "seating": "seating",
        "organizer": "organizer",
        "planner": "planner",
    }

    # Confirmation keywords that mean "go ahead with the plan"
    _CONTINUE_KEYWORDS = {
        "继续", "开始", "执行", "创建", "好", "好的", "可以",
        "开始执行", "继续创建", "继续吧", "创建吧", "执行计划",
        "是", "是的", "没问题", "确认", "ok", "go",
    }

    async def _orchestrator(state: AgentState) -> dict[str, Any]:
        # 1) Forced scope → route directly to that plugin
        scope = state.get("scope")
        if scope:
            target = _SCOPE_MAP.get(scope)
            if target and registry.get(target) is not None:
                return {"current_plugin": target}

        # 2) Attachments present and no plan yet → planner
        attachments = state.get("attachments") or []
        task_plan = state.get("task_plan") or []
        if attachments and not task_plan:
            if registry.get("planner") is not None:
                return {"current_plugin": "planner"}

        # 3) If there's an active task_plan or event_draft and user is
        #    confirming / continuing → route to organizer directly
        event_draft = state.get("event_draft")
        if task_plan or event_draft:
            from langchain_core.messages import HumanMessage as HM
            last_msg = ""
            for msg in reversed(state["messages"]):
                if isinstance(msg, HM):
                    last_msg = msg.content.strip()
                    break
            # Strip attachment prefixes for matching
            clean = last_msg
            if clean.startswith("["):
                clean = clean.split("]", 1)[-1].strip()
            if clean.lower() in _CONTINUE_KEYWORDS:
                if registry.get("organizer") is not None:
                    return {"current_plugin": "organizer"}
            # If event_draft exists and user is providing follow-up info
            # (like "500人" or dimensions), route to organizer
            if event_draft and registry.get("organizer") is not None:
                return {"current_plugin": "organizer"}

        # 4) Normal LLM-based intent routing
        return await orchestrator_node(state, registry, llm)

    graph.add_node("orchestrator", _orchestrator)
    graph.set_entry_point("orchestrator")

    # ── Chat fallback node ───────────────────────────────────
    async def _chat(state: AgentState) -> dict[str, Any]:
        return await chat_fallback_node(state, llm)

    graph.add_node("chat", _chat)
    graph.add_edge("chat", END)

    # ── Plugin nodes ─────────────────────────────────────────
    for plugin in registry.active_plugins:
        def _make_plugin_node(p):
            async def _plugin_node(state: AgentState) -> dict[str, Any]:
                return await p.handle(state)
            return _plugin_node

        graph.add_node(plugin.name, _make_plugin_node(plugin))
        graph.add_conditional_edges(
            plugin.name,
            lambda state: (
                END if state.get("turn_output") else "orchestrator"
            ),
        )

    # ── Conditional routing from orchestrator ────────────────
    def _route(state: AgentState) -> str:
        target = state.get("current_plugin", "chat")
        if target == "chat":
            return "chat"
        if registry.get(target) is not None:
            return target
        return "chat"

    route_map = {"chat": "chat"}
    for p in registry.active_plugins:
        route_map[p.name] = p.name

    graph.add_conditional_edges("orchestrator", _route, route_map)

    return graph.compile()
