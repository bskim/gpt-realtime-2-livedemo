"""
Module-level singleton for demo injection state.
Tool functions import get() to read current values at call time.
"""
from i18n import t

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

# Scenario presets (S1~S4) for CSaaS voice escalation demo.
# label과 order_status_history 는 locale별 값을 렌더링 시점에 t() 로 해석한다.
PRESETS = {
    "S1": {
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
    },
    "S2": {
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
    },
    "S3": {
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
    },
    "S4": {
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
    },
}

# active_preset이 설정되면 order_status_history 는 locale에서 가져온다.
_PRESET_HISTORY_KEYS = {"S3", "S4"}


def preset_label(preset_id: str) -> str:
    return t(f"preset.{preset_id}.label")


def preset_labels() -> dict[str, str]:
    return {pid: preset_label(pid) for pid in PRESETS}


def _preset_history(preset_id: str) -> list:
    value = t(f"preset.{preset_id}.history")
    return value if isinstance(value, list) else []


def get() -> dict:
    snapshot = _state.copy()
    pid = snapshot.get("active_preset")
    if pid in _PRESET_HISTORY_KEYS:
        snapshot["order_status_history"] = list(_preset_history(pid))
    return snapshot


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
        _state.update(preset)
        _state["active_preset"] = preset_id
        if preset_id in _PRESET_HISTORY_KEYS:
            _state["order_status_history"] = list(_preset_history(preset_id))
        else:
            _state["order_status_history"] = []
    return get()


def is_default_state(state: dict) -> bool:
    return all(state.get(k) == v for k, v in DEFAULT_STATE.items())
