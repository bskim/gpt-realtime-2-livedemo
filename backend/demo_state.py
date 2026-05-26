"""
Module-level singleton for demo injection state.
Tool functions import get() to read current values at call time.
"""

_state: dict = {
    "customer_id":       "CUST-001",
    "customer_tier":     "regular",          # vip | regular | problem | urgent
    "order_status":      "normal",           # normal | delayed | lost | refund_requested
    "workflow_resolved": True,               # False → UI shows RT-2 Fallback indicator
    "inquiry_type":      "simple",           # simple | complex | emotional | ambiguous
    "has_coupon":        False,
}

# Scenario presets (S1~S4) for CSaaS voice escalation demo
PRESETS = {
    "S1": {
        "label":             "S1 단순 FAQ",
        "customer_tier":     "regular",
        "order_status":      "normal",
        "workflow_resolved": True,
        "inquiry_type":      "simple",
        "has_coupon":        False,
    },
    "S2": {
        "label":             "S2 복합 의도",
        "customer_tier":     "vip",
        "order_status":      "normal",
        "workflow_resolved": False,
        "inquiry_type":      "complex",
        "has_coupon":        True,
    },
    "S3": {
        "label":             "S3 불만 고객",
        "customer_tier":     "problem",
        "order_status":      "delayed",
        "workflow_resolved": False,
        "inquiry_type":      "emotional",
        "has_coupon":        False,
    },
    "S4": {
        "label":             "S4 모호 요청",
        "customer_tier":     "regular",
        "order_status":      "refund_requested",
        "workflow_resolved": False,
        "inquiry_type":      "ambiguous",
        "has_coupon":        False,
    },
}


def get() -> dict:
    return _state.copy()


def update(payload: dict) -> None:
    _state.update(payload)


def apply_preset(preset_id: str) -> dict:
    preset = PRESETS.get(preset_id)
    if preset:
        update({k: v for k, v in preset.items() if k != "label"})
    return get()
