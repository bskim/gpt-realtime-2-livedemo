import logging

logger = logging.getLogger(__name__)

GLOBAL_AGENT_RULES = """

## 공통 운영 규칙
- 고객이 상담원 연결/재연락/담당자 연락을 요청하면, 추가 대기 멘트를 반복하지 말고 같은 턴에서 즉시 `request_human_followup` function을 호출하세요.
- `request_human_followup` 결과를 전달할 때는 다른 번호 수신이 필요한지만 간단히 확인하세요.
- 배송지/연락처/개인정보 변경 요청은 사용자가 새 값을 직접 말하고 명시적으로 확인하기 전까지 함수 호출로 확정 처리하지 마세요.
- 사용자가 제공하지 않은 주소/번호를 임의로 추정하거나 예시값으로 입력해 처리하지 마세요.
- 보상/추가보상/쿠폰 증액 요청은 우선 현재 에이전트의 보상 정책 처리(또는 환불/보상 에이전트 전환)를 먼저 수행하세요.
- 사용자가 명시적으로 상담원 연결/담당자 연락을 요구한 경우에만 `request_human_followup`를 호출하세요. 단순 보상 문의만으로는 먼저 호출하지 마세요.
"""


class AssistantService:
    def __init__(self, language: str = "Korean"):
        self.language = language
        self.agents: dict = {}

    def register_agent(self, agent: dict) -> None:
        agent = dict(agent)
        agent["system_message"] = agent["system_message"].format(language=self.language)
        agent["system_message"] += GLOBAL_AGENT_RULES
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
        root_agent["system_message"] = root_agent["system_message"].format(
            language=self.language
        )
        root_agent["system_message"] += GLOBAL_AGENT_RULES
        self._attach_human_followup_tool(root_agent)
        self.agents["root"] = self.agents[root_agent["id"]] = root_agent

    def _attach_human_followup_tool(self, agent: dict) -> None:
        if any(t.get("name") == "request_human_followup" for t in agent.get("tools", [])):
            return

        def _request_human_followup(inp: dict) -> str:
            callback_phone = (inp.get("callback_phone") or "").strip()
            issue_summary = (inp.get("issue_summary") or "현재 상담 내용").strip()

            if callback_phone:
                return (
                    "바로 연결은 어렵습니다. 상담 내용은 안전하게 기록되어 확인 후 상담원이 순차적으로 연락드리거나 문자로 안내드릴 예정입니다. "
                    f"요청하신 연락처({callback_phone})로 접수했고, 접수 사유는 '{issue_summary}'입니다. "
                    "불편 사항을 즉시 해결해드리지 못해 죄송합니다."
                )

            return (
                "바로 연결은 어렵습니다. 상담 내용은 안전하게 기록되어 확인 후 상담원이 순차적으로 연락드리거나 문자로 안내드릴 예정입니다. "
                "고객 프로파일에 있는 전화번호로 연락드릴 예정인데, 혹시 다른 번호로 연락받아야 하신다면 말씀해 주세요. "
                "불편 사항을 즉시 해결해드리지 못해 죄송합니다."
            )

        agent.setdefault("tools", []).append(
            {
                "name": "request_human_followup",
                "description": "고객이 상담원 연결/재연락을 요청할 때 연락 접수를 진행합니다. callback_phone이 있으면 해당 번호로 접수합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "callback_phone": {"type": "string", "description": "고객이 요청한 회신 전화번호(선택)"},
                        "issue_summary": {"type": "string", "description": "현재 상담 요약"},
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
