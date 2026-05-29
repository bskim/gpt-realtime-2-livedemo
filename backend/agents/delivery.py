"""Delivery management agent."""
from datetime import datetime

import demo_state
from i18n import t


def _resolved_order(state: dict, inp: dict) -> tuple[str, str]:
    oid = inp.get("order_id") or state.get("recent_order_id") or state["customer_id"]
    oat = state.get("recent_order_at") or t("label.unknown")
    return oid, oat


def _meta(oid: str, oat: str) -> str:
    return t("order.label.order_meta", oid=oid, oat=oat)


def _days_since_order(order_at: str) -> int | None:
    # Expected demo format: "YYYY-MM-DD HH:mm KST"
    try:
        dt = datetime.strptime(order_at.replace(" KST", ""), "%Y-%m-%d %H:%M")
    except Exception:
        return None
    return max((datetime.now() - dt).days, 0)


def _lookup_delivery(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    status = state["order_status"]
    tier = state["customer_tier"]
    days_since = _days_since_order(oat)
    auto_comp = days_since is not None and days_since >= 3
    meta = _meta(oid, oat)

    if auto_comp:
        return t("delivery.lookup.auto_comp", meta=meta, days=days_since)

    if status == "normal":
        eta = t("delivery.eta.normal_vip") if tier == "vip" else t("delivery.eta.normal_regular")
        return t("delivery.lookup.normal", meta=meta, eta=eta)
    if status == "delayed":
        return t("delivery.lookup.delayed", meta=meta)
    if status == "lost":
        return t("delivery.lookup.lost", meta=meta)
    return t("delivery.lookup.unknown", meta=meta)


def _update_address(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    new_addr = str(inp.get("new_address", "")).strip()
    customer_confirmed = bool(inp.get("customer_confirmed", False))
    status = state["order_status"]
    meta = _meta(oid, oat)

    if not new_addr or len(new_addr) < 5:
        return t("delivery.address.need_input", meta=meta)
    if not customer_confirmed:
        return t("delivery.address.need_confirm", meta=meta, addr=new_addr)
    if status == "delayed":
        return t("delivery.address.delayed", meta=meta, addr=new_addr)
    if status == "lost":
        return t("delivery.address.lost", meta=meta)
    return t("delivery.address.normal", meta=meta, addr=new_addr)


def build_delivery_assistant() -> dict:
    return {
        "id": "Assistant_DeliveryAssistant",
        "name": t("agent.delivery.name"),
        "description": """Call this if:
        - Customer asks about delivery status or tracking
        - Customer wants to change delivery address
        - Customer reports delayed or missing delivery
        DO NOT CALL THIS IF:
        - Customer asks about order contents or order cancellation
        - Customer asks about refunds""",
        "system_message": t("agent.delivery.system_message"),
        "tools": [
            {
                "name": "lookup_delivery",
                "description": t("agent.delivery.tool.lookup_delivery.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": t("agent.delivery.tool.lookup_delivery.param.order_id")},
                    },
                },
                "returns": _lookup_delivery,
            },
            {
                "name": "update_address",
                "description": t("agent.delivery.tool.update_address.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": t("agent.delivery.tool.update_address.param.order_id")},
                        "new_address": {"type": "string", "description": t("agent.delivery.tool.update_address.param.new_address")},
                        "customer_confirmed": {
                            "type": "boolean",
                            "description": t("agent.delivery.tool.update_address.param.customer_confirmed"),
                        },
                    },
                },
                "returns": _update_address,
            },
        ],
    }
