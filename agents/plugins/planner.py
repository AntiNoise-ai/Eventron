"""Planner Agent — multimodal input analysis + task decomposition.

This is the "brain" of the multi-agent system. When a user uploads files
(images, Excel, PDF) or describes complex requirements, the planner:

1. Analyzes all inputs (vision LLM for images, parsers for docs)
2. Extracts structured event information
3. Decomposes into parallel sub-tasks for other plugins
4. Returns a task plan + immediate summary to the user

The planner uses the STRONG tier LLM (Claude) for vision/reasoning.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from agents.llm_utils import extract_text_content
from agents.plugins.base import AgentPlugin
from agents.state import AgentState


PLANNER_SYSTEM = """你是 Eventron 活动规划助手。你擅长从各种输入（图片、文件、自然语言描述）中
提取活动信息，并自动拆解成可执行的子任务。

## 你的工作流程

1. **分析输入** — 理解用户上传的图片/文件/描述
2. **提取信息** — 活动名称、日期、地点、人数、布局需求等
3. **拆解任务** — 自动分解为并行子任务

## 可分配的子任务（对应系统中的 plugin）

- **organizer**: 创建活动、设置会场参数（行列数、布局类型）
- **seating**: 生成座位网格、自动排座
- **badge**: 设计铭牌/胸牌/桌签
- **checkin**: 设计签到流程（时间、方式）
- **pagegen**: 生成 H5 签到页面/活动介绍页

## 输出格式

请输出两部分：

### Part 1: 中文分析摘要
用自然语言总结你从输入中理解到的活动需求。

### Part 2: 结构化任务计划
在回复末尾输出 JSON：
```plan
{{
  "event_info": {{
    "name": "活动名称",
    "date": "YYYY-MM-DD 或 null",
    "time": "HH:MM-HH:MM 或 null",
    "location": "地点",
    "layout_type": "theater|classroom|roundtable|banquet|u_shape",
    "estimated_rows": 行数或null,
    "estimated_cols": 列数或null,
    "estimated_attendees": 估计人数或null
  }},
  "sub_tasks": [
    {{
      "id": "任务ID",
      "plugin": "目标plugin",
      "description": "具体要做什么",
      "priority": 1
    }}
  ],
  "questions": ["需要用户确认的问题（如果有）"]
}}
```

## 推理原则（不要套规则，要思考）

- 信息够 → 给完整计划；不够 → 列 questions 让用户补
- 有图片 → 先把图片里**写出来的字**全部读完（标题/日期/地点/主办方）
- 有 Excel → 别假定它就是花名册；先看结构事实
- **场地尺寸不要从 Excel 行数推断**；要么用户给具体尺寸，要么调
  suggest_venue_dims 让另一个 LLM 推荐候选
- 不要写死"<30 人就 u_shape, >100 就 theater"这种规则；类型由活动
  性质决定（讲座=theater, 研讨=u_shape/roundtable, 培训=classroom），
  不确定就问用户

## 当前上下文
{context}"""


class PlannerPlugin(AgentPlugin):
    """Analyzes multimodal inputs and decomposes into sub-tasks."""

    @property
    def name(self) -> str:
        return "planner"

    @property
    def description(self) -> str:
        return (
            "Analyze uploaded files (images/Excel/PDF) and text "
            "requirements, extract event info, decompose into sub-tasks "
            "for venue design, badge design, check-in setup"
        )

    @property
    def intent_keywords(self) -> list[str]:
        return [
            "规划", "plan", "拆解", "设计", "分析",
            "上传", "upload", "图片", "附件", "文件",
            "帮我做", "全部", "一站式", "自动",
            "需求", "requirement",
        ]

    @property
    def tools(self) -> list:
        return []

    @property
    def requires_identity(self) -> bool:
        return False

    @property
    def llm_model(self) -> str | None:
        return "strong"  # Needs vision + complex reasoning

    async def handle(self, state: AgentState) -> dict[str, Any]:
        """Analyze inputs and create task plan."""
        attachments = list(state.get("attachments") or [])
        last_msg = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_msg = extract_text_content(msg.content)
                break

        # If no current attachments but user references files,
        # look up previously uploaded event files.
        if not attachments and state.get("event_id"):
            attachments = self._find_event_files(state["event_id"])

        # If there are image attachments, use vision analysis
        if any(a.get("type") == "image" for a in attachments):
            return await self._handle_with_vision(
                state, attachments, last_msg
            )

        # If there are Excel attachments, extract attendee data
        if any(a.get("type") == "excel" for a in attachments):
            return await self._handle_with_excel(
                state, attachments, last_msg
            )

        # Text-only planning
        return await self._handle_text_only(state, last_msg)

    @staticmethod
    def _find_event_files(event_id: str) -> list[dict]:
        """Look up all files from the event's file store."""
        try:
            from tools.event_files import load_manifest, event_dir
            manifest = load_manifest(event_id)
            results = []
            edir = event_dir(event_id)
            for entry in manifest:
                p = edir / entry["stored_name"]
                if p.exists():
                    results.append({**entry, "path": str(p)})
            return results
        except Exception:
            return []

    async def _handle_with_vision(
        self,
        state: AgentState,
        attachments: list[dict],
        user_msg: str,
    ) -> dict[str, Any]:
        """Use vision LLM to analyze image and plan."""
        from tools.file_extract import build_vision_message

        image_att = next(
            a for a in attachments if a.get("type") == "image"
        )
        image_path = image_att["path"]
        filename = image_att.get("filename", "image.png")

        # Build vision messages
        llm = self.get_llm("strong")
        if not llm:
            # Fallback to smart
            llm = self.get_llm("smart")

        if not llm:
            reply = "LLM 未配置，无法分析图片。"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }

        try:
            vision_msgs = build_vision_message(image_path, filename)

            # Add user context if any
            if user_msg and user_msg not in ("上传", "分析"):
                vision_msgs.append({
                    "role": "user",
                    "content": f"用户补充说明：{user_msg}",
                })

            response = await llm.ainvoke(vision_msgs)
            extracted = response.content

            # Now use the planner LLM to create task plan
            return await self._create_plan_from_analysis(
                state, extracted, user_msg, attachments
            )
        except Exception as e:
            # If vision fails, try text-based approach
            reply = (
                f"图片分析出错：{e}\n"
                "请用文字描述您的活动需求，我来帮您规划。"
            )
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }

    async def _handle_with_excel(
        self,
        state: AgentState,
        attachments: list[dict],
        user_msg: str,
    ) -> dict[str, Any]:
        """Surface Excel **facts** to the planner LLM. No classification here.

        The planner reads:
          - structural facts (sheet names, header rows, sample rows,
            stage-word matches, name-cell density)
          - raw text excerpt
        and reasons about what kind of file it is + what to plan next.
        Whether it's a roster or seat chart is the LLM's call.
        """
        from tools.excel_io import (
            inspect_excel_structure,
            read_excel_sheets_as_text,
        )

        excel_att = next(
            a for a in attachments if a.get("type") == "excel"
        )
        try:
            facts = inspect_excel_structure(file_path=excel_att["path"])
            preview = read_excel_sheets_as_text(
                file_path=excel_att["path"], max_rows_per_sheet=8,
            )
            analysis = (
                "Excel 结构事实（你需要自己判断这是花名册还是座位图）：\n"
                + json.dumps(facts, ensure_ascii=False, indent=2)
                + "\n\nExcel 行级预览：\n"
                + preview
                + "\n\n判断与规划提示（你来拍板）：\n"
                "- 若 sheet 列名看起来是 姓名/公司/部门/职位/电话/邮箱"
                "+ stage_words 为空 → 花名册：让 seating 用 "
                "smart_import_roster 一次性导入并自动拆 公司+职位 字段\n"
                "- 若 stage_words 有命中 + 单元格散布 → 空间座位图：让 "
                "seating 用 analyze_seat_chart + import_from_seat_chart\n"
                "- 不论哪种，**不要把 Excel 的 total_rows 当成场地排数**；"
                "venue_rows / venue_cols 应当来自用户的场地描述或者 "
                "suggest_venue_dims 的推荐\n"
                "- 不确定 → questions 里追问用户"
            )
            return await self._create_plan_from_analysis(
                state, analysis, user_msg, attachments,
            )
        except Exception as e:
            reply = f"Excel 读取出错：{e}"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }

    async def _handle_text_only(
        self,
        state: AgentState,
        user_msg: str,
    ) -> dict[str, Any]:
        """Create plan from text description only."""
        return await self._create_plan_from_analysis(
            state, "", user_msg, []
        )

    async def _create_plan_from_analysis(
        self,
        state: AgentState,
        analysis: str,
        user_msg: str,
        attachments: list[dict],
    ) -> dict[str, Any]:
        """Use planner LLM to create structured task plan."""
        llm = self.get_llm("smart")
        if not llm:
            reply = "LLM 未配置。"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }

        context_parts = []
        if state.get("event_id"):
            context_parts.append(f"当前活动ID: {state['event_id']}")
        if analysis:
            context_parts.append(f"文件分析结果:\n{analysis}")
        if attachments:
            att_desc = ", ".join(
                f"{a.get('filename', '未知')}({a.get('type', '?')})"
                for a in attachments
            )
            context_parts.append(f"上传文件: {att_desc}")

        prompt_tpl = self._effective_prompt(PLANNER_SYSTEM)
        system = prompt_tpl.format(
            context="\n".join(context_parts) or "无上下文",
        )

        msgs = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg or "请分析并制定计划"},
        ]

        if analysis:
            msgs.insert(1, {
                "role": "user",
                "content": f"[文件分析结果]\n{analysis}",
            })

        try:
            response = await llm.ainvoke(msgs)
            raw = response.content
        except Exception as e:
            reply = f"规划失败：{e}"
            return {
                "messages": [AIMessage(content=reply)],
                "turn_output": reply,
            }

        # Extract plan JSON
        reply_text, plan_data = _extract_plan(raw)
        task_plan = []

        if plan_data:
            sub_tasks = plan_data.get("sub_tasks", [])
            for st in sub_tasks:
                task_plan.append({
                    "id": st.get("id", ""),
                    "plugin": st.get("plugin", ""),
                    "description": st.get("description", ""),
                    "status": "pending",
                    "result": None,
                })

            # Append plan summary to reply (user-friendly, no plugin names)
            _PLUGIN_LABEL = {
                "organizer": "🏢 创建活动",
                "seating": "🪑 排座布局",
                "badge": "🏷️ 铭牌设计",
                "checkin": "✅ 签到设置",
                "pagegen": "📱 页面生成",
            }
            if task_plan:
                reply_text += "\n\n📋 接下来我会依次完成：\n"
                for i, t in enumerate(task_plan, 1):
                    label = _PLUGIN_LABEL.get(
                        t["plugin"], t["description"]
                    )
                    reply_text += f"  {i}. {label}\n"
                reply_text += (
                    "\n说「开始」我会自动处理，"
                    "或者你可以先修改计划。"
                )

            # If there are questions, add them
            questions = plan_data.get("questions", [])
            if questions:
                reply_text += "\n\n❓ 需要确认：\n"
                for q in questions:
                    reply_text += f"  · {q}\n"

        result: dict[str, Any] = {
            "messages": [AIMessage(content=reply_text)],
            "turn_output": reply_text,
        }
        if task_plan:
            result["task_plan"] = task_plan
            # Quick reply buttons for plan confirmation
            qr = [
                {"label": "▶️ 开始执行", "value": "开始执行", "style": "primary"},
            ]
            if questions:
                qr.append({"label": "修改计划", "value": "我想修改计划", "style": "default"})
            result["quick_replies"] = qr

        # Store structured event_info as event_draft for organizer
        if plan_data and plan_data.get("event_info"):
            result["event_draft"] = plan_data["event_info"]

        return result


def _extract_plan(text: str) -> tuple[str, dict | None]:
    """Extract plan JSON from LLM response."""
    pattern = r'```plan\s*\n?(.*?)\n?```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        clean = text[:match.start()].strip()
        try:
            plan = json.loads(match.group(1).strip())
            return clean, plan
        except json.JSONDecodeError:
            return text, None
    return text, None
