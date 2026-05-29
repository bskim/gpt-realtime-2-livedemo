"""Refund / exchange agent."""
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
    try:
        dt = datetime.strptime(order_at.replace(" KST", ""), "%Y-%m-%d %H:%M")
    except Exception:
        return None
    return max((datetime.now() - dt).days, 0)


# Locale-independent semantic keywords. Refunds branch on intent, not surface text,
# so we look for both KO and EN markers in the customer's reason.
_REPEAT_KEYWORDS = ("반복", "재차", "계속", "repeated", "again", "품절", "취소", "cancel")
_HISTORY_KEYWORDS = ("delayed", "cancelled", "cancel", "품절", "취소", "배송준비", "preparing")
_SEVERE_KEYWORDS = ("2주", "14일", "14 days", "two weeks", "2 weeks")
_HISTORY_SEVERE = ("14", "2주", "two weeks")
_DAMAGE_KEYWORDS = ("파손", "깨", "불량", "손상", "broken", "damaged", "defect")
_EXTRA_COMP_KEYWORDS = ("보상", "쿠폰", "compensation", "coupon", "credit")
_DELAY_KEYWORDS = ("지연", "늦", "delay", "late")


def _process_refund(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    reason = inp.get("reason") or t("human_followup.summary_default")
    reason_lower = str(reason).lower()
    tier = state["customer_tier"]
    status = state["order_status"]
    days_since = _days_since_order(oat)
    meta = _meta(oid, oat)

    repeat_count = inp.get("repeat_count")
    if not isinstance(repeat_count, int):
        try:
            repeat_count = int(repeat_count) if repeat_count is not None else 0
        except Exception:
            repeat_count = 0
    seller_fault = bool(inp.get("seller_fault", False))
    history = inp.get("order_status_history")
    history_text = " ".join(str(x).lower() for x in history) if isinstance(history, list) else ""

    auto_comp = days_since is not None and days_since >= 3
    repeated_issue = (
        repeat_count >= 2
        or seller_fault
        or any(k in reason_lower for k in _REPEAT_KEYWORDS)
        or any(k in history_text for k in _HISTORY_KEYWORDS)
    )
    severe_delay = (
        (days_since is not None and days_since >= 14)
        or any(k in reason_lower for k in _SEVERE_KEYWORDS)
        or any(k in history_text for k in _HISTORY_SEVERE)
    )
    damage_signal = any(k in reason_lower for k in _DAMAGE_KEYWORDS)
    asks_extra_comp = any(k in reason_lower for k in _EXTRA_COMP_KEYWORDS)
    vip_discretionary_comp = tier == "vip" and (
        severe_delay or repeated_issue or damage_signal or status == "lost" or asks_extra_comp
    )
    regular_discretionary_comp = tier == "regular" and seller_fault and repeated_issue

    if vip_discretionary_comp:
        elapsed = (
            t("refund.elapsed.with_days", days=days_since)
            if days_since is not None
            else t("refund.elapsed.long_repeat")
        )
        repeat_notice = (
            t("refund.repeat_notice.with_count", count=repeat_count)
            if repeat_count >= 2
            else t("refund.repeat_notice.vip_generic")
        )
        return t("refund.vip_discretionary", meta=meta, reason=reason, repeat_notice=repeat_notice, elapsed=elapsed)

    if regular_discretionary_comp:
        elapsed = (
            t("refund.elapsed.with_days", days=days_since)
            if days_since is not None
            else t("refund.elapsed.repeat")
        )
        repeat_notice = (
            t("refund.repeat_notice.with_count", count=repeat_count)
            if repeat_count >= 2
            else t("refund.repeat_notice.regular_generic")
        )
        return t("refund.regular_discretionary", meta=meta, reason=reason, repeat_notice=repeat_notice, elapsed=elapsed)

    if tier == "vip":
        return t("refund.vip_immediate", meta=meta, reason=reason)
    if status == "lost":
        return t("refund.lost", meta=meta)
    if auto_comp or status == "delayed" or any(k in reason_lower for k in _DELAY_KEYWORDS):
        elapsed = (
            t("refund.elapsed.with_days", days=days_since)
            if days_since is not None
            else t("refund.elapsed.delay_default")
        )
        return t("refund.delayed", meta=meta, reason=reason, elapsed=elapsed)
    return t("refund.default", meta=meta, reason=reason)


def _apply_coupon(inp: dict) -> str:
    state = demo_state.get()
    code = inp.get("coupon_code", "")
    oid, oat = _resolved_order(state, inp)
    meta = _meta(oid, oat)
    if not state["has_coupon"]:
        return t("refund.coupon.invalid", meta=meta, code=code)
    return t("refund.coupon.applied", meta=meta, code=code)


def build_refund_assistant() -> dict:
    return {
        "id": "Assistant_RefundAssistant",
        "name": t("agent.refund.name"),
        "description": """Call this if:
        - Customer wants to request a refund or exchange
        - Customer wants to apply a coupon or discount
        - Customer has a complaint about a product
        DO NOT CALL THIS IF:
        - Customer asks about delivery status
        - Customer asks about order status only""",
        "system_message": t("agent.refund.system_message"),
        "tools": [
            {
                "name": "process_refund",
                "description": t("agent.refund.tool.process_refund.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": t("agent.refund.tool.process_refund.param.order_id")},
                        "reason": {"type": "string", "description": t("agent.refund.tool.process_refund.param.reason")},
                        "type": {"type": "string", "description": t("agent.refund.tool.process_refund.param.type")},
                        "repeat_count": {
                            "type": "integer",
                            "description": t("agent.refund.tool.process_refund.param.repeat_count"),
                        },
                        "seller_fault": {
                            "type": "boolean",
                            "description": t("agent.refund.tool.process_refund.param.seller_fault"),
                        },
                        "order_status_history": {
                            "type": "array",
                            "description": t("agent.refund.tool.process_refund.param.order_status_history"),
                            "items": {"type": "string"},
                        },
                    },
                },
                "returns": _process_refund,
            },
            {
                "name": "apply_coupon",
                "description": t("agent.refund.tool.apply_coupon.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": t("agent.refund.tool.apply_coupon.param.order_id")},
                        "coupon_code": {"type": "string", "description": t("agent.refund.tool.apply_coupon.param.coupon_code")},
                    },
                },
                "returns": _apply_coupon,
            },
        ],
    }
