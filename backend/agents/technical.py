"""A/S (after-service) agent."""
import demo_state
from i18n import t


def _resolved_order(state: dict, inp: dict) -> tuple[str, str]:
    oid = inp.get("order_id") or state.get("recent_order_id") or state["customer_id"]
    oat = state.get("recent_order_at") or t("label.unknown")
    return oid, oat


def _report_defect(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    description = inp.get("description") or t("as.report.description_default")
    tier = state["customer_tier"]
    tone = state.get("request_tone", "normal")

    ticket_id = f"AS-{oid[-4:]}-{abs(hash(description)) % 10000:04d}"
    priority = t("as.priority.urgent") if tier == "vip" or tone == "urgent" else t("as.priority.normal")
    return t(
        "as.report.done",
        ticket=ticket_id,
        priority=priority,
        oid=oid,
        oat=oat,
        description=description,
    )


def _check_warranty(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    if state["order_status"] == "refund_requested":
        return t("as.warranty.refund_requested", oid=oid, oat=oat)
    return t("as.warranty.normal", oid=oid, oat=oat)


def build_afterservice_assistant() -> dict:
    return {
        "id": "Assistant_AfterServiceAssistant",
        "name": t("agent.afterservice.name"),
        "description": """Call this if:
        - Customer reports a defective, broken, or damaged product
        - Customer wants to check warranty coverage or status
        - Customer needs product repair or replacement due to a defect
        DO NOT CALL THIS IF:
        - Customer wants a refund for a non-defective item (route to refund agent)
        - Customer asks about delivery status""",
        "system_message": t("agent.afterservice.system_message"),
        "tools": [
            {
                "name": "report_defect",
                "description": t("agent.afterservice.tool.report_defect.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": t("agent.afterservice.tool.report_defect.param.order_id")},
                        "description": {"type": "string", "description": t("agent.afterservice.tool.report_defect.param.description")},
                    },
                },
                "returns": _report_defect,
            },
            {
                "name": "check_warranty",
                "description": t("agent.afterservice.tool.check_warranty.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": t("agent.afterservice.tool.check_warranty.param.order_id")},
                    },
                },
                "returns": _check_warranty,
            },
        ],
    }
