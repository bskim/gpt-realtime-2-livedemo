"""Membership / points agent."""
import demo_state
from i18n import t


def _check_points(inp: dict) -> str:
    state = demo_state.get()
    cid = inp.get("customer_id", state["customer_id"])
    tier = state["customer_tier"]
    key = f"membership.points.{tier}" if tier in ("vip", "regular") else "membership.points.unknown"
    return t(key, cid=cid)


def _register_membership(inp: dict) -> str:
    state = demo_state.get()
    cid = inp.get("customer_id", state["customer_id"])
    plan = inp.get("membership_type", "STANDARD").upper()
    if plan in ("VIP", "PREMIUM", "STANDARD"):
        benefits = t(f"membership.plan.{plan}")
    else:
        benefits = t("membership.plan.unknown")
    return t("membership.register.done", cid=cid, plan=plan, benefits=benefits)


def build_membership_assistant() -> dict:
    return {
        "id": "Assistant_MembershipAssistant",
        "name": t("agent.membership.name"),
        "description": """Call this if:
        - Customer asks about their points balance or expiry
        - Customer wants to join or upgrade their membership plan
        - Customer asks about membership tier benefits
        DO NOT CALL THIS IF:
        - Customer asks about a specific order, delivery, or refund
        - Customer wants to apply a coupon to an order (route to refund agent)""",
        "system_message": t("agent.membership.system_message"),
        "tools": [
            {
                "name": "check_points",
                "description": t("agent.membership.tool.check_points.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": t("agent.membership.tool.check_points.param.customer_id")},
                    },
                },
                "returns": _check_points,
            },
            {
                "name": "register_membership",
                "description": t("agent.membership.tool.register_membership.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": t("agent.membership.tool.register_membership.param.customer_id")},
                        "membership_type": {
                            "type": "string",
                            "description": t("agent.membership.tool.register_membership.param.membership_type"),
                        },
                    },
                },
                "returns": _register_membership,
            },
        ],
    }
