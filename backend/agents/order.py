"""Order management agent."""
import demo_state
from i18n import t


def _resolved_order(state: dict, inp: dict) -> tuple[str, str]:
    oid = inp.get("order_id") or state.get("recent_order_id") or state["customer_id"]
    oat = state.get("recent_order_at") or t("label.unknown")
    return oid, oat


def _meta(oid: str, oat: str) -> str:
    return t("order.label.order_meta", oid=oid, oat=oat)


def _lookup_order(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    status = state["order_status"]
    tier = state["customer_tier"]
    meta = _meta(oid, oat)

    if status == "normal":
        eta = t("order.eta.normal_vip") if tier == "vip" else t("order.eta.normal_regular")
        return t("order.lookup.normal", meta=meta, eta=eta)
    if status == "delayed":
        return t("order.lookup.delayed", meta=meta)
    if status == "lost":
        return t("order.lookup.lost", meta=meta)
    if status == "refund_requested":
        return t("order.lookup.refund_requested", meta=meta)
    return t("order.lookup.unknown", meta=meta)


def _cancel_order(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    meta = _meta(oid, oat)
    if state["order_status"] == "refund_requested":
        return t("order.cancel.already_refund", meta=meta)
    return t("order.cancel.done", meta=meta)


def build_order_assistant() -> dict:
    return {
        "id": "Assistant_OrderAssistant",
        "name": t("agent.order.name"),
        "description": """Call this if:
        - Customer wants to check order status
        - Customer wants to change or cancel an order
        - Customer asks about their purchase
        DO NOT CALL THIS IF:
        - Customer asks about delivery address or shipping status
        - Customer asks about refunds or exchanges""",
        "system_message": t("agent.order.system_message"),
        "tools": [
            {
                "name": "lookup_order",
                "description": t("agent.order.tool.lookup_order.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": t("agent.order.tool.lookup_order.param.order_id"),
                        },
                    },
                },
                "returns": _lookup_order,
            },
            {
                "name": "cancel_order",
                "description": t("agent.order.tool.cancel_order.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": t("agent.order.tool.cancel_order.param.order_id")},
                        "reason": {"type": "string", "description": t("agent.order.tool.cancel_order.param.reason")},
                    },
                },
                "returns": _cancel_order,
            },
        ],
    }
