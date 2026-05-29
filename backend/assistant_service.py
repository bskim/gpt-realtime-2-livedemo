import logging

from i18n import t

logger = logging.getLogger(__name__)


def _global_agent_rules() -> str:
    return t("agent.global_rules")


class AssistantService:
    def __init__(self, language: str = "Korean"):
        self.language = language
        self.agents: dict = {}

    def register_agent(self, agent: dict) -> None:
        agent = dict(agent)
        try:
            agent["system_message"] = agent["system_message"].format(language=self.language)
        except (KeyError, IndexError):
            pass
        agent["system_message"] += _global_agent_rules()
        self._attach_human_followup_tool(agent)
        self.agents[agent["id"]] = agent

    def register_root_agent(self, root_agent: dict) -> None:
        root_agent = dict(root_agent)
        for agent_data in self.agents.values():
            agent_data["tools"].append(
                {
                    "name": root_agent["id"],
                    "description": (
                        f"If the customer asks any question that is outside of "
                        f"your work scope, use this to switch back to {root_agent['id']}."
                    ),
                    "parameters": {"type": "object", "properties": {}},
                    "returns": lambda _: root_agent["id"],
                }
            )
        try:
            root_agent["system_message"] = root_agent["system_message"].format(
                language=self.language
            )
        except (KeyError, IndexError):
            pass
        root_agent["system_message"] += _global_agent_rules()
        self._attach_human_followup_tool(root_agent)
        self.agents["root"] = self.agents[root_agent["id"]] = root_agent

    def _attach_human_followup_tool(self, agent: dict) -> None:
        if any(t.get("name") == "request_human_followup" for t in agent.get("tools", [])):
            return

        def _request_human_followup(inp: dict) -> str:
            callback_phone = (inp.get("callback_phone") or "").strip()
            issue_summary = (inp.get("issue_summary") or t("human_followup.summary_default")).strip()

            if callback_phone:
                return t("human_followup.with_phone", phone=callback_phone, summary=issue_summary)
            return t("human_followup.without_phone")

        agent.setdefault("tools", []).append(
            {
                "name": "request_human_followup",
                "description": t("human_followup.tool.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "callback_phone": {"type": "string", "description": t("human_followup.param.callback_phone")},
                        "issue_summary": {"type": "string", "description": t("human_followup.param.issue_summary")},
                    },
                },
                "returns": _request_human_followup,
            }
        )

    def get_agent(self, id: str) -> dict | None:
        return self.agents.get(id)

    def get_tools_for_session(self, agent_id: str, include_human_followup: bool = True) -> list[dict]:
        agent = self.agents[agent_id]
        own_tools = agent["tools"]
        if not include_human_followup:
            own_tools = [
                tool for tool in own_tools
                if tool.get("name") != "request_human_followup"
            ]

        other_agents_as_tools = [
            {
                "type": "function",
                "name": a["id"],
                "description": a["description"],
                "parameters": {"type": "object", "properties": {}},
            }
            for aid, a in self.agents.items()
            if aid != agent_id and aid != "root"  # dedupe root alias
        ]

        own_tool_defs = [
            {
                "type": "function",
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            }
            for t in own_tools
        ]

        seen: set = set()
        result = []
        for t in own_tool_defs + other_agents_as_tools:
            if t["name"] not in seen:
                seen.add(t["name"])
                result.append(t)
        return result

    def find_tool(self, tool_name: str):
        """Return the tool dict (with 'returns') by name, searching all agents."""
        for agent_data in self.agents.values():
            for tool in agent_data["tools"]:
                if tool["name"] == tool_name:
                    return tool
        return None
