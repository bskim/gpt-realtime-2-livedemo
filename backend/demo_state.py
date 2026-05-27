"""
Module-level singleton for demo injection state.
Tool functions import get() to read current values at call time.
"""

DEFAULT_STATE: dict = {
    "customer_id":       "CUST-001",
    "recent_order_id":   "ORD-20260527-1001",
    "recent_order_at":   "2026-05-25 14:20 KST",
    "repeat_count":      0,
    "seller_fault":      False,
    "order_status_history": [],
    "customer_tier":     "regular",          # vip | regular
    "request_tone":      "normal",           # normal | urgent | complaint
    "order_status":      "normal",           # normal | delayed | lost | refund_requested
    "workflow_resolved": True,               # False → UI shows RT-2 Fallback indicator
    "inquiry_type":      "simple",           # simple | complex | ambiguous
    "has_coupon":        False,
    "active_preset":     None,
}

_state: dict = DEFAULT_STATE.copy()

# Scenario presets (S1~S4) for CSaaS voice escalation demo
PRESETS = {
    "S1": {
        "label":             "S1 단순 FAQ",
        "customer_tier":     "regular",
        "request_tone":      "normal",
        "recent_order_id":   "ORD-S1-1001",
        "recent_order_at":   "2026-05-25 10:10 KST",
        "order_status":      "normal",
        "workflow_resolved": True,
        "inquiry_type":      "simple",
        "has_coupon":        False,
        "repeat_count":      0,
        "seller_fault":      False,
        "order_status_history": [],
    },
    "S2": {
        "label":             "S2 복합 의도",
        "customer_tier":     "vip",
        "request_tone":      "urgent",
        "recent_order_id":   "ORD-S2-2207",
        "recent_order_at":   "2026-05-23 16:45 KST",
        "order_status":      "normal",
        "workflow_resolved": False,
        "inquiry_type":      "complex",
        "has_coupon":        True,
        "repeat_count":      0,
        "seller_fault":      False,
        "order_status_history": [],
    },
    "S3": {
        "label":             "S3 불만 고객",
        "customer_tier":     "regular",
        "request_tone":      "complaint",
        "recent_order_id":   "ORD-S3-3304",
        "recent_order_at":   "2026-05-19 09:35 KST",
        "order_status":      "delayed",
        "workflow_resolved": False,
        "inquiry_type":      "simple",
        "has_coupon":        False,
        "repeat_count":      2,
        "seller_fault":      True,
        "order_status_history": ["배송준비", "품절취소", "재주문", "배송지연"],
    },
    "S4": {
        "label":             "S4 모호 요청",
        "customer_tier":     "regular",
        "request_tone":      "normal",
        "recent_order_id":   "ORD-S4-4412",
        "recent_order_at":   "2026-05-21 11:50 KST",
        "order_status":      "refund_requested",
        "workflow_resolved": False,
        "inquiry_type":      "ambiguous",
        "has_coupon":        False,
        "repeat_count":      1,
        "seller_fault":      False,
        "order_status_history": ["배송준비", "취소요청"],
    },
}


def get() -> dict:
    return _state.copy()


def update(payload: dict) -> None:
    scenario_keys = {
        "customer_tier",
        "request_tone",
        "order_status",
        "workflow_resolved",
        "inquiry_type",
        "has_coupon",
        "recent_order_id",
        "recent_order_at",
        "repeat_count",
        "seller_fault",
        "order_status_history",
    }
    if any(k in payload for k in scenario_keys):
        _state["active_preset"] = None
    _state.update(payload)


def apply_preset(preset_id: str) -> dict:
    preset = PRESETS.get(preset_id)
    if preset:
        _state.update({k: v for k, v in preset.items() if k != "label"})
        _state["active_preset"] = preset_id
    return get()


def is_default_state(state: dict) -> bool:
    return all(state.get(k) == v for k, v in DEFAULT_STATE.items())
